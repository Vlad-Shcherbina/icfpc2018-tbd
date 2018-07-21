from production.model import Model
from production.commands import *
from production.basics import Pos, Diff
from production.solver_utils import *

# Default solver: compute a bounding box, set harmonics to High, use a
# single bot to sweep each xz-plane of the bounding box from bottom to top
# filling the voxel below the bot if necessary, return to the origin,
# set harmonics to Low, and halt
def default_strategy(model): # -> [Commands]
    commands = []

    commands.append(Flip())

    pos_min,pos_max = bounding_box(model)
    
    commands.append(SMove(Diff(0,0,1)))
    commands.append(SMove(Diff(0,1,0)))
    commands.append(SMove(Diff(1,0,0)))

    x = 1
    z = 1
    xup = True
    zup = True

    for y in range(1,pos_max.y+2):
        while (x >= pos_min.x and not xup) or (x <= pos_max.x and xup):
            while (z >= pos_min.z and not zup) or (z <= pos_max.z and zup):
                if model[Pos(x,y-1,z)]:
                    commands.append(Fill(Diff(0, -1, 0)))
                if (not zup and z == pos_min.z) or (z == pos_max.z and zup):
                    break
                commands.append(SMove(Diff(0,0, 1 if zup else -1)))
                z += (1 if zup else -1)
            if (not xup and x == pos_min.x) or (xup and x == pos_max.x):
                break
            commands.append(SMove(Diff(1 if xup else -1,0,0)))
            x += (1 if xup else -1)
            zup = not zup
        commands.append(SMove(Diff(0,1,0)))
        xup = not xup
        zup = not zup    

    for i in reversed(range(z)):
        commands.append(SMove(Diff(0,0,-1)))
    for i in reversed(range(y+1)):
        commands.append(SMove(Diff(0,-1,0)))
    for i in reversed(range(x)):
        commands.append(SMove(Diff(-1,0,0)))

    commands.append(Flip())
    commands.append(Halt())

    return commands


def write_solution(bytetrace, number): # -> IO ()
    with open('LA'+number+'.nbt', 'wb') as f:
        f.write(bytetrace)

def solve(strategy, model, number = 'XXX'): # -> IO ()
    commands = strategy(model)
    trace = compose_commands(commands)
    write_solution(trace, number)

def main():
    from production import data_files

    task_number = '001'

    name = 'LA'+task_number+'_tgt.mdl'
    data = data_files.lightning_problem(name)
    m = Model.parse(data)
    
    solve(default_strategy, m, task_number)

if __name__ == '__main__':
    main()
