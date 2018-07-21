from production.solver_interface import TheirDefaultSolver
from production.default_solver import DefaultSolver
from production.bottom_up_solver import BottomUpSolver
from production.pillar_solver import PillarSolver

ALL_SOLVERS = {
    'their_default': TheirDefaultSolver,
    'default': DefaultSolver,
    'bottom_up': BottomUpSolver,
    'pillar': PillarSolver,
}
