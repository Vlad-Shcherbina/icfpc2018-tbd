import sys
from io import StringIO
from typing import List
import traceback

from production.model import Model
from production.commands import *
from production.basics import Pos, Diff
from production.solver_utils import *
from production.solver_interface import ProblemType, Solver, SolverResult, Fail

# Default solver: compute a bounding box, set harmonics to High, use a
# single bot to sweep each xz-plane of the bounding box from bottom to top
# filling the voxel below the bot if necessary, return to the origin,
# set harmonics to Low, and halt
def default_assembly(model_src, model_tgt) -> List[Command]:

    start,finish = bounding_box(model_tgt)

    return apply_default_strategy(Model(model_tgt.R), model_tgt, (3,1,1), start)

# Default disassembly solver: compute a bounding box, use a single bot to
# sweep each xz-plane of the bounding box from top to bottom emptying the
# voxel below the bot if necessary, return to the origin, halt
def default_disassembly(model_src,model_tgt = None) -> List[Command]:

    finish, start = bounding_box(model_src)
    start = Pos(finish.x,start.y,finish.z)

    return apply_default_strategy(model_src, Model(model_src.R), (3,-1,1), start, False)

# Default reassembly solver: compute a bounding box, set harmonics to High, use a
# single bot to sweep each xz-plane of the bounding box from top to bottom
# emptying and filling the voxel in front of the bot if necessary, return to origin,
# set harmonics to Low, halt
def default_reassembly(model_src, model_tgt) -> List[Command]:

    finish,start = merge_bounding_boxes(bounding_box(model_src),bounding_box(model_tgt))
    start = Pos(finish.x,start.y,finish.z)

    return apply_default_strategy(model_src, model_tgt, (3,-1,1), start, True)

# So for every type of problems, our strategies are basically the same:
# compute bounding box, sweep every layer on the same harmonics, entering
# it only once, return to origin, halt.
# This function deals with the common behaviour of three problem types.
def apply_default_strategy(model_src, model_tgt, speeds : Tuple[int,int,int], starting_point : Pos,
                           reassembly : Optional[bool] = False) -> List[Command]:


    # make a pass on that xz-layer's bounding box in a snake-like manner
    # (perusing default_solver2 functionality)
    # behaviour_func describes what actions a single bot should execute
    # between each move
    # also scoping is fucking me up, hence the stupid extra args
    def make_layer_pass(x,y,z,zup, layer_bounding_box, behaviour_func):
        bbox_min,bbox_max = layer_bounding_box

        while (x >= bbox_min.x and not xup) or (x <= bbox_max.x and xup):
            while (z >= bbox_min.z and not zup) or (z <= bbox_max.z and zup):

                behaviour_func(x,y,z,zup, layer_bounding_box)

                if (not zup and z == bbox_min.z) or (z == bbox_max.z and zup):
                    break
                dz = z_speed if zup else -z_speed
                commands.append(SMove(Diff(0,0,dz)))
                z += dz
            if (not xup and x == bbox_min.x) or (xup and x == bbox_max.x):
                break

            dx = x_speed if xup else -x_speed

            if not is_inside_region(Pos(x+dx,y-offset,z),bbox_min,bbox_max):
                bbox = bbox_max
                if not xup:
                    bbox = bbox_min

                dx = bbox.x - x

            if reassembly:

                off = 1 if zup else -1
                commands.append(SMove(Diff(0,0,off)))
                if model_tgt[Pos(x,y,z)]:
                    commands.append(Fill(Diff(0,0,-off)))
                commands.append(SMove(Diff(dx,0,0)))
                x += dx

                if model_src[Pos(x,y,z)]:
                    commands.append(Void(Diff(0,0,-off)))
                commands.append(SMove(Diff(0,0,-off)))
            else:
                commands.append(SMove(Diff(dx,0,0)))
                x += dx

            zup = not zup

        return x,y,z,zup

    def filling_func(x,y,z,zup,bbox):
        bbox_min, bbox_max = bbox

        lookahead = (0 if z == bbox_max.z else int(reassembly))\
                        if zup else (0 if z == bbox_min.z else -int(reassembly))
        lookbehind = (0 if z == bbox_min.z else -int(reassembly))\
                        if zup else (0 if z == bbox_max.z else int(reassembly))

        if reassembly and model_src[Pos(x,y-offset,z+lookahead)]:
            if lookahead != 0:
                commands.append(Void(Diff(0,-offset,lookahead)))
        if x != bbox_min.x:
            action = choose_action(model_src, model_tgt, Pos(x-1,y-offset,z))
            if action is not None:
                commands.append(action(Diff(-1, -offset, 0)))
        if not reassembly or lookbehind != 0:
            action = choose_action(model_src, model_tgt, Pos(x,y-offset,z+lookbehind), lookbehind != 0)
            if action is not None:
                commands.append(action(Diff(0, -offset, lookbehind)))
        if x != bbox_max.x:
            action = choose_action(model_src, model_tgt, Pos(x+1,y-offset,z))
            if action is not None:
                commands.append(action(Diff(1, -offset, 0)))

    ####################################################################


    if model_src == model_tgt:
        return [Halt()]

    offset = int(not reassembly)
    x_speed, y_speed, z_speed = speeds
    bbox_min,bbox_max = merge_bounding_boxes(bounding_box(model_src),bounding_box(model_tgt))
    y_finish = bbox_max.y if y_speed > 0 else bbox_min.y

    corner_voxel = reassembly and model_src[starting_point]
    mind_the_corner = Diff(0,0,1) if corner_voxel else Diff(0,0,0)

    commands = list(navigate(Pos(0,0,0), starting_point + Diff(0,offset,0) + mind_the_corner * -1))

    if corner_voxel:
        commands.append(Void(mind_the_corner))
        commands.append(SMove(mind_the_corner))

    x,y,z = starting_point.x, starting_point.y + offset, starting_point.z

    xup = zup = True

    if y_speed < 0:
        commands.append(Flip())

    while (y != y_finish+2*int(y_speed > 0)-int(reassembly)):

        x,y,z,zup = make_layer_pass(x,y,z,zup, (bbox_min,bbox_max),filling_func)

        if not reassembly and y == offset+int(y_speed < 0):
            commands.append(Flip())
        if y == y_finish+int(y_speed > 0):
            break

        if reassembly:
            if model_src[Pos(x,y+y_speed,z)]:
                commands.append(Void(Diff(0,y_speed,0)))

        commands.append(SMove(Diff(0,y_speed,0)))
        y += y_speed
        if reassembly:
            if model_tgt[Pos(x,y-y_speed,z)]:
                commands.append(Fill(Diff(0,-y_speed,0)))
        xup = not xup
        zup = not zup

    if y_speed > 0 or reassembly:
        commands.append(Flip())

    corner_voxel = reassembly and model_tgt[Pos(x,y,z)]
    mind_the_corner = Diff(0,0,-1) if corner_voxel else Diff(0,0,0)

    if corner_voxel:
        commands.append(SMove(mind_the_corner))
        z -= 1
        commands.append(Fill(mind_the_corner * -1))

    commands += list(navigate(Pos(x,y,z), Pos(0,0,0)))

    commands.append(Halt())

    return commands

def choose_action(m_src, m_tgt, pt, reassemble_behind = False):
    if not reassemble_behind and m_src[pt] and not m_tgt[pt]:
        return Void
    if not m_src[pt] and m_tgt[pt]:
        return Fill
    if reassemble_behind and m_src[pt] and m_tgt[pt]:
        return Fill
    return None


class DefaultSolver(Solver):
    def __init__(self, args):
        assert not args

    def scent(self) -> str:
        # note that 'Default 2.0' (and perhaps higher)
        # are already taken by default_solver2.py :(
        return 'Default 1.4.1'

    def supports(self, problem_type: ProblemType) -> bool:
        result = \
                 problem_type == ProblemType.Assemble\
              or problem_type == ProblemType.Disassemble\
              or problem_type == ProblemType.Reassemble
        return result

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        m_src = m_tgt = None
        if src_model is not None:
            m_src = Model.parse(src_model)
            strategy = default_disassembly
        if tgt_model is not None:
            m_tgt = Model.parse(tgt_model)
            strategy = default_assembly
        if src_model is not None and tgt_model is not None:
            strategy = default_reassembly

        trace = strategy(m_src, m_tgt)
        trace_data = compose_commands(trace)
        return SolverResult(trace_data, extra={})


def write_solution(bytetrace, name): # -> IO ()
    with open(name+'.nbt', 'wb') as f:
        f.write(bytetrace)

def main():
    from production import data_files

    task_name = sys.argv[1] if len(sys.argv) > 1 else 'FA001'

    data_src,data_tgt = data_files.full_problem(task_name)
    m_src = m_tgt = None
    if data_src is not None:
        m_src = Model.parse(data_src)
    if data_tgt is not None:
        m_tgt = Model.parse(data_tgt)

    commands = default_disassembly(m_src,m_tgt)
    trace = compose_commands(commands)
    write_solution(trace, task_name)

if __name__ == '__main__':
    main()
