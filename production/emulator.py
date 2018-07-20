from typing import List, Set, Callable, Tuple
from dataclasses import dataclass

from production.basics import Pos, Diff
from production.commands import *


LOW = "LOW"
HIGH = "HIGH"


@dataclass
class Bot:
    bid: int
    pos: Pos
    seeds: List[int]


class State:
    # TODO: from model

    def __init__(self, R):
        self.R = R
        self.matrix = [[[0] * R for _ in range(R)] for _ in range(R)]
        self.harmonics = LOW
        self.energy = 0
        self.bots = []  # TODO

    def __getitem__(self, pos: Pos):
        return self.matrix[pos.x][pos.y][pos.z]

    def __setitem__(self, pos: Pos, value):
        assert value == 0 or value == 1
        self.matrix[pos.x][pos.y][pos.z] = value

    def enum_voxels(self):
        for x in range(R):
            for y in range(R):
                for z in range(R):
                    yield Pos(x, y, z)

    def grounded(self) -> Set[Pos]:
        visited = set()

        def visit(pos):
            if pos in visited:
                return
            if self[pos] == 0:
                return
            visited.add(pos)
            for p in pos.enum_adjacent(self.R):
                visit(p)

        for x in range(self.R):
            for z in range(self.R):
                visit(Pos(x, 0, z))

        return visited

    def assert_well_formed(self):
        if self.harmonics == LOW:
            grounded = self.grounded()
            for p in self.enum_voxels():
                if self[p] == 1:
                    assert p in grounded

        bids = {bot.bid for bot in self.bots}
        assert len(bids) == len(self.bots), 'bids not unique'

        poss = {bot.pos for bot in self.bots}
        assert len(poss) == len(self.bots), 'positions not unique'

        for bot in self.bots:
            assert matrix[bot.pos.x][bot.pos.y][bot.pos.z] == 0, 'bot in Full voxel'

        all_seeds = {seed for bot in self.bots for seed in bot.seeds}
        assert len(all_seeds) == sum(len(bot.seeds) for bot in self.bots)

        for bot in self.bots:
            assert bot.bid not in all_seeds

    def time_step(self, trace):
        assert len(trace) >= len(self.bots)

        # TODO: check preconditions
        # TODO: check volatile sets don't overlap

        if self.harmonics == HIGH:
            self.energy += 30 * self.R**3
        elif self.harmonics == LOW:
            self.energy += 3 * self.R**3
        else:
            assert False, self.harmonics

        s.energy += 20 * len(self.bots)

        bc = list(zip)

        # TODO: run commands

        # TODO: drop prefix from trace


class PreconditionError(Exception):
    pass


def process_command(state, bot, cmd) -> Tuple[Set[Pos], Callable[..., None]]:
    '''Checks preconditions and returns (volatile set, effect) pair.'''
    c = bot.pos
    if isinstance(cmd, Halt):
        if c != Pos(0, 0, 0):
            raise PreconditionError()
        if len(state.bots) != 1:
            raise PreconditionError()
        if state.harmonics != LOW:
            raise PreconditionError()
        def effect():
            state.bots = []
        return {c}, effect

    elif isinstance(cmd, Wait):
        def effect():
            pass
        return {c}, effect

    elif isinstance(cmd, Flip):
        def effect():
            if state.harmonics == HIGH:
                state.harmonics = LOW
            elif state.harmonics == LOW:
                state.harmonics = HIGH
            else:
                assert state.harmonics
        return {c}

    elif isinstance(cmd, SMove):
        assert cmd.lld.is_long_linear()
        c1 = c + cmd.lld
        if not c1.is_inside_matrix(state.R):
            raise PreconditionError()
        vol = set(enum_region_cells(c, c1))
        for p in vol:
            if stat[p] != 0:
                raise PreconditionError()
        def effect():
            bot.pos = c1
            state.energy += 2 * cmd.lld.mlen()
        return vol, effect()

    elif isinstance(cmd, LMove):
        assert cmd.sld1.is_short_linear()
        assert cmd.sld2.is_short_linear()
        c1 = c + cmd.sld1
        c2 = c1 + cmd.sld2
        if not c1.is_inside_matrix(state.R):
            raise PreconditionError()
        if not c2.is_inside_matrix(state.R):
            raise PreconditionError()
        vol = set(enum_region_cells(c, c1)) + set(enum_region_cells(c1, c2))
        for p in vol:
            if stat[p] != 0:
                raise PreconditionError()
        def effect():
            bot.pos = c2
            state.energy += 2 * (cmd.sld1.mlen() + 2 + cmd.sld2.mlen())
        return vol, effect

    elif isinstance(cmd, Fission):
        assert cmd.nd.is_near()
        assert bot.seeds
        c1 = c + cmd.nd
        if not c1.is_inside_matrix(state.R):
            raise PreconditionError()
        if stat[c1] != 0:
            raise PreconditionError()
        if len(bot.seeds) < m + 1:
            raise PreconditionError()
        bot.seeds.sort()

        def effect():
            new_bot = Bot(
                bid=bot.seeds[0],
                pos=c1,
                seeds=bot.seeds[1 : m + 1])
            bot.seeds = bot.seeds[m + 1:]
            state.bots.append(new_bot)
            state.energy += 24

        return {c, c1}, effect

    elif isinstance(cmd, Fill):
        assert cmd.nd.is_near()
        c1 = c + cmd.nd
        if not c1.is_inside_matrix(state.R):
            raise PreconditionError()

        def effect():
            if state[c1] == 0:
                state[c1] = 1
                state.energy += 12
            elif state[c1] == 1:
                state.energy += 6

        return {c, c1}, effect

    elif isinstance(cmd, FusionP):
        raise NotImplementedError()  # TODO

    elif isinstance(cmd, FusionS):
        raise NotImplementedError()  # TODO

    else:
        assert False, cmd
