from production.commands import parse_command, Diff, \
    Halt, Wait, Flip, SMove, LMove, FusionP, FusionS, Fission, Fill

def test_command_examples():
    def p(*args):
        return parse_command(iter(args))
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


def test_commands_roundrip():
    ''


if __name__ == '__main__':
    import pytest, sys
    sys.exit(pytest.main([__file__, '-v']))
