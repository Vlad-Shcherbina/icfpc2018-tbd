

if __name__ == '__main__':
    import sys
    import production.utils as utils
    from production.cpp_emulator.emulator import Emulator

    model = str(utils.project_root() / 'julie_scratch' / 'LA014_tgt.mdl')
    trace = str(utils.project_root() / 'julie_scratch' / 'LA014.nbt')
    em = Emulator()
    em.run(model, trace)
    # f = open(utils.project_root() / 'julie_scratch' / 'LA014_tgt.mdl', 'r')
    print(em.energy())