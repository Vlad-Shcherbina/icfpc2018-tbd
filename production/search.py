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

def breadth_first_search(roots, valid_neighbors):
    # a FIFO open_set
    open_set = []
    
    # an empty set to maintain visited nodes
    closed_set = set()

    # an empty list to store the order in which nodes are visited
    traversal = []
    
    # initialize
    for root in roots:
        open_set.append(root)

    # For each node on the current level expand and process, if no children 
    # (leaf) then unwind
    while len(open_set) > 0:

        # get first item from queue
        subtree_root = open_set.pop(0)
    
        # For each child of the current tree process
        for child in valid_neighbors(subtree_root):
      
            # The node has already been processed, so skip over it
            if child in closed_set:
                continue
      
            # The child is not enqueued to be processed, so enqueue this level of
            # children to be expanded
            if child not in open_set:
                open_set.append(child)              # enqueue these nodes
    
        # We finished processing the root of this subtree, so add it to the closed 
        # set
        closed_set.add(subtree_root)
        traversal.append(subtree_root)

    return traversal
