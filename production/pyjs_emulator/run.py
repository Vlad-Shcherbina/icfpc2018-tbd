import subprocess
import os.path
import sys
from dataclasses import dataclass
from typing import Optional

from production import utils
from production import data_files


def dictify(result):
    res = {}
    etc = []
    for line in result:
        l = line.split(': ', 1)
        if len(l) > 1:
            res[l[0]] = l[1].strip()
        elif line:
            etc.append(line)
    return res, etc

class SimulatorException(Exception):
    pass


@dataclass
class EmulatorResult:
    energy: Optional[int]  # None on failures
    extra: dict  # some additional info, format might bu unstable


def do_run(model, trace) -> EmulatorResult:
    fname = os.path.join(os.path.dirname(__file__), "trace.js")
    proc = subprocess.Popen(
        ["node", fname, model, trace],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        return EmulatorResult(
            energy=None,
            extra=dict(returncode=proc.returncode, stdout=stdout, stderr=stderr))
    result = stdout.split('=== ')[-1].split('\n')
    if result[0].startswith("Failure"):
        res, etc = dictify(result)
        return EmulatorResult(
            energy=None,
            extra=dict(res=res, etc=etc, stderr=stderr))
    elif result[0].startswith("Success"):
        res, etc = dictify(result)
        return EmulatorResult(
            energy=int(res['Energy']),
            extra=dict(res=res, etc=etc, stderr=stderr))
    else:
        raise SimulatorException("simulation returned unknown result", result)


def run(model_data: bytes, trace_data: bytes) -> EmulatorResult:
    model_name = utils.project_root() / '_tmp_model.mdl'
    with open(model_name, 'wb') as fout:
        fout.write(model_data)

    trace_name = utils.project_root() / '_tmp_trace.nbt'
    with open(trace_name, 'wb') as fout:
        fout.write(trace_data)

    return do_run(str(model_name), str(trace_name))

def read_trace_data(task_number):
    fname = 'LA{0:03d}.nbt'.format(task_number)
    with open(fname, 'rb') as f:
        return f.read()

# Usage:
#   run.py <task_number>
#   run.py <default_solver_cmd.py> <task_number>
def main():
    if len(sys.argv) == 3:
        (_, solver_cmd, task_number_str) = sys.argv
    else:
        solver_cmd = "../default_solver.py"
        (_, task_number_str) = sys.argv

    task_number = int(task_number_str)

    model_data = data_files.lightning_problem('LA{0:03d}_tgt.mdl'.format(task_number))
    subprocess.call("python " + solver_cmd + " " + task_number_str, shell=True)
    trace_data = read_trace_data(task_number)

    result = run(model_data, trace_data)
    print(f"| {task_number} | {result.energy}")

if __name__ == "__main__":
    main()
