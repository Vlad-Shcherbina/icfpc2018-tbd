from typing import Tuple, Optional

from math import floor

import logging
logger = logging.getLogger(__name__)

from production.basics import MAX_BOTS, JUMP_LONG, Pos, Diff
from production.commands import *
from production.model import Model
from production.orchestrate import parallel, sequential, wait_for

def bounding_box(model) -> Tuple[Pos, Pos]:
    return bounding_box_region(model)

def bounding_box_region(model, fx : Optional[int] = None, fy : Optional[int] = None, fz : Optional[int] = None) -> Tuple[Pos, Pos]:
    def rangify(R, fv = None):
        if fv is None:
            fv = range(R)
        else:
            fv = [fv]
        return fv
    fx = rangify(model.R, fx)
    fy = rangify(model.R, fy)
    fz = rangify(model.R, fz)

    filled_cell_visited = False
    for x in fx:
        for y in fy:
            for z in fz:
                if model[Pos(x,y,z)]:
                    if not filled_cell_visited:
                        pos0 = pos1 = Pos(x,y,z)
                        filled_cell_visited = True
                    else:
                        pos0 = Pos(min(pos0.x,x),min(pos0.y,y),min(pos0.z,z))
                        pos1 = Pos(max(pos1.x,x),max(pos1.y,y),max(pos1.z,z))

    assert filled_cell_visited
    return (pos0,pos1)

def is_inside_region(pt : Pos, pt0 : Pos, pt1 : Pos) -> bool:
    return pt0.x <= pt.x <= pt1.x and pt0.y <= pt.y <= pt1.y and pt0.z <= pt.z <= pt1.z


# Orthographic (orthogonal) projection from the top
def projection_top(m):
    return [ [any([m[Pos(x,y,z)] for y in range(m.R)]) for z in range(m.R)] for x in range(m.R) ]


####
# Fission / fusion
####

# Seeds is the list of seeds of the current bot.
# This function will make the current bot fission and fill the space to the right
# (increasing x) with copies as evenly as possible.

# seeds = seeds he has
# space_right = width of the line (including the cell of the first bot)
# Assumption: `[bid] ++ seeds` is contiguous.

#TODO: currently they just telescope, but it would be better to do the log thing
def fission_fill_right(seeds, space_right):
    strips = []
    strips_sum = 0

    def fork_and_move_new(seeds, space_right):
        if not seeds: return []
        #logger.debug('space_right = %d', space_right)

        # Each bot gets its own strip
        bots = 1 + len(seeds)
        #logger.debug('Bots = %d', bots)
        strip_width = floor(space_right / bots)
        #logger.debug('Strip width = %d', strip_width)
        strips.append(strip_width)
        nonlocal strips_sum
        strips_sum += strip_width

        ticks = []

        # fork right giving them all our seeds
        ticks.append([Fission(Diff(1,0,0), len(seeds) - 1)])

        # move the new bot to its position
        ticks.extend(wait_for(sequential(move_x(strip_width - 1))))

        # Let the new bot do the same
        ticks.extend(wait_for(fork_and_move_new(seeds[1:], space_right - strip_width)))

        return ticks
    steps = fork_and_move_new(seeds, space_right)
    strips.append(space_right - strips_sum)
    return (steps, strips)

def fusion(positions):
    '''Return a sequence of commands that merges the bot ids given in bids.
    Assumes bids is in increasing order and their corresponding positions are in
    an empty xz plane, have identical y and z coordinates and increasing x
    coordinates. Assumes no other bots exist. Returns commands that end with all
    bots merged into the first one.'''
    commands = []
    while len(positions) > 1:
        newpositions = []
        i = 0
        while i < len(positions):
            if i + 1 < len(positions):
                if positions[i].x + 1 == positions[i + 1].x:
                    # FUSE
                    commands.append(FusionP(Diff(1, 0, 0)))
                    commands.append(FusionS(Diff(-1, 0, 0)))
                    newpositions.append(positions[i])
                    i += 2
                else:
                    # MOVE CLOSER
                    dist = Diff(max(-15, positions[i] + 1 - positions[i + 1]),
                            0, 0)
                    commands.append(Wait())
                    commands.append(SMove(dist))
                    newpositions.append(positions[i])
                    newpositions.append(positions[i + 1] + dist)
                    i += 2
            else:
                dist = Diff(max(-15, positions[i - 1] + 1 - positions[i]), 0, 0)
                commands.append(SMove(dist))
                newpositions.append(positions[i] + dist)
                i += 1
        positions = newpositions
    return commands


# Move current bot dx to the right (left)
# Returns a list of moves for the current bot
def move_x(dx):
    c = 1 - 2 * (dx < 0)
    dx = abs(dx)
    full_steps = dx // JUMP_LONG
    last = dx - JUMP_LONG * full_steps
    return [SMove(Diff(c * JUMP_LONG,0,0))] * full_steps + [SMove(Diff(c * last,0,0))] * (last > 0)

# See ^
def move_z(dz):
    c = 1 - 2 * (dz < 0)
    dz = abs(dz)
    full_steps = dz // JUMP_LONG
    last = dz - JUMP_LONG * full_steps
    return [SMove(Diff(0,0,c * JUMP_LONG))] * full_steps + [SMove(Diff(0,0,c * last))] * (last > 0)



####
# 2D printing
####

# Prints a 2D layer with y = i.
# Assumption: all bots are at y = i + 1.
# Assumption: all bots are at z = 1. # TODO: relax this
# Assumption: first bot it at x = 0.
# Assumption: bots are spaced by distances in `strips`.
def print_layer_below(model, i, strips):
    bots = []
    lbound = 0
    logging.debug('%d', len(strips))
    for strip in strips:
        rbound = lbound + strip
        bots.append(print_strip_below(model, i, lbound, rbound))
        lbound = rbound
    return parallel(*bots)

# Prints part of the model layer with y = i which lies at
# lbound <= x < rbound
def print_strip_below(model, i, lbound, rbound):
    moves = []
    for z in range(0, model.R - 2):
        if model[Pos(lbound,i,z)]:
            moves.append(Fill(Diff(0,-1,0)))
        for x in range(lbound + 1, rbound):
            moves.append(SMove(Diff(1,0,0)))
            if model[Pos(x,i,z)]:
                moves.append(Fill(Diff(0,-1,0)))
        moves.extend(move_x(-1 * (rbound - lbound - 1)))
        moves.append(SMove(Diff(0,0,1))) # TODO: optimise this part, make an L move
    moves.extend(move_z(-1 * (model.R - 2)))
    return moves
