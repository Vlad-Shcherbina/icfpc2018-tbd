import ast
import textwrap


def dump(node, *, include_attributes=False):
    elems = []
    def rec(node, indent):
        if isinstance(node, ast.AST):
            elems.append(f'<{node.__class__.__name__}>\n')
            if include_attributes:
                for a in node._attributes:
                    elems.append(indent)
                    elems.append(f'    (attr){a} = ')
                    rec(getattr(node, a), indent + '    ')
            for k, v in ast.iter_fields(node):
                elems.append(indent)
                elems.append(f'    {k} = ')
                rec(v, indent + '    ')
        elif isinstance(node, list):
            if node:
                elems.append('list:\n')
            else:
                elems.append('[]\n')
            for e in node:
                elems.append(indent)
                elems.append(f'    ')
                rec(e, indent + '    ')
        else:
            elems.append(f'{node!r}\n')

    rec(node, '')
    return ''.join(elems)


def main():
    a = ast.parse(textwrap.dedent('''\
    def f(n):
        x = y[None] = 2
        return 2 * n
    '''))
    print(dump(a, include_attributes=True))


if __name__ == '__main__':
    main()
