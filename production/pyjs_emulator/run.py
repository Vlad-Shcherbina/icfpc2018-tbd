import subprocess
import os.path

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

def do_run(model, trace):
    """run the emulator, return (success, desc, dict, log)"""
    fname = os.path.join(os.path.dirname(__file__), "trace.js")
    proc = subprocess.Popen(["node", fname, model, trace], stdout=subprocess.PIPE)
    stdout,stderr = proc.communicate()
    result = stdout.decode('ascii').split('=== ')[-1].split('\n')
    if result[0].startswith("Failure"):
        res, etc = dictify(result)
        return (False, "Failure") + dictify(result)
    elif result[0].startswith("Success"):
        res, etc = dictify(result)
        return (True, "Success") + dictify(result)
    else:
        raise SimulatorException("simulation returned unknown result", result)


def run(model_data: bytes, trace_data: bytes):
    model_name = utils.project_root() / '_tmp_model.mdl'
    with open(model_name, 'wb') as fout:
        fout.write(model_data)

    trace_name = utils.project_root() / '_tmp_trace.nbt'
    with open(trace_name, 'wb') as fout:
        fout.write(trace_data)

    return do_run(str(model_name), str(trace_name))


def main():
    problem = 'LA005'

    model_data = data_files.lightning_problem(f'{problem}_tgt.mdl')
    trace_data = data_files.lightning_default_trace(f'{problem}.nbt')

    result = run(model_data, trace_data)
    print(result)


if __name__ == "__main__":
    main()
