from typing import Tuple, Optional

from production.model import Model
from production.basics import Pos

def bounding_box(model) -> Tuple[Pos, Pos]:
    return bounding_box_region(model)

def bounding_box_region(model, fx : Optional[int] = None, fy : Optional[int] = None, fz : Optional[int] = None) -> Tuple[Pos, Pos]:
    def rangify(R, fv = None):
        if fv is None:
            fv = range(R)
        else:
            fv = [fv]
        return fv
    fx = rangify(model.R, fx)
    fy = rangify(model.R, fy)
    fz = rangify(model.R, fz)

    filled_cell_visited = False
    for x in fx:
        for y in fy:
            for z in fz:
                if model[Pos(x,y,z)]:
                    if not filled_cell_visited:
                        pos0 = pos1 = Pos(x,y,z)
                        filled_cell_visited = True
                    else:
                        pos0 = Pos(min(pos0.x,x),min(pos0.y,y),min(pos0.z,z))
                        pos1 = Pos(max(pos1.x,x),max(pos1.y,y),max(pos1.z,z))

    assert filled_cell_visited
    return (pos0,pos1)

def is_inside_region(pt : Pos, pt0 : Pos, pt1 : Pos) -> bool:
    return pt0.x <= pt.x <= pt1.x and pt0.y <= pt.y <= pt1.y and pt0.z <= pt.z <= pt1.z
