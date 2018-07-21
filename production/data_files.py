from typing import List
from zipfile import ZipFile

from production import utils


def lightning_problem_names() -> List[str]:
    with ZipFile(utils.project_root() / 'data' / 'problemsL.zip') as z:
        return z.namelist()


def lightning_problem(name: str) -> bytes:
    with ZipFile(utils.project_root() / 'data' / 'problemsL.zip') as z:
        with z.open(name, 'r') as fin:
            return fin.read()


def lightning_default_trace_names() -> List[str]:
    with ZipFile(utils.project_root() / 'data' / 'dfltTracesL.zip') as z:
        return z.namelist()


def lightning_default_trace(name: str) -> bytes:
    with ZipFile(utils.project_root() / 'data' / 'dfltTracesL.zip') as z:
        with z.open(name, 'r') as fin:
            return fin.read()
