import logging
logger = logging.getLogger(__name__)
import random
import json
import time

from production import db


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    cars = {}
    logger.info('Pretending to scrape some cars...')
    for _ in range(10):
        name = random.choice('abcdefgh') + random.choice('qwerty')
        data = [random.randrange(10) for _ in range(random.randrange(5, 10))]
        logger.info(f'Found car {name!r} {data}')
        cars[name] = data

    conn = db.get_conn()
    cur = conn.cursor()
    for name, data in cars.items():
        cur.execute('''
            INSERT INTO cars(name, data, invocation_id, timestamp)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
            ''',
            [name, json.dumps(data), db.get_this_invocation_id(conn), time.time()])
        res = cur.fetchall()
        if res:
            [[car_id]] = res
            logger.info(f'Adding car/{car_id}')
        else:
            logger.info(f'Car {name!r} already exists')
        conn.commit()


if __name__ == '__main__':
    main()
