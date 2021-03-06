import production.cpp_emulator.emulator as Cpp
import production.cpp_mediator as cppm
import production.commands as commands
from production import utils

# from production.emulator import Bot, State, LOW, HIGH
# from production.basics import Pos, Diff
# from production.model import Model
# import production.commands as commands
# from bitarray import bitarray


def test_cpp_functions():
    assert Cpp.run_tests()


def test_run_from_file():
    modelfile = utils.project_root() / 'julie_scratch' / 'LA014_tgt.mdl'
    tracefile = utils.project_root() / 'julie_scratch' / 'LA014_dflt.nbt'
    logfilename = str(utils.project_root() / 'outputs' / 'cpp_emulator.log')

    mf = open(modelfile, 'rb')
    m = Cpp.Matrix.parse(mf.read())
    mf.close()

    em = Cpp.Emulator(None, m)      # (source, target)

    errmsg = ""
    tf = open(tracefile, 'rb')
    cmds = commands.parse_commands(tf.read(), errmsg)
    tf.close()
    commandlist = list(map(cppm.cmd_to_cpp, cmds))
    em.set_trace(commandlist)

    em.setlogfile(logfilename)
    em.run()

    assert em.energy() == 501700108

if __name__ == '__main__':
    test_run_from_file()
    test_cpp_functions()