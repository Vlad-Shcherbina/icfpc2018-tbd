import zipfile
import hashlib
import time
import zlib
import re

from production import utils
from production import db
from production import data_files


def main():
    t = int(time.time())

    conn = db.get_conn()
    cur = conn.cursor()

    cur.execute('''
        SELECT
            problems.name, traces.id, traces.energy
        FROM problems
        JOIN traces ON traces.problem_id = problems.id
        WHERE problems.name LIKE 'F%' AND traces.status = 'DONE'
    ''')
    rows = cur.fetchall()
    best_by_problem = {}
    for problem_name, trace_id, energy in rows:
        assert energy is not None
        k = (energy, trace_id)
        if problem_name not in best_by_problem:
            best_by_problem[problem_name] = k
        else:
            if k < best_by_problem[problem_name]:
                best_by_problem[problem_name] = k

    print(best_by_problem)

    with open(utils.project_root() / 'outputs' / f'submission_{t}.manifest', 'w') as fout:
        for problem_name, (score, trace_id) in sorted(best_by_problem.items()):
            fout.write(f'{problem_name} {score:>15} /trace/{trace_id}\n')

    path = (
        utils.project_root() / 'outputs' /
        f'submission_{t}.zip')
    z = zipfile.ZipFile(path, 'w')

    for problem_name, (score, trace_id) in sorted(best_by_problem.items()):
        print(problem_name)
        cur.execute('SELECT data FROM traces WHERE id = %s', [trace_id])
        [data] = cur.fetchone()
        data = zlib.decompress(data)
        z.writestr(zipfile.ZipInfo(f'{problem_name}.nbt'), data)

    for name in data_files.full_names():
        if name not in best_by_problem:
            print(name, 'from defaults')
            z.writestr(
                zipfile.ZipInfo(f'{name}.nbt'),
                data_files.full_default_trace(name))

    z.close()

    with open(path, 'rb') as fin:
       h = hashlib.sha256(fin.read()).hexdigest()

    print(f'File:   {path}')
    print(f'SHA256: {h}')


if __name__ == '__main__':
    main()
