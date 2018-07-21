import production.model as M
import production.commands as Cmd
import sys
from production.model import Model
from production.basics import (Diff, Pos)
from production import data_files


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
    yield Diff(0, 1, 0)
    yield Diff(0, 0, 1)

    # State
    x = a.x
    y = a.y + 1
    z = a.z + 1

    x_dir = 1
    y_dir = 1
    z_dir = 3

    def inside():
        return (y >= a.x and y <= b.x and
                x >= a.x and x <= b.x and
                z >= a.x and z <= b.x)

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
                if inside():
                    yield Diff(x_dir, 0, 0)
                else:
                    flip_x()
                    inc_x() # return back
                    break
            inc_z()
            if inside():
                yield Diff(0, 0, z_dir)
            else:
                flip_z()
                while not inside(): # slowly return back
                    z = z + sign(z_dir)
                break
        inc_y()
        if inside():
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
            if (nextPos + d).is_inside_matrix(m.R) and m[nextPos + d]:
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
                if (nextPos + d).is_inside_matrix(m.R) and m[nextPos + d]:
                    yield Cmd.Fill(d)
                    m[nextPos + d] = False

            prevPos = nextPos

    yield prevPos


def return_home_gen(f: 'Pos', t: 'Pos'):
    # y is last
    for x in split_linear_move(Diff(-f.x, 0, 0)): yield x
    for x in split_linear_move(Diff(0, 0, -f.z)): yield x
    for x in split_linear_move(Diff(0, -f.y, 0)): yield x


def solve_gen(m: 'Model'):
    yield Cmd.Flip()

    pos = None
    for x in snake_fill_gen(m, Pos(0, 0, 0), Pos(m.R - 1, m.R - 1, m.R - 1)):
        if type(x) == Pos:
            pos = x
        else:
            yield x

    for x in return_home_gen(pos, Pos(0, 0, 0)): yield x

    yield Cmd.Flip()
    yield Cmd.Halt()


if __name__ == '__main__':
    task_number = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    name = 'LA{0:03d}_tgt.mdl'.format(task_number)
    data = data_files.lightning_problem(name)
    m    = Model.parse(data)

    with open('LA{0:03d}.nbt'.format(task_number), 'wb') as f:
        for cmd in solve_gen(m):
            f.write(bytearray(cmd.compose()))
