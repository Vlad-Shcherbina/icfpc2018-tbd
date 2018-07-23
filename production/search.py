from typing import TypeVar, Generic, List, Callable, Iterable, Set
from itertools import chain

T = TypeVar('T')


def depth_first_search(graph: Iterable[T], valid_neighbors: Callable[[T], Iterable[T]]) -> List[T]:
    visited = set()
    order = []
    
    def visit(vertex):
        if vertex in visited:
            return
        visited.add(pos)
        order.append(pos)
        for v in valid_neighbors(vertex):
            visit(v)

    for vertex in graph:
        visit(vertex)

    return order



def breadth_first_search(graph: Iterable[T], valid_neighbors: Callable[[T], Iterable[T]]) -> List[T]:
    g = iter(graph)
    try:
        first = g.__next__()
    except StopIteration:
        return graph

    return chain(
        iter([first]),
        breadth_first_search(
            chain(
                g,
                valid_neighbors(first)),
            valid_neighbors))
