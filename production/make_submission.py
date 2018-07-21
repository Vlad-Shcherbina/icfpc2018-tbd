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
            models.name, traces.id, traces.energy
        FROM models
        JOIN traces ON traces.model_id = models.id
        WHERE traces.status = 'DONE'
    ''')
    rows = cur.fetchall()
    best_by_model = {}
    for model_name, trace_id, energy in rows:
        assert energy is not None
        k = (energy, trace_id)
        if model_name not in best_by_model:
            best_by_model[model_name] = k
        else:
            if k < best_by_model[model_name]:
                best_by_model[model_name] = k

    print(best_by_model)

    with open(utils.project_root() / 'outputs' / f'submission_{t}.manifest', 'w') as fout:
        for model_name, (score, trace_id) in sorted(best_by_model.items()):
            fout.write(f'{model_name} {score:>15} /trace/{trace_id}\n')

    path = (
        utils.project_root() / 'outputs' /
        f'submission_{t}.zip')
    z = zipfile.ZipFile(path, 'w')

    for model_name, (score, trace_id) in sorted(best_by_model.items()):
        print(model_name)
        cur.execute('SELECT data FROM traces WHERE id = %s', [trace_id])
        [data] = cur.fetchone()
        data = zlib.decompress(data)
        z.writestr(zipfile.ZipInfo(f'{model_name}.nbt'), data)

    for file_name in data_files.lightning_default_trace_names():
        m = re.match(r'(LA\d+).nbt', file_name)
        assert m is not None, file_name
        name = m.group(1)
        if name not in best_by_model:
            print(name, 'from defaults')
            z.writestr(
                zipfile.ZipInfo(f'{name}.nbt'),
                data_files.lightning_default_trace(file_name))

    z.close()

    with open(path, 'rb') as fin:
       h = hashlib.sha256(fin.read()).hexdigest()

    print(f'File:   {path}')
    print(f'SHA256: {h}')


if __name__ == '__main__':
    main()
