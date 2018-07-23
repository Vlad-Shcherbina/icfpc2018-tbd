from production.basics import Pos

def floor(model):
    for x in range(model.R):
        for z in range(model.R):
            yield Pos(x, 0, z)


def floor_contact(model):
    for voxel in floor(model):
        if model.is_filled(voxel):
            yield voxel
            
def filled_neighbors(model):
    def filled_neighbors_of_voxel(voxel):
        for neighbor in voxel.enum_adjacent(model.R):
            if model.is_filled(neighbor):
                yield neighbor
    return filled_neighbors_of_voxel

             
def empty_neighbors(model, voxel):
    for neighbor in voxel.enum_adjacent(model.R):
         if model.is_empty(neighbor):
             yield neighbor
    
