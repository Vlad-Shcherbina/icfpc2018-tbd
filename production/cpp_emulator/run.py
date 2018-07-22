# Copied from pyjs_emulator

import subprocess
import os
import os.path
import sys

import tempfile
from tempfile import NamedTemporaryFile
from dataclasses import dataclass
from typing import Optional

import production.cpp_emulator.emulator as Cpp
from production import utils
from production import data_files


@dataclass
class EmulatorResult:
    energy: Optional[int]  # None on failures
    extra: dict  # some additional info, format might be unstable


def run_full(
        src_model_data: Optional[bytes],
        tgt_model_data: Optional[bytes],
        trace_data: bytes) -> EmulatorResult:
    em = Cpp.Emulator()
    if src_model_data:
        em.set_model(src_model_data, 's')
    if tgt_model_data:
        em.set_model(tgt_model_data, 's')
    em.set_trace(trace_data)
    em.setlogfile(str(utils.project_root() / 'outputs' / 'cpp_emulator.log'))

    try:
        em.run()
    except Cpp.SimulatorException as e:
        return EmulatorResult(energy = None, 
                              extra = {'error message' : str(e)})

    return EmulatorResult(energy = em.energy(), extra = {})


# Usage:
#   run.py <task_number>
#   run.py <default_solver_cmd.py> <task_number>
def main():
    if len(sys.argv) == 3:
        (_, solver_cmd, task_number_str) = sys.argv
    else:
        solver_cmd = "production.default_solver"
        (_, task_number_str) = sys.argv

    task_number = int(task_number_str)

    (src, tgt) = data_files.full_problem('FR{0:03d}'.format(task_number))
    # subprocess.call("python -m " + solver_cmd + " " + task_number_str, shell=True, cwd = os.path.join(os.path.dirname(__file__), "../../"))
    trace_data = data_files.full_default_trace("FR{0:03d}".format(task_number))
    #trace_data = read_trace_data(task_number)

    result = run_full(src, tgt, trace_data)
    print(result)
    print(f"| {task_number} | {result.energy}")

if __name__ == "__main__":
    main()
