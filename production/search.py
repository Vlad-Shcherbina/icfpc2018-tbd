from typing import TypeVar, Generic, List, Callable, Iterable, Set

T = TypeVar('T')


def breadth_first_search(graph: Set[T], valid_neighbors: Callable[[T], Iterable[T]]) -> List[T]:
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
