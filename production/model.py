from typing import Optional, Set
from bitarray import bitarray

from production.basics import Pos, Region


class Model:
    def __init__(self, R: int, data: Optional[bytes] = None):
        if data is None:
            data = b'\0' * ((R**3 - 1) // 8 + 1)
        self.R = R
        assert len(data) == (R**3 - 1) // 8 + 1
        self._data = bitarray(0, endian='little')
        self._data.frombytes(data)

    def __getitem__(self, pos: Pos) -> bool:
        R = self.R
        assert pos.is_inside_matrix(R), pos
        return self._data[pos.x * R * R + pos.y * R + pos.z]

    def __setitem__(self, pos: Pos, value: bool):
        R = self.R
        assert pos.is_inside_matrix(R)
        self._data[pos.x * R * R + pos.y * R + pos.z] = value

    def __eq__(self, other):
        return self.R == other.R\
           and self.filled_voxels() == other.filled_voxels()

    @staticmethod
    def parse(data: bytes) -> 'Model':
        return Model(R=data[0], data=data[1:])

    def enum_voxels(self):
        for x in range(self.R):
            for y in range(self.R):
                for z in range(self.R):
                    yield Pos(x, y, z)


    def filled_voxels(self) -> Set[Pos]:
        filled = set()
        for x in range(self.R):
            for y in range(self.R):
                for z in range(self.R):
                    if self[Pos(x,y,z)]:
                        filled.add(Pos(x,y,z))
        return filled


    def grounded_voxels(self) -> Set[Pos]:
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

    def bounding_box(self) -> Optional[Region]:
        end = Pos(self.R - 1, self.R - 1, self.R - 1)
        box = None
        for pos in Region(Pos(0, 0, 0), end):
            if self[pos]:
                if not box:
                    box = Region(pos, pos)
                else:
                    box.expand(pos)
        return box


def main():
    from production import data_files

    name = 'LA004_tgt.mdl'
    data = data_files.lightning_problem(name)
    m = Model.parse(data)

    print(f'Central vertical slice of {name}:')
    x = m.R // 2
    for y in reversed(range(m.R)):
        s = []
        for z in range(m.R):
            if m[Pos(x, y, z)]:
                s.append('*')
            else:
                s.append('.')
        print(' '.join(s))
    print('R =', m.R)


if __name__ == '__main__':
    main()
