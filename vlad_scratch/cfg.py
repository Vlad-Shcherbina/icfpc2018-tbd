from typing import List
import textwrap


class Node:
    text: str
    exits: List['Node']

    def __init__(self, text, exits=None):
        self.text = text
        if exits is None:
            exits = []
        self.exits = exits

    def __repr__(self):
        return f'Node({self.text!r}, {len(self.exits)} exits)'


# Often represents a natural linearization of the control flows.
# https://en.wikipedia.org/wiki/Depth-first_search#Vertex_orderings
def reverse_postorder(node):
    visited = set()
    result = []
    def rec(node):
        if node in visited:
            return
        visited.add(node)
        for n in reversed(node.exits):
            rec(n)
        result.append(node)
    rec(node)
    result.reverse()
    return result


def generate_code(nodes: List[Node]):
    # TODO: remove nops

    jump_targets = {e for n in nodes for e in n.exits[1:]}
    for node, next_node in zip(nodes, nodes[1:] + [None]):
        if node.exits and node.exits[0] != next_node:
            jump_targets.add(node.exits[0])

    labels = {}
    for node in nodes:
        if node in jump_targets:
            labels[node] = f'label_{len(labels)}'

    for node, next_node in zip(nodes, nodes[1:] + [None]):
        if node in labels:
            print(labels[node] + ':')
        assert len(node.exits) <= 2
        if len(node.exits) == 2:
            assert '<addr>' in node.text, node
            print(textwrap.indent(node.text.replace("<addr>", labels[node.exits[1]]), '    '))
        else:
            print(textwrap.indent(node.text, '    '))
        if node.exits and node.exits[0] != next_node:
            print(f'    jmp {labels[node.exits[0]]}')


def main():
    d = Node('d')
    b = Node('b', [d])
    c = Node('c', [d])
    a = Node('cmp a, 42\njnz <addr>', [b, c])
    print(reverse_postorder(a))
    generate_code(reverse_postorder(a))


if __name__ == '__main__':
    main()
