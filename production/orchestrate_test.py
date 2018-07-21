from production.orchestrate import *


def test_sequential():
    bot1 = [(1,1), (1,2), (1,3)]
    bot2 = [(2,1)]
    bot3 = [(3,1), (3,2)]
    assert sequential(bot1, bot2, bot3, skip=None) == [
        [(1,1), None, None],
        [(1,2), None, None],
        [(1,3), None, None],

        [None, (2,1), None],

        [None, None, (3,1)],
        [None, None, (3,2)]
    ]
