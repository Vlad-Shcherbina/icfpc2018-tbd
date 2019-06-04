import logging
logger = logging.getLogger(__name__)

from dataclasses import dataclass
from typing import Iterable, Union
import itertools as it

from production.commands import *


@dataclass(frozen=True)
class GroupProgram:
    startSize: int
    endSize: int
    stepsSequence: Iterable[Iterable[Command]]

    # Compose two groups into a larger one (>>).
    # Make the two original groups act sequentially.
    def __rshift__(self: "GroupProgram", other: "GroupProgram") -> "GroupProgram":
        seq1 = map(lambda step: it.chain(step, it.repeat(Wait(), other.startSize)), self.stepsSequence)
        seq1 = map(lambda step: it.chain(it.repeat(Wait(), self.endSize), step), other.stepsSequence)
        newSeq = it.chain(seq1, seq2)
        return GroupProgram(self.startSize + other.startSize,
                self.endSize + other.endSize,
                newSeq)

    # Compose two groups into a larger one (//).
    # Run their actions in parallel
    def __floordiv__(self: "GroupProgram", other: "GroupProgram") -> "GroupProgram":
        def combine(step1: Iterable[Command], step2: Iterable[Command]) -> Iterable[Command]:
            if step1 is None:
                step1 = it.repeat(Wait(), self.endSize)
            if step2 is None:
                step2 = it.repeat(Wait(), other.endSize)
            return it.chain(step1, step2)

        newSeq = it.starmap(combine, it.zip_longest(self.stepsSequence, other.stepsSequence))
        return GroupProgram(self.startSize + other.startSize,
                self.endSize + other.endSize,
                newSeq)

    # Repeat the same program for a number of groups (**).
    def __pow__(self: "GroupProgram", times: int) -> "GroupProgram":
        newSeq = map(lambda step: it.chain(*it.repeat(list(step), times)), self.stepsSequence)
        return GroupProgram(self.startSize * times, self.endSize * times, newSeq)


    # Concatenate two sequences of steps by the same group (+).
    def __add__(self: "GroupProgram", other: "GroupProgram") -> "GroupProgram":
        assert self.endSize == other.startSize, '{} != {}'.format(self.endSize, other.startSize)
        newSeq = it.chain(self.stepsSequence, other.stepsSequence)
        return GroupProgram(self.startSize, other.endSize, newSeq)


    # Indicates that during the sequence the group grows by one (unary +).
    def __pos__(self: "GroupProgram") -> "GroupProgram":
        return GroupProgram(self.startSize, self.endSize + 1, self.stepsSequence)

    # Indicates that during the sequence the group shrinks by one (unary -).
    def __neg__(self: "GroupProgram") -> "GroupProgram":
        return GroupProgram(self.startSize, self.endSize - 1, self.stepsSequence)


    # Turn a sequence of moves of a single bot into a group program.
    @staticmethod
    def singleton(*moves: Iterable[Command], endSize=1) -> "GroupProgram":
        return GroupProgram(1, endSize, map(lambda move: [move], moves))

    # Turn a sequence of moves of an empty group into a group program.
    @staticmethod
    def empty(*moves: Iterable[Command]) -> "GroupProgram":
        return GroupProgram(0, 0, [])


    # Turns the iterable inside the program into a list which makes it safe
    # to refer to this program multiple times.
    def frozen(self):
        return GroupProgram(self.startSize, self.endSize,
                list(map(list, self.stepsSequence)))


    def __iter__(self):
        return it.chain(*self.stepsSequence)


single = GroupProgram.singleton

def singles(moves):
    return single(*moves)

empty = GroupProgram.empty
