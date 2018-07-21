from typing import List, Tuple, Optional
from zipfile import ZipFile
import re

from production import utils

_zipfiles = {}
def _open_datazipfile(name):
    if name not in _zipfiles:
        _zipfiles[name] = ZipFile(utils.project_root() / 'data' / f'{name}.zip')
    return _zipfiles[name]


def full_names() -> List[str]:
    '''Returns names like 'FR042'.'''
    result = set()
    for filename in _open_datazipfile('problemsF').namelist():
        if filename == 'problemsF.txt':
            continue
        m = re.match(r'(F[ADR]\d+)_(src|tgt).mdl$', filename)
        assert m is not None, filename
        result.add(m.group(1))
    return list(result)


def full_problem(name: str) -> Tuple[Optional[bytes], Optional[bytes]]:
    '''Takes name like 'FR042', returns (src_model, tgt_model).'''
    src_model = tgt_model = None

    if name.startswith('FD') or name.startswith('FR'):
        with _open_datazipfile('problemsF').open(f'{name}_src.mdl', 'r') as fin:
            src_model = fin.read()

    if name.startswith('FA') or name.startswith('FR'):
        with _open_datazipfile('problemsF').open(f'{name}_tgt.mdl', 'r') as fin:
            tgt_model = fin.read()

    return src_model, tgt_model

def full_default_trace(name: str) -> bytes:
    with _open_datazipfile('dfltTracesF').open(f'{name}.nbt', 'r') as fin:
        return fin.read()

def lightning_problem_names() -> List[str]:
    result = _open_datazipfile('problemsL').namelist()
    result.remove('problemsL.txt')
    return result


def lightning_problem(name: str) -> bytes:
    with _open_datazipfile('problemsL').open(name, 'r') as fin:
        return fin.read()

def lightning_problem_by_id(id: int) -> bytes:
    return lightning_problem('LA{0:03d}_tgt.mdl'.format(id))

def lightning_default_trace_names() -> List[str]:
    return _open_datazipfile('dfltTracesL').namelist()


def lightning_default_trace(name: str) -> bytes:
    with _open_datazipfile('dfltTracesL').open(name, 'r') as fin:
        return fin.read()

# I want a load_trace function here that magically determines what to do.
