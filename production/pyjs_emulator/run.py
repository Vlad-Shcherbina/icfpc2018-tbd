import subprocess
import os.path

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
        raise SimulatorException("simulation returned unknown result", res, etc)
                

if __name__ == "__main__":
    directory = os.path.join(os.path.dirname(__file__), "../../../icfpcontest2018.github.io/assets/")
    print(do_run(directory + "LA005_tgt.mdl", directory + "LA005.nbt"))
