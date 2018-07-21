import subprocess
import os
import os.path
import sys
import tempfile
from tempfile import NamedTemporaryFile
from dataclasses import dataclass
from typing import Optional

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


def do_run(*args) -> EmulatorResult:
    fname = os.path.join(os.path.dirname(__file__), "trace.js")
    proc = subprocess.Popen(
        ("node", fname) + args,
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

def run_full(
        src_model_data: Optional[bytes],
        tgt_model_data: Optional[bytes],
        trace_data: bytes) -> EmulatorResult:

    src_name, tgt_name = "None", "None"
    if src_model_data:
        with NamedTemporaryFile(delete=False, suffix="_src.mdl") as src_mdl:
            src_mdl.write(src_model_data)
            src_name = src_mdl.name
    if tgt_model_data:
        with NamedTemporaryFile(delete=False, suffix="_tgt.mdl") as tgt_mdl:
            tgt_mdl.write(tgt_model_data)
            tgt_name = tgt_mdl.name

    with NamedTemporaryFile(delete=False, suffix=".nbt") as trace:
         trace.write(trace_data)
    
    result = do_run("full", src_name, tgt_name, trace.name)

    if src_model_data: os.remove(src_name)
    if tgt_model_data: os.remove(tgt_name)
    os.remove(trace.name)

    return result

def run(model_data: bytes, trace_data: bytes) -> EmulatorResult:
    model_name = tempfile.NamedTemporaryFile(delete=False).name
    with open(model_name, 'wb') as fout:
        fout.write(model_data)

    trace_name = tempfile.NamedTemporaryFile(delete=False).name
    with open(trace_name, 'wb') as fout:
        fout.write(trace_data)

    result = do_run("lgtn", str(model_name), str(trace_name))

    os.remove(model_name)
    os.remove(trace_name)
    return result


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
