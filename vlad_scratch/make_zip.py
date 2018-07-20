import zipfile
import hashlib

from production import invocation
from production import utils


def main():
    inv = invocation.get_this_invocation()
    if inv['version']['diff_stat']:
        print(inv['version']['diff_stat'])
        print("Refuse to make submissions from uncommited code!")
        exit(1)

    path = (
        utils.project_root() / 'outputs' /
        f'submission_{inv["version"]["commit"][:8]}.zip')
    z = zipfile.ZipFile(path, 'w')

    z.writestr(zipfile.ZipInfo('stuff.txt'), 'Hello, world!')
    z.writestr(zipfile.ZipInfo('dir/more_stuff.txt'), 'zzz')

    z.close()

    with open(path, 'rb') as fin:
        h = hashlib.sha256(fin.read()).hexdigest()

    print(f'File:   {path}')
    print(f'SHA256: {h}')


if __name__ == '__main__':
    main()
