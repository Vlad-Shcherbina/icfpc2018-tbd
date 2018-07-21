from dataclasses import dataclass

MAX_BOTS = 20
JUMP_LONG = 15
JUMP_SHORT = 5


@dataclass(frozen=True)
class Pos:
    x: int
    y: int
    z: int

    def __add__(self, d: 'Diff') -> 'Pos':
        return Pos(self.x + d.dx, self.y + d.dy, self.z + d.dz)

    def __sub__(self, other: 'Pos') -> 'Diff':
        return Diff(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, c: 'int') -> 'Pos':
        return Diff(self.x*c, self.y*c, self.z*c)

    def is_inside_matrix(self, R) -> bool:
        return 0 <= self.x < R and 0 <= self.y < R and 0 <= self.z < R

    def enum_adjacent(self, R):
        if self.x > 0:
            yield Pos(self.x - 1, self.y, self.z)
        if self.y > 0:
            yield Pos(self.x, self.y - 1, self.z)
        if self.z > 0:
            yield Pos(self.x, self.y, self.z - 1)
        if self.x + 1 < R:
            yield Pos(self.x + 1, self.y, self.z)
        if self.y + 1 < R:
            yield Pos(self.x, self.y + 1, self.z)
        if self.z + 1 < R:
            yield Pos(self.x, self.y, self.z + 1)


@dataclass(frozen=True)
class Diff:
    dx: int
    dy: int
    dz: int

    def __add__(self, d: 'Diff') -> 'Pos':
        return Diff(self.dx + d.dx, self.dy + d.dy, self.dz + d.dz)

    def __mul__(self, c: 'int') -> 'Pos':
        return Diff(self.dx*c, self.dy*c, self.dz*c)

    def mlen(self):
        return abs(self.dx) + abs(self.dy) + abs(self.dz)

    def clen(self):
        return max(abs(self.dx), abs(self.dy), abs(self.dz))

    def is_linear(self):
        return sum(1 for d in (self.dx, self.dy, self.dz) if d != 0) == 1

    def is_short_linear(self):
        return self.is_linear() and self.mlen() <= 5

    def is_long_linear(self):
        return self.is_linear() and self.mlen() <= 15

    def is_near(self):
        return 0 < self.mlen() <= 2 and self.clen() == 1

    def is_far(self):
        return 0 < self.clen() <= 30


@dataclass()
class Region:
    pos_min: Pos
    pos_max: Pos

    def __init__(self, pos1: Pos, pos2: Pos):
        self.pos_min = Pos(min(pos1.x, pos2.x), min(pos1.y, pos2.y),
                min(pos1.z, pos2.z))
        self.pos_max = Pos(max(pos1.x, pos2.x), max(pos1.y, pos2.y),
                max(pos1.z, pos2.z))

    def dimension(self):
        return (self.pos_min.x != self.pos_max.x) + \
                (self.pos_min.y != self.pos_max.y) + \
                (self.pos_min.z != self.pos_max.z)

    def __iter__(self):
        for x in range(self.pos_min.x, self.pos_max.x + 1):
            for y in range(self.pos_min.y, self.pos_max.y + 1):
                for z in range(self.pos_min.z, self.pos_max.z + 1):
                    yield Pos(x, y, z)


def region_dimension(c1: Pos, c2: Pos):
    result = 0
    if c1.x != c2.x:
        result += 1
    if c1.y != c2.y:
        result += 1
    if c1.z != c2.z:
        result += 1
    return result


def enum_region_cells(c1: Pos, c2: Pos):
    for x in range(min(c1.x, c2.x), max(c1.x, c2.x) + 1):
        for y in range(min(c1.y, c2.y), max(c1.y, c2.y) + 1):
            for z in range(min(c1.z, c2.z), max(c1.z, c2.z) + 1):
                yield Pos(x, y, z)
