from production.basics import *


def test_arith():
    p = Pos(1, 2, 3)
    q = Pos(4, 6, 10)
    d = q - p
    p += d
    assert p == q


def test_len():
    d = Diff(1, 2, -3)
    assert d.mlen() == 6
    assert d.clen() == 3
