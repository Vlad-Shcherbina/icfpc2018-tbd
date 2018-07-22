import production.cpp_emulator.emulator as Cpp
from production import utils

# from production.emulator import Bot, State, LOW, HIGH
# from production.basics import Pos, Diff
# from production.model import Model
# import production.commands as commands
# from bitarray import bitarray




def test_run_from_file():
    modelfile = utils.project_root() / 'julie_scratch' / 'LA014_tgt.mdl'
    tracefile = utils.project_root() / 'julie_scratch' / 'LA014_dflt.nbt'
    logfilename = str(utils.project_root() / 'outputs' / 'cpp_emulator.log')

    em = Cpp.Emulator()

    mf = open(modelfile, 'rb')
    em.set_size(ord(mf.read(1)))
    em.set_tgt_model(mf.read())
    mf.close()

    tf = open(tracefile, 'rb')
    em.set_trace(tf.read())
    tf.close()

    em.setlogfile(logfilename)
    em.run()

    assert em.energy() == 501700108

if __name__ == '__main__':
    test_run_from_file()