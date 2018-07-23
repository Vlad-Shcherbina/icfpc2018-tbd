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
from production.solver_utils import bounding_box


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
    # Well, I didn't check if a.x == b.x works ^_^
    assert(a.x <= b.x)
    assert(a.y <= b.y)
    assert(a.z <= b.z)

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
    for x in split_linear_move(Diff(0, 0, dz)): yield x
    for x in split_linear_move(Diff(dx, 0, 0)): yield x
    if dy < 0:
        for x in split_linear_move(Diff(0, dy, 0)): yield x

def navigate_pos(f: 'Pos', t: 'Pos'):
    return add_pos(t, navigate(f, t))

def merge(gens):
    saw_pos = False
    iters = [iter(x) for x in gens]
    pos   = [None for x in gens]
    ok    = True
    buff  = []
    while ok:
        ok = False
        for i in range(len(iters)):
            x = next(iters[i], None)
            if not x:
                buff.append( Cmd.Wait() )
            else:
                ok = True
                if type(x) == Pos:
                    saw_pos = True
                    pos[i] = x
                    buff.append( Cmd.Wait() )
                else:
                    ok = True
                    buff.append( x )
        if ok:
            for x in buff: yield x
            buff = []
    if saw_pos:
        yield pos

def append(a, b):
    for x in a: yield x
    for x in b: yield x

def sequence(a, nxt):
    pos = None
    for x in a:
        if type(x) == Pos:
            pos = x
        else:
            yield x
    b = nxt(pos)
    for x in b: yield x

def rm_pos(g):
    for x in g:
        if type(x) == Pos or type(x) == list or type(x) == dict:
            pass
        else:
            yield x

def print_gen(g):
    for x in g:
        print(x)
        yield x

def add_pos(pos, g):
    for x in rm_pos(g): yield x
    yield pos

def agent_gen(m: 'Model', start: 'Pos', a: 'Pos', b: 'Pos'):
    for x in navigate(start, a):
        yield x

    for x in snake_fill_gen(m, a, b):
        yield x

def go_to_start(a, b):
    def go(src):
        return navigate_pos(src, Pos(a.x, b.y + 1, a.z))

    return go

def auto_str(cls):
    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % item for item in vars(self).items())
        )
    cls.__str__ = __str__
    return cls

@auto_str
class Bot():
    def __init__(self, id, pos, seeds):
        self.state = None
        self.id = id
        self.seeds = seeds
        self.pos = pos

    def spawn_keep(self, diff, give_seeds):
        x = len(self.seeds) - give_seeds - 1
        return self.spawn(diff, x)

    def spawn(self, diff, give_seeds):
        bot = Bot(self.seeds.pop(0), self.pos + diff, self.seeds[:give_seeds])
        self.seeds = self.seeds[give_seeds:]
        cmd = Fission(diff, len(bot.seeds))

        self.state.add_move(self, cmd)
        self.state.add_bot(bot)

        return bot.id

    def cmd(self, cmd):
        self.state.add_move(self, cmd)

@auto_str
class State():
    def __init__(self, bots):
        self.bots = {}
        self.next_bots = {}
        for x in bots:
            self.bots[x.id] = x
            x.state = self
        self._clear()

    def __getitem__(self, id) -> bool:
        return self.bots.get(id) or self.next_bots.get(id)

    def add_bot(self, bot):
        bot.state = self
        self.next_bots[bot.id] = bot

    def add_move(self, bot, cmd):
        assert(type(self.moves[bot.id]) == Cmd.Wait)
        self.moves[bot.id] = cmd

    def _clear(self):
        self.moves = {}
        for i in self.next_bots:
            x = self.next_bots[i]
            self.bots[x.id] = x
        self.next_bots = {}
        for i in self.bots:
            self.moves[i] = Cmd.Wait()

    def step(self):
        for k in sorted( self.moves.keys() ):
            yield self.moves[k]
        self._clear()

    @staticmethod
    def initial_state(total_seeds):
        bots = [Bot(1, Pos(0, 0, 0), [x + 2 for x in range(total_seeds)])]
        return State(bots)

    # assuming initial state
    def spawn_bots(self, x, y):
        row = [1]
        p = 1
        for i in range(x - 1):
            p = self[p].spawn_keep(Diff(1, 0, 0), y - 1)
            row.append(p)
            yield from self.step()

        all_rows = [row]
        for j in range(y - 1):
            row = [self[i].spawn_keep(Diff(0, 1, 0), 0) for i in row]
            all_rows.append(row)
            yield from self.step()

        self.grid = all_rows


def partition_space(a, b, x_cnt, z_cnt):
    x_step = (b.x - a.x + 1) // x_cnt
    z_step = (b.z - a.z + 1) // z_cnt

    res = []
    for z in range(z_cnt):
        row = []
        z1 = a.z + z_step*z
        if z != z_cnt - 1:
            z2 = a.z + z_step*(z + 1) - 1
        else:
            z2 = b.z
        for x in range(x_cnt):
            x1 = a.x + x_step*x
            if x != x_cnt - 1:
                x2 = a.x + x_step*(x + 1) - 1
            else:
                x2 = b.x
            row.append((Pos(x1, 0, z1), Pos(x2, b.y + 1, z2)))

        res.append(row)

    return res

def with_delay(n, x):
    return append([Cmd.Wait() for x in range(n)], x)

def merge_tasks(tasks):
    keys = sorted( tasks.keys() )
    pos = None
    for x in merge([tasks[x] for x in keys]):
        if type(x) == list or type(x) == Pos:
            pos = x
        else:
            yield x
    if not pos:
        return

    res = {}
    for (id, pos) in zip(keys, pos):
        res[id] = pos
    yield res

def merge_line(bots, pos, delta):
    tasks1 = {}
    for i in bots:
        tasks1[i] = []

    for i in range(0, len(bots) - 1, 2):
        a = bots[i]
        b = bots[i + 1]
        tasks1[b] = navigate(pos[b], pos[a] + delta)

    yield tasks1

    # Issue fussion commands
    tasks = {}
    for i in bots:
        tasks[i] = []

    new_bots = []
    for i in range(0, len(bots) - 1, 2):
        a = bots[i]
        b = bots[i + 1]
        tasks[a] = [Cmd.FusionP(delta)]
        tasks[b] = [Cmd.FusionS(delta * (-1))]

        new_bots.append(a)
        del pos[b]

    if len(bots) % 2:
        new_bots.append(bots[-1])
        tasks[bots[-1]] = [Cmd.Wait()]
    yield tasks

    if len(new_bots) > 1:
        yield from merge_line(new_bots, pos, delta)


def merge_bots(bots, pos):
    pass


def solve_gen(m: 'Model', x_cnt: 'int', z_cnt: 'int'):
    (bb_a, bb_b) = bounding_box(m)

    # For narrow models
    x_cnt = min(x_cnt, bb_b.x - bb_a.x + 1)
    z_cnt = min(z_cnt, bb_b.z - bb_a.z + 1)

    yield Cmd.Flip()

    zones = partition_space(bb_a, bb_b, x_cnt, z_cnt)

    # Spawn bots
    #
    # State is used to spawn bots and to provide initial coords and ids
    st = State.initial_state(39)
    yield from st.spawn_bots(x_cnt, z_cnt)
    bots = st.grid

    # Navigate solve, and go to safe position for merging
    tasks = {}
    for z in range(z_cnt):
        for x in range(x_cnt):
            id     = bots[z][x]
            bot    = st[ bots[z][x] ]
            (a, b) = zones[z][x]
            d = (x_cnt + z_cnt) - (bot.pos.x + bot.pos.y)
            tasks[id] = sequence( with_delay(d, agent_gen(m, bot.pos, a, b))
                                , go_to_start(a, bb_b))

    for x in merge_tasks(tasks):
        if type(x) == dict:
            pos = x
        else:
            yield x

    #
    # Merging
    #

    # Combine rows
    t = []
    for i in range(len(bots)):
        t.append( [x for x in merge_line(bots[i], pos, Diff(1, 0, 0))] )

    for i in range(len(t[0])):
        tasks = {}
        for j in range(len(bots)):
            tasks.update(t[j][i])
        yield from merge_tasks(tasks)

    # Combine col
    col = [x[0] for x in bots]
    for t in merge_line(col, pos, Diff(0, 0, 1)):
        yield from merge_tasks(t)

    # Return home
    for x in navigate(pos[1], Pos(0, 0, 0)): yield x

    yield Cmd.Flip()
    yield Cmd.Halt()


class DefaultSolver2(Solver):
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        return 'Default 2.4-6x6'

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type == ProblemType.Assemble

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        assert src_model is None
        m = Model.parse(tgt_model)
        trace_data = compose_commands(solve_gen(m, 6, 6))
        return SolverResult(trace_data, extra={})

if __name__ == '__main__':
    task_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    name = 'LA{0:03d}_tgt.mdl'.format(task_number)
    data = data_files.lightning_problem(name)
    m    = Model.parse(data)

    with open('out.nbt'.format(task_number), 'wb') as f:
        for cmd in solve_gen(m, 6, 6):
            f.write(bytearray(cmd.compose()))
