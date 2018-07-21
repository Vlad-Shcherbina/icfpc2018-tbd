from production.cpp_emulator.emulator import Emulator as CppEmulator
from production.emulator import State, Bot, LOW
from production.basics import Pos, Diff
from production.model import Model
import production.commands as commands

from bitarray import bitarray


def encode_matrix(m):
    a = []
    count = 0
    x = 0
    for b in m._data:
        x = (x * 2) + int(b)
        count += 1
        if count == 8:
            a.append(x)
            x = 0
            count = 0
    if count: a.append(x)
    return a


def set_state(state):
    em = CppEmulator()
    m = encode_matrix(state.matrix)
    em.reconstruct(state.R, m, state.harmonics == LOW, state.energy)
    print(em.count_active())
    for b in state.bots:
        em.add_bot(b.bid, b.pos.x, b.pos.y, b.pos.z, b.seeds)
    return em


if __name__ == '__main__':
    import production.utils as utils

    m = Model(3)
    m._data = bitarray('000010000')
    s = State(3)
    s.matrix = m
    s.harmonics = LOW
    s.energy = 30
    s.bots = [Bot(bid = 2, pos = Pos(0, 0, 1), seeds = [3, 4, 5])]

    em = set_state(s)

    cmds = [commands.Fill(Diff(1, 1, 0)), commands.SMove(Diff(0, 0, -1))]
    from itertools import chain
    cmdlist = list(chain.from_iterable(x.compose() for x in cmds))
    em.run_commands(cmdlist)

    # s = get_state(em)