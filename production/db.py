import logging
logger = logging.getLogger(__name__)
import time

import psycopg2
import psycopg2.extras

from production.invocation import get_this_invocation


def get_conn():
    logger.info('Connecting to the db...')
    return psycopg2.connect(
        dbname='arst',
        host='35.205.226.98',
        user='postgres', password='kl3lzp9a83eeklxm9348lm')


def create_tables(conn):
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS invocations(
        id SERIAL PRIMARY KEY,
        data JSON NOT NULL
    );

    CREATE TABLE IF NOT EXISTS cars(
        id SERIAL PRIMARY KEY,

        -- how to identify a car to their server when submitting a fuel for it
        name TEXT NOT NULL UNIQUE,

        data JSON NOT NULL,

        invocation_id INTEGER NOT NULL REFERENCES invocations,
        timestamp DOUBLE PRECISION NOT NULL
    );
    ''')


_invocation = None
_invocation_id = None

def record_this_invocation(conn, **kwargs):
    '''
    Creates or updates entry for current invocation.
    kwargs are added to the invocation json.
    '''
    global _invocation, _invocation_id

    if _invocation is None:
        _invocation = get_this_invocation()
    _invocation.update(kwargs)
    _invocation.update(last_update_time=time.time())

    cur = conn.cursor()
    if _invocation_id is None:
        cur.execute(
            'INSERT INTO invocations(data) VALUES(%s) RETURNING id',
            [psycopg2.extras.Json(_invocation)])
        [_invocation_id] = cur.fetchone()
    else:
        cur.execute(
            'UPDATE invocations SET data = %s WHERE id = %s',
            [psycopg2.extras.Json(_invocation), _invocation_id])

def get_this_invocation_id(conn) -> int:
    if _invocation_id is None:
        record_this_invocation(conn)
    return _invocation_id


def main():
    conn = get_conn()

    create_tables(conn)

    record_this_invocation(conn)
    record_this_invocation(conn, comment='hi')
    conn.commit()


if __name__ == '__main__':
    main()