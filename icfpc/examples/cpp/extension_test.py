import pytest
from icfpc.examples.cpp import extension

def test_stuff():
    assert extension.N == 42
    assert extension.square(2) == 4
    assert isinstance(extension.square(2), int)
    assert isinstance(extension.square(2.0), float)
    assert extension.reverse([1, 2, 3]) == [3, 2, 1]

    hz = extension.Hz()
    with pytest.raises(AttributeError):
        hz.zzz = 0

    assert extension.flip_opt(None) == 42
    assert extension.flip_opt(1) == None
