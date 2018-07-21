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

    for file_name in data_files.lightning_problem_names():
        m = re.match(r'(LA\d{3})_tgt.mdl$', file_name)
        assert m, file_name
        name = m.group(1)
        logging.info(name)

        m_data = data_files.lightning_problem(file_name)
        m = Model.parse(m_data)

        num_full_voxels = 0
        for pos in m.enum_voxels():
            if m[pos]:
                num_full_voxels += 1

        stats = dict(R=m.R, num_full_voxels=num_full_voxels)
        logging.info(stats)

        extra = {}

        cur.execute('''
            INSERT INTO models(name, data, stats, extra, invocation_id, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
            ''',
            [name, zlib.compress(m_data), json.dumps(stats), json.dumps(extra),
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
