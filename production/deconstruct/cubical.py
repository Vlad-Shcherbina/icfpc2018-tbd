import logging
logger = logging.getLogger(__name__)
import sys
from io import StringIO
from typing import List

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
        return 'Cubical 0'

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type == ProblemType.Disassemble

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        assert tgt_model is None
        m = Model.parse(src_model)
        trace = cubical(m)
        trace_data = compose_commands(trace)
        return SolverResult(trace_data, extra={})


def write_solution(bytetrace, number): # -> IO ()
    with open('./FD{0:03d}.nbt'.format(number), 'wb') as f:
        f.write(bytetrace)


def deconstruction_by_id(id):
    (src, tgt) = full_problem('FD{0:03d}'.format(id))
    return src

def main():
    task_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    mbytes = deconstruction_by_id(task_number)

    solver = CubicalDeconstructor([])
    res = solver.solve('main', mbytes, None)

    write_solution(res.trace_data, task_number)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
    main()

