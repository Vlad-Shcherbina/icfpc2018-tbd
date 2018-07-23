from dataclasses import dataclass
from production.cpp_emulator.emulator import Pos, Diff, region_dimension


JUMP_LONG = 15
JUMP_SHORT = 5

# not implemented in C++ currently
@dataclass()
class Region:
    pos_min: Pos
    pos_max: Pos

    def __init__(self, pos1: Pos, pos2: Pos):
        self.pos_min = pos1.min(pos2)
        self.pos_max = pos1.max(pos2)

    def dimension(self):
        return (self.pos_min.x != self.pos_max.x) + \
                (self.pos_min.y != self.pos_max.y) + \
                (self.pos_min.z != self.pos_max.z)

    def __iter__(self):
        for x in range(self.pos_min.x, self.pos_max.x + 1):
            for y in range(self.pos_min.y, self.pos_max.y + 1):
                for z in range(self.pos_min.z, self.pos_max.z + 1):
                    yield Pos(x, y, z)

    def expand(self, pos: Pos):
        '''Expand region to include the specified position.'''
        self.pos_min = self.pos_min.min(pos)
        self.pos_max = self.pos_max.max(pos)


