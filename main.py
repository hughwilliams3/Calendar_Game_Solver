import gurobipy as gp
from gurobipy import GRB

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
        self.orientations_set = {}
        for piece_name in self.pieces:
            for ornt in self.pieces[piece_name].orientations:
                self.orientations_set[piece_name, ornt] = self.pieces[piece_name].orientations[ornt]
                #print(f"{piece_name}, {ornt}, {self.pieces[piece_name].orientations[ornt]}")
        return self.orientations_set
        

    def get_ornts_and_anchors(self):
        self.full_pcs_set = {}
        for anch in self.graph.verts:
            for ornt in self.orientations_set.keys():
                self.full_pcs_set[ornt,anch] = set((x+anch[0],y+anch[1]) for x,y in self.orientations_set[ornt])
                #print(ornt, anch, self.full_pcs_set[ornt,anch])
        #print(self.full_pcs_set)
        return self.full_pcs_set

    def add_variables(self):
        self.x = {} # main decision variable, for whether a specific piece is used and in which orientation per anchor point
        for piece_name in self.full_pcs_set:
           # print(f"\nPiece: {piece_name}")
           # print(piece.orientations.keys())
            self.x[piece_name] = self.model.addVar(
                vtype=GRB.BINARY,
                name=f"{piece_name}"
            )

        #print(f"self.x: \n {self.x}")    

               # print(f"  Created {count} variables")
        #print(self.x)
        self.v = {} #1 if pc i covers pt j, 0 if not
        for pc in self.full_pcs_set:
            for pt in self.graph.verts:
                self.v[pc,pt] = self.model.addVar(
                    vtype=GRB.BINARY,
                    name=f"{pc},{pt}"
                )

        
    def add_constraints(self):
        # indicator constraint


        # each piece is used maximum of once
        #print(self.full_pcs_set)
        for parent in self.pieces:
            self.model.addConstr(
                gp.quicksum(self.x[(parent,ornt),anch] 
                    for ornt in self.pieces[parent].orientations
                    for anch in self.graph.verts) <= 1
                    )
            #print(self.x)
        
        self.model.update()

        # pieces must be in the gameboard
        for pc,pcverts in self.full_pcs_set.items():
            #print(pcverts)
            if pcverts.issubset(self.graph.verts):
                continue
            else:
                self.model.addConstr(
                    self.x[pc] == 0
                )

        # pieces cannot overlap
        #disjoint_sets = 0
        #overlapping_sets = 0
        #print(self.full_pcs_set)
        for pc1,pc1verts in self.full_pcs_set.items():
            for pc2,pc2verts in self.full_pcs_set.items():
                if pc1verts.isdisjoint(pc2verts):
                    #print(f"{pc1verts} disjoint {pc2verts}")
                    self.model.addConstr(
                        self.x[pc1] + self.x[pc2] == 0
                    )
                    continue
                    #disjoint_sets += 1
                else:
                    
                    #print(self.x[pc1])
                    #print("self.x[pc1]^")
                    self.model.addConstr(
                        self.x[pc1] + self.x[pc2] <= 1
                    )
                    #overlapping_sets += 1
                    #print(f"not disjoint: {pc1verts,pc2verts}")
                    continue
        #print(f"disjoint sets: {disjoint_sets}")
        #print(f"overlapping sets: {overlapping_sets}")
        self.model.update()
        

        # no points are shared
        for pt in self.graph.verts:
            self.model.addConstr(
                gp.quicksum(self.v[i,pt] for i in self.full_pcs_set) ==1
            )
        self.model.update()

        for p, pverts in self.full_pcs_set.items():
            for vrt in self.graph.verts:
                # vert v can only be covered by a piece if that piece contains that point
                if vrt in pverts: 
                    print(f"{vrt} in {pverts}")
                    self.model.addConstr(self.v[p,vrt] <= 1)
                    self.model.addConstr(self.v[p,vrt] >= self.x[p])
                else:
                    print(f"{vrt} not in {pverts}")
                    self.model.addConstr(self.v[p,vrt] == 0)
                # if a piece is used, all of its vertices are covered
                print(self.x[p])
        self.model.update()




    def set_objective(self):
        self.model.setObjective(gp.quicksum(self.v[pc,pt] for pc in self.full_pcs_set for pt in self.graph.verts))
        self.model.ModelSense = GRB.MAXIMIZE

    def solve_model(self):
        self.model.optimize()
        if self.model.Status == GRB.OPTIMAL:
            print(f"Optimal objective: {self.model.ObjVal}")
            for v in self.model.getVars():
                if v.X == 1:
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