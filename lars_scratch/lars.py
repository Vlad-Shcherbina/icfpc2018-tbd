from pprint import pprint

from lars_scratch.state import *
from production.basics import Pos, Diff
from production.commands import *
from production.model import Model
from production.data_files import lightning_problem_by_id

def get_model(model_id):
    return Model.parse(lightning_problem_by_id(model_id))

def solve(source, target):
    state = State(source, target)

    state.bots[0].command = Fission(Diff(1, 0, 0), 20)
    state.tick()

    state.bots[0].command = Fill(Diff(0, 1, 0))
    state.bots[1].command = SMove(Diff(0, 1, 0))
    state.tick()

    state.bots[1].command = Void(Diff(-1, 0, 0))
    state.tick()

    state.bots[0].fuse(state.bots[1])
    state.tick()

    pprint(state.bots)

    state.bots[0].command = Halt()
    state.tick()

    print(state.correct())
    pprint(state.trace)
    return state.dump_trace()

binary_trace = solve(get_model(1), get_model(2))
