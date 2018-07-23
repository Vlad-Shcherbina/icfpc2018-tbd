from typing import Tuple

from production.basics import Diff, Pos
from production.commands import *
from production.group_programs import move_x, move_y, move_z
from production.orchestrate2 import GroupProgram, empty, single


# Program for 1 bot located at x,y,z.
# It will spawn 7 more bots and remove a hyperrectangle of given dimensions
# in front and below it.
def clear_down(model, x, y, z, width, height, depth) -> GroupProgram:
    assert width <= 31 and height <= 31 and depth <= 31

    prog7  = move_z(depth) + spawn_down(model, x + (width-1), y, z + (depth-1)) + \
             (single() // drill_down(model, x + (width-1), y-1, z + (depth-1), height-1))

    prog57 = move_x(width-2) + spawn_down(model, x + (width-1), y, z) + \
             (+single(Fission(Diff(0,0,1), 1)) // single()) + \
             (single() // move_y(-height+1) // prog7)

    prog3  = move_z(depth) + spawn_down(model, x, y, z + (depth-1)) + \
             (single() // drill_down(model, x, y - 1, z + (depth-1), height-1))

    prog1  = +single(Fission(Diff(0,-1,0), 0)) + \
             (+single(Fission(Diff(0,0,1), 1)) // single()) + \
             (+single(Fission(Diff(1,0,0), 3)) // single() // single()) + \
             (single() // move_y(-height+1) // prog3 // prog57)

    prog_expand = prog1

    prog_clear = single(GVoid(Diff(0,-1, 1), Diff(width-1,-height+1,depth-1)))   // \
                 single(GVoid(Diff(0, 0, 1), Diff(width-1,height-1,depth-1)))    // \
                 single(GVoid(Diff(0,-1,-1), Diff(width-1,-height+1,-depth+1)))  // \
                 single(GVoid(Diff(0, 0,-1), Diff(width-1,height-1,-depth+1)))   // \
                 single(GVoid(Diff(0,-1, 1), Diff(-width+1,-height+1,depth-1)))  // \
                 single(GVoid(Diff(0, 0, 1), Diff(-width+1,height-1,depth-1)))   // \
                 single(GVoid(Diff(0,-1,-1), Diff(-width+1,-height+1,-depth+1))) // \
                 single(GVoid(Diff(0, 0,-1), Diff(-width+1,height-1,-depth+1)))

    # Move 1 down to 2 (3 to 4, 5 to 6, 7 to 8)
    prog_contract_down = (move_y(-height+1) // single()) + -(single(FusionP(Diff(0,-1,0))) // single(FusionS(Diff(0,1,0))))
    # Move 3 back to 1 (7 to 5)
    prog_contract_back = (single() // move_z(-depth)) + -(single(FusionP(Diff(0,0,1))) // single(FusionS(Diff(0,0,-1))))
    # Move 5 left to 1
    prog_contract_left = (single() // move_x(-width+2)) + -(single(FusionP(Diff(1,0,0))) // single(FusionS(Diff(-1,0,0))))

    prog_contract = (prog_contract_down ** 4) + (prog_contract_back ** 2) + prog_contract_left + move_y(-1)

    return prog_expand + prog_clear + prog_contract + single(Halt())


# Program for 1 bot. Spawns second bot below current one (clears the voxel if needed).
def spawn_down(model, x, y, z):
    prog = single()

    if model[Pos(x,y-1,z)]:
        prog += single(Void(Diff(0,-1,0)))
    prog += +single(Fission(Diff(0,-1,0), 0))

    return prog

# Program for 1 bot. Makes it go down to given depth, drilling
# the path where necessary.
def drill_down(model, x, y, z, depth) -> GroupProgram:
    prog = single()

    while depth > 0:
        if model[Pos(x, y - 1, z)]:
            prog += single(Void(Diff(0,-1,0)))

        step = 1
        for i in range(2, depth + 1):
            if model[Pos(x, y - i, z)]:
                break
            else:
                step += 1
        prog += move_y(-1 * step)
        depth -= step
    return prog
