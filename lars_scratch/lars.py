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
    state.tick([Fission(Diff(1, 0, 0), 20)])
    state.tick([Fill(Diff(0, 1, 0)), SMove(Diff(0, 1, 0))])
    state.tick([Wait(), Void(Diff(-1, 0, 0))])
    state.tick([FusionP(Diff(1, 1, 0)), FusionS(Diff(-1, -1, 0))])
    state.tick([Halt()])

    print(state.correct())

    pprint(state.trace)
    pprint(state.bots)
    return state.dump_trace()

binary_trace = solve(get_model(1), get_model(2))
