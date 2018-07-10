import random
import time
import json
from typing import Optional, Any
from dataclasses import dataclass
import multiprocessing
import multiprocessing.queues
import logging
logger = logging.getLogger(__name__)

from production import db
from production import utils


Json = Any

@dataclass
class Result:
    score: Optional[float]
    solution: Optional[Json]
    extra: Json


def solve(car_data: Json) -> Result:
    t = random.randrange(10)
    time.sleep(t)

    if random.randrange(4) == 0:
        return Result(
            score=None, solution=None, extra=dict(comment='whatever'))

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
    cur = conn.cursor()
    cur.execute('''
        SELECT
            cars.id AS car_id, fuels.id, fuels.score, invocations.data
        FROM cars
        LEFT OUTER JOIN fuels
        ON fuels.car_id = cars.id
        LEFT OUTER JOIN invocations
        ON fuels.invocation_id = invocations.id
    ''')
    attempts_by_car_id = {}
    for car_id, fuel_id, fuel_score, inv_data in cur:
        attempts = attempts_by_car_id.setdefault(car_id, [])
        if fuel_id is None:
            continue
        attempts.append((fuel_score, inv_data))

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
            cur.execute('''
                SELECT fuels.score, invocations.id
                FROM fuels
                JOIN invocations
                ON fuels.invocation_id = invocations.id
                WHERE fuels.car_id = %s
            ''', [car_id])
            attempts = cur.fetchall()
            if want_solve(attempts):
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

            if output_entry.result.solution is not None:
                fuel_data = json.dumps(output_entry.result.solution)
            else:
                fuel_data = None
            extra = json.dumps(output_entry.result.extra)

            cur.execute('''
                INSERT INTO fuels(score, data, extra, car_id, invocation_id, timestamp)
                VALUES(%s, %s, %s, %s, %s, %s)
                RETURNING id
                ''',
                [output_entry.result.score, fuel_data, extra,
                output_entry.car_id, db.get_this_invocation_id(conn), time.time()])
            [fuel_id] = cur.fetchone()
            conn.commit()
            logging.info(f'Recorded as fuel/{fuel_id}')

    logging.info('All done, joining workers...')
    for iq in input_queues:
        iq.put(None)
    for w in workers:
        join()


if __name__ == '__main__':
    main()
