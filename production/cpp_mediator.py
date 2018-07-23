import production.cpp_emulator.emulator as Cpp
from production.emulator import Bot, State, LOW, HIGH
from production.basics import Pos, Diff
from production.model import Model
import production.commands as commands

from bitarray import bitarray

MAXBOTNUMBER = 40


#----------- conversions --------------#

def bot_from_cpp(cb):
    return Bot(bid=cb.bid, pos=pos_from_cpp(cb.pos), seeds=cb.seeds)

def bot_from_cpp(b):
    return Cpp.Bot(b.bid, pos_to_cpp(b.pos), b.seeds, True)


def state_to_cpp(s):
    rawdata = bytes([s.R]) + s.matrix._data.tobytes()
    cbots = list(Cpp.Bot(i) for i in range(MAXBOTNUMBER + 1))
    for b in s.bots:
        cb = Cpp.Bot(b.bid, b.pos, b.seeds, True)
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
        return commands.SMove(ccmd.lld)
    if isinstance(ccmd, Cpp.LMove):
        return commands.LMove(ccmd.sld1, ccmd.sld2)
    if isinstance(ccmd, Cpp.Fission):
        return commands.Fission(ccmd.nd, ccmd.m)
    if isinstance(ccmd, Cpp.Fill):
        return commands.Fill(ccmd.nd)
    if isinstance(ccmd, Cpp.Void):
        return commands.Void(ccmd.nd)
    if isinstance(ccmd, Cpp.GFill):
        return commands.GFill(ccmd.nd, ccmd.fd)
    if isinstance(ccmd, Cpp.GVoid):
        return commands.GVoid(ccmd.nd, ccmd.fd)
    assert False, ccmd


def cmd_to_cpp(cmd):
    if isinstance(cmd, commands.Halt):
        return Cpp.Halt()
    if isinstance(cmd, commands.Wait):
        return Cpp.Wait()
    if isinstance(cmd, commands.Flip):
        return Cpp.Flip()
    if isinstance(cmd, commands.SMove):
        return Cpp.SMove(cmd.lld)
    if isinstance(cmd, commands.LMove):
        return Cpp.LMove(cmd.sld1,
                         cmd.sld2)
    if isinstance(cmd, commands.Fission):
        return Cpp.Fission(cmd.nd, cmd.m)
    if isinstance(cmd, commands.Fill):
        return Cpp.Fill(cmd.nd)
    if isinstance(cmd, commands.Void):
        return Cpp.Void(cmd.nd)
    if isinstance(cmd, commands.GFill):
        return Cpp.GFill(cmd.nd, cmd.fd)
    if isinstance(cmd, commands.GVoid):
        return Cpp.GVoid(cmd.nd, cmd.fd)
    assert False, cmd

#----------- examples --------------#

def main_run_interactive():

    import production.utils as utils

    # assuming we have left state and expecting right state
    #   x->
    # z ...  ...  ...  |  2..  ...  ...
    # | 2o.  ...  ...  |  .o.  .o.  ...
    # v ...  ...  ...  |  3..  ...  ...
    #   y ---------->

    m = Model(3)
    m[Pos(1, 0, 1)] = 1

    s = State(3)
    s.matrix = m
    s.harmonics = LOW
    s.energy = 30
    s.bots = [Bot(bid = 2, pos = Pos(0, 0, 1), seeds = [3, 4, 5])]

    cmds = [commands.Fill(Diff(1, 1, 0)), 
            commands.Fission(Diff(0, 0, 1), 2),
            commands.SMove(Diff(0, 0, -1)),
            commands.Wait()]

    # pass state to emulator (step count set to 0)

    em = Cpp.Emulator(state_to_cpp(s))

    # LOGGING -- temporary out of service
    # if no logfile name given, emulator doesn't log
    # problemname & solutionname are optional

    from production import utils
    em.setlogfile(str(utils.project_root() / 'outputs' / 'cpp_emulator.log'))
    em.setproblemname("some handmade problem")
    em.setsolutionname("John Doe's ingenious alg")

    # OPTION 1: Run set of commands

    cpp_cmds = list(map(cmd_to_cpp, cmds))
    em.run_commands(cpp_cmds)

    cs = em.get_state()
    print("Energy: ", cs.energy)
    print("Central cell: ", cs[Cpp.Pos(1, 1, 1)])
    print("Active bots: ", sum(b.active for b in cs.bots))

    # OPTION 2: Command by command

    #    x->
    # z  2..  ...  ...
    # |  .o.  .o.  ...
    # v  3..  ...  ...
    #    y ---------->

    ccmd = cmd_to_cpp(commands.LMove(Diff(1, 0, 0), Diff(0, 0, 1)))
    msg = em.check_command(ccmd)
    print(msg == '', 'Error: ', msg)

    # void string if command is valid 

    ccmd = cmd_to_cpp(commands.Fill(Diff(0, 0, 1)))
    msg = em.check_command(ccmd)
    print(msg == '', 'Error: ', msg)

    em.add_command(ccmd)

    ccmd = cmd_to_cpp(commands.SMove(Diff(0, 0, -1)))
    msg = em.check_command(ccmd)
    print(msg == '', 'Error: ', msg)

    # to check command and add iff it's valid

    ccmd = cmd_to_cpp(commands.Wait())
    msg = em.check_add_command(ccmd)
    print(msg == '', 'Error: ', msg)

    # if there are enough commands for next step, new commands cannot 
    # be checked until change of state, and every check will fail

    ccmd = cmd_to_cpp(commands.Wait())
    msg = em.check_add_command(ccmd)
    print(msg == '', 'Error: ', msg)

    # you can still add command without checks

    print('Trace is full: ', em.steptrace_is_complete())
    print('Energy: ', em.energy())
    em.add_command(ccmd)
    em.run_step()
    print('Trace is full: ', em.steptrace_is_complete())
    print('Energy: ', em.energy())


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
