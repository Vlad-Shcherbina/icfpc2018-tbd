from typing import List
from zipfile import ZipFile

from production import utils

_zipfiles = {}
def _open_datazipfile(name):
    if name not in _zipfiles:
        _zipfiles[name] = ZipFile(utils.project_root() / 'data' / f'{name}.zip')
    return _zipfiles[name]


def lightning_problem_names() -> List[str]:
    result = _open_datazipfile('problemsL').namelist()
    result.remove('problemsL.txt')
    return result


def lightning_problem(name: str) -> bytes:
    with _open_datazipfile('problemsL').open(name, 'r') as fin:
        return fin.read()

def lightning_problem_by_id(id: int) -> bytes:
    return lightning_problem(list(filter(lambda x: str(id) in x, lightning_problem_names()))[0])

def lightning_default_trace_names() -> List[str]:
    return _open_datazipfile('dfltTracesL').namelist()


def lightning_default_trace(name: str) -> bytes:
    with _open_datazipfile('dfltTracesL').open(name, 'r') as fin:
        return fin.read()

# I want a load_trace function here that magically determines what to do.
