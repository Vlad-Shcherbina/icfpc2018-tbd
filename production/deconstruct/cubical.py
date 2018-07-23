import logging
logger = logging.getLogger(__name__)
import sys
from io import StringIO
from typing import List
import traceback

from production.model import Model
from production.commands import *
from production.basics import Pos, Diff
from production.solver_interface import ProblemType, Solver, SolverResult, Fail

from production.data_files import *
from production.pyjs_emulator.run import run

from production.deconstruct.lib import clear_down
from production.group_programs import move_y

def cubical(model):
    prog = move_y(19)
    prog += clear_down(model, 0, 19, 0, 20, 19, 18)

    return prog


class CubicalDeconstructor(Solver):
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        return 'destroy-cubical-0'

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type == ProblemType.Assemble

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        assert src_model is None
        m = Model.parse(tgt_model)
        try:
            trace = [cmd for step in up_pass(m) for cmd in step]
            trace_data = compose_commands(trace)
            return SolverResult(trace_data, extra={})
        except KeyboardInterrupt:
            raise
        except:
            exc = StringIO()
            traceback.print_exc(file=exc)
            return SolverResult(Fail(), extra=dict(tb=exc.getvalue()))


def write_solution(bytetrace, number): # -> IO ()
    with open('./FD{0:03d}.nbt'.format(number), 'wb') as f:
        f.write(bytetrace)


def deconstruction_by_id(id):
    (src, tgt) = full_problem('FD{0:03d}'.format(id))
    return src

def solve(strategy, model, number): # -> IO ()
    commands = strategy(model)
    trace = compose_commands(commands)
    logger.info(run(deconstruction_by_id(number), trace))
    write_solution(trace, number)

def main():
    from production import data_files

    task_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    m = Model.parse(deconstruction_by_id(task_number))


    solve(cubical, m, task_number)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
    main()

