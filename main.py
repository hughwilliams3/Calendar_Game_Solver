import gurobipy as gp
from gurobipy import GRB

from dataclasses import dataclass

import sys



class Graph:
    def __init__(self,name,verts):
        self.name = name
        self.verts = gp.tuplelist(verts)


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
        self.orientations_set = self.get_orientations_set()
        self.full_pcs_set = self.get_ornts_and_anchors()
    
    def get_orientations_set(self):
        orientations_set = {}
        for piece_name in self.pieces:
            for ornt in self.pieces[piece_name].orientations:
                orientations_set[piece_name, ornt] = self.pieces[piece_name].orientations[ornt]
                print(f"{piece_name}, {ornt}, {self.pieces[piece_name].orientations[ornt]}")
        print(orientations_set)
        return orientations_set
        

    def get_ornts_and_anchors(self):
        self.full_pcs_set = {}

    def add_variables(self):
        self.x = {}
        for piece_name, piece in self.pieces.items():
           # print(f"\nPiece: {piece_name}")
           # print(piece.orientations.keys())

            for orientation in piece.orientations:
                #print(f"Creating orientation: {orientation}")

                count = 0
                for anchor in self.graph.verts:
                    self.x[piece_name, orientation, anchor] = self.model.addVar(
                        vtype=GRB.BINARY,
                        name=f"{piece_name}, {orientation}, {anchor}"
                    )
                    count += 1

               # print(f"  Created {count} variables")
                    
    def add_constraints(self):
        # each piece is used exactly once
        for pc in self.pieces:
            self.model.addConstr(
                gp.quicksum(self.x[pc,j,k] 
                    for j in self.pieces[pc].orientations
                    for k in self.graph.verts) == 1)
        
        # no points are shared

    def set_objective(self):
        self.model.setObjective(gp.quicksum(self.x[i,j,k] for i in self.pieces.keys() for j in self.pieces[i].orientations for k in self.graph.verts))
        self.model.ModelSense = GRB.MINIMIZE

    def solve_model(self):
        self.model.optimize()
       # if self.model.Status == GRB.OPTIMAL:
           # print(f"Optimal objective: {self.model.ObjVal}")
            #for v in self.model.getVars():
                #print(f"{v.VarName} = {v.X}")

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
    x_verts = m.x['U','parent',(0,0)]
    print(x_verts)

    m.solve_model()

    print(x_verts)
    #### Variables ####

    # anchor points (each)


    


if __name__ == "__main__":
    sys.exit(main())