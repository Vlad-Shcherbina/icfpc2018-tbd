from production.cpp_emulator.emulator import Matrix, Pos
from production.cpp_emulator import emulator as cpp
from production.cpp_mediator import cmd_from_cpp
from production import data_files


def test_pack():
    p = Pos(1, 2, 3)
    assert Pos.unpack(10, p.pack(10)) == p


def test_matrix():
    name = 'LA004_tgt.mdl'
    data = data_files.lightning_problem(name)
    m = Matrix.parse(data)
    assert m.R == 20

    print(f'Central vertical slice of {name}')
    print('with a blip in the bottom left corner')
    print('and a hole in the middle')
    x = m.R // 2

    m0 = Matrix(m)
    assert m0 == m
    assert m.num_full == 559
    m[Pos(m.R // 2, 1, 1)] = True
    assert m.num_full == 560
    assert m0 != m
    m[Pos(m.R // 2, 4, 8)] = False
    assert m.num_full == 559

    for y in reversed(range(m.R)):
        s = []
        for z in range(m.R):
            if m[Pos(x, y, z)]:
                s.append('*')
            else:
                s.append('.')
        print(' '.join(s))

    assert m.count_inside_region(Pos(0, 0, 0), Pos(m.R - 1, m.R - 1, m.R - 1)) == 559

    # assert False  # uncomment to visually inspect what it prints


def test_pathfinding():
    matrix = [
        #   z
        #  ---->
        [[1, 0, 0],   # |
        [0, 1, 0],   # | y
        [0, 0, 0]],  # v
        # x = 0

        [[0, 0, 0],
        [0, 0, 0],
        [1, 1, 1]],
        # x = 1

        [[0, 0, 1],
        [0, 1, 1],
        [0, 0, 0]],
        # x = 2
    ]
    m = Matrix(3)
    for x, slice in enumerate(matrix):
        for y, row in enumerate(slice):
            for z, cell in enumerate(row):
                m[Pos(x, y, z)] = bool(cell)

    dst, path = cpp.path_to_nearest_of(m, Pos(0, 0, 1), [Pos(0, 0, 1)])
    assert dst == Pos(0, 0, 1)
    assert path == []

    dst, path = cpp.path_to_nearest_of(m, Pos(0, 0, 1), [Pos(0, 2, 1)])
    assert dst == Pos(0, 2, 1)
    assert len(path) == 2
    for cmd in path:
        print(cmd_from_cpp(cmd))

    assert cpp.path_to_nearest_of(m, Pos(0, 0, 1), [Pos(100, 0, 0)]) is None
