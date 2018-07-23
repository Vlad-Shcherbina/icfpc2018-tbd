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


def diff_from_cpp(cdiff):
    return Diff(dx=cdiff.dx, dy=cdiff.dy, dz=cdiff.dz)

def diff_to_cpp(diff):
    return Cpp.Diff(diff.dx, diff.dy, diff.dz)


def bot_from_cpp(cb):
    return Bot(bid=cb.bid, pos=pos_from_cpp(cb.pos), seeds=cb.seeds)

def bot_from_cpp(b):
    return Cpp.Bot(b.bid, pos_to_cpp(b.pos), b.seeds, True)


# forget it
# def state_from_cpp(cs):
#     s = State(cs.R)
#     s.harmonics = HIGH if cs.high_harmonics else LOW
#     s.energy = cs.energy
#     s.matrix = Model(cs.R, bytes(cs.matrix))
#     s.bots = list(bot_from_cpp(cb) for cb in cs.bots if cb.active)
#     return s


def state_to_cpp(s):
    rawdata = bytes([s.R]) + s.matrix._data.tobytes()
    cbots = list(Cpp.Bot() for i in range(MAXBOTNUMBER + 1))
    for b in s.bots:
        cb = Cpp.Bot(b.bid, pos_to_cpp(b.pos), b.seeds, True)
        cbots[b.bid] = cb
    cm = Cpp.Matrix.parse(rawdata)      # source matrix
    return Cpp.State(cm, None, s.harmonics == HIGH, s.energy, cbots)


def from_cpp(item):
    if isinstance(item, Cpp.Pos):
        return pos_from_cpp(item)
    if isinstance(item, Cpp.Bot):
        return bot_from_cpp(item)
    if isinstance(item, Cpp.State):
        raise NotImplementedError()

def to_cpp(item):
    if isinstance(item, Pos):
        return pos_to_cpp(item)
    if isinstance(item, Bot):
        return bot_to_cpp(item)
    if isinstance(item, State):
        return state_to_cpp(item)


#----------- commands --------------#

def cmd_from_cpp(ccmd):
    if isinstance(ccmd, Cpp.Halt):
        return commands.Halt()
    if isinstance(ccmd, Cpp.Wait):
        return commands.Wait()
    if isinstance(ccmd, Cpp.Flip):
        return commands.Flip()
    if isinstance(ccmd, Cpp.SMove):
        return commands.SMove(diff_from_cpp(ccmd.lld))
    if isinstance(ccmd, Cpp.LMove):
        return commands.LMove(diff_from_cpp(ccmd.sld1), 
                              diff_from_cpp(ccmd.sld2))
    if isinstance(ccmd, Cpp.Fission):
        return commands.Fission(diff_from_cpp(ccmd.nd), ccmd.m)
    if isinstance(ccmd, Cpp.Fill):
        return commands.Fill(diff_from_cpp(ccmd.nd))
    if isinstance(ccmd, Cpp.Void):
        return commands.Void(diff_from_cpp(ccmd.nd))
    if isinstance(ccmd, Cpp.GFill):
        return commands.GFill(diff_from_cpp(ccmd.nd), 
                              diff_from_cpp(ccmd.fd))
    if isinstance(ccmd, Cpp.GVoid):
        return commands.GVoid(diff_from_cpp(ccmd.nd), 
                              diff_from_cpp(ccmd.fd))
    assert False, ccmd


def cmd_to_cpp(cmd):
    if isinstance(cmd, commands.Halt):
        return Cpp.Halt()
    if isinstance(cmd, commands.Wait):
        return Cpp.Wait()
    if isinstance(cmd, commands.Flip):
        return Cpp.Flip()
    if isinstance(cmd, commands.SMove):
        return Cpp.SMove(diff_to_cpp(cmd.lld))
    if isinstance(cmd, commands.LMove):
        return Cpp.LMove(diff_to_cpp(cmd.sld1),
                         diff_to_cpp(cmd.sld2))
    if isinstance(cmd, commands.Fission):
        return Cpp.Fission(diff_to_cpp(cmd.nd), cmd.m)
    if isinstance(cmd, commands.Fill):
        return Cpp.Fill(diff_to_cpp(cmd.nd))
    if isinstance(cmd, commands.Void):
        return Cpp.Void(diff_to_cpp(cmd.nd))
    if isinstance(cmd, commands.GFill):
        return Cpp.GFill(diff_to_cpp(cmd.nd),
                         diff_to_cpp(cmd.fd))
    if isinstance(cmd, commands.GVoid):
        return Cpp.GVoid(diff_to_cpp(cmd.nd),
                         diff_to_cpp(cmd.fd))
    assert False, cmd

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

    em = Cpp.Emulator(state_to_cpp(s))

    # if no logfile name given, emulator doesn't log
    # problemname and solutionname are optional

    from production import utils
    em.setlogfile(str(utils.project_root() / 'outputs' / 'cpp_emulator.log'))
    em.setproblemname("some handmade problem")
    em.setsolutionname("John Doe's ingenious alg")

    for c in map(cmd_to_cpp, cmds):
        em.add_command(c)

    # emulator runs bunch of commands and throws exceptions
    # if some are invalid or illegal

    try:
        em.run_step()
    except Cpp.SimulatorException as e:
        print(e)


    # current state;
    # previous state if exception was raised

    print("\nSuccessful run: ", not em.aborted)

    cs = em.get_state()
    print("Energy: ", cs.energy)
    print("Central cell: ", cs[Cpp.Pos(1, 1, 1)])
    print("Bot position: ", s.bots[0].pos)


def main_run_file():
    from production import utils
    modelfile = utils.project_root() / 'julie_scratch' / 'LA014_tgt.mdl'
    tracefile = utils.project_root() / 'julie_scratch' / 'LA014_dflt.nbt'
    logfile = str(utils.project_root() / 'outputs' / 'cpp_emulator.log')

    mf = open(modelfile, 'rb')
    m = Cpp.Matrix.parse(mf.read())
    mf.close()

    em = Cpp.Emulator(None, m)      # (source, target)

    error = ""
    tf = open(tracefile, 'rb')
    cmds = commands.parse_commands(tf.read(), error)
    tf.close()
    cmdlist = list(map(cmd_to_cpp, cmds))
    em.set_trace(cmdlist)

    em.setlogfile(logfile)
    em.run()

    print("Energy: ", em.energy())


def main_simple_cmd_check():
    x = commands.Fill(Diff(-1, 1, 0))
    y = cmd_to_cpp(x)
    z = cmd_from_cpp(y)
    print("PyCommand -> CppCommand -> PyCommand gives initial: ", x == z, "\n")

if __name__ == '__main__':
    # main_run_file()
    main_run_interactive()
