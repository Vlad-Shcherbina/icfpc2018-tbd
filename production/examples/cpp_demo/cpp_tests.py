import pytest
from production.examples.cpp_demo import sample


def test_stuff():
    assert sample.N == 42
    assert sample.square(2) == 4
    assert isinstance(sample.square(2), int)
    assert isinstance(sample.square(2.0), float)
    assert sample.reverse([1, 2, 3]) == [3, 2, 1]

    hz = sample.Hz()
    with pytest.raises(AttributeError):
        hz.zzz = 0
