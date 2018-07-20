from bitarray import bitarray

from production.basics import Pos


class Model:
    def __init__(self, R: int, data: bytes):
        self.R = R
        assert len(data) == (R**3 - 1) // 8 + 1
        self._data = bitarray(0, endian='little')
        self._data.frombytes(data)

    def __getitem__(self, pos: Pos) -> bool:
        R = self.R
        assert pos.is_inside_matrix(R)
        return self._data[pos.x * R * R + pos.y * R + pos.z]

    def __setitem__(self, pos: Pos, value: bool):
        R = self.R
        assert pos.is_inside_matrix(R)
        self._data[pos.x * R * R + pos.y * R + pos.z] = value

    @staticmethod
    def parse(data: bytes) -> 'Model':
        return Model(R=data[0], data=data[1:])


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
