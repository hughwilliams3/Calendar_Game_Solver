import gurobipy as gp
from gurobipy import GRB

from dataclasses import dataclass

import sys



@dataclass
class Graph:
    name: str
    verts: set[int, int]

@dataclass
class Piece:
    name: str
    parent: str
    verts: set[tuple[int,int]]

    def __post_init__(self):
        self.verts = set(self.verts)
        self.mirrored = self.mirror_y()

    def rotate90(self):
        x_max = max(x[0] for x in self.verts)
        return set((y,-x + x_max) for x, y in self.verts)
    
    def rotate180(self):
        x_max = max(x[0] for x in self.verts)
        y_max = max(y[1] for y in self.verts)
        return set((-x+x_max,-y+y_max) for x, y in self.verts)
    
    def rotate270(self):
        y_max = max(y[1] for y in self.verts)
        return set((-y+y_max,x) for x, y in self.verts)
    
    def mirror_y(self):
        x_max = max(x[0] for x in self.verts)
        return set((-x+x_max,y) for x, y in self.verts)
    


    


def main() -> int:
    V = Graph('X', ((x,y) for x in range(0,4) for y in range(0,4)))

    pieces = {
    "U" : Piece('U', 'U', {(0,0),(1,0),(2,0),(2,1),(0,1)}),
    "L" : Piece('L', 'L', {(0,0),(1,0),(2,0),(0,1),(0,2)}),
    "t" : Piece('t', 't', {(0,0),(0,1),(0,2),(0,3),(1,1)})
    }

    # dictionary of all unique orientations of a shape, saved as instances of Piece class
    orientations = {}
    for i in pieces:
        unmirrored = []
        orientations[f"{i}"] = Piece(f"{i}",i, pieces[i].verts)
        orientations[f"{i}+90"] = Piece(f"{i}+90",i,pieces[i].rotate90())
        if pieces[i].rotate180() == i: # if the 180 degree rotation is the same as the original, then there are only two orientations and we can stop
            continue
        else:
            orientations[f"{i}+180"] = Piece(f"{i}+180",i,pieces[i].rotate180())
            orientations[f"{i}+270"] = Piece(f"{i}+270",i,pieces[i].rotate270())
            unmirrored.append([
                orientations[f"{i}"],
                orientations[f"{i}+90"],
                orientations[f"{i}+180"],
                orientations[f"{i}+270"]
                ])
        if any(pieces[i].mirrored == orientations[j].verts for j in orientations): # if the mirrored version is contained in any of the original 4 rotations, we can stop
            continue
        else:
            orientations[f"{i}_mir"] = Piece(f"{i}_mir",i,pieces[i].mirror_y())
            orientations[f"{i}_mir+90"] = Piece(f"{i}_mir+90", i,orientations[f"{i}_mir"].rotate90())
            orientations[f"{i}_mir+180"] = Piece(f"{i}_mir+180", i,orientations[f"{i}_mir"].rotate180())
            orientations[f"{i}_mir+270"] = Piece(f"{i}_mir+270", i,orientations[f"{i}_mir"].rotate270())

    print(orientations)
    for i in orientations:
        if orientations[i].parent == 't':
            print(orientations[i].verts)
 

    m = gp.Model()

    #### Variables ####

    # anchor points (each)

    x = m.addVars(
        pieces.keys(),
        orientations,
        V.verts,
        vtype=GRB.BINARY,
        name='anchor_point'
    )
    


if __name__ == "__main__":
    sys.exit(main())