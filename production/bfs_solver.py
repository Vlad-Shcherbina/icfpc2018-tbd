import production.model as M
import production.commands as Cmd
import sys
from production.model import Model
from production.basics import (Diff, Pos)
from production import data_files
from production.solver_interface import ProblemType, Solver, SolverResult, Fail
from production.solver_utils import *


def direction(diff) -> 'Diff':
    return Diff(sign(diff.dx), sign(diff.dy), sign(diff.dz))


def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    elif x == 0:
        return 0

    
def solve_gen(m: 'Model'):
    a = (m.R - 1) // 2
    b = m.R - 1

    pos = None

    def with_delay(n, x): return append([Cmd.Wait() for x in range(n)], x)

    a1 = with_delay(2, agent_gen(m, Pos(0, 0, 0), Pos(0, 0, 0), Pos(a, m.R, a)))
    a2 = with_delay(1, agent_gen(m, Pos(0, 1, 0), Pos(0, 0, a + 1), Pos(a, m.R, b)))
    a3 =               agent_gen(m, Pos(1, 1, 0), Pos(a + 1, 0, a + 1), Pos(b, m.R, b))
    a4 = with_delay(1, agent_gen(m, Pos(1, 0, 0), Pos(a + 1, 0, 0), Pos(b, m.R, a)))
    for x in merge([a1, a2, a3, a4]):
        if type(x) == list:
            pos = x
        else:
            yield x

    b1 = []
    b2 = navigate(pos[1], pos[0] + Diff(0, 0, 1))
    b3 = navigate(pos[2], pos[3] + Diff(0, 0, 1))
    b4 = []
    for x in merge([b1, b2, b3, b4]):
        if type(x) == list:
            pass
        else:
            yield x

    yield Cmd.FusionP(Diff(0, 0, 1));
    yield Cmd.FusionS(Diff(0, 0, -1));
    yield Cmd.FusionS(Diff(0, 0, -1));
    yield Cmd.FusionP(Diff(0, 0, 1));

    for x in merge([[], navigate(pos[3], pos[0] + Diff(1, 0, 0))]):
        if type(x) == list:
            pass
        else:
            yield x

    yield Cmd.FusionP(Diff(1, 0, 0));
    yield Cmd.FusionS(Diff(-1, 0, 0));

    for x in navigate(pos[0], Pos(0, 0, 0)): yield x

    yield Cmd.Flip()
    yield Cmd.Halt()


class BFSSolver(Solver):
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        return 'BFS 0.1'

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type == ProblemType.Assemble

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        assert src_model is None
        m = Model.parse(tgt_model)
        try:
            trace_data = compose_commands(solve_gen(m))

            return SolverResult(trace_data, extra={})
        except KeyboardInterrupt:
            raise
        except:
            exc = StringIO()
            traceback.print_exc(file=exc)
            return SolverResult(Fail(), extra=dict(tb=exc.getvalue()))


if __name__ == '__main__':
    task_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    name = 'LA{0:03d}_tgt.mdl'.format(task_number)
    data = data_files.lightning_problem(name)
    m    = Model.parse(data)

    with open('LA{0:03d}.nbt'.format(task_number), 'wb') as f:
        for cmd in solve_gen(m):
            f.write(bytearray(cmd.compose()))
