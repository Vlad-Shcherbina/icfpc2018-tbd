'''
A simple compiler from a subset of Python to a stack machine.
'''

from importlib.util import find_spec
if __name__ == '__main__' and find_spec('hintcheck'):
    import hintcheck
    hintcheck.monkey_patch_named_tuple_constructors()

import ast
import textwrap
from typing import List
from dataclasses import dataclass

from vlad_scratch import cfg
from vlad_scratch import ast_utils


@dataclass
class Ctx:
    return_node: cfg.Node


def compile_function(f: ast.FunctionDef):
    return_node = cfg.Node('return')
    exit_node = cfg.Node('push None', [return_node])
    ctx = Ctx(return_node=return_node)

    return compile_statements(f.body, exit_node, ctx)


def compile_statements(stmts, exit_node, ctx):
    node = exit_node
    for stmt in reversed(stmts):
        node = compile_statement(stmt, node, ctx)
    return node


def compile_statement(stmt, exit_node, ctx):
    if isinstance(stmt, ast.Return):
        assert stmt.value is not None
        return compile_expr(stmt.value, ctx.return_node, ctx)
    if isinstance(stmt, ast.Assign):
        [target] = stmt.targets
        assert isinstance(target, ast.Name)
        node = cfg.Node(f'store {target.id!r}', [exit_node])
        return compile_expr(stmt.value, node, ctx)
    if isinstance(stmt, ast.While):
        loopback = cfg.Node('nop')
        body = compile_statements(stmt.body, loopback, ctx)
        node = compile_cond(stmt.test, true_exit=body, false_exit=exit_node, ctx=ctx)
        loopback.exits = [node]
        return node
    else:
        assert False, stmt


def compile_expr(expr, exit_node, ctx):
    if isinstance(expr, ast.Num):
        return cfg.Node(f'push {expr.n}', [exit_node])
    elif isinstance(expr, ast.Name):
        return cfg.Node(f'load {expr.id!r}', [exit_node])
    elif isinstance(expr, ast.BinOp):
        if isinstance(expr.op, ast.Add):
            node = cfg.Node('add', [exit_node])
        elif isinstance(expr.op, ast.Mult):
            node = cfg.Node('mul', [exit_node])
        else:
            assert False, expr.op
        node = compile_expr(expr.right, node, ctx)
        node = compile_expr(expr.left, node, ctx)
        return node
    else:
        assert False, expr


def compile_cond(expr, true_exit, false_exit, ctx):
    if isinstance(expr, ast.Compare):
        [op] = expr.ops
        [right] = expr.comparators
        if isinstance(op, ast.Lt):
            node = cfg.Node('if lt jump <addr>', [false_exit, true_exit])
        if isinstance(op, ast.GtE):
            node = cfg.Node('if gte jump <addr>', [false_exit, true_exit])
        else:
            assert False, op
        node = compile_expr(right, node, ctx)
        node = compile_expr(expr.left, node, ctx)
        return node
    if isinstance(expr, ast.UnaryOp):
        if isinstance(expr.op, ast.Not):
            return compile_cond(expr.operand, false_exit, true_exit, ctx)
        else:
            assert False, expr.op
    else:
        assert False, expr


def main():
    tree = ast.parse(textwrap.dedent('''\
    def factorial(n):
        result = 1
        i = 1
        while not i >= n:
            i = i + 1
            result = result * i
        return result
    '''))

    assert isinstance(tree, ast.Module)

    for f in tree.body:
        print(ast_utils.dump(f))
        graph = compile_function(f)
        print(f'Compiled {f.name}:')
        cfg.generate_code(cfg.reverse_postorder(graph))


if __name__ == '__main__':
    if 'hintcheck' in globals():
        hintcheck.hintcheck_all_functions()
    main()
