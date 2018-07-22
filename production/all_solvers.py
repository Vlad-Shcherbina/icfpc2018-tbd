from production.solver_interface import TheirDefaultSolver
from production.default_solver import DefaultSolver
from production.bottom_up_solver import BottomUpSolver
from production.pillar_solver import PillarSolver
from production.default_solver2 import DefaultSolver2
from production.swarm import SwarmSolver
from production.bfs_solver import BFSSolver

ALL_SOLVERS = {
    'their_default': TheirDefaultSolver,
    'default': DefaultSolver,
    'default2': DefaultSolver2,
    'bottom_up': BottomUpSolver,
    'pillar': PillarSolver,
    'swarm': SwarmSolver,
    'bfs': BFSSolver,
}
