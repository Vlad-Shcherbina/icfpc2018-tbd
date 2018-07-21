from typing import List
from zipfile import ZipFile

from production import utils

_zipfiles = {}
def _open_datazipfile(name):
    if name not in _zipfiles:
        _zipfiles[name] = ZipFile(utils.project_root() / 'data' / f'{name}.zip')
    return _zipfiles[name]


def lightning_problem_names() -> List[str]:
    return _open_datazipfile('problemsL').namelist()


def lightning_problem(name: str) -> bytes:
    with _open_datazipfile('problemsL').open(name, 'r') as fin:
        return fin.read()


def lightning_default_trace_names() -> List[str]:
    return _open_datazipfile('dfltTracesL').namelist()


def lightning_default_trace(name: str) -> bytes:
    with _open_datazipfile('dfltTracesL').open(name, 'r') as fin:
        return fin.read()

# I want a load_trace function here that magically determines what to do.
