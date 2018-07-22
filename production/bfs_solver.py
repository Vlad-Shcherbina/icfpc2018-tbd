# The first deffirence from defalt_solver is the here we use simple hardcoded
# parallelization to 4 workers.
#
# The second difference is that this version better optimizes "useless"
# movements where we don't fill anything. Instead of using Bounding Box it goes
# directly to the next point which should be filled.
#
# See snake_fill_gen for details

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


# Walk along the X coordinate until we went outside of the map. In that case
# make long step along the Z coordinate and flip X direction. Similartly with Y
# and Z cordinates.
def snake_path_gen(a, b):
    assert(a.x < b.x)
    assert(a.y < b.y)
    assert(a.z < b.z)

    yield Diff(0, 1, 0)
    yield Diff(0, 0, 1)

    # State
    x = a.x
    y = a.y + 1
    z = a.z + 1

    x_dir = 1
    y_dir = 1
    z_dir = 3

    def inside_x(): return x >= a.x and x <= b.x
    def inside_y(): return y >= a.y and y <= b.y
    def inside_z(): return z >= a.z and z <= b.z

    def flip_x(): nonlocal x_dir; x_dir = -x_dir
    def flip_y(): nonlocal y_dir; y_dir = -y_dir
    def flip_z(): nonlocal z_dir; z_dir = -z_dir
    def inc_x(): nonlocal x; x = x + x_dir
    def inc_y(): nonlocal y; y = y + y_dir
    def inc_z(): nonlocal z; z = z + z_dir

    while True:
        while True:
            while True:
                inc_x()
                if inside_x():
                    yield Diff(x_dir, 0, 0)
                else:
                    flip_x()
                    inc_x() # return back
                    break
            prev_z = z
            inc_z()
            if inside_z():
                yield Diff(0, 0, z_dir)
            else:
                flip_z()
                z = z + sign(z_dir)
                if inside_z():
                    yield Diff(0, 0, z - prev_z)
                else:
                    z = z + 2*sign(z_dir)
                    break
        inc_y()
        if inside_y():
            yield Diff(0, y_dir, 0)
        else:
            flip_y()
            inc_y() # return back
            break


# We expect moves only in one dimension
def split_linear_move(diff):
    if diff.mlen() == 0:
        return
    assert(diff.is_linear())

    l = abs(diff.mlen())
    norm = direction(diff)
    while l > 0:
        c = min(l, 15)
        l -= c
        yield Cmd.SMove(norm * c)


def inside_region(p: 'Pos', a: 'Pos', b: 'Pos'):
    return (a.x <= p.x and p.x <= b.x and
            a.y <= p.y and p.y <= b.y and
            a.z <= p.z and p.z <= b.z)
# Fill the regin [a, b] using optimized default stratagy
#
# Returns: commands stream wich is terminated by a final Pos
#
# + model is modified during execution to track state
# + a is the initial coordinate for the robot
#
# Assuming:
# + top "surface" of the model is empty
# + no obstracles in the region
#
# Optimization:
# + 3-wide filling
# + cut paths which lead to no useful location (improved Bounding Box)
# + use long lenear movements where possible
def snake_fill_gen(m: 'Model', a: Pos, b: Pos):
    prevPos = a
    nextPos = a

    # The main idea is to skip path points where model has no voxels below it.
    # And then go to the next "job" using long lenear move. We always above our
    # buildings so we will never collide with anything.
    for diff in snake_path_gen(a, b):
        nextPos = nextPos + diff

        fillBelow = False
        for d in [Diff(0, -1, 0), Diff(0, -1, 1), Diff(0, -1, -1)]:
            if inside_region((nextPos + d), a, b) and m[nextPos + d]:
                fillBelow = True
        if fillBelow:
            dx = nextPos.x - prevPos.x
            dy = nextPos.y - prevPos.y
            dz = nextPos.z - prevPos.z

            # y first
            for x in split_linear_move(Diff(0, dy, 0)): yield x
            for x in split_linear_move(Diff(0, 0, dz)): yield x
            for x in split_linear_move(Diff(dx, 0, 0)): yield x

            for d in [Diff(0, -1, 0), Diff(0, -1, 1), Diff(0, -1, -1)]:
                if inside_region((nextPos + d), a, b) and m[nextPos + d]:
                    yield Cmd.Fill(d)
                    m[nextPos + d] = False

            prevPos = nextPos

    yield prevPos


def navigate(f: 'Pos', t: 'Pos'):
    # y is last
    dx = t.x - f.x
    dy = t.y - f.y
    dz = t.z - f.z
    if dy > 0:
        for x in split_linear_move(Diff(0, dy, 0)): yield x
    for x in split_linear_move(Diff(dx, 0, 0)): yield x
    for x in split_linear_move(Diff(0, 0, dz)): yield x
    if dy > 0:
        for x in split_linear_move(Diff(0, dy, 0)): yield x

def merge(gens):
    iters = [iter(x) for x in gens]
    pos = [None for x in gens]
    ok = True
    while ok:
        ok = False
        for i in range(len(iters)):
            x = next(iters[i], None)
            if not x:
                yield Cmd.Wait()
            elif type(x) == Pos:
                pos[i] = x
                yield Cmd.Wait()
            else:
                ok = True
                yield x
    yield pos

def append(a, b):
    for x in a: yield x
    for x in b: yield x

def agent_gen(m: 'Model', start: 'Pos', a: 'Pos', b: 'Pos'):
    for x in navigate(start, a):
        yield x

    for x in snake_fill_gen(m, a, b):
        yield x

def breadth_first_search():
    pass
        
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
