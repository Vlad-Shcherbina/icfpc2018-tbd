from typing import List
from itertools import chain

import production.commands as Cmd
from production.model import Model
from production.basics import (Diff, Pos)


def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    elif x == 0:
        return 0


def direction(diff: 'Diff') -> 'Diff':
    return Diff(sign(diff.dx), sign(diff.dy), sign(diff.dz))


def components(diff: 'Diff') -> List['Diff']:
    return [
        Diff(diff.dx,   0,         0),
        Diff(0,         diff.dy,   0),
        Diff(0,         0,         diff.dz)
    ]


# We expect moves only in one dimension
def split_linear_move(diff: 'Diff'):
    #TODO: detect collisions with already-filled voxels or other bots
    
    if diff.mlen() == 0:
        return
    assert(diff.is_linear())

    l = abs(diff.mlen())
    norm = direction(diff)
    while l > 0:
        c = min(l, 15)
        l -= c
        yield Cmd.SMove(norm * c)


def navigate(f: 'Pos', t: 'Pos'):
    #TODO: detect collisions
    
    # y is last
    diff = t - f
    (dx, dy, dz) = components(diff)
    return chain(
        split_linear_move(dx),
        split_linear_move(dz),
        split_linear_move(dy),
    )


def nearby_voxel(voxel: 'Pos'):
    '''
    Compute a voxel near enough to the requested voxel so that `Fill`ing it is possible
    but not *on* the requested voxel (as a bot cannot `Fill` the voxel it is occupying).

    Right now, just the voxel's top neighbor. This will most likely need to change, as that voxel
    may already be full or may have another bot there. Can actually be any voxel within a near
    coordinate difference (nd) of the requested one.
    '''
    
    #TODO: detect a voxel near the requested one that is not occupied by an already-filled
    #      voxel or another bot

    return voxel + Diff(0, 1, 0)


def navigate_near_voxel(current_position: 'Pos', voxel: 'Pos'):
    return navigate(current_position, nearby_voxel(voxel))
