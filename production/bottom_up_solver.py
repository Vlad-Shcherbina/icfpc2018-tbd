import logging
logger = logging.getLogger(__name__)
import sys
from io import StringIO
from typing import List
import traceback

from production.model import Model
from production.commands import *
from production.basics import Pos, Diff
from production.solver_utils import *
from production.solver_interface import Solver, SolverResult, Fail

def up_pass(model):
    steps = []

    # TODO: REMOVE ME
    steps.append([Flip()])

    # Up 1 and forward 1
    steps.append([LMove(Diff(0,1,0), Diff(0,0,1))])

    # Distribute
    (steps_distr, strips) = fission_fill_right(list(range(2, 21)), model.R)
    steps.extend(steps_distr)

    for layer in range(0, model.R - 1):
        steps.extend(print_layer_below(model, layer, strips))
        steps.extend([[SMove(Diff(0,1,0))]] * len(strips))

    return steps


class BottomUpSolver(Solver):
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        return 'Bottom Up 1.1'

    def solve(self, name: str, model_data: bytes) -> SolverResult:
        m = Model.parse(model_data)
        try:
            trace = [cmd for step in up_pass(m) for cmd in step]
            trace_data = compose_commands(trace)
            return SolverResult(trace_data, extra={})
        except:
            exc = StringIO()
            traceback.print_exc(file=exc)
            return SolverResult(Fail(), extra=dict(tb=exc.getvalue()))


def write_solution(bytetrace, number): # -> IO ()
    with open('problemsL/LA{0:03d}.nbt'.format(number), 'wb') as f:
        f.write(bytetrace)

def solve(strategy, model, number = 0): # -> IO ()
    commands = [cmd for step in strategy(model) for cmd in step]
    trace = compose_commands(commands)
    write_solution(trace, number)

def main():
    from production import data_files

    task_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    name = 'LA{0:03d}_tgt.mdl'.format(task_number)
    data = data_files.lightning_problem(name)
    m = Model.parse(data)

    solve(up_pass, m, task_number)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname).1s %(asctime)s %(module)10.10s:%(lineno)-4d %(message)s')
    main()
