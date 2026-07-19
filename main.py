import gurobipy as gp
from gurobipy import GRB

from dataclasses import dataclass

import sys



class Graph:
    def __init__(self,name,verts):
        self.name = name
        self.verts = verts


class Piece:
    def __init__(self,name,parent,verts):
        self.name=name
        self.parent =  parent
        self.verts = verts
        self.mirrored = self.mirror_y()
        self.orientations = self.get_orientations()

    def rotate90(self,verts):
        x_max = max(x for x, y in verts)
        return set((y,-x + x_max) for x, y in verts)
    
    def rotate180(self,verts):
        x_max = max(x for x, y in verts)
        y_max = max(y for x, y in verts)
        return set((-x+x_max,-y+y_max) for x, y in verts)
    
    def rotate270(self,verts):
        y_max = max(y for x, y in verts)
        return set((-y+y_max,x) for x, y in verts)
    
    def mirror_y(self):
        x_max = max(x for x, y in self.verts)
        verts_new = set((-x+x_max,y) for x, y in self.verts)
        return verts_new
    
    def get_orientations(self):
        orientations = {}
        orientations['parent'] = self.verts
        orientations['90'] = self.rotate90(self.verts)
        if self.rotate180(self.verts) == self.verts:
            return orientations
        else:
            orientations['180'] = self.rotate180(self.verts)
            orientations['270'] = self.rotate270(self.verts)
            if self.mirror_y() in orientations.values():
                return orientations
            else:
                orientations['m'] = self.mirrored
                orientations['m_90'] = self.rotate90(orientations['m'])
                orientations['m_180'] = self.rotate180(self.mirrored)
                orientations['m_270'] = self.rotate270(self.mirrored)
                return orientations


    

class CalendarGameModel:
    def __init__(self,graph,pieces):
        self.graph=graph
        self.pieces=pieces
        self.model=gp.Model()

    def add_variables(self):
        for pc in self.pieces:
            self.x = self.model.addVars(
                self.pieces.keys(), # parent piece i
                range(len(self.pieces[pc].orientations)), # orientation j #there are 8 possible orientations... could change the orientations thing to make it zero if isn't unique? or just a constraint that says only one of each parent is used, and all the orientations exist
                self.graph.verts,# anchored on vertex (k,l)
                vtype=GRB.BINARY 
            )

    def add_constraints(self):
        for pc in self.pieces:
            self.model.addConstr(gp.quicksum(self.x[i,j,k] for i in self.pieces.keys() for j in range(len(self.pieces[pc].orientations)) for k in self.graph.verts) == 3)

    def solve_model(self):
        self.model.optimize()
        if self.model.Status == GRB.OPTIMAL:
            print(f"Optimal objective: {self.model.ObjVal}")
            for v in self.model.getVars():
                print(f"{v.VarName} = {v.X}")

def main() -> int:
    V = Graph('X', ((x,y) for x in range(0,4) for y in range(0,4)))

    pieces = {
    "U" : Piece('U', 'U', {(0,0),(1,0),(2,0),(2,1),(0,1)}),
    "L" : Piece('L', 'L', {(0,0),(1,0),(2,0),(0,1),(0,2)}),
    "t" : Piece('t', 't', {(0,0),(0,1),(0,2),(0,3),(1,1)})
    }


    m = CalendarGameModel(V,pieces)
    m.add_variables()
    m.add_constraints()
    m.solve_model()

    #### Variables ####

    # anchor points (each)


    


if __name__ == "__main__":
    sys.exit(main())