from importlib.util import find_spec
if __name__ == '__main__' and find_spec('hintcheck'):
    import hintcheck
    hintcheck.monkey_patch_named_tuple_constructors()

import sys
import random
import time
import json
import zlib
from typing import Optional, Any, List, Dict
from dataclasses import dataclass
import multiprocessing
import multiprocessing.queues
import logging
logger = logging.getLogger(__name__)

from production import db
from production import utils
from production import solver_interface
from production.pyjs_emulator.run import run as pyjs_run
from production.all_solvers import ALL_SOLVERS

Json = dict


@dataclass
class Result:
    '''Information about the trace that we want to write to the DB.'''
    status: str  # see db.py for explanation
    scent: str
    energy: Optional[int]
    trace: Optional[bytes]
    extra: Json


def put_trace(conn, model_id: int, result: Result):
    assert result.status in ('DONE', 'PASS', 'FAIL', 'CHECK_FAIL'), result.status

    if result.trace is not None:
        trace_data = zlib.compress(result.trace)
    else:
        trace_data = None
    extra = json.dumps(result.extra)

    cur = conn.cursor()
    cur.execute('''
        INSERT INTO traces(
            scent, status, energy, data, extra,
            model_id, invocation_id, timestamp)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        ''',
        [result.scent, result.status, result.energy, trace_data, extra,
         model_id, db.get_this_invocation_id(conn), time.time()])
    [trace_id] = cur.fetchone()
    logging.info(f'Recorded as trace/{trace_id}')


def solve(solver: solver_interface.Solver, name: str, model_data: bytes) -> Result:
    logging.info('Solving...')
    start = time.time()
    sr = solver.solve(name, model_data)
    solver_time = time.time() - start
    logging.info(f'It took {solver_time}')
    if isinstance(sr.trace_data, solver_interface.Pass):
        logging.info(f'Solver passed: {sr.extra}')
        return Result(
            scent=solver.scent(), status='PASS', energy=None, trace=None,
            extra=dict(solver=sr.extra, solver_time=solver_time))
    if isinstance(sr.trace_data, solver_interface.Fail):
        logging.info(f'Solver failed: {sr.extra}')
        return Result(
            scent=solver.scent(), status='FAIL', energy=None, trace=None,
            extra=dict(solver=sr.extra, solver_time=solver_time))
    elif isinstance(sr.trace_data, (bytes, bytearray)):
        logging.info('Checking with pyjs...')
        start = time.time()
        er = pyjs_run(model_data, sr.trace_data)
        pyjs_time = time.time() - start
        logging.info(f'It took {pyjs_time}')
        if er.energy is None:
            logging.info(f'Check failed: {er.extra}')
            return Result(
                scent=solver.scent(), status='CHECK_FAIL', energy=None, trace=sr.trace_data,
                extra=dict(
                    solver=sr.extra, pyjs=er.extra,
                    solver_time=solver_time, pyjs_time=pyjs_time))
        else:
            logging.info(f'Solution verified, energy={er.energy}')
            return Result(
                scent=solver.scent(), status='DONE', energy=er.energy, trace=sr.trace_data,
                extra=dict(
                    solver=sr.extra, pyjs=er.extra,
                    solver_time=solver_time, pyjs_time=pyjs_time))
    else:
        assert False, sr.energy


@dataclass
class InputEntry:
    solver: solver_interface.Solver
    model_id: int
    model_name: str  # like 'LA042'
    model_data: bytes


@dataclass
class OutputEntry:
    worker_index: int
    model_id: int
    result: Result


def work(
        index,
        log_path,
        input_queue: multiprocessing.queues.SimpleQueue,
        output_queue: multiprocessing.queues.SimpleQueue):
    logging.basicConfig(
        filename=log_path,
        filemode='w',
        level=logging.INFO,
        format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
    while True:
        input_entry = input_queue.get()
        if input_entry is None:
            logging.info('No more tasks.')
            break
        logging.info(f'Solving model/{input_entry.model_id}...')
        result = solve(input_entry.solver, input_entry.model_name, input_entry.model_data)
        logging.info(f'Done, energy={result.energy}')
        output_entry = OutputEntry(
            worker_index=index,
            model_id=input_entry.model_id,
            result=result)
        output_queue.put(output_entry)


def main():
    if len(sys.argv) < 2 :
        print('Usage:')
        print('    python -m production.solver_worker <solver> [<solver args>...]')
        print(f'where <solver> is one of {ALL_SOLVERS.keys()}')
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    conn = db.get_conn()
    cur = conn.cursor()

    solver = ALL_SOLVERS[sys.argv[1]](sys.argv[2:])
    logger.info(f'Solver scent: {solver.scent()!r}')

    cur.execute('''
        SELECT models.id
        FROM models
        LEFT OUTER JOIN (
            SELECT model_id AS trace_model_id FROM traces WHERE scent = %s
        ) AS my_traces
        ON trace_model_id = models.id
        WHERE trace_model_id IS NULL
        ''', [solver.scent()])

    model_ids = [id for [id] in cur]
    logging.info(f'Models to solve: {model_ids}')

    # to reduce collisions when multiple solvers are working in parallel
    random.shuffle(model_ids)
    #model_ids.sort(reverse=True)

    num_workers = multiprocessing.cpu_count()
    # num_workers = 1
    output_queue = multiprocessing.SimpleQueue()
    input_queues = [multiprocessing.SimpleQueue() for _ in range(num_workers)]
    workers = []
    for i, iq in enumerate(input_queues):
        log_path = utils.project_root() / 'outputs' / f'solver_worker_{i:02}.log'
        logging.info(f'Worker logging to {log_path}')
        w = multiprocessing.Process(target=work, args=(i, log_path, iq, output_queue))
        w.start()
    available_workers = set(range(num_workers))

    cur = conn.cursor()
    while True:
        if available_workers and model_ids:
            model_id = model_ids.pop()
            cur.execute(
                'SELECT COUNT(*) FROM traces WHERE model_id = %s AND scent = %s',
                [model_id, solver.scent()])
            [num_attempts] = cur.fetchone()
            if num_attempts == 0:
                cur.execute('SELECT name, data FROM models WHERE id = %s', [model_id])
                [model_name, model_data] = cur.fetchone()
                worker_index = available_workers.pop()
                input_queues[worker_index].put(InputEntry(
                    solver=solver,
                    model_id=model_id,
                    model_name=model_name,
                    model_data=zlib.decompress(model_data)))
                logging.info(f'model/{model_id} goes to worker {worker_index}')
            else:
                logging.info(f'Skipping model/{model_id}')
        else:
            if len(available_workers) == num_workers:
                break
            output_entry = output_queue.get()
            assert output_entry.worker_index not in available_workers
            available_workers.add(output_entry.worker_index)
            logging.info(
                f'Got trace for model/{output_entry.model_id}, '
                f'energy={output_entry.result.energy} '
                f'from worker {output_entry.worker_index}')
            put_trace(conn, output_entry.model_id, output_entry.result)
            conn.commit()

    logging.info('All done, joining workers...')
    for iq in input_queues:
        iq.put(None)
    for w in workers:
        join()


if __name__ == '__main__':
    if 'hintcheck' in globals():
        hintcheck.hintcheck_all_functions()
    main()
