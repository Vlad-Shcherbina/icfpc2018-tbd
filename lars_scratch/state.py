from dataclasses import dataclass
from typing import List
from pprint import pprint
from enum import Enum

from production.model import Model
from production.basics import Pos, Diff, Region
from production.commands import *

# TODO: Track volatility using a set
# TODO: Track total energy used

# Feel free not to use some values or to add more values
class Cell(Enum):
    EMPTY = 1
    WILL_BE_FILLED = 3 # when a bot is scheduled to fill a cell
    FULL = 4
    WILL_BE_EMPTIED = 6 # when a bot is scheduled to empty a cell
    RESERVED = 8
    BOT = 9

@dataclass()
class Bot:
    bid: int
    pos: Pos
    seeds: List[int]

    def move(self, diff: Diff):
        self.pos += diff

@dataclass()
class State:
    antigrav: bool
    bots: List[Bot]
    trace: List[Command]
    R: int
    _data: List[Cell]
    target: Model

    def __init__(self, source: Model, target: Model):
        assert source.R == target.R
        self.R = source.R
        self._data = [Cell.FULL if source._data[i] else Cell.EMPTY
                for i in range(self.R ** 3)]
        self.target = target
        self.bots = [Bot(1, Pos(0, 0, 0), list(range(2, 41)))]
        self._set(Pos(0, 0, 0), Cell.BOT)
        self.trace = []
        self.antigrav = False

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
        newbots = []

        for bot, command in zip(self.bots, commands):
            if isinstance(command, Halt):
                assert len(self.bots) == 1
                assert self.bots[0].pos == Pos(0, 0, 0)
            elif isinstance(command, Wait):
                newbots.append(bot)
            elif isinstance(command, Flip):
                self.antigrav = not self.antigrav
                newbots.append(bot)

            elif isinstance(command, SMove):
                assert command.lld.is_long_linear()
                self._set(bot.pos, Cell.EMPTY)
                bot.move(command.lld)
                self._set(bot.pos, Cell.BOT)
                newbots.append(bot)
            elif isinstance(command, LMove):
                assert command.sld1.is_short_linear()
                assert command.sld2.is_short_linear()
                self._set(bot.pos, Cell.EMPTY)
                bot.move(command.sld1)
                assert bot.pos.is_inside_matrix(self.R)
                bot.move(command.sld1)
                self._set(bot.pos, Cell.BOT)
                newbots.append(bot)

            elif isinstance(command, Fission):
                newbot = Bot(bot.seeds[0], bot.pos + command.nd,
                        bot.seeds[1:command.m + 1])
                self._set(newbot.pos, Cell.BOT)
                bot.seeds = bot.seeds[command.m + 1:]
                newbots.append(bot)
                newbots.append(newbot)

            elif isinstance(command, Fill):
                assert command.nd.is_near()
                self._set(bot.pos + command.nd, Cell.FULL)
                newbots.append(bot)
            elif isinstance(command, Void):
                assert command.nd.is_near()
                self._set(bot.pos + command.nd, Cell.EMPTY)
                newbots.append(bot)

            elif isinstance(command, FusionP):
                assert self[(bot.pos + command.nd)] == Cell.BOT
                self._set(bot.pos + command.nd, Cell.EMPTY)
                newbots.append(bot)
            elif isinstance(command, FusionS):
                assert self[(bot.pos + command.nd)] == Cell.BOT

            elif isinstance(command, GFill):
                assert command.nd.is_near()
                assert command.fd.is_far()
                for pos in Region(bot.pos + command.nd, bot.pos + command.nd +
                        command.fd):
                    self._set(pos, Cell.FULL)
                newbots.append(bot)
            elif isinstance(command, GVoid):
                assert command.nd.is_near()
                assert command.fd.is_far()
                for pos in Region(bot.pos + command.nd, bot.pos + command.nd +
                        command.fd):
                    self._set(pos, Cell.EMPTY)
                newbots.append(bot)

        self.bots = newbots
        self.bots.sort(key=lambda bot: bot.bid)
        self.trace.append(commands)

    def dump_trace(self):
        return compose_commands(cmd for tick in self.trace for cmd in tick)
