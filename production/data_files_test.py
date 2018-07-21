from production.data_files import *
from production.model import Model
from production.commands import parse_commands


def test_full():
    assert 'FR042' in full_names()

    src_model, tgt_model = full_problem('FA001')
    assert src_model is None
    Model.parse(tgt_model)

    src_model, tgt_model = full_problem('FD001')
    Model.parse(src_model)
    assert tgt_model is None

    src_model, tgt_model = full_problem('FR001')
    Model.parse(src_model)
    Model.parse(tgt_model)

    trace = full_default_trace('FR001')
    parse_commands(trace, source='FR001.nbt')
