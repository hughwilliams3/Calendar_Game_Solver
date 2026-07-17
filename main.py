import gurobipy as gp
from gurobipy import GRB

from dataclasses import dataclass

import sys



@dataclass
class Graph:
    name: str
    verts: tuple[int, int]

@dataclass
class Piece:
    name: str
    verts: tuple[tuple[int,int]]

    def rotate90(self):
        x_max = max(x[0] for x in self.verts)
        return tuple((y,-x + x_max) for x, y in self.verts)
    
    def rotate180(self):
        x_max = max(x[0] for x in self.verts)
        y_max = max(y[1] for y in self.verts)
        return tuple((-x+x_max,-y+y_max) for x, y in self.verts)
    
    def rotate270(self):
        y_max = max(y[1] for y in self.verts)
        return tuple((-y+y_max,x) for x, y in self.verts)
    


def main() -> int:
    V = Graph('X', ((x,y) for x in range(0,4) for y in range(0,4)))

    pieces = {
    "U" : Piece('U', ((0,0),(1,0),(2,0),(2,1),(0,1))),
    "L" : Piece('L',((0,0),(1,0),(2,0),(0,1),(0,2))),
    "t" : Piece('t', ((0,0),(0,1),(0,2),(0,3),(1,1)))
    }

    orientations = {}
    for i in pieces:
        orientations[f"{i}"] = pieces[i].verts
        orientations[f"{i}+90"] = pieces[i].rotate90()
        if pieces[i].rotate180() == i:
            continue
        else:
            orientations[f"{i}+180"] = pieces[i].rotate180()
            orientations[f"{i}+270"] = pieces[i].rotate270()


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
    print(x['U','U+90',1,1])
    # 
    


if __name__ == "__main__":
    sys.exit(main())