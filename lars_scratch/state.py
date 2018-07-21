from dataclasses import dataclass
from typing import List
from pprint import pprint
from enum import Enum

from production.basics import Pos, Diff
from production.commands import Command

# Feel free not to use some values or to add more values
class Cell(Enum):
    EMPTY = 1
    WILL_BE_FILLED = 3 # when a bot is scheduled to fill a cell
    FULL = 4
    WILL_BE_EMPTIED = 6 # when a bot is scheduled to empty a cell
    VOLATILE = 7
    RESERVED = 8
    BOT = 9

@dataclass(frozen=True)
class Bot:
    bid: int
    pos: Pos

@dataclass(frozen=True)
class State:
    bots: List[Bot]
    trace: List[Command]
    R: int
    _data: List[Cell]
    target: Model

    def __init__(self, source: Model, target: Model):
        assert source.R == target.R
        self.R = source.R
        for i in range(R * R * R):
            _data[i] = Cell.FULL if source._data[i] else Cell.EMPTY
        self.target = target
        self.bots = [Bot(1, Pos(0, 0, 0))]
        self._set(Pos(0, 0, 0), Cell.BOT)
        self.trace = []

    def __getitem__(self, pos: Pos) -> Cell:
        R = self.R
        assert pos.is_inside_matrix(R), pos
        return self._data[pos.x * R * R + pos.y * R + pos.z]

    def _set(self, pos: Pos, value: Cell):
        R = self.R
        assert pos.is_inside_matrix(R)
        self._data[pos.x * R * R + pos.y * R + pos.z] = value

    def tick(self, commands: List[Command]):
        assert len(commands) == len(self.bots)

        for bot, command in zip(self.bots, commands):
            pass
