from production.model import Model
from production.basics import *


def test_grounded():
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
    m = Model(3)
    for x, slice in enumerate(matrix):
        for y, row in enumerate(slice):
            for z, cell in enumerate(row):
                m[Pos(x, y, z)] = bool(cell)

    assert m.grounded_voxels() == {
        Pos(0, 0, 0),
        Pos(2, 0, 2), Pos(2, 1, 2), Pos(2, 1, 1),
    }
