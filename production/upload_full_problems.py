import logging
logger = logging.getLogger(__name__)
import json
import time
import re
import json
import zlib

from production import db
from production import data_files
from production.model import Model


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname).1s %(module)10.10s:%(lineno)-4d %(message)s')

    conn = db.get_conn()
    cur = conn.cursor()

    for name in sorted(data_files.full_names()):
        if not name.startswith('FR'):
            continue
        logging.info(name)

        src_data, tgt_data = data_files.full_problem(name)
        tgt_data = None

        stats = {}
        if src_data is not None:
            m = Model.parse(src_data)
            num_full_voxels = 0
            for pos in m.enum_voxels():
                if m[pos]:
                    num_full_voxels += 1
            stats.update(R=m.R, src_size=num_full_voxels)
            src_data = zlib.compress(src_data)
        if tgt_data is not None:
            m = Model.parse(tgt_data)
            num_full_voxels = 0
            for pos in m.enum_voxels():
                if m[pos]:
                    num_full_voxels += 1
            stats.update(R=m.R, tgt_size=num_full_voxels)
            tgt_data = zlib.compress(tgt_data)

        logging.info(stats)

        name = name.replace('FR', 'ZD')
        logging.info(name)

        extra = {}

        cur.execute('''
            INSERT INTO problems(
                name, src_data, tgt_data, stats, extra, invocation_id, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
            ''',
            [name, src_data, tgt_data, json.dumps(stats), json.dumps(extra),
             db.get_this_invocation_id(conn), time.time()])
        res = cur.fetchall()
        if res:
            [[model_id]] = res
            logger.info(f'Recorded as model/{model_id}')
        else:
            logger.info(f'Model {name!r} already exists')
        conn.commit()


if __name__ == '__main__':
    main()
