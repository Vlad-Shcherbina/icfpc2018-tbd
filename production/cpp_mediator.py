import production.cpp_emulator.emulator as Cpp
from production.emulator import Bot, State, LOW, HIGH
from production.basics import Pos, Diff
from production.model import Model
import production.commands as commands

from bitarray import bitarray

MAXBOTNUMBER = 40


#----------- conversions --------------#

def pos_from_cpp(cpos):
    return Pos(x=cpos.x, y=cpos.y, z=cpos.z)

def pos_to_cpp(pos):
    return Cpp.Pos(pos.x, pos.y, pos.z)


def bot_from_cpp(cb):
    return Bot(bid=cb.bid, pos=pos_from_cpp(cb.pos), seeds=cb.seeds)

def bot_from_cpp(b):
    return Cpp.Bot(b.bid, pos_to_cpp(b.pos), b.seeds, True)


def state_from_cpp(cs):
    s = State(cs.R)
    s.harmonics = HIGH if cs.high_harmonics else LOW
    s.energy = cs.energy
    s.matrix = Model(cs.R, bytes(cs.matrix))
    s.bots = list(bot_from_cpp(cb) for cb in cs.bots if cb.active)
    return s

def state_to_cpp(s):
    cm = s.matrix._data.tobytes()
    # cbots = list(Cpp.Bot(i, Cpp.Pos(0, 0, 0), [], False) 
    #                      for i in range(MAXBOTNUMBER + 1))
    cbots = list(Cpp.Bot() for i in range(MAXBOTNUMBER + 1))
    for b in s.bots:
        cb = Cpp.Bot(b.bid, pos_to_cpp(b.pos), b.seeds, True)
        cbots[b.bid] = cb
    cs = Cpp.State()
    cs.set_state(s.R, s.harmonics == HIGH, s.energy, cm, cbots)
    return cs


def from_cpp(item):
    if isinstance(item, Cpp.Pos):
        return pos_from_cpp(item)
    if isinstance(item, Cpp.Bot):
        return bot_from_cpp(item)
    if isinstance(item, Cpp.State):
        return state_from_cpp(item)

def to_cpp(item):
    if isinstance(item, Pos):
        return pos_to_cpp(item)
    if isinstance(item, Bot):
        return bot_to_cpp(item)
    if isinstance(item, State):
        return state_to_cpp(item)


#----------- examples --------------#

def main_run_interactive():
    import production.utils as utils

    # assuming we have left state and expecting right state
    #   x->
    # z ...  ...  ...  |  b..  ...  ...
    # | bo.  ...  ...  |  .o.  .o.  ...
    # v ...  ...  ...  |  ...  ...  ...
    #   y ---------->

    m = Model(3)
    m._data = bitarray('000100000000000000000000000')

    s = State(3)
    s.matrix = m
    s.harmonics = LOW
    s.energy = 30
    s.bots = [Bot(bid = 2, pos = Pos(0, 0, 1), seeds = [3, 4, 5])]

    cmds = [commands.Fill(Diff(1, 1, 0)), commands.SMove(Diff(0, 0, -1))]


    # we can run steps in cpp emulator and get new state

    em = Cpp.Emulator()
    em.set_state(state_to_cpp(s))

    # if no logfile name given, emulator doesn't log
    # problemname and solutionname are optional

    from production import utils
    em.setlogfile(str(utils.project_root() / 'outputs' / 'cpp_emulator.log'))
    em.setproblemname("some handmade problem")
    em.setsolutionname("John Doe's ingenious alg")

    # commands are passed encoded

    from itertools import chain
    cmdlist = list(chain.from_iterable(x.compose() for x in cmds))

    # emulator runs bunch of commands and throws exceptions
    # if some are invalid or illegal

    em.run_commands(cmdlist)

    # current state;
    # previous state if exception was raised

    print("\nSuccessful run: ", not em.aborted)

    s = state_from_cpp(em.get_state())
    print("Energy: ", s.energy)
    print("Central cell: ", s.matrix[Pos(1, 1, 1)])
    print("Bot position: ", s.bots[0].pos)


def main_run_file():
    from production import utils
    modelfile = str(utils.project_root() / 'julie_scratch' / 'LA014_tgt.mdl')
    tracefile = str(utils.project_root() / 'julie_scratch' / 'LA014_dflt.nbt')
    logfile = str(utils.project_root() / 'outputs' / 'cpp_emulator.log')

    em = Cpp.Emulator()
    em.load_model(modelfile, 't')   # t - target model, s - source or current model
    em.load_trace(tracefile)
    em.setlogfile(logfile)
    em.run()

    print("Energy: ", em.energy())

if __name__ == '__main__':
    main_run_file()
    main_run_interactive()
