import logging
logger = logging.getLogger(__name__)

import itertools

from production.commands import *

# Current bot waits for some action to be completed by other bots
# with ids larger than its.
def wait_for(other_steps):
    return map(lambda ms: [Wait()] + ms, other_steps)

# Takes a list of lists of moves performed by different bots independently
# and executes them in parallel.
def parallel(*bots_moves):
    return itertools.zip_longest(*bots_moves, fillvalue=Wait())

# Takes a list of lists of moves performed by different bots independently
# and executes them one move per tick
def sequential(*bots_moves, skip=Wait()):
    res = []
    n_bots = len(bots_moves)
    for (i,bot) in enumerate(bots_moves):
        res.extend(list(map(lambda mv: [skip]*i + [mv] + [skip]*(n_bots-i-1), bot)))
    return res
