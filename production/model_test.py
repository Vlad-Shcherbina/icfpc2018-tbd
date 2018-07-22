import unittest

from production.model import Model
from production.basics import *

from production.cpp_emulator import emulator as cppe


class CommonTests():
    def test_grounded(self):
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
        m = self.Model(3)
        for x, slice in enumerate(matrix):
            for y, row in enumerate(slice):
                for z, cell in enumerate(row):
                    m[self.Pos(x, y, z)] = bool(cell)

        assert sorted(m.grounded_voxels()) == sorted([
            self.Pos(0, 0, 0),
            self.Pos(2, 0, 2), self.Pos(2, 1, 2), self.Pos(2, 1, 1),
        ])


class PyModelTests(unittest.TestCase, CommonTests):
    def setUp(self):
        self.Pos = Pos
        self.Model = Model


class CppMatrixTests(unittest.TestCase, CommonTests):
    def setUp(self):
        self.Pos = cppe.Pos
        self.Model = cppe.Matrix
