from typing import Optional
import zlib
import logging
logger = logging.getLogger(__name__)

from production.solver_interface import ProblemType, Solver, SolverResult, Fail, Pass
from production.cpp_emulator.emulator import Matrix
from production import db

_conn = None
def get_shared_conn():
    global _conn
    if _conn is None:
        _conn = db.get_conn()
    return _conn

class Combiner(Solver):
    def __init__(self, args):
        [self.epoch] = args

    def scent(self) -> str:
        return 'Combiner ' + self.epoch

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type == ProblemType.Reassemble

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        conn = get_shared_conn()
        cur = conn.cursor()

        assert name.startswith('FR')

        traces = {}
        energies = {}
        for part in ['ZD', 'ZA']:
            cur.execute('''
                SELECT
                    traces.data, energy
                FROM problems
                JOIN traces
                ON traces.problem_id = problems.id
                WHERE problems.name = %s AND traces.status = 'DONE'
                ORDER BY traces.energy
                LIMIT 1
            ''', [name.replace('FR', part)])
            rows = cur.fetchall()
            if not rows:
                return SolverResult(Pass())
            [[trace, energy]] = rows
            traces[part] = zlib.decompress(trace)
            energies[part] = energy

        R = Matrix.parse(src_model).R
        assert traces['ZD'][-1] == 255
        return SolverResult(
            traces['ZD'][:-1] + traces['ZA'],
            dict(expected_energy=energies['ZD'] - 3 * R**3 - 20 + energies['ZA']))
