from production.cpp_emulator.emulator import Emulator as CppEmulator
from production.emulator import State, Bot, LOW, HIGH
from production.basics import Pos, Diff
from production.model import Model
import production.commands as commands

from bitarray import bitarray


def set_state(em, state):
    m = state.matrix._data.tobytes()
    em.reconstruct(state.R, m, state.harmonics == HIGH, state.energy)
    for b in state.bots:
        em.add_bot(b.bid, b.pos.x, b.pos.y, b.pos.z, b.seeds)
    return em


def get_bots(em):
    a = em.get_bots()
    i = 0
    bots = []
    while i < len(a):
        bid = a[i]
        p = Pos(a[i+1], a[i+2], a[i+3])
        sl = a[i+4]
        i += 5
        seeds = list(a[i+j] for j in range(sl))
        i += sl
        b = Bot(bid = bid, pos = p, seeds = seeds)
        bots.append(b)
    return bots


def get_state(em):
    a = em.get_state()
    s = State(a[0])
    s.harmonics = HIGH if a[1] else LOW
    b = bitarray(endian='little')
    b.frombytes(bytes(a[2:]))
    m = Model(s.R)
    m._data = b
    s.bots = get_bots(em)
    s.matrix = m
    s.energy = em.energy()
    return s


def main_run_interactive():
    import production.utils as utils

    em = CppEmulator()
    
    m = Model(3)
    m._data = bitarray('000100000' + '000000000' + '000000000')
    s = State(3)
    s.matrix = m
    s.harmonics = LOW
    s.energy = 30
    s.bots = [Bot(bid = 2, pos = Pos(0, 0, 1), seeds = [3, 4, 5])]

    set_state(em, s)

    cmds = [commands.Fill(Diff(1, 1, 0)), commands.SMove(Diff(0, 0, -1))]
    from itertools import chain
    cmdlist = list(chain.from_iterable(x.compose() for x in cmds))

    em.run_commands(cmdlist)

    s = get_state(em)
    print("\nEnergy: ", s.energy)
    print("Central cell: ", s.matrix[Pos(1, 1, 1)])
    print("Bot position: ", s.bots[0].pos)


def main_run_file():
    from production import utils
    modelfile = str(utils.project_root() / 'julie_scratch' / 'LA014_tgt.mdl')
    tracefile = str(utils.project_root() / 'julie_scratch' / 'LA014.nbt')

    em = CppEmulator()
    em.load_model(modelfile, 't')   # t - target model, s - source or current model
    em.load_trace(tracefile)
    em.run()

    print("Energy: ", em.energy())

if __name__ == '__main__':
    main_run_file()
    main_run_interactive()