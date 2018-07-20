from dataclasses import dataclass


@dataclass(frozen=True)
class Pos:
    x: int
    y: int
    z: int

    def __add__(self, d: 'Diff') -> 'Pos':
        return Pos(self.x + d.dx, self.y + d.dy, self.z + d.dz)

    def __sub__(self, other: 'Pos') -> 'Diff':
        return Diff(self.x - other.x, self.y - other.y, self.z - other.z)

    def is_inside_matrix(self, R) -> bool:
        return 0 <= self.x < R and 0 <= self.y < R and 0 <= self.z < R


@dataclass(frozen=True)
class Diff:
    dx: int
    dy: int
    dz: int

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


def region_dimension(c1: Pos, c2: Pos):
    result = 0
    if c1.x != c2.x:
        result += 1
    if c1.y != c2.y:
        result += 1
    if c1.z != c2.z:
        result += 1
    return result
