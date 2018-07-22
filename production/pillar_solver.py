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
        return 'pillar 0.4.2'

    def supports(self, problem_type: ProblemType) -> bool:
        return problem_type == ProblemType.Assemble

    def solve(
            self, name: str,
            src_model: Optional[bytes],
            tgt_model: Optional[bytes]) -> SolverResult:
        assert src_model is None
        model = Model.parse(tgt_model)
        model_height = get_model_height(model)

        plots = create_plots(model)

        trace = single_bot_trace(model, model_height, plots)

        trace_data = compose_commands(trace)
        return SolverResult(trace_data, extra={})


def single_bot_trace(model, model_height, plots):
  trace = []
  trace.append(Flip())
  empty = True
  current_pos = Pos(0, 0, 0)
  for plot in plots:
    plot_pos, plot_height = plot
    trace.extend(move_in_empty_space(plot_pos - current_pos))
    current_pos = plot_pos
    plot_trace, current_pos = fill_plot(model, model_height, plot)
    trace.extend(plot_trace)
  trace.append(Flip())
  trace.extend(move_in_empty_space(Pos(0, 0, 0) - current_pos))
  trace.append(Halt())
  return trace


def fill_plot(model, model_height, plot):
  pos, plot_height = plot
  trace = []
  while True:
    for diff in eight_around_one_below(pos, model.R):
      if model[pos + diff]:
        trace.append(Fill(diff))
    if pos.y == plot_height:
      break
    else:
      shift = Diff(0, 1, 0)
      trace.append(SMove(shift))
      pos += shift

  if pos.y != model_height:
      shift = Diff(0, model_height - pos.y, 0)
      trace.extend(move_in_empty_space(shift))
      pos += shift
  return trace, pos


def dx_dz_3x3(x, z, R):
  dx_low = -1 if x > 0 else 0
  dx_high = 1 if x < R - 1 else 0
  dz_low = -1 if z > 0 else 0
  dz_high = 1 if z < R - 1 else 0
  for dx in range(dx_low, dx_high + 1):
    for dz in range(dz_low, dz_high + 1):
      yield (dx, dz)


def eight_around_one_below(pos, R):
  if pos.y > 0:
    yield Diff(0, -1, 0)
  for (dx, dz) in dx_dz_3x3(pos.x, pos.z, R):
    if (dx != 0) or (dz != 0):
      yield Diff(dx, 0, dz)


def get_model_height(model):
  pos0, pos1 = bounding_box_region(model)
  return pos1.y + 1


def create_plots(model):
  pos0, pos1 = bounding_box_footprint(model)
  plots = []
  for x in range(pos0.x + 1, min(pos1.x + 2, model.R), 3):
    for z in range(pos0.z + 1, min(pos1.z + 2, model.R), 3):
      plot_pos = Pos(x, 0, z)
      plot_height = get_plot_height(model, plot_pos)
      if plot_height > 0:
        plots.append((plot_pos, plot_height))
  return plots


def get_plot_height(model, plot_pos):
  x_z = [(plot_pos.x + dx, plot_pos.z + dz) \
    for (dx, dz) in dx_dz_3x3(plot_pos.x, plot_pos.z, model.R)]
  for y in range(model.R - 2, -1, -1):
    for x, z in x_z:
      if model[Pos(x, y, z)]:
        return y + 1
  return 0


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
  import sys
  name = sys.argv[-1]
  model_data = production.data_files.lightning_problem(f'{name}_tgt.mdl')
  solver = PillarSolver(None)
  result = solver.solve(name, None, model_data).trace_data
  write_solution(result, name)
