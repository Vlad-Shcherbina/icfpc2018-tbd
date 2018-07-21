from production.model import Model
from production.basics import Pos, Diff
from production.solver_interface import *
from production.solver_utils import *
from production.commands import *


class PillarSolver(Solver):
    def __init__(self, args):
        pass

    def scent(self) -> str:
        # Iz govna i palok.
        return 'pillar 0.1'

    def solve(self, name: str, model_data: bytes) -> SolverResult:
        self.model = Model.parse(model_data)
        self.model_height = model_height(self.model)

        self.plots = create_plots(self.model)

        trace = self.single_bot_trace()

        trace_data = compose_commands(trace)
        return SolverResult(trace_data, extra={})

    def single_bot_trace(self):
      trace = []
      trace.append(Flip())
      empty = True
      current_pos = Pos(0, 0, 0)
      for plot in self.plots:
        trace.extend(move_in_empty_space(plot - current_pos))
        current_pos = plot
        plot_trace, current_pos = self.fill_plot(current_pos)
        trace.extend(plot_trace)
      trace.append(Flip())
      trace.extend(move_in_empty_space(Pos(0, 0, 0) - current_pos))
      trace.append(Halt())
      return trace

    def fill_plot(self, pos):
      trace = []
      while pos.y <= self.model_height:
        for diff in eight_around_and_maybe_one_below(pos):
          if self.model[pos + diff]:
            trace.append(Fill(diff))
        shift = Diff(0, 1, 0)
        trace.append(SMove(shift))
        pos += shift
      return trace, pos


def eight_around_and_maybe_one_below(pos):
  if pos.y > 0:
    yield Diff(0, -1, 0)
  for dx in range(-1, 2):
    for dz in range(-1, 2):
      if (dx != 0) or (dz != 0):
        yield Diff(dx, 0, dz)


def model_height(model):
  pos0, pos1 = bounding_box_region(model)
  return pos1.y + 1

def create_plots(model):
  pos0, pos1 = bounding_box_region(model, fy=0)
  plots = []
  for x in range(pos0.x, pos1.x + 1, 3):
    for z in range(pos0.z, pos1.z + 1, 3):
      plots.append(Pos(x + 1, 0, z + 1))
  return plots

def long_distances(d):
  assert d != 0
  if d > 0:
    while d > 15:
      yield 15
      d -= 15
    yield d
  elif d < 0:
    while d < -15:
      yield -15
      d += 15
    yield d

def move_in_empty_space(diff):
  # Move in XZ plane first, that way we can use this to float above model.
  commands = []
  if diff.dx != 0:
    for dx in long_distances(diff.dx):
      commands.append(SMove(Diff(dx, 0, 0)))
  if diff.dz != 0:
    for dz in long_distances(diff.dz):
      commands.append(SMove(Diff(0, 0, dz)))
  if diff.dy != 0:
    for dy in long_distances(diff.dy):
      commands.append(SMove(Diff(0, dy, 0)))

  return commands


def write_solution(bytetrace, name): # -> IO ()
    with open(f'{name}.nbt', 'wb') as f:
        f.write(bytetrace)


if __name__ == '__main__':
  import production.data_files
  name = 'LA109'
  model_data = production.data_files.lightning_problem(f'{name}_tgt.mdl')
  solver = PillarSolver(None)
  result = solver.solve(name, model_data).trace_data
  write_solution(result, name)
