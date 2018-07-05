import random
import time
import json
from typing import Optional, Any
from dataclasses import dataclass
import logging
logger = logging.getLogger(__name__)

from production import db


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

    for car_id in car_ids:
        cur.execute('''
            SELECT fuels.score, invocations.id
            FROM fuels
            JOIN invocations
            ON fuels.invocation_id = invocations.id
            WHERE fuels.car_id = %s
        ''', [car_id])
        attempts = cur.fetchall()
        if not want_solve(attempts):
            logging.info(f'Skipping car/{car_id}')
            continue
        logging.info(f'Solving car/{car_id}...')

        cur.execute('SELECT data FROM cars WHERE id = %s', [car_id])
        [car_data] = cur.fetchone()

        result = solve(car_data)
        logging.info(result)

        if result.solution is not None:
            fuel_data = json.dumps(result.solution)
        else:
            fuel_data = None
        extra = json.dumps(result.extra)

        cur.execute('''
            INSERT INTO fuels(score, data, extra, car_id, invocation_id, timestamp)
            VALUES(%s, %s, %s, %s, %s, %s)
            RETURNING id
            ''',
            [result.score, fuel_data, extra,
             car_id, db.get_this_invocation_id(conn), time.time()])
        [fuel_id] = cur.fetchone()
        conn.commit()
        logging.info(f'Recorded as fuel/{fuel_id}')


if __name__ == '__main__':
    main()
