import logging
logger = logging.getLogger(__name__)
import sys
from io import StringIO
from typing import List
import traceback

from production.model import Model
from production.commands import *
from production.basics import Pos, Diff
from production.orchestrate import sequential
from production.solver_utils import *
from production.solver_interface import ProblemType, Solver, SolverResult, Fail

from production.data_files import *
from production.pyjs_emulator.run import run

def up_pass(model):
    steps = []

    # TODO: REMOVE ME
    steps.append([Flip()])

    # Up 1 and forward 1
    steps.append([LMove(Diff(0,1,0), Diff(0,0,1))])

    # Fission into a line
    (steps_distr, strips) = fission_fill_right(list(range(2, 21)), model.R)
    steps.extend(steps_distr)

    (_, pos_high) = bounding_box(model)
    maxy = pos_high.y

    # Print layer by layer
    for layer in range(0, maxy + 1):
        last = (layer == pos_high.y)
        steps.extend(print_layer_below(model, layer, strips, last))
        steps.extend([[SMove(Diff(0,1,0))]] * len(strips))

    steps.extend(fusion_unfill_right(strips))
    steps.extend(sequential(move_y(-1 * (maxy + 2))))

    # TODO: REMOVE ME
    steps.append([Flip()])

    steps.append([Halt()])


    return steps


class BottomUpSolver(Solver):
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        return 'Bottom Up 1.2'

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
        except:
            exc = StringIO()
            traceback.print_exc(file=exc)
            return SolverResult(Fail(), extra=dict(tb=exc.getvalue()))


def write_solution(bytetrace, number): # -> IO ()
    with open('./LA{0:03d}.nbt'.format(number), 'wb') as f:
        f.write(bytetrace)

def solve(strategy, model, number): # -> IO ()
    commands = [cmd for step in strategy(model) for cmd in step]
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
