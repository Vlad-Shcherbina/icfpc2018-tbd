from typing import List, Set
from dataclasses import dataclass

from production.basics import Pos, Diff


LOW = "LOW"
HIGH = "HIGH"


@dataclass
class Bot:
    bid: int
    pos: Pos
    seeds: List[int]


def adjacent(pos, R):
    if pos.x > 0:
        yield Pos(pos.x - 1, pos.y, pos.z)
    if pos.y > 0:
        yield Pos(pos.x, pos.y - 1, pos.z)
    if pos.z > 0:
        yield Pos(pos.x, pos.y, pos.z - 1)
    if pos.x + 1 < R:
        yield Pos(pos.x + 1, pos.y, pos.z)
    if pos.y + 1 < R:
        yield Pos(pos.x, pos.y + 1, pos.z)
    if pos.z + 1 < R:
        yield Pos(pos.x, pos.y, pos.z + 1)


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
            for p in adjacent(pos, self.R):
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
