from dataclasses import dataclass
from functools import update_wrapper
from typing import Tuple, ClassVar, Dict, Union
import itertools

from production.basics import Diff

__all__ = ['parse_command', 'parse_1command', 'parse_commands', 'compose_commands',
        'Halt', 'Wait', 'Flip', 'SMove', 'LMove', 'FusionP', 'FusionS', 'Fission', 'Fill',
        'Void', 'GFill', 'GVoid', 'Command']

__doc__ = '''
Python classes encapsulating commands, can be parsed and composed to and from binary representations.

The structure of this file is as follows:

- a bunch of helper functions

- commands, with their parse and compose methods

- low-level interface

- high-level interface
'''


#region Helper functions

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
    assert v.is_near(), v
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

#endregion

#region Commands

@command
class Halt:
    bid : ClassVar = 0b11111111
    bsize : ClassVar = 1

    @classmethod
    def parse(cls, b):
        return cls()

    def compose(self):
        return [self.bid]


@command
class Wait:
    bid : ClassVar = 0b11111110
    bsize : ClassVar = 1

    @classmethod
    def parse(cls, b):
        return cls()

    def compose(self):
        return [self.bid]


@command
class Flip:
    bid : ClassVar = 0b11111101
    bsize : ClassVar = 1

    @classmethod
    def parse(cls, b):
        return cls()

    def compose(self):
        return [self.bid]


@command
class SMove:
    bid : ClassVar = 0b0100
    bsize : ClassVar = 2

    lld : Diff

    @classmethod
    def parse(cls, b, b2):
        return cls(lld_table[((b & 0b0011_0000) << 1) + (b2 & 0b11111)])

    def compose(self):
        lld = encode_lld(self.lld)
        return [self.bid | ((lld & 0b0110_0000) >> 1), lld & 0b11111]


@command
class LMove:
    bid : ClassVar = 0b1100
    bsize : ClassVar = 2

    sld1 : Diff
    sld2 : Diff

    @classmethod
    def parse(cls, b, b2) -> 'LMove':
        return cls(
            sld_table[((b & 0b0011_0000)     ) + ((b2     ) & 0b1111)],
            sld_table[((b & 0b1100_0000) >> 2) + ((b2 >> 4) & 0b1111)])

    def compose(self):
        sld1 = encode_sld(self.sld1)
        sld2 = encode_sld(self.sld2)
        return [self.bid | (sld1 & 0b0011_0000) | ((sld2 & 0b0011_0000) << 2),
                (sld1 & 0b1111) | ((sld2 & 0b1111) << 4)]


@command
class Fission:
    bid : ClassVar = 0b101
    bsize : ClassVar = 2

    nd : Diff
    m : int

    @classmethod
    def parse(cls, b, b2):
        return cls(nd_table[b >> 3], b2)

    def compose(self):
        nd = encode_nd(self.nd)
        return [self.bid | nd << 3, self.m]


@command
class Fill:
    bid : ClassVar = 0b011
    bsize : ClassVar = 1

    nd : Diff

    @classmethod
    def parse(cls, b):
        return cls(nd_table[b >> 3])

    def compose(self):
        nd = encode_nd(self.nd)
        return [self.bid | nd << 3]


@command
class Void:
    bid : ClassVar = 0b010
    bsize : ClassVar = 1

    nd : Diff

    @classmethod
    def parse(cls, b):
        return cls(nd_table[b >> 3])

    def compose(self):
        nd = encode_nd(self.nd)
        return [self.bid | nd << 3]


@command
class FusionP:
    bid : ClassVar = 0b111
    bsize : ClassVar = 1

    nd : Diff

    @classmethod
    def parse(cls, b):
        return cls(nd_table[b >> 3])

    def compose(self):
        nd = encode_nd(self.nd)
        return [self.bid | nd << 3]


@command
class FusionS:
    bid : ClassVar = 0b110
    bsize : ClassVar = 1

    nd : Diff

    @classmethod
    def parse(cls, b):
        return cls(nd_table[b >> 3])

    def compose(self):
        nd = encode_nd(self.nd)
        return [self.bid | nd << 3]


@command
class GFill:
    bid : ClassVar = 0b001
    bsize : ClassVar = 4

    nd : Diff
    fd : Diff

    @classmethod
    def parse(cls, b, x, y, z):
        return cls(nd_table[b >> 3], Diff(x - 30, y - 30, z - 30))

    def compose(self):
        nd = encode_nd(self.nd)
        fd = self.fd
        return [self.bid | nd << 3, fd.dx + 30, fd.dy + 30, fd.dz + 30]


@command
class GVoid:
    bid : ClassVar = 0b000
    bsize : ClassVar = 4

    nd : Diff
    fd : Diff

    @classmethod
    def parse(cls, b, x, y, z):
        return cls(nd_table[b >> 3], Diff(x - 30, y - 30, z - 30))

    def compose(self):
        nd = encode_nd(self.nd)
        fd = self.fd
        return [self.bid | nd << 3, fd.dx + 30, fd.dy + 30, fd.dz + 30]


Command = Union[Halt, Wait, Flip, SMove, LMove, FusionP, FusionS, Fission, Fill,
        Void, GFill, GVoid]

#endregion

#region Low level interface

@dataclass
class ParserState:
    'Reimplementing the wheel because io sucks'
    buf: bytes
    source: str
    pos: int = 0

    def readbyte(self):
        if self.pos < len(self.buf):
            r = self.buf[self.pos]
            self.pos += 1
            return r


def parse_command(input: ParserState):
    pos = input.pos
    b = input.readbyte()
    if b is None:
        return None
    cmd = commands_by_id.get(b)
    if cmd is None:
        cmd = commands_by_id.get(b & 0b1111)
    if cmd is None:
        cmd = commands_by_id.get(b & 0b111)
    if cmd is None:
        raise ValueError(f'Unrecognized command byte 0b{b:08b} at {input.source!r}[{pos}]')
    if cmd.bsize == 2:
        b2 = input.readbyte()
        if b2 is None:
            raise ValueError(f'Unexpected EOF after 0b{b:08b} at {input.source!r}[{pos}]')
        try:
            return cmd.parse(b, b2)
        except Exception as exc:
            raise ValueError(f'Invalid data for command {cmd.__name__} 0b{b:08b} 0b{b2:08b} at {input.source!r}[{pos}]: {repr(exc)}') \
                    from exc
    else:
        try:
            return cmd.parse(b)
        except Exception as exc:
            raise ValueError(f'Invalid data for command {cmd.__name__} 0b{b:08b} at {input.source!r}[{pos}]: {repr(exc)}') \
                    from exc


def parse_1command(input):
    'Utility function that parses a single command from a bytes object'
    input = ParserState(bytes(input), 'parse_1command')
    return parse_command(input)

#endregion

#region High-level interface

def parse_commands(buf: bytes, source: str):
    'source is used for error reporting'
    input = ParserState(buf, source)
    res = []
    while True:
        cmd = parse_command(input)
        if cmd is None:
            return res
        res.append(cmd)


def compose_commands(commands, res: bytearray = None) -> bytearray:
    if res is None:
        res = bytearray()
    for cmd in commands:
        res.extend(cmd.compose())
    return res

#endregion
