from typing import Optional
import logging
logger = logging.getLogger(__name__)

from production.solver_interface import ProblemType, Solver, SolverResult, Fail
from production.cpp_emulator.emulator import Pos, Diff, Matrix
from production.cpp_emulator import emulator as cpp
from production.cpp_mediator import cmd_from_cpp
from production import commands


class SwarmSolver(Solver):
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        return 'Swarm 0.0'

    def supports(self, problem_type: ProblemType) -> bool:
        return True

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
        if R > 20:
            return SolverResult(Fail(), extra=dict(msd='too large'))

        cur_model = Matrix(src_model)

        trace = []
        bot_pos = Pos(0, 0, 0)

        while cur_model != tgt_model:
            sz = cur_model.num_grounded_voxels()

            diff = []
            total_diff_size = 0
            for x in range(R):
                for y in range(R):
                    for z in range(R):
                        p = Pos(x, y, z)
                        if cur_model[p] == tgt_model[p]:
                           continue
                        total_diff_size += 1
                        if cur_model[p]:
                            cur_model[p] = False
                            sz2 = sz - 1
                        else:
                            cur_model[p] = True
                            sz2 = sz + 1
                        if cur_model.num_grounded_voxels() == sz2:
                            diff.append(p)
                        cur_model[p] = not cur_model[p]
            if total_diff_size % 100 == 0:
                logger.info(f'total diff {total_diff_size}')
            assert diff

            targets = list(cpp.near_neighbors(R, diff).keys())

            obstacles = Matrix(cur_model)
            p = cpp.path_to_nearest_of(obstacles, bot_pos, targets)
            if p is None:
                return SolverResult(Pass(), extra=dict(msg='no reachable targets'))

            target, path = p
            for cmd in path:
                trace.append(cmd)
                bot_pos += cmd.move_offset()
            assert bot_pos == target

            for nd in cpp.enum_near_diffs():
                p = bot_pos + nd
                if p not in diff:
                    continue
                if cur_model[p]:
                    trace.append(cpp.Void(nd))
                    cur_model[p] = False
                else:
                    trace.append(cpp.Fill(nd))
                    cur_model[p] = True
                break # TODO articulation point recheck


        # get back
        p = cpp.path_to_nearest_of(cur_model, bot_pos, [Pos(0, 0, 0)])
        if p is None:
            return SolverResult(Fail(), extra=dict(msg="done but can't reach exit"))
        trace.extend(p[1])
        trace.append(cpp.Halt())

        trace = [cmd_from_cpp(cmd) for cmd in trace]
        trace = commands.compose_commands(trace)
        return SolverResult(trace)
