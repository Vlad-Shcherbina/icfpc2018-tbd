#!/bin/env python3

# very incomplete but better than nothing

from production.solver_worker import solve
from production.solver_interface import Solver, TheirDefaultSolver, SolverResult, Fail
from production import data_files

def test_successful_solve():
    solver = TheirDefaultSolver([])
    for c, energy in (('A', 204790024), ('D', 204782296), ('R', 615699776)):
        name = f'F{c}011'
        src_model, tgt_model = data_files.full_problem(name)
        r = solve(solver, name, src_model, tgt_model)
        assert r.status == 'DONE'
        assert r.energy == energy
        assert r.extra['pyjs']['res']['Energy'] == str(energy)


def test_errors():
    name = f'FR011'
    src_model, tgt_model = data_files.full_problem(name)

    class Broken(TheirDefaultSolver):
        def solve(self, *args, **kwargs):
            return SolverResult(Fail())

    r = solve(Broken([]), name, src_model, tgt_model)
    assert r.status == 'FAIL'

    class Broken(TheirDefaultSolver):
        def solve(self, *args, **kwargs):
            return 1/0

    r = solve(Broken([]), name, src_model, tgt_model)
    assert r.status == 'FAIL'

    class Broken(TheirDefaultSolver):
        def solve(self, *args, **kwargs):
            return SolverResult(b'123213')

    r = solve(Broken([]), name, src_model, tgt_model)
    assert r.status == 'CHECK_FAIL'



if __name__ == '__main__':
    test_successful_solve()
    test_errors()