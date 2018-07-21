import production.model as M
import production.commands as Cmd
import sys

from production.model import Model
from production.basics import (Diff, Pos)

def all_commands(fname):
    with open(fname, 'rb') as f:
        src = Cmd.ParserState(f.read(), fname)
        while True:
            x = Cmd.parse_command(src)
            if x:
                yield x
            else:
                break


if __name__ == '__main__':
    fname = str(sys.argv[1])

    pos = Pos(0, 0, 0)
    for cmd in all_commands(fname):
        if type(cmd) == Cmd.SMove:
            pos = pos + cmd.lld
            print(pos)
        elif type(cmd) in [Cmd.Fill, Cmd.Flip, Cmd.Halt]:
            pass
        else:
            print(type(cmd))
            assert(False)
