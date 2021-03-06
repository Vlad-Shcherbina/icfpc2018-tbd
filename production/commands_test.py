from pathlib import Path
import pytest
import production.commands as commands
from production.commands import parse_command, parse_commands, compose_commands, ParserState, Diff, \
    Halt, Wait, Flip, SMove, LMove, FusionP, FusionS, Fission, Fill, Void, GFill, GVoid


def p(*args):
    return parse_command(ParserState(bytes(args), 'testsource'))


def test_command_examples():
    assert p(0b11111111) == Halt()
    assert p(0b11111110) == Wait()
    assert p(0b11111101) == Flip()
    assert p(0b00010100, 0b00011011) == SMove(Diff(12, 0, 0))
    assert p(0b00110100, 0b00001011) == SMove(Diff(0, 0, -4))
    assert p(0b10011100, 0b00001000) == LMove(Diff(3, 0, 0), Diff(0, -5, 0))
    assert p(0b11101100, 0b01110011) == LMove(Diff(0, -2, 0), Diff(0, 0, 2))
    assert p(0b00111111) == FusionP(Diff(-1, 1, 0))
    assert p(0b10011110) == FusionS(Diff(1, -1, 0))
    assert p(0b01110101, 0b00000101) == Fission(Diff(0, 0, 1), 5)
    assert p(0b01010011) == Fill(Diff(0, -1, 0))
    assert p(0b10111010) == Void(Diff(1, 0, 1))
    assert p(0b01010001, 0b00101000, 0b00001111, 0b00110010) == \
            GFill(Diff(0, -1, 0), Diff(10, -15, 20))
    assert p(0b10110000, 0b00100011, 0b00100011, 0b00011001) == \
            GVoid(Diff(1, 0, 0), Diff(5, 5, -5))


def test_command_exceptions():
    # No longer possible, all prefixes map to a command
    # with pytest.raises(ValueError, match=r"Unrecognized command byte 0b00000000 at 'testsource'\[0\]"):
    #     p(0b00000000)
    with pytest.raises(ValueError, match=r"Unexpected EOF after 0b00010100 at 'testsource'\[0\]"):
        p(0b00010100)
    with pytest.raises(ValueError, match=r"Invalid data for command LMove 0b11111100 0b11111100 at 'testsource'\[0\]: KeyError\(60\)"):
        p(0b11111100, 0b11111100)
    with pytest.raises(ValueError, match=r"Invalid data for command FusionS 0b11110110 at 'testsource'\[0\]: KeyError\(30\)"):
        p(0b11110110)




def test_commands_roundtrip():
    far_distances = (Diff(10, 20, 30), Diff(-30, -20, -10))
    cmds = []
    cmds.extend([Halt(), Wait(), Flip()])
    cmds.extend(SMove(v) for v in commands.lld_table.values())
    cmds.extend(LMove(v1, v2) for v1 in commands.sld_table.values() for v2 in commands.sld_table.values())
    cmds.extend(FusionP(n) for n in commands.nd_table.values())
    cmds.extend(FusionS(n) for n in commands.nd_table.values())
    cmds.extend(Fission(n, m) for n in commands.nd_table.values() for m in range(256))
    cmds.extend(Fill(n) for n in commands.nd_table.values())
    cmds.extend(Void(n) for n in commands.nd_table.values())
    cmds.extend(GFill(n, d) for n in commands.nd_table.values() for d in far_distances)
    cmds.extend(GVoid(n, d) for n in commands.nd_table.values() for d in far_distances)
    composed = compose_commands(cmds)
    if 0: # for manual checking against their chk-trace
        with open(Path(__file__) / '..' / 'testtrace.nbt', 'wb') as f:
            f.write(composed)

    reparsed = parse_commands(composed, 'testinput')
    assert len(cmds) == len(reparsed)
    for i, [a, b] in enumerate(zip(cmds, reparsed)):
        assert a == b, f'{a} != {b} at {i}'


if __name__ == '__main__':
    import pytest, sys
    sys.exit(pytest.main([__file__, '-v']))
