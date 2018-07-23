import logging
logger = logging.getLogger(__name__)

from math import floor

from production.basics import JUMP_LONG, Pos, Diff
from production.commands import *
from production.orchestrate2 import GroupProgram, empty, single, singles


###
# Movement and navigation
###

# Move a group consisting of a single bot right (left).
def move_x(delta):
    if delta == 0: return single()
    c = 1 - 2 * (delta < 0)
    delta = abs(delta)
    full_steps = delta // JUMP_LONG
    last = delta - JUMP_LONG * full_steps
    return singles([SMove(Diff(c * JUMP_LONG,0,0))] * full_steps + [SMove(Diff(c * last,0,0))] * (last > 0))

# Move a group consisting of a single bot up (down).
def move_y(delta):
    if delta == 0: return single()
    c = 1 - 2 * (delta < 0)
    delta = abs(delta)
    full_steps = delta // JUMP_LONG
    last = delta - JUMP_LONG * full_steps
    return singles([SMove(Diff(0,c * JUMP_LONG,0))] * full_steps + [SMove(Diff(0,c * last,0))] * (last > 0))

# Move a group consisting of a single bot farther (closer).
def move_z(delta):
    if delta == 0: return single()
    c = 1 - 2 * (delta < 0)
    delta = abs(delta)
    full_steps = delta // JUMP_LONG
    last = delta - JUMP_LONG * full_steps
    return singles([SMove(Diff(0,0,c * JUMP_LONG))] * full_steps + [SMove(Diff(0,0,c * last))] * (last > 0))



####
# Fission / fusion
####


# Group program for a single bot to fission and fill the space to the right
# (increasing x) with copies as evenly as possible.

# seeds = seeds it has
# space_right = width of the line (including the cell of the first bot)
# Assumption: `[bid] ++ seeds` is contiguous.
# Assumption: len(seeds) <= space_right - 1
#TODO: currently they just telescope, but it would be better to do the log thing
def fission_fill_right(seeds, space_right):
    strips = []
    strips_sum = 0

    def fork_and_move_new(seeds, space_right):
        if not seeds: return single()

        # Each bot gets its own strip
        bots = 1 + len(seeds)
        strip_width = floor(space_right / bots)
        strips.append(strip_width)
        nonlocal strips_sum
        strips_sum += strip_width

        # fork right giving them all our seeds
        prog = +single(Fission(Diff(1,0,0), len(seeds) - 1))

        # the new bot moves into its position and does the same
        newprog = move_x(strip_width - 1) + fork_and_move_new(seeds[1:], space_right - strip_width)
        # wait for it do this
        prog += single() // newprog

        return prog
    prog = fork_and_move_new(seeds, space_right)
    strips.append(space_right - strips_sum)
    return (prog, strips)

def fusion_unfill_right(strips):
    num_bots = len(strips)
    def move_and_unfork(strips):
        if not strips: return single()

        # Wait for everyone on the right to finish
        prog = single() // move_and_unfork(strips[1:])

        # Move our child bot to the left
        prog += single() // move_x(-1 * (strips[0] - 1))

        # Unfork the bot immediately to the right
        prog += -single(FusionP(Diff(1,0,0))) // single(FusionS(Diff(-1,0,0)))

        return prog
    prog = move_and_unfork(strips[:-1])
    return prog



####
# 2D printing
####

# Prints a 2D layer with y = i.
# Each strip is printed by its own bot.
# Assumption: all bots are at y = i + 1.
# Assumption: all bots are at z = 1. # TODO: relax this
# Assumption: first bot it at x = 0.
# Assumption: bots are spaced by distances in `strips`.
def print_layer_below(model, i, strips, last):
    prog = empty()
    lbound = 0
    for strip in strips:
        rbound = lbound + strip
        prog //= print_strip_below(model, i, lbound, rbound, last)
        lbound = rbound
    return prog

# Prints part of the model layer with y = i which lies at
# Single-bot program.
# lbound <= x < rbound
def print_strip_below(model, i, lbound, rbound, last_layer):
    prog = single()
    for z in range(1, model.R - 1):
        if model[Pos(lbound,i,z)]:
            prog += single(Fill(Diff(0,-1,0)))
        for x in range(lbound + 1, rbound):
            prog += single(SMove(Diff(1,0,0)))
            if model[Pos(x,i,z)]:
                prog += single(Fill(Diff(0,-1,0)))
        prog += move_x(-1 * (rbound - lbound - 1))
        prog += single(SMove(Diff(0,0,1))) # TODO: optimise this part, make an L move
    prog += move_z(-1 * (model.R - 2 + last_layer))
    return prog


# Prints an orthotope (right rectangular prism), i.e. a part of the model
# starting from where the bot stands currentlty and extending right and up.
# Assumption: bot is at y = 1, z = 1
def print_hyperrectangle(model, x, width, height):
    prog = single()
    for i in range(height):
        last = i == height - 1
        prog += print_strip_below(model, i, x, x + width, last)
        if not last:
            prog += single(SMove(Diff(0,1,0)))
    return prog
