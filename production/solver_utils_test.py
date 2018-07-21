from production.model import Model
from production.basics import *
from production.solver_utils import *


def test_bounding_box():
    matrix = [
        #   z
        #  ---->
        [[1, 0, 0],   # |
         [0, 1, 0],   # | y
         [0, 0, 0]],  # v
        # x = 0

        [[0, 0, 0],
         [0, 1, 0],
         [0, 0, 0]],
        # x = 1

        [[0, 0, 0],
         [1, 1, 0],
         [0, 0, 0]],
        # x = 2
    ]
    m = Model(3)
    for x, slice in enumerate(matrix):
        for y, row in enumerate(slice):
            for z, cell in enumerate(row):
                m[Pos(x, y, z)] = bool(cell)

    assert bounding_box(m) == (Pos(0, 0, 0), Pos(2, 1, 1))

def test_bounding_box_region():
    matrix = [
        #   z
        #  ---->
        [[1, 0, 0],   # |
         [0, 1, 0],   # | y
         [0, 0, 0]],  # v
        # x = 0

        [[0, 0, 0],
         [0, 1, 0],
         [0, 0, 0]],
        # x = 1

        [[0, 0, 0],
         [1, 1, 0],
         [0, 0, 0]],
        # x = 2
    ]
    m = Model(3)
    for x, slice in enumerate(matrix):
        for y, row in enumerate(slice):
            for z, cell in enumerate(row):
                m[Pos(x, y, z)] = bool(cell)

    assert bounding_box_region(m, fx = 2) == (Pos(2, 1, 0), Pos(2, 1, 1))


def test_projection_top():
    matrix = [
        #   z
        #  ---->
        [[1, 0, 0],   # |
         [0, 1, 0],   # | y
         [0, 0, 0]],  # v
        # x = 0

        [[0, 0, 0],
         [0, 1, 0],
         [0, 0, 0]],
        # x = 1

        [[0, 0, 0],
         [1, 1, 0],
         [0, 0, 0]],
        # x = 2
    ]
    m = Model(3)
    for x, slice in enumerate(matrix):
        for y, row in enumerate(slice):
            for z, cell in enumerate(row):
                m[Pos(x, y, z)] = bool(cell)

    assert projection_top(m) == [
        [1, 1, 0],
        [0, 1, 0],
        [1, 1, 0]
    ]
