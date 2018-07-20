from dataclasses import dataclass


@dataclass
class Pos:
    x: int
    y: int
    z: int

    def __add__(self, d: 'Diff') -> 'Pos':
        return Pos(self.x + d.dx, self.y + d.dy, self.z + d.dz)

    def __sub__(self, other: 'Pos') -> 'Diff':
        return Diff(self.x - other.x, self.y - other.y, self.z - other.z)


@dataclass
class Diff:
    dx: int
    dy: int
    dz: int

    def mlen(self):
        return abs(self.dx) + abs(self.dy) + abs(self.dz)

    def clen(self):
        return max(abs(self.dx), abs(self.dy), abs(self.dz))
