from dataclasses import dataclass
from functools import update_wrapper
from typing import Tuple, ClassVar, Dict

from production.basics import Diff


def encode_sld(v : Diff):
    assert v.is_short_linear()
    if v.dx:
        return 0x010000 | v.dx + 5
    if v.dy:
        return 0x100000 | v.dy + 5
    if v.dz:
        return 0x110000 | v.dz + 5
    assert False, f'Invalid sld: {v}'


def encode_lld(v : Diff):
    assert v.is_long_linear()
    if v.dx:
        return 0x0100000 | v.dx + 15
    if v.dy:
        return 0x1000000 | v.dy + 15
    if v.dz:
        return 0x1100000 | v.dz + 15
    assert False, f'Invalid sld: {v}'


def generate_table(encoder):
    return lambda generator: { encoder(it) : it for it in generator() }


@generate_table(encode_sld)
def sld_map():
    for i in range(1, 6):
        yield Diff( i,  0,  0)
        yield Diff(-i,  0,  0)
        yield Diff( 0,  i,  0)
        yield Diff( 0, -i,  0)
        yield Diff( 0,  0,  i)
        yield Diff( 0,  0, -i)
assert len(sld_map) == 30


@generate_table(encode_lld)
def lld_map():
    for i in range(1, 16):
        yield Diff( i,  0,  0)
        yield Diff(-i,  0,  0)
        yield Diff( 0,  i,  0)
        yield Diff( 0, -i,  0)
        yield Diff( 0,  0,  i)
        yield Diff( 0,  0, -i)
assert len(lld_map) == 90


commands_by_id = {}
def command(cls):
    res = dataclass(frozen=True)(cls)
    commands_by_id[cls.bid] = res
    return res


@command
class Halt:
    bid : ClassVar = 0b11111111
    bsize : ClassVar = 1

    @classmethod
    def parse(cls, b):
        return cls()


@command
class Wait:
    bid : ClassVar = 0b11111110
    bsize : ClassVar = 1

    @classmethod
    def parse(cls, b):
        return cls()


@command
class Flip:
    bid : ClassVar = 0b11111101
    bsize : ClassVar = 1

    @classmethod
    def parse(cls, b):
        return cls()


@command
class SMove:
    bid : ClassVar = 0b0101
    bsize : ClassVar = 2

    lld : Diff

    @classmethod
    def parse(cls, b, b2):
        return cls(lld_map[((b & 0b00110000) << 1) + b2 & 0b11111])


@command
class LMove:
    bid : ClassVar = 0b1101
    bsize : ClassVar = 2

    sld1 : Diff
    sld2 : Diff

    @classmethod
    def parse(cls, b, b2):
        return cls(
            sld_map[((b & 0b11000000) >> 2) + b2 & 0b11111])

@command
class Fission:
    bid : ClassVar = 0b101
    bsize : ClassVar = 2

    nd : Diff
    m : int


@command
class Fill:
    bid : ClassVar = 0b011
    bsize : ClassVar = 1

    nd : Diff


@command
class FusionP:
    bid : ClassVar = 0b111
    bsize : ClassVar = 1

    nd : Diff


@command
class FusionS:
    bid : ClassVar = 0b110
    bsize : ClassVar = 1

    nd : Diff


def parse_command(it):
    '`it` should be an iterator returning bytes'
    #todo: buffer protocol(?), better error exceptions
    b = next(it, None)
    if b is None:
        return None
    cmd = commands_by_id.get(b)
    if cmd is None:
        cmd = commands_by_id.get(b & 0b1111)
    if cmd is None:
        cmd = commands_by_id.get(b & 0b111)
    if cmd is None:
        assert False, f'Unrecognized command byte {b:01X}'
    if cmd.bsize == 2:
        b2 = next(it, None)
        if b2 is None:
            assert False, f'Unexpected EOF after {b:01X}'
        return cmd.parse(b, b2)
    else:
        return cmd.parse(b)

