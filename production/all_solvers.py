from production.solver_interface import TheirDefaultSolver
from production.default_solver import DefaultSolver
from production.bottom_up_solver import BottomUpSolver
from production.pillar_solver import PillarSolver
from production.default_solver2 import DefaultSolver2
from production.default_solver2_dec import DefaultSolver2Dec
from production.default_solver2_dec_low import DefaultSolver2DecLow
from production.swarm import SwarmSolver
from production.bfs_solver import BFSSolver
import production.deconstruct.cubical as cubical
import production.deconstruct.cubical2 as cubical2
from production.combiner import Combiner


ALL_SOLVERS = {
    'their_default': TheirDefaultSolver,
    'default': DefaultSolver,
    'default2': DefaultSolver2,
    'default2_dec': DefaultSolver2Dec,
    'default2_dec_low': DefaultSolver2DecLow,
    'bottom_up': BottomUpSolver,
    'pillar': PillarSolver,
    'swarm': SwarmSolver,
    'bfs': BFSSolver,
    'cubical': cubical.CubicalDeconstructor,
    'cubical2': cubical2.CubicalDeconstructor,
    'combiner': Combiner,
}
