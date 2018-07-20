from production.cpp_emulator.emulator import *


def test_arith():
    p = Pos(1, 2, 3)
    q = Pos(4, 6, 10)
    d = q - p
    p += d
    assert p == q


def test_inside_matrix():
    assert Pos(1, 2, 3).is_inside_matrix(4)
    assert not Pos(1, 2, 3).is_inside_matrix(3)
    # test is excluded : cannot create Pos with negative coordinates
    # assert not Pos(-1, 2, 3).is_inside_matrix(4)



def test_len():
    d = Diff(1, 2, -3)
    assert d.mlen() == 6
    assert d.clen() == 3


def test_linear():
    assert Diff(10, 0, 0).is_linear()
    assert Diff(0, 4, 0).is_linear()
    assert not Diff(1, 0, 1).is_linear()

    num_short = 0
    num_long = 0
    for dx in range(-16, 16 + 1):
        for dy in range(-16, 16 + 1):
            for dz in range(-16, 16 + 1):
                d = Diff(dx, dy, dz)
                if d.is_short_linear():
                    num_short += 1
                if d.is_long_linear():
                    num_long += 1
    assert num_short == 30
    assert num_long == 90


def test_near():
    num_near = 0
    for dx in range(-3, 3 + 1):
        for dy in range(-3, 3 + 1):
            for dz in range(-3, 3 + 1):
                if Diff(dx, dy, dz).is_near():
                    num_near += 1
    assert num_near == 18


def test_dimension():
    assert region_dimension(Pos(1, 2, 3), Pos(1, 2, 3)) == 0
    assert region_dimension(Pos(1, 2, 3), Pos(1, 20, 3)) == 1
    assert region_dimension(Pos(1, 2, 3), Pos(0, 0, 0)) == 3


if __name__ == '__main__':
    p = Pos(1, 2, 3)
    q = Pos(4, 6, 10)
    d = q - p
    p += d
    assert p == q
