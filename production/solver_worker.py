#!/bin/env python3

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
import argparse
import multiprocessing.queues
import logging
import traceback
from io import StringIO
logger = logging.getLogger(__name__)

from production import db
from production import utils
from production import solver_interface
from production.pyjs_emulator.run import run_full as pyjs_run_full
from production.all_solvers import ALL_SOLVERS
from production.combiner import Combiner

Json = dict


@dataclass
class Result:
    '''Information about the trace that we want to write to the DB.'''
    status: str  # see db.py for explanation
    scent: str
    energy: Optional[int]
    trace: Optional[bytes]
    extra: Json


def put_trace(conn, problem_id: int, result: Result):
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
            problem_id, invocation_id, timestamp)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        ''',
        [result.scent, result.status, result.energy, trace_data, extra,
         problem_id, db.get_this_invocation_id(conn), time.time()])
    [trace_id] = cur.fetchone()
    logging.info(f'Recorded as trace/{trace_id}')


def solve(
        solver: solver_interface.Solver, name: str,
        src_data: Optional[bytes], tgt_data: Optional[bytes],
        pyjs_validate: bool = False) -> Result:

    # check again to simplify things for users
    if not solver.supports(solver_interface.ProblemType.from_name(name)):
        return Result(
            scent=solver.scent(), status='PASS', energy=None, trace=None,
            extra={})

    logging.info('Solving...')
    start = time.time()
    try:
        sr = solver.solve(name, src_model=src_data, tgt_model=tgt_data)
    except KeyboardInterrupt:
        raise
    except:
        exc = StringIO()
        traceback.print_exc(file=exc)
        sr = solver_interface.SolverResult(solver_interface.Fail(), extra=dict(tb=exc.getvalue()))
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
        er = pyjs_run_full(src_data, tgt_data, sr.trace_data)
        pyjs_time = time.time() - start
        logging.info(f'It took {pyjs_time}')

        if isinstance(solver, Combiner):
            # With the combiner we already know that the solution is correct
            # and what it's energy is supposed to be.
            # Maaaaybe, if this assertion never fails, we can
            # skip running pyjs to save time.
            assert er.energy == sr.extra['expected_energy'], (
                er.energy, sr.extra['expected_energy'])

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
    problem_id: int
    problem_name: str  # like 'FR042'
    src_data: Optional[bytes]
    tgt_data: Optional[bytes]


@dataclass
class OutputEntry:
    worker_index: int
    problem_id: int
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
        logging.info(f'Solving problem/{input_entry.problem_id}...')
        result = solve(
            input_entry.solver, input_entry.problem_name,
            input_entry.src_data, input_entry.tgt_data)
        logging.info(f'Done, energy={result.energy}')
        output_entry = OutputEntry(
            worker_index=index,
            problem_id=input_entry.problem_id,
            result=result)
        output_queue.put(output_entry)


def parse_args():
    cores = multiprocessing.cpu_count() or 1
    parser = argparse.ArgumentParser(prog='python -m production.solver_worker')
    # optional
    parser.add_argument('-j', '--jobs', metavar='N', help=f'number of worker threads (default: all {cores} cores)',
            type=int, default=cores)
    parser.add_argument('-r', '--max-size', metavar='R', help='Limit the size of the considered problems to at most R',
            type=int, default=999)
    parser.add_argument('-n', '--dry-run', help='Do not submit solutions to the database',
            action='store_true')
    # positional
    parser.add_argument('solver', help='solver to use', choices=ALL_SOLVERS.keys())
    parser.add_argument('solver_args', metavar='ARG', help='argument for the solver', nargs='*')
    return parser.parse_args()


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    args = parse_args()

    conn = db.get_conn()
    cur = conn.cursor()

    solver = ALL_SOLVERS[args.solver](args.solver_args)
    logger.info(f'Solver scent: {solver.scent()!r}')

    cur.execute('''
        SELECT problems.id, problems.name
        FROM problems
        LEFT OUTER JOIN (
            SELECT problem_id AS trace_problem_id FROM traces WHERE scent = %s
        ) AS my_traces
        ON trace_problem_id = problems.id
        WHERE ((problems.name LIKE 'F%%') OR (problems.name LIKE 'Z%%')) AND trace_problem_id IS NULL
          AND (problems.stats->>'R')::integer <= %s
        ''', [solver.scent(), args.max_size])

    problem_ids = []
    for id, name in cur:
        if solver.supports(solver_interface.ProblemType.from_name(name)):
            problem_ids.append(id)
    logging.info(f'{len(problem_ids)} problems to solve: {problem_ids}')

    # to reduce collisions when multiple solvers are working in parallel
    random.shuffle(problem_ids)
    #problem_ids.sort(reverse=True)

    num_workers = args.jobs
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
        if available_workers and problem_ids:
            problem_id = problem_ids.pop()
            cur.execute(
                'SELECT COUNT(*) FROM traces WHERE problem_id = %s AND scent = %s',
                [problem_id, solver.scent()])
            [num_attempts] = cur.fetchone()
            if num_attempts == 0:
                cur.execute(
                    'SELECT name, src_data, tgt_data FROM problems WHERE id = %s',
                    [problem_id])
                [problem_name, src_data, tgt_data] = cur.fetchone()
                if src_data is not None:
                    src_data = zlib.decompress(src_data)
                if tgt_data is not None:
                    tgt_data = zlib.decompress(tgt_data)
                worker_index = available_workers.pop()
                input_queues[worker_index].put(InputEntry(
                    solver=solver,
                    problem_id=problem_id,
                    problem_name=problem_name,
                    src_data=src_data,
                    tgt_data=tgt_data))
                logging.info(f'problem/{problem_id} goes to worker {worker_index}')
            else:
                logging.info(f'Skipping problem/{problem_id}')
            logging.info(f'{len(problem_ids)} remaining')
        else:
            if len(available_workers) == num_workers:
                break
            output_entry = output_queue.get()
            assert output_entry.worker_index not in available_workers
            available_workers.add(output_entry.worker_index)
            logging.info(
                f'Got trace for problem/{output_entry.problem_id}, '
                f'energy={output_entry.result.energy} '
                f'from worker {output_entry.worker_index}')
            if args.dry_run:
                logging.info(f'Skip saving because dry-run')
            else:
                put_trace(conn, output_entry.problem_id, output_entry.result)
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
