import pytest
z3 = pytest.importorskip('z3')


def test_smoke():
    solver = z3.Solver()
    x = z3.Int('x')
    solver.add(2 * x == 42)
    result = solver.check()
    assert result == z3.sat
    m = solver.model()
    assert m.eval(x).as_long() == 21


if __name__ == '__main__':
    import sys, pytest
    pytest.main([__file__] + sys.argv[1:])
