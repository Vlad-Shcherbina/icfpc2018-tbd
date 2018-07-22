import production.cpp_emulator.emulator as Cpp
from production import utils

# from production.emulator import Bot, State, LOW, HIGH
# from production.basics import Pos, Diff
# from production.model import Model
# import production.commands as commands
# from bitarray import bitarray


def test_run_from_file():
    modelfile = str(utils.project_root() / 'julie_scratch' / 'LA014_tgt.mdl')
    tracefile = str(utils.project_root() / 'julie_scratch' / 'LA014_dflt.nbt')
    logfile = str(utils.project_root() / 'outputs' / 'cpp_emulator.log')
    em = Cpp.Emulator()
    em.load_model(modelfile, 't')   # t - target model, s - source or current model
    em.load_trace(tracefile)
    em.setlogfile(logfile)
    em.run()
    assert em.energy() == 501700108

if __name__ == '__main__':
    test_run_from_file()