import production.model as M
import production.commands as Cmd
import sys

from production.model import Model
from production.basics import (Diff, Pos)

# Walk along the X coordinate until we went outside of the map. In that case
# make one step along the Y coordinate and flip X direction. Similartly with Y
# and Z cordinates.
def snake_path_gen(r):
    x = 0
    y = 0
    z = 1
    yield(Diff(0, 0, 1), Pos(x, y, z))

    x_dir = 1
    y_dir = 1
    z_dir = 1

    def inside(val): return val >= 0 and val < r
    def flip_x(): nonlocal x_dir; x_dir = -x_dir
    def flip_y(): nonlocal y_dir; y_dir = -y_dir
    def inc_x(): nonlocal x; x = x + x_dir
    def inc_y(): nonlocal y; y = y + y_dir
    def inc_z(): nonlocal z; z = z + z_dir

    while True:
        while True:
            while True:
                inc_x()
                if inside(x):
                    yield (Diff(x_dir, 0, 0), Pos(x, y, z))
                else:
                    flip_x()
                    inc_x() # return back
                    break
            inc_y()
            if inside(y):
                yield (Diff(0, y_dir, 0), Pos(x, y, z))
            else:
                flip_y()
                inc_y() # return back
                break
        inc_z()
        if inside(z):
            yield (Diff(0, 0, z_dir), Pos(x, y, z))
        else:
            z = z - 1
            break

    z = z - z_dir

def return_path_gen(pos):
    (x, y, z) = [pos.x, pos.y, pos.z]
    while z > 0:
        z = z - 1
        yield (Diff(0, 0, -1), Pos(x, y, z))
    while y > 0:
        y = y - 1
        yield (Diff(0, -1, 0), Pos(x, y, z))
    while x > 0:
        x = x - 1
        yield (Diff(-1, 0, 0), Pos(x, y, z))

def solve(m: 'Model'):
    yield Cmd.Flip()

    dz = Diff(0, 0, -1)

    for (diff, pos) in snake_path_gen(m.R):
        last_pos = pos

        yield Cmd.SMove(diff)
        below = pos + Diff(0, 0, -1)
        if m[below]:
            yield Cmd.Fill(Diff(0, 0, -1))

    for (diff, pos) in return_path_gen(last_pos):
        yield Cmd.SMove(diff)

    yield Cmd.Flip()
    yield Cmd.Halt()

if __name__ == '__main__':
    from production import data_files

    name = str(sys.argv[1])
    data = data_files.lightning_problem(name)
    m = Model.parse(data)


    res = Cmd.compose_commands(solve(m))
    f = open('path.nbt', 'wb')
    f.write(res)
    f.close()
