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

from production.deconstruct.lib2 import clear_all_squads
from production.group_programs import move_x, move_y, move_z, single
from production.solver_utils import bounding_box

def cubical(model, high=False):
    (pos1, pos2) = bounding_box(model)

    width  = pos2.x - pos1.x + 1
    height = pos2.y - pos1.y + 1
    depth  = pos2.z - pos1.z + 1

    (x_cur, x_next) = (0, pos1.x)
    (y_cur, y_next) = (0, pos2.y + 1)
    (z_cur, z_next) = (0, pos1.z)

    prog  = move_x(pos1.x)
    prog += move_z(pos1.z - 1)

    if high:
        prog += single(Flip())

    prog += clear_all_squads(model, pos1.x, 0, pos1.z - 1, width, height, depth)

    if high:
        prog += single(Flip())

    prog += move_x(-pos1.x)
    prog += move_z(-pos1.z + 1)

    return prog + single(Halt())


class CubicalDeconstructor(Solver):
    def __init__(self, args):
        self.high = len(args) > 0 and args[0] == 'high'

    def scent(self) -> str:
        return 'Cubical 2.0' + (' (high)' if self.high else '')

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type == ProblemType.Disassemble

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        assert tgt_model is None
        m = Model.parse(src_model)
        trace = cubical(m, high=self.high)
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

    solver = CubicalDeconstructor(["high"])
    res = solver.solve('main', mbytes, None)

    write_solution(res.trace_data, task_number)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
    main()

