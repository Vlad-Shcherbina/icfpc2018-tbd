from typing import Union, List
from dataclasses import dataclass

from production import data_files
from production.model import Model


@dataclass
class Pass:
    pass


@dataclass
class Fail:
    pass


@dataclass
class SolverResult:
    trace_data: Union[bytes, Pass, Fail]

    extra: dict
    # any additional informaion (stats, errors, comments)
    # should be json-encodable


class Solver:
    def __init__(self, args: List[str]):
        '''
        args come from the command line, could be used as tuning parameters
        or something
        '''
        pass

    def scent(self) -> str:
        '''Solver identifier to avoid redundant reruns.

        Use something like "My solver 1.0" and bump version when
        the solver changed significantly and you want to rerun on all problems.

        Args can be included in the scent if they affect significantly
        how the solver works.
        '''
        raise NotImplementedError()

    def solve(self, name: str, model_data: bytes) -> SolverResult:
        '''
        Name is like 'LA042'. Ignore it.

        Return SolverData(compose_commands(solution), extra={...}) on success.

        Return SolverData(Pass(), extra={...}) if the solver failed
        in an intended way (for example solver that does not support holes
        got a model with holes).

        Return SolverData(Fail(), extra={...}) if the solver failed
        in an unintended way worth investigating and fixing.
        '''
        raise NotImplementedError()


class TheirDefaultSolver(Solver):
    '''Example pseudo-solver that just takes their default traces.'''
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        return 'their default'

    def solve(self, name: str, model_data: bytes) -> SolverResult:
        Model.parse(model_data)  # as a sanity check

        trace_data = data_files.lightning_default_trace(f'{name}.nbt')
        return SolverResult(trace_data, extra={})
