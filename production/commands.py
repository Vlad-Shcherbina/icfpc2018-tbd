from dataclasses import dataclass
from functools import update_wrapper
from typing import Tuple, ClassVar, Dict
import itertools

from production.basics import Diff

__all__ = ['parse_command', 'Halt', 'Wait', 'Flip', 'SMove', 'LMove', 'FusionP', 'FusionS', 'Fission', 'Fill']


def encode_sld(v : Diff):
    assert v.is_short_linear()
    if v.dx:
        return 0b01_0000 | (v.dx + 5)
    if v.dy:
        return 0b10_0000 | (v.dy + 5)
    if v.dz:
        return 0b11_0000 | (v.dz + 5)
    assert False, f'Invalid sld: {v}'


def encode_lld(v : Diff):
    assert v.is_long_linear()
    if v.dx:
        return 0b010_0000 | (v.dx + 15)
    if v.dy:
        return 0b100_0000 | (v.dy + 15)
    if v.dz:
        return 0b110_0000 | (v.dz + 15)
    assert False, f'Invalid lld: {v}'


def encode_lld(v : Diff):
    assert v.is_long_linear()
    if v.dx:
        return 0b010_0000 | (v.dx + 15)
    if v.dy:
        return 0b100_0000 | (v.dy + 15)
    if v.dz:
        return 0b110_0000 | (v.dz + 15)
    assert False, f'Invalid lld: {v}'


def encode_nd(v : Diff):
    assert v.is_near()
    return (v.dx + 1) * 9 + (v.dy + 1) * 3 + v.dz + 1


def generate_table(encoder):
    'A decorator that generates reverse-lookup tables from encode_xxx functions'
    return lambda generator: { encoder(it) : it for it in generator() }


@generate_table(encode_sld)
def sld_table():
    for i in range(1, 6):
        yield Diff( i,  0,  0)
        yield Diff(-i,  0,  0)
        yield Diff( 0,  i,  0)
        yield Diff( 0, -i,  0)
        yield Diff( 0,  0,  i)
        yield Diff( 0,  0, -i)
assert len(sld_table) == 30


@generate_table(encode_lld)
def lld_table():
    for i in range(1, 16):
        yield Diff( i,  0,  0)
        yield Diff(-i,  0,  0)
        yield Diff( 0,  i,  0)
        yield Diff( 0, -i,  0)
        yield Diff( 0,  0,  i)
        yield Diff( 0,  0, -i)
assert len(lld_table) == 90


@generate_table(encode_nd)
def nd_table():
    for xyz in itertools.product(* [[-1, 0, 1]] * 3):
        d = Diff(*xyz)
        if d.is_near():
            yield d
assert len(nd_table) == 18


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
    bid : ClassVar = 0b0100
    bsize : ClassVar = 2

    lld : Diff

    @classmethod
    def parse(cls, b, b2):
        return cls(lld_table[((b & 0b0011_0000) << 1) + (b2 & 0b11111)])


@command
class LMove:
    bid : ClassVar = 0b1100
    bsize : ClassVar = 2

    sld1 : Diff
    sld2 : Diff

    @classmethod
    def parse(cls, b, b2):
        return cls(
            sld_table[((b & 0b0011_0000)     ) + ((b2     ) & 0b1111)],
            sld_table[((b & 0b1100_0000) >> 2) + ((b2 >> 4) & 0b1111)])

@command
class Fission:
    bid : ClassVar = 0b101
    bsize : ClassVar = 2

    nd : Diff
    m : int

    @classmethod
    def parse(cls, b, b2):
        return cls(nd_table[b >> 3], b2)


@command
class Fill:
    bid : ClassVar = 0b011
    bsize : ClassVar = 1

    nd : Diff

    @classmethod
    def parse(cls, b):
        return cls(nd_table[b >> 3])


@command
class FusionP:
    bid : ClassVar = 0b111
    bsize : ClassVar = 1

    nd : Diff

    @classmethod
    def parse(cls, b):
        return cls(nd_table[b >> 3])


@command
class FusionS:
    bid : ClassVar = 0b110
    bsize : ClassVar = 1

    nd : Diff

    @classmethod
    def parse(cls, b):
        return cls(nd_table[b >> 3])


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
