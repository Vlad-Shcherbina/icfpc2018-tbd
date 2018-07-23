import logging
logger = logging.getLogger(__name__)
from typing import Tuple

from math import ceil

from production.basics import Diff, Pos
from production.commands import *
from production.group_programs import move_x, move_y, move_z
from production.orchestrate2 import GroupProgram, empty, single


G_DIST = 30
CUBES = 5
SQUAD_W = (G_DIST + 1) * CUBES


# Program for 1 bot located at x,y,z.
# It will spawn the given number of cubes (and take part in one itself)
# which will line up to the right and clean things up
def clear_all_squads(model, x, y, z, width, height, depth) -> GroupProgram:
    logging.debug("Model %d x %d x %d", width,height,depth)
    deltax = 0
    prog = single()
    while width > 0:
        last = width <= SQUAD_W
        this_w = min(SQUAD_W, width)
        prog += execute_squad(model, x+deltax,y,z, this_w, height, depth, 39)
        if not last:
            prog += move_x(this_w)
            deltax += this_w
        width -= this_w

    prog += move_x(-deltax)
    return prog

def execute_squad(model, x, y, z, width, height, depth, seeds):
    assert width <= SQUAD_W
    logging.debug("Start squad at %d %d %d; (%d x %d x %d)", x,y,z,width,height,depth)

    (full_w, last_w) = divmod(width, G_DIST + 1)
    # HACK HACK HACK
    if last_w == 1:
        last_w += 1
    prog_dist = distribute_roots(x, y, z, full_w, last_w, seeds)

    (full_h, last_h) = divmod(height, G_DIST + 1)
    prog_er = erase_layers(model, x, y + height, z, full_w, last_w, full_h, last_h, depth)

    prog_clps = collapse_roots(full_w, last_w)

    return move_y(height) + prog_dist + prog_er + prog_clps + move_y(-last_h)


def distribute_roots(x, y, z, full_w, last_w, seeds):
    if full_w == 0: return single()
    if full_w == 1 and last_w == 0: return single()

    return +single(Fission(Diff(0,1,0),6)) + \
           (+single(Fission(Diff(1,0,0),seeds-7-1)) // single()) + \
           (-(single(FusionP(Diff(0,1,0))) // single(FusionS(Diff(0,-1,0)))) // (move_x(G_DIST) + distribute_roots(x+G_DIST, y, z, full_w - 1, last_w, seeds-7-1)))

def collapse_roots(full_w, last_w):
    if full_w == 0: return single()
    if full_w == 1 and last_w == 0: return single()

    return (single() // (collapse_roots(full_w - 1, last_w) + move_x(-G_DIST))) + \
           -(single(FusionP(Diff(1,0,0))) // single(FusionS(Diff(-1,0,0))))


def erase_layers(model, x, y, z, full_w, last_w, full_h, last_h, depth):
    logging.debug("erase layers at %d %d %d; full_h=%d, last_h=%d; %d", x,y,z,full_h,last_h,depth)
    if full_h == 0:
        if last_h != 0:
            return erase_layer(model, x, y, z, full_w, last_w, last_h, depth)
        else:
            return single() ** (full_w + (1 if last_w else 0))

    return erase_layer(model, x, y, z, full_w, last_w, G_DIST + 1, depth) + \
           (move_y(-G_DIST - 1) ** (full_w + (1 if last_w else 0))) + \
           erase_layers(model, x, y - G_DIST - 1, z, full_w, last_w, full_h - 1, last_h, depth)

def erase_layer(model, x, y, z, full_w, last_w, height, depth):
    (full_d, last_d) = divmod(depth, G_DIST + 1)

    return erase_rows(model, x, y, z, full_w, last_w, height, full_d, last_d)

def erase_rows(model, x, y, z, full_w, last_w, height, full_d, last_d):
    cubes = full_w + (1 if last_w else 0)
    if full_d == 0:
        if last_d != 0:
            return erase_row(model, x, y, z, full_w, last_w, height, last_d)
        else:
            return single() ** (full_w + (1 if last_w else 0))
    else:
        prog  = erase_row(model, x, y, z, full_w, last_w, height, G_DIST + 1)
        prog += move_z(G_DIST + 1) ** cubes
        prog += erase_rows(model, x, y, z + G_DIST + 1, full_w, last_w, height, full_d - 1, last_d)
        prog += move_z(-G_DIST - 1) ** cubes
        return prog

def erase_row(model, x, y, z, full_w, last_w, height, depth):
    logging.debug("erase row at %d %d %d; full_w=%d, last_w=%d; %d x %d", x,y,z,full_w,last_w,height,depth)

    # SAME UGLY HACK
    prog_init = single()
    prog_fini = single()
    if depth == 1:
        depth += 1
        prog_init += move_z(-1)
        prog_fini += move_z(+1)
        z -= 1
    if height == 1:
        height += 1
        prog_init += move_y(+1)
        prog_fini += move_y(-1)
        y += 1


    prog_depl = empty()
    for i in range(full_w):
        prog_depl //= deploy_cube(model, x + i * (G_DIST + 1),y,z, G_DIST + 1,height,depth)
    if last_w != 0:
        prog_depl //= deploy_cube(model, x + full_w * (G_DIST + 1),y,z, last_w,height,depth)

    prog_void = empty()
    for i in range(full_w):
        prog_void //= void_cube(G_DIST + 1, height, depth)
    if last_w != 0:
        prog_void //= void_cube(last_w, height, depth)

    prog_clps = empty()
    for i in range(full_w):
        prog_clps //= collapse_cube(G_DIST + 1,height,depth)
    if last_w != 0:
        prog_clps //= collapse_cube(last_w,height,depth)

    return prog_init + prog_depl + prog_void + prog_clps + prog_fini

def deploy_cube(model, x, y, z, width, height, depth):
    prog7  = move_z(depth) + spawn_down(model, x + (width-1), y, z + (depth+1)) + \
             (single() // drill_down(model, x + (width-1), y-1, z + (depth+1), height-1))

    prog57 = move_x(width-2) + spawn_down(model, x + (width-1), y, z) + \
             (+single(Fission(Diff(0,0,1), 1)) // single()) + \
             (single() // move_y(-height+1) // prog7)

    prog3  = move_z(depth) + spawn_down(model, x, y, z + (depth+1)) + \
             (single() // drill_down(model, x, y - 1, z + (depth+1), height-1))

    prog1  = +single(Fission(Diff(0,-1,0), 0)) + \
             (+single(Fission(Diff(0,0,1), 1)) // single()) + \
             (+single(Fission(Diff(1,0,0), 3)) // single() // single()) + \
             (single() // move_y(-height+1) // prog3 // prog57)

    return prog1

def void_cube(width, height, depth):
    return single(GVoid(Diff(0,-1, 1), Diff(width-1,-height+1,depth-1)))   // \
           single(GVoid(Diff(0, 0, 1), Diff(width-1,height-1,depth-1)))    // \
           single(GVoid(Diff(0,-1,-1), Diff(width-1,-height+1,-depth+1)))  // \
           single(GVoid(Diff(0, 0,-1), Diff(width-1,height-1,-depth+1)))   // \
           single(GVoid(Diff(0,-1, 1), Diff(-width+1,-height+1,depth-1)))  // \
           single(GVoid(Diff(0, 0, 1), Diff(-width+1,height-1,depth-1)))   // \
           single(GVoid(Diff(0,-1,-1), Diff(-width+1,-height+1,-depth+1))) // \
           single(GVoid(Diff(0, 0,-1), Diff(-width+1,height-1,-depth+1)))


def collapse_cube(width, height, depth):
    # Move 2 up to 1 (4 to 3, 6 to 5, 8 to 7)
    prog_contract_up = (single() // move_y(height-1)) + -(single(FusionP(Diff(0,-1,0))) // single(FusionS(Diff(0,1,0))))
    # Move 3 back to 1 (7 to 5)
    prog_contract_back = (single() // move_z(-depth)) + -(single(FusionP(Diff(0,0,1))) // single(FusionS(Diff(0,0,-1))))
    # Move 5 left to 1
    prog_contract_left = (single() // move_x(-width+2)) + -(single(FusionP(Diff(1,0,0))) // single(FusionS(Diff(-1,0,0))))

    return (prog_contract_up ** 4) + (prog_contract_back ** 2) + prog_contract_left


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
        prog += move_y(-step)
        y -= step
        depth -= step
    return prog
