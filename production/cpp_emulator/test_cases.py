from production.emulator import Bot, State, LOW, HIGH
from production.basics import Pos, Diff
from production.model import Model
import production.commands as pc

import production.cpp_emulator.emulator as Cpp
from production.cpp_mediator import cmd_to_cpp as ctp
from production.cpp_mediator import state_to_cpp

from production import utils

def set_cpp_state():
    m = Model(5)
    m[Pos(2, 0, 2)] = 1
    m[Pos(2, 1, 2)] = 1
    m[Pos(2, 2, 2)] = 1
    m[Pos(2, 3, 2)] = 1

    s = State(5)
    s.matrix = m
    s.harmonics = LOW
    s.energy = 0
    s.bots = [Bot(bid = 1, pos = Pos(0, 0, 1), seeds = []),
              Bot(bid = 2, pos = Pos(0, 0, 2), seeds = list(range(4, 40))),
              Bot(bid = 40, pos = Pos(1, 0, 0), seeds = [])]

    return state_to_cpp(s)


def test_grounded():
    pass


def test_illegal_smoves():
    em = Cpp.Emulator(set_cpp_state())

    # bot 2 moves out of bounds
    assert em.check_add_command(ctp(pc.Wait())) == ''
    msg = em.check_command(ctp(pc.SMove(Diff(0, 0, 3))))
    assert msg != ''
    
    # bot 2 moves through the filled area
    msg = em.check_command(ctp(pc.SMove(Diff(3, 0, 0))))
    assert msg != ''

    # ...
    c = ctp(pc.Wait())
    em.add_command(c)
    em.add_command(c)
    em.run_step()

    # bot 1 moves through bot 2
    msg = em.check_command(ctp(pc.SMove(Diff(0, 0, 3))))
    assert msg != ''

    # bot 2 moves through volatile area
    assert em.check_add_command(ctp(pc.Fill(Diff(0, 1, 1)))) == ''
    msg = em.check_command(ctp(pc.SMove(Diff(0, 1, 0))))
    assert msg != ''

    # bots 2 & 3 move freely
    assert em.check_add_command(ctp(pc.SMove(Diff(1, 0, 0)))) == ''
    assert em.check_add_command(ctp(pc.SMove(Diff(0, 4, 0)))) == ''
    assert em.steptrace_is_complete()
    em.run_step()


def test_illegal_lmoves():
    em = Cpp.Emulator(set_cpp_state())

    # bot 2 moves out of bounds
    assert em.check_add_command(ctp(pc.Wait())) == ''
    msg = em.check_add_command(ctp(pc.LMove(Diff(0, -1, 0), Diff(0, 0, 3))))
    assert msg != ''
    
    msg = em.check_add_command(ctp(pc.LMove(Diff(0, 1, 0), Diff(0, 0, 3))))
    assert msg != ''
    
    msg = em.check_add_command(ctp(pc.LMove(Diff(0, 0, 2), Diff(0, 0, 2))))
    assert msg != ''
    
    # bot 2 moves through the filled area
    msg = em.check_add_command(ctp(pc.LMove(Diff(2, 0, 0), Diff(0, 0, 1))))
    assert msg != ''

    msg = em.check_add_command(ctp(pc.LMove(Diff(0, 3, 0), Diff(3, 0, 0))))
    assert msg != ''

    # ...
    em.add_command(ctp(pc.Wait()))

    # bot 3 moves through bots 1 & 2
    msg = em.check_add_command(ctp(pc.LMove(Diff(-1, 0, 0), Diff(0, 0, 4))))
    assert msg != ''

    # ...
    em.add_command(ctp(pc.Wait()))
    em.run_step()

    # bot 2 moves through volatile area
    assert em.check_add_command(ctp(pc.Fill(Diff(0, 1, 0)))) == ''
    msg = em.check_add_command(ctp(pc.LMove(Diff(0, 1, 0), Diff(0, 0, -1))))
    assert msg != ''

    # bot 2 moves freely
    assert em.check_add_command(ctp(pc.LMove(Diff(0, 2, 0), Diff(0, 0, -1)))) == ''

    # bot 2 dangles around freely
    assert em.check_add_command(ctp(pc.LMove(Diff(2, 0, 0), Diff(-3, 0, 0)))) == ''



    # assert em.check_add_command(ctp(pc.SMove(Diff(1, 0, 0)))) == ''
    # assert em.check_add_command(ctp(pc.SMove(Diff(0, 4, 0)))) == ''
    # assert em.steptrace_is_complete()
    # em.run_step()

if __name__ == '__main__':
    test_illegal_smoves()
    test_illegal_lmoves()
