from typing import Optional
import logging
logger = logging.getLogger(__name__)

from production.solver_interface import ProblemType, Solver, SolverResult, Fail, Pass
from production.cpp_emulator.emulator import Pos, Diff, Matrix
from production.cpp_emulator import emulator as cpp
from production.cpp_mediator import cmd_from_cpp
from production import commands


class SwarmSolver(Solver):
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        return 'Swarm 0.7 3x3x3 up'

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type != ProblemType.Disassemble  # no competing with cubical

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        if src_model is not None:
            src_model = Matrix.parse(src_model)
        if tgt_model is not None:
            tgt_model = Matrix.parse(tgt_model)
        if src_model is None:
            src_model = Matrix(tgt_model.R)
        if tgt_model is None:
            tgt_model = Matrix(src_model.R)

        logger.info((src_model, tgt_model))

        R = src_model.R

        cur_model = Matrix(src_model)

        trace = []
        bot_pos = Pos(0, 0, 0)
        logger.info(f'R = {R}')

        while cur_model != tgt_model:
            changed = False
            for nd in cpp.enum_near_diffs():
                p = bot_pos + nd
                if not p.is_inside(R):
                    continue
                if cur_model[p] == tgt_model[p]:
                    continue
                if not cpp.safe_to_change(cur_model, p):
                    continue
                if cur_model[p]:
                    trace.append(cpp.Void(nd))
                    cur_model[p] = False
                else:
                    trace.append(cpp.Fill(nd))
                    cur_model[p] = True
                changed = True
                break
            if changed:
                continue

            p = cpp.path_to_nearest_safe_change_point(cur_model, bot_pos, cur_model, tgt_model)
            if p is None:
                return SolverResult(Pass(), extra=dict(msg='no reachable targets'))

            target, path = p
            for cmd in path:
                trace.append(cmd)
                bot_pos += cmd.move_offset()
            assert bot_pos == target

        # get back
        p = cpp.path_to_nearest_of(cur_model, bot_pos, [Pos(0, 0, 0)])
        if p is None:
            return SolverResult(Fail(), extra=dict(msg="done but can't reach exit"))
        trace.extend(p[1])
        trace.append(cpp.Halt())

        trace = [cmd_from_cpp(cmd) for cmd in trace]
        trace = commands.compose_commands(trace)
        return SolverResult(trace)
