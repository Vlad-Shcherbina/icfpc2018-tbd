import logging
logger = logging.getLogger(__name__)
import sys
from io import StringIO
from typing import List
import traceback

from production.model import Model
from production.commands import *
from production.basics import Pos, Diff
from production.orchestrate2 import GroupProgram, single, empty
from production.group_programs import *
from production.solver_utils import bounding_box
from production.solver_interface import ProblemType, Solver, SolverResult, Fail

from production.data_files import *
from production.pyjs_emulator.run import run

def up_pass(model, high=False):
    prog = single()

    (pos1, pos2) = bounding_box(model)
    width  = pos2.x - pos1.x + 1
    height = pos2.y + 1
    depth  = pos2.z - pos1.z + 1

    prog += move_x(pos1.x)
    x = pos1.x
    prog += move_y(1)
    prog += move_z(pos1.z)
    z = pos1.z

    max_bots = min(20, width)

    # Fission into a line
    (steps_distr, strips) = fission_fill_right(list(range(2, max_bots + 1)), width)
    prog += steps_distr


    if high:
        prog += single(Flip()) // (single() ** (max_bots - 1))

    # Print each strip layer by layer in parallel
    print_prog = empty()
    for strip in strips:
        print_prog //= print_hyperrectangle(model, x, z, strip, height, depth)
        x += strip

    prog += print_prog

    if high:
        prog += single(Flip()) // (single() ** (max_bots - 1))

    prog += fusion_unfill_right(strips)

    prog += move_x(-pos1.x)
    prog += move_y(-height)

    prog += single(Halt())

    return prog


class BottomUpSolver(Solver):
    def __init__(self, args):
        self.high = len(args) > 0 and args[0] == 'high'

    def scent(self) -> str:
        return 'Bottom Up 2.1.2' + (' (high)' if self.high else '')

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type == ProblemType.Assemble

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        assert src_model is None
        m = Model.parse(tgt_model)
        trace = up_pass(m, high=self.high)
        trace_data = compose_commands(trace)
        return SolverResult(trace_data, extra={})


def write_solution(bytetrace, number): # -> IO ()
    with open('./FA{0:03d}.nbt'.format(number), 'wb') as f:
        f.write(bytetrace)

def solve(strategy, model, number): # -> IO ()
    commands = strategy(model, high=True)
    trace = compose_commands(commands)
    logger.info(run(lightning_problem_by_id(number), trace))
    write_solution(trace, number)

def main():
    from production import data_files

    task_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    m = Model.parse(lightning_problem_by_id(task_number))

    solve(up_pass, m, task_number)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
    main()
