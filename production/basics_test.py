import unittest, pytest
import production.basics_reference_implementation as py_
import production.basics as cpp_


class CommonTests:

    def test_arith(self):
        p = self.Pos(1, 2, 3)
        q = self.Pos(4, 6, 10)
        d = q - p
        p += d
        assert p == q


    def test_inside_matrix(self):
        assert self.Pos(1, 2, 3).is_inside_matrix(4)
        assert not self.Pos(1, 2, 3).is_inside_matrix(3)
        assert not self.Pos(-1, 2, 3).is_inside_matrix(4)


    def test_len(self):
        d = self.Diff(1, 2, -3)
        assert d.mlen() == 6
        assert d.clen() == 3


    def test_linear(self):
        assert self.Diff(10, 0, 0).is_linear()
        assert self.Diff(0, 4, 0).is_linear()
        assert not self.Diff(1, 0, 1).is_linear()

        num_short = 0
        num_long = 0
        for dx in range(-16, 16 + 1):
            for dy in range(-16, 16 + 1):
                for dz in range(-16, 16 + 1):
                    d = self.Diff(dx, dy, dz)
                    if d.is_short_linear():
                        num_short += 1
                    if d.is_long_linear():
                        num_long += 1
        assert num_short == 30
        assert num_long == 90


    def test_near(self):
        num_near = 0
        for dx in range(-3, 3 + 1):
            for dy in range(-3, 3 + 1):
                for dz in range(-3, 3 + 1):
                    if self.Diff(dx, dy, dz).is_near():
                        num_near += 1
        assert num_near == 18


    def test_dimension(self):
        assert self.region_dimension(self.Pos(1, 2, 3), self.Pos(1, 2, 3)) == 0
        assert self.region_dimension(self.Pos(1, 2, 3), self.Pos(1, 20, 3)) == 1
        assert self.region_dimension(self.Pos(1, 2, 3), self.Pos(0, 0, 0)) == 3


    def test_byaxis(self):
        r = self.Diff.byaxis(0, 10) + self.Diff.byaxis(1, 20) + self.Diff.byaxis(2, 30)
        assert r[0] == 10
        assert r[1] == 20
        assert r[2] == 30

        with pytest.raises((ValueError, AssertionError)):
            x = r[-1]
        with pytest.raises((ValueError, AssertionError)):
            x = r[4]
        with pytest.raises((ValueError, AssertionError)):
            x = self.Diff.byaxis(-1, 10)
        with pytest.raises((ValueError, AssertionError)):
            x = self.Diff.byaxis(4, 10)


class PyTest(unittest.TestCase, CommonTests):
    def setUp(self):
        self.Pos = py_.Pos
        self.Diff = py_.Diff
        self.region_dimension = py_.region_dimension

class CppTest(unittest.TestCase, CommonTests):
    def setUp(self):
        self.Pos = cpp_.Pos
        self.Diff = cpp_.Diff
        self.region_dimension = cpp_.region_dimension



if __name__ == '__main__':
    unittest.main(verbosity=2)
