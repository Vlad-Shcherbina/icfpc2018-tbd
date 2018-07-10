import random
import time
import json
from typing import Optional, Any, List, Dict
from dataclasses import dataclass
import multiprocessing
import multiprocessing.queues
import logging
logger = logging.getLogger(__name__)

from production import db
from production import utils


Json = Any


@dataclass
class Attempt:
    '''Information about the fuel that we read from the DB.'''
    score: Optional[float]
    invocation: Json


CarId = int

def get_attempts(conn, *, car_id: Optional[CarId] = None) -> Dict[CarId, List[Attempt]]:
    query = '''
        SELECT
            cars.id, fuels.id, fuels.score, invocations.data
        FROM cars
        LEFT OUTER JOIN fuels
            ON fuels.car_id = cars.id
        LEFT OUTER JOIN invocations
            ON fuels.invocation_id = invocations.id
    '''
    args = []
    if car_id is not None:
        query += ' WHERE cars.id = %s'
        args.append(car_id)
    cur = conn.cursor()
    cur.execute(query, args)
    attempts_by_car_id = {}
    for car_id, fuel_id, fuel_score, inv_data in cur:
        attempts = attempts_by_car_id.setdefault(car_id, [])
        if fuel_id is not None:
            attempts.append(Attempt(score=fuel_score, invocation=inv_data))
    return attempts_by_car_id


@dataclass
class Result:
    '''Information about the fuel that we want to write to the DB.'''
    score: Optional[float]
    solution: Optional[Json]
    extra: Json


def put_fuel(conn, car_id, result):
    if result.solution is not None:
        fuel_data = json.dumps(result.solution)
    else:
        fuel_data = None
    extra = json.dumps(result.extra)

    cur = conn.cursor()
    cur.execute('''
        INSERT INTO fuels(score, data, extra, car_id, invocation_id, timestamp)
        VALUES(%s, %s, %s, %s, %s, %s)
        RETURNING id
        ''',
        [result.score, fuel_data, extra,
         car_id, db.get_this_invocation_id(conn), time.time()])
    [fuel_id] = cur.fetchone()
    logging.info(f'Recorded as fuel/{fuel_id}')


def solve(car_data: Json) -> Result:
    logging.info(f'Pretending to solve {car_data}...')
    t = random.randrange(10)
    time.sleep(t)

    if random.randrange(4) == 0:
        logging.info(f'Solver failed')
        return Result(
            score=None, solution=None, extra=dict(comment='whatever'))

    logging.info(f'Solver succeeded')
    return Result(
        score=random.randrange(100),
        solution=list(reversed(car_data)),
        extra=dict(it_took=t))


@dataclass
class InputEntry:
    car_id: int
    car_data: Json


@dataclass
class OutputEntry:
    worker_index: int
    car_id: int
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
        logging.info(f'Solving car/{input_entry.car_id}...')
        result = solve(input_entry.car_data)
        logging.info(f'Done, score={result.score}')
        output_entry = OutputEntry(
            worker_index=index,
            car_id=input_entry.car_id,
            result=result)
        output_queue.put(output_entry)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    conn = db.get_conn()
    attempts_by_car_id = get_attempts(conn)

    def want_solve(attempts):
        return not attempts

    car_ids = [
        car_id for car_id, attempts in attempts_by_car_id.items()
        if want_solve(attempts)]
    logging.info(f'Found {len(car_ids)} cars to solve')

    # to reduce collisions when multiple solvers are working in parallel
    random.shuffle(car_ids)

    num_workers = multiprocessing.cpu_count()
    output_queue = multiprocessing.SimpleQueue()
    input_queues = [multiprocessing.SimpleQueue() for _ in range(num_workers)]
    workers = []
    for i, iq in enumerate(input_queues):
        log_path = utils.project_root() / 'outputs' / f'solver_worker_{i:02}.log'
        logging.info(f'Worker logging to {log_path}')
        w = multiprocessing.Process(target=work, args=(i, log_path, iq, output_queue))
        w.start()
    available_workers = set(range(num_workers))

    while True:
        if available_workers and car_ids:
            car_id = car_ids.pop()
            attempts = get_attempts(conn, car_id=car_id)[car_id]
            if want_solve(attempts):
                cur = conn.cursor()
                cur.execute('SELECT data FROM cars WHERE id = %s', [car_id])
                [car_data] = cur.fetchone()
                worker_index = available_workers.pop()
                input_queues[worker_index].put(InputEntry(car_id=car_id, car_data=car_data))
                logging.info(f'car/{car_id} goes to worker {worker_index}')
            else:
                logging.info(f'Skipping car/{car_id}')
        else:
            if len(available_workers) == num_workers:
                break
            output_entry = output_queue.get()
            assert output_entry.worker_index not in available_workers
            available_workers.add(output_entry.worker_index)
            logging.info(
                f'Got fuel for car/{output_entry.car_id}, '
                f'score={output_entry.result.score} '
                f'from worker {output_entry.worker_index}')
            put_fuel(conn, output_entry.car_id, output_entry.result)
            conn.commit()

    logging.info('All done, joining workers...')
    for iq in input_queues:
        iq.put(None)
    for w in workers:
        join()


if __name__ == '__main__':
    main()
