from production.all_solvers import ALL_SOLVERS
from production.solver_worker import solve
from production import data_files


def test_all_successful_solvers():
    for solver_class in ALL_SOLVERS.values():
        # Wall of shame in code form
        if solver_class.__name__ in ['SwarmSolver', 'Combiner', 'DefaultSolver2', 'DefaultSolver2Dec']: continue
        solver = solver_class([])
        for c in 'ADR':
            name = f'F{c}011'
            src_model, tgt_model = data_files.full_problem(name)
            r = solve(solver, name, src_model, tgt_model)
            assert r.status in ('DONE', 'PASS'), f'{solver_class.__name__} failed'


if __name__ == '__main__':
    test_all_successful_solvers()
