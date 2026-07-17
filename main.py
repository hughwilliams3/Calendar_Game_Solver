import gurobipy as gp
from gurobipy import GRB

from dataclasses import dataclass

import sys



@dataclass
class Graph:
    name: str
    verts: list[tuple[int, int]]

@dataclass
class Piece:
    name: str
    verts: list[tuple[int,int]]

    def rotate90(self):
        x_max = max(x[0] for x in self.verts)
        return tuple((y,-x + x_max) for x, y in self.verts)
    
    def rotate180(self):
        x_max = max(x[0] for x in self.verts)
        y_max = max(y[1] for y in self.verts)
        print(x_max,y_max)
        return tuple((-x+x_max,-y+y_max) for x, y in self.verts)
    
    def rotate270(self):
        y_max = max(y[1] for y in self.verts)
        return tuple((-y+y_max,x) for x, y in self.verts)
    


def main() -> int:
    X = Graph('X', [(x,y) for x in range(0,4) for y in range(0,4)])

    U = Piece('U', [(0,0),(1,0),(2,0),(2,1),(0,1)])
    L = Piece('L',[(0,0),(1,0),(2,0),(0,1),(0,2)])
    t = Piece('t', [(0,0),(0,1),(0,2),(0,3),(1,1)])

    m = gp.Model

    


if __name__ == "__main__":
    sys.exit(main())