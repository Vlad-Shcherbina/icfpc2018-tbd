from production.model import Model
from production.basics import Pos

def bounding_box(model) -> (Pos, Pos):
    filled_cell_visited = False
    for x in range(model.R):
        for y in range(model.R):
            for z in range(model.R):
                if model[Pos(x,y,z)]:
                    if not filled_cell_visited:
                        pos0 = Pos(x,y,z)
                        pos1 = Pos(x,y,z)
                        filled_cell_visited = True
                    else:
                        pos0 = Pos(min(pos0.x,x),min(pos0.y,y),min(pos0.z,z))
                        pos1 = Pos(max(pos1.x,x),max(pos1.y,y),max(pos1.z,z))

    assert filled_cell_visited
    return (pos0,pos1)
