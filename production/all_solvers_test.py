import pytest

from production.all_solvers import ALL_SOLVERS
from production.solver_worker import solve
from production import data_files


@pytest.mark.parametrize('solver_class', ALL_SOLVERS.values())
def test_all_successful_solvers(solver_class):
    # Wall of shame in code form
    if solver_class.__name__ in ['SwarmSolver', 'Combiner', 'DefaultSolver2', 'DefaultSolver2Dec', 'DefaultSolver2DecLow']:
        pytest.skip()
    solver = solver_class([])
    for c in 'ADR':
        name = f'F{c}011'
        src_model, tgt_model = data_files.full_problem(name)
        r = solve(solver, name, src_model, tgt_model)
        assert r.status in ('DONE', 'PASS'), f'{solver_class.__name__} failed'
