from dataclasses import dataclass
import random
import json
import time
import signal
import logging
logger = logging.getLogger(__name__)

from production import db


@dataclass
class FuelInfo:
    id: int
    score: float
    has_successful_submission: bool = False


def submit(car_name, fuel_data):
    logging.info(f'Pretending to submit fuel for car {car_name!r}')
    time.sleep(1)
    if random.randrange(5) == 0:
        submission_data = None
        extra = dict(comment='rejected by the server')
    else:
        submission_data = dict(comment='whatever')
        extra = {}

    return submission_data, extra


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            cars.name,
            fuels.id,
            fuels.score,
            COUNT(fuel_submissions.id),
            COUNT(fuel_submissions.data)
        FROM fuels
        JOIN cars ON fuels.car_id = cars.id
        LEFT OUTER JOIN fuel_submissions
        ON fuel_submissions.fuel_id = fuels.id
        WHERE fuels.score IS NOT NULL
        GROUP BY cars.name, fuels.id
    ''')

    # For each car, take all fuels that don't have failed submissions,
    # and submit the one with the best score
    # (unless it already has a successful submission).

    fuels_by_car_name = {}
    for car_name, fuel_id, fuel_score, num_submissions, num_successful_submissions in cur:
        if num_submissions > 0 and num_successful_submissions == 0:
            continue  # failed submission
        fuels = fuels_by_car_name.setdefault(car_name, [])
        fuels.append(FuelInfo(
            id=fuel_id, score=fuel_score,
            has_successful_submission=bool(num_successful_submissions)))

    done = False
    def signal_handler(sig, frame):
        nonlocal done
        done = True
        logging.warning('Caught Ctrl-C, will finish current item and exit.')
        logging.warning('To abort immediately, hit Ctrl-C again.')
        signal.signal(signal.SIGINT, old_signal_handler)
    old_signal_handler = signal.signal(signal.SIGINT, signal_handler)

    for car_name, fuels in fuels_by_car_name.items():
        if done:
            break

        fuel = max(fuels, key=lambda f: f.score)
        if fuel.has_successful_submission:
            logging.info(f'Best fuel for car {car_name!r} already submitted')
            continue

        cur.execute('SELECT data FROM fuels WHERE id = %s', [fuel.id])
        [fuel_data] = cur.fetchone()

        submission_data, extra = submit(car_name, fuel_data)
        if submission_data is not None:
            submission_data = json.dumps(submission_data)
        extra = json.dumps(extra)
        cur.execute('''
            INSERT INTO fuel_submissions(
                data, extra, fuel_id, invocation_id, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            ''',
            [submission_data, extra, fuel.id, db.get_this_invocation_id(conn), time.time()])
        [submission_id] = cur.fetchone()
        logging.info(f'Submission recorded as fuel_sub/{submission_id}')
        conn.commit()


if __name__ == '__main__':
    main()
