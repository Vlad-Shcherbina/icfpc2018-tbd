import production.model as M
import production.commands as Cmd
import sys
from io import StringIO
from itertools import chain

from production.model import Model
from production.basics import (Diff, Pos)
from production import data_files
from production.solver_interface import ProblemType, Solver, SolverResult, Fail
from production.solver_utils import *
from production.model_helpers import floor_contact, filled_neighbors
from production.search import breadth_first_search
from production.navigation import navigate_near_voxel

    
def fill(voxel):
    navigate_near_voxel(current_pos, voxel)
    Cmd.Fill(voxel)
    
    
def solve_gen(model: 'Model'):
    commands = iter([])

    def add_commands(new_commamnds):
        commands = chain(comands, new_commands)
    
    voxels_to_fill = breadth_first_search(floor_contact(model), filled_neighbors(model))

    for voxel in voxels_to_fill:
        add_commands(fill(voxel))

    add_commands(finish())
        
def finish():
    for x in navigate(pos[0], Pos(0, 0, 0)): yield x
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
