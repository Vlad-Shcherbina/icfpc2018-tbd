from typing import List, Set, Callable, Tuple
from dataclasses import dataclass

from production.cpp_emulator.emulator import Pos, Diff
from production.commands import *
from production.model import Model


LOW = "LOW"
HIGH = "HIGH"


def enum_region_cells(c1: Pos, c2: Pos):
    for x in range(min(c1.x, c2.x), max(c1.x, c2.x) + 1):
        for y in range(min(c1.y, c2.y), max(c1.y, c2.y) + 1):
            for z in range(min(c1.z, c2.z), max(c1.z, c2.z) + 1):
                yield Pos(x, y, z)



@dataclass
class Bot:
    bid: int
    pos: Pos
    seeds: List[int]


class State:
    # TODO: from model

    def __init__(self, R):
        self.R = R
        self.matrix = Model(R)
        self.harmonics = LOW
        self.energy = 0
        self.bots = [Bot(1, Pos(0, 0, 0), list(range(39)))]  # TODO

    def __setitem__(self, pos: Pos, value):
        assert value == 0 or value == 1
        self.matrix[pos] = bool(value)

    def __getitem__(self, pos: Pos):
        return self.matrix[pos]
        
    def assert_well_formed(self):
        if self.harmonics == LOW:
            grounded = self.matrix.grounded_voxels()
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

        self.energy += 20 * len(self.bots)

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
        return {c}, effect

    elif isinstance(cmd, SMove):
        assert cmd.lld.is_long_linear()
        c1 = c + cmd.lld
        if not c1.is_inside_matrix(state.R):
            raise PreconditionError()
        vol = set(enum_region_cells(c, c1))
        for p in vol:
            if state[p] != 0:
                raise PreconditionError()
        def effect():
            bot.pos = c1
            state.energy += 2 * cmd.lld.mlen()
        return vol, effect

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
            if state[p] != 0:
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
        if state[c1] != 0:
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


def main():
    from production import data_files

    name = 'LA004'
    m = Model.parse(data_files.lightning_problem(f'{name}_tgt.mdl'))

    trace_name = f'{name}.nbt'
    trace = parse_commands(
        buf=data_files.lightning_default_trace(trace_name),
        source=trace_name)

    state = State(m.R)
    state.time_step(trace)


if __name__ == '__main__':
    main()
