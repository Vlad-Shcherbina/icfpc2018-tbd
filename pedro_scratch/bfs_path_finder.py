# See navigate and bfs functions

from production.basics import (Diff, Pos)
from production.model import Model
import production.commands as Cmd


def direction(diff) -> 'Diff':
    return Diff(sign(diff.dx), sign(diff.dy), sign(diff.dz))


def udirection(self) -> 'Diff':
    def f(x): return 0 if x == 0 else 1
    return Diff(f(self.dx), f(self.dy), f(self.dz))


def sign(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    elif x == 0:
        return 0


def iterate_region(m, a: Pos, b: Pos):
    def rg(t1, t2): return range(min(t1, t2), max(t1, t2) + 1)
    for x in rg(a.x, b.x):
        for z in rg(a.z, b.z):
            for y in rg(a.y, b.y):
                yield (m[Pos(x, y, z)], (x, y, z))


def test_region(m, a: Pos, b: Pos, f):
    for (st, c) in iterate_region(m, a, b):
        if not f(st):
            return False
    return True


def region_is_clear(m, a, b):
    return test_region(m, a, b, lambda x: not x)


# 3d array indexed by Pos
class Matrix:
    def __init__(self, R):
        self.R = R
        self._data = [0 for i in range(R ** 3)]

    def __getitem__(self, pos: Pos):
        R = self.R
        assert pos.is_inside_matrix(R), pos
        return self._data[pos.x * R * R + pos.y * R + pos.z]

    def __setitem__(self, pos, value):
        R = self.R
        assert pos.is_inside_matrix(R)
        self._data[pos.x * R * R + pos.y * R + pos.z] = value


# Simplest possible path finder. Combined with grouping and long moves it can
# produce acceptable results. Producess list of Pos
def bfs(m, src: 'Point', dst: 'Point'):
    weights = Matrix(m.R)
    sources = Matrix(m.R)

    queue = [src]
    weights[src] = 1
    while len(queue) and weights[dst] == 0:
        p = queue.pop(0)

        ds = [ Diff(0, 1, 0), Diff(0, -1, 0)
             , Diff(1, 0, 0), Diff(-1, 0, 0)
             , Diff(0, 0, 1), Diff(0, 0, -1)]
        for d in ds:
            nxt = p + d
            if nxt.is_inside_matrix(m.R) and not m[nxt] and not weights[nxt]:
                queue.append(nxt)
                weights[nxt] = weights[p] + 1
                sources[nxt] = p

    if weights[dst] == 0:
        return None
    else:
        res = []
        p = dst
        while p != src:
            res.insert(0, p)
            p = sources[p]
        return res

# bfs version which produces list of Diffs
def bfs_diffs(m, src: 'Point', dst: 'Point'):
    path = bfs(m, src, dst)
    if not path:
        return None

    res = []
    p = src
    while len(path):
        n = path.pop(0)
        res.append(n - p)
        p = n

    return res

# Combine consequetive collinear Diffs. Here we handle only linear Diffs.
def group_diffs_gen(path):
    if not len(path):
        return []
    res = []
    acc = path.pop(0)
    while len(path):
        x = path.pop(0)
        if udirection(acc) == udirection(x) or acc.mlen() == 0:
            acc = acc + x
        else:
            yield acc
            acc = x
    yield acc


# Split one "Big" Diff into a series of smaller Diffs sutable for SMoves
def split_linear_move_gen(diff):
    if diff.mlen() == 0:
        return
    assert(diff.is_linear())

    l = abs(diff.mlen())
    norm = direction(diff)
    while l > 0:
        c = min(l, 15)
        l -= c
        yield norm * c


def split_each_linear_move_gen(seq):
    for x in seq:
        for y in split_linear_move_gen(x):
            yield y


def navigate_gen(m, src, dst):
    diffs = bfs_diffs(m, src, dst) or []
    for x in split_each_linear_move_gen( group_diffs_gen(diffs) ):
        yield Cmd.SMove(x)


# Returns list of SMoves
# See bfs for details about navigation strategy
# Returns [] on failure
def navigate(m, src, dst):
    return [x for x in navigate_gen(m, src, dst)]


def test_navigation(m, a, b):
    pos = a
    for diff in [x.lld for x in navigate(m, a, b)]:
        new_pos = pos + diff
        assert( region_is_clear(m, pos, new_pos) )
        pos = new_pos
    assert(pos == b)


if __name__ == '__main__':
    test_navigation(Model(3), Pos(0, 0, 0), Pos(2, 2, 2))

    m1 = Model(3)
    m1[Pos(0, 0, 1)] = True
    m1[Pos(1, 0, 1)] = True
    m1[Pos(2, 0, 1)] = True
    m1[Pos(0, 1, 1)] = True
    m1[Pos(1, 1, 1)] = True
    m1[Pos(2, 1, 1)] = True
    m1[Pos(1, 2, 1)] = True
    m1[Pos(2, 2, 1)] = True
    test_navigation(m1, Pos(0, 0, 0), Pos(2, 0, 2))

    m2 = Model(3)
    m2[Pos(0, 0, 1)] = True
    m2[Pos(1, 0, 1)] = True
    m2[Pos(2, 0, 1)] = True
    m2[Pos(0, 1, 1)] = True
    m2[Pos(1, 1, 1)] = True
    m2[Pos(2, 1, 1)] = True
    m2[Pos(0, 2, 1)] = True
    m2[Pos(1, 2, 1)] = True
    m2[Pos(2, 2, 1)] = True
    assert( [] == navigate(m2, Pos(0, 0, 0), Pos(2, 0, 2)) )
