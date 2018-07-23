from production.emulator import Bot, State, LOW, HIGH
from production.basics import Pos, Diff
from production.model import Model
import production.commands as commands

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
              Bot(bid = 2, pos = Pos(0, 0, 2), seeds = list(range(3, 40))),
              Bot(bid = 40, pos = Pos(1, 0, 0), seeds = [])]

    return state_to_cpp(s)


def test_grounded():
    pass


def test_illegal_smoves():
    em = Cpp.Emulator(set_cpp_state())

    # bot 2 moves out of bounds
    assert em.check_add_command(ctp(commands.Wait())) == ''
    msg = em.check_command(ctp(commands.SMove(Diff(0, 0, 3))))
    assert msg != ''
    
    # bot 2 moves through the filled area
    msg = em.check_command(ctp(commands.SMove(Diff(3, 0, 0))))
    assert msg != ''

    # ...
    c = ctp(commands.Wait())
    em.add_command(c)
    em.add_command(c)
    em.run_step()

    # bot 1 moves through bot 2
    msg = em.check_command(ctp(commands.SMove(Diff(0, 0, 3))))
    assert msg != ''

    # bot 2 moves through volatile area
    assert em.check_add_command(ctp(commands.Fill(Diff(0, 1, 1)))) == ''
    msg = em.check_command(ctp(commands.SMove(Diff(0, 1, 0))))
    assert msg != ''

    # bots 2 & 3 move freely
    assert em.check_add_command(ctp(commands.SMove(Diff(1, 0, 0)))) == ''
    assert em.check_add_command(ctp(commands.SMove(Diff(0, 4, 0)))) == ''
    assert em.steptrace_is_complete()
    em.run_step()



if __name__ == '__main__':
    test_illegal_smoves()
