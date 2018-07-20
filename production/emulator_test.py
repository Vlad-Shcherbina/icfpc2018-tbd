from production.emulator import State
from production.basics import Pos


def test_grounded():
    state = State(3)
    state.matrix = [
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
    assert state.grounded() == {
        Pos(0, 0, 0),
        Pos(2, 0, 2), Pos(2, 1, 2), Pos(2, 1, 1),
    }
