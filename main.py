import gurobipy as gp
from gurobipy import GRB
import streamlit as st
import ast

import sys



class Graph:
    def __init__(self,name,omit,verts):
        self.name = name
        self.verts = gp.tuplelist(verts - omit)
        self.omit = gp.tuplelist(omit)


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
                self.full_pcs_set[ornt[0],ornt[1],anch] = set((x+anch[0],y+anch[1]) for x,y in self.orientations_set[ornt])
                #print(ornt, anch, self.full_pcs_set[ornt,anch])
        #print(self.full_pcs_set)
        return self.full_pcs_set

    def add_variables(self):
        self.x = {} # main decision variable, for whether a specific piece is used and in which orientation per anchor point
        for piece in self.full_pcs_set:
            #print(f"\nPiece: {piece}")
           # print(piece.orientations.keys())
            self.x[piece] = self.model.addVar(
                vtype=GRB.BINARY,
                name=f"{piece}"
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


        # each piece is used exactly of once
        #print(self.full_pcs_set)
        for parent in self.pieces:
            self.model.addConstr(
                gp.quicksum(
                    self.x[parent, ornt, anch]
                    for ornt in self.pieces[parent].orientations
                    for anch in self.graph.verts
                ) == 1,
                name=f"parent_used_once_{parent}"
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
                    self.x[pc] == 0,
                    name="pieces_in_gameboard"
                )

        # pieces cannot overlap
        #disjoint_sets = 0
        #overlapping_sets = 0
        #print(self.full_pcs_set)
        items = list(self.full_pcs_set.items())
        for i in range(len(items)):
            pc1, pc1verts = items[i]
            for j in range(i+1, len(items)):
                pc2, pc2verts = items[j]
                if not pc1verts.isdisjoint(pc2verts):
                    self.model.addConstr(
                        self.x[pc1] + self.x[pc2] <= 1,
                        name="dont_overlap"
                    )
        #print(f"disjoint sets: {disjoint_sets}")
        #print(f"overlapping sets: {overlapping_sets}")
        self.model.update()
        

        # no points are shared
        for pt in self.graph.verts:
            self.model.addConstr(
                gp.quicksum(self.v[i,pt] for i in self.full_pcs_set) <=1,
                name="points_covered_once"
            )
        self.model.update()

        for p, pverts in self.full_pcs_set.items():
            for vrt in self.graph.verts:
                # vert v can only be covered by a piece if that piece contains that point
                if vrt in pverts:
                    self.model.addConstr(self.v[p,vrt] == self.x[p], name="v_equals_x_when_covering")
                else:
                    self.model.addConstr(self.v[p,vrt] == 0, name="vert_not_in_piece")
                # if a piece is used, all of its vertices are covered
                #print(self.x[p])
                    
                    

        self.model.update()


    def set_objective(self):
        self.model.setObjective(gp.quicksum(self.v[pc,pt] for pc in self.full_pcs_set for pt in self.graph.verts))
        self.model.ModelSense = GRB.MAXIMIZE

    def solve_model(self):
        self.model.optimize()

        target = ('hook', 'm_180', (2, 2))
        matches = [k for k in self.full_pcs_set if k == target]
        print("exact match found:", matches)

        close = [k for k in self.full_pcs_set if k[0]=='hook' and k[2]==(2,2)]
        print("close matches (any ornt string):", [repr(k) for k in close])

        #print(self.full_pcs_set)
        #print(self.full_pcs_set[('hook', 'm_180', (2, 2))])
        if self.model.Status == GRB.OPTIMAL:
            print(f"Optimal objective: {self.model.ObjVal}")
            #st.write(f"Optimal objective: {self.model.ObjVal}")
            for key,var in self.x.items():
                if var.X == 1:
                    name = ast.literal_eval(var.VarName)
                    st.session_state.soln[name[0]] = self.full_pcs_set[key]
                    print(f"{var.VarName} = {var.X}")
                    #st.write(f"{var.VarName} = {var.X}")
                    print(f"{self.full_pcs_set[key]}")
                    #st.write(f"{self.full_pcs_set[key]}")
                    print("\n")





def main() -> int:
    # This is the game board.
    V = Graph('X', {(0,5),(4,2)}, {
                (0,6),(1,6),(2,6),(3,6),(4,6),(5,6),
                (0,5),(1,5),(2,5),(3,5),(4,5),(5,5),
                (0,4),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),
                (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),
                (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
                (0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),
                (0,0),(1,0),(2,0)
                    }
                )
    

    pieces = {
    "U" : Piece('U', 'U', {(0,0),(1,0),(2,0),(2,1),(0,1)}),
    "L" : Piece('L', 'L', {(0,0),(1,0),(2,0),(0,1),(0,2)}),
    "t" : Piece('t', 't', {(0,0),(0,1),(0,2),(0,3),(1,1)}),
    "zig": Piece('zig', 'zig', {(0,0),(1,0),(1,1),(1,2),(2,2)}),
    "zag": Piece('zag', 'zag', {(0,0),(1,0),(2,0),(2,1),(3,1)}),
    "rect": Piece('rect', 'rect', {(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)}),
    "goto": Piece('goto','goto', {(0,0),(1,0),(2,0),(1,1),(0,1)}),
    "hook": Piece('hook','hook', {(0,0),(0,1),(0,2),(0,3),(1,3)})
    }

    piece_colors = {
    "U" : "#BBFFAD",
    "L" : "#ADFFE8",
    "t" : "#ADC7FF",
    "zig": "#CCADFF",
    "zag": "#FFADFF",
    "rect": "#FFADAD",
    "goto": "#FFDEAD",
    "hook": "#FFF3AD"
    }



    
    #m.add_variables()
    #m.add_constraints()


    #m.solve_model()

    ### streamlit app test zone 
    # ---------------------------------------------------------------------------
    # Streamlit app
    # ---------------------------------------------------------------------------
    
    st.set_page_config(page_title="Calendar Puzzle Solver", layout="centered")
    st.title("Calendar Puzzle Solver")
    
    board_width = 7
    board_height = 7

    valid_verts = {"Jan": (0,6),"Feb": (1,6), "Mar": (2,6),"Apr": (3,6),"May": (4,6),"Jun": (5,6),
                "Jul": (0,5),"Aug": (1,5),"Sep": (2,5),"Oct": (3,5),"Nov": (4,5),"Dec": (5,5),
                1: (0,4),2: (1,4),3: (2,4),4: (3,4),5: (4,4),6: (5,4),7: (6,4),
                8: (0,3),9: (1,3),10: (2,3),11: (3,3),12: (4,3),13: (5,3),14: (6,3),
                15: (0,2),16: (1,2),17: (2,2),18: (3,2),19: (4,2),20: (5,2),21: (6,2),
                22: (0,1),23: (1,1),24: (2,1),25: (3,1),26: (4,1),27: (5,1),28: (6,1),
                29: (0,0),30: (1,0),31: (2,0)}
    
    coord_to_name = {coord: name for name, coord in valid_verts.items()}

    if "omitted_vars" not in st.session_state:
        st.session_state.omitted_vars = set()

    if "solve_date" not in st.session_state:
        st.session_state.solve_date = set()

    if "soln" not in st.session_state:
        st.session_state.soln = dict()

    ### Generate game board

    for y in reversed(range(board_height)):
        cols = st.columns(board_width)

        for x in range(board_width):
            with cols[x]:
                if (x, y) in coord_to_name:
                    name = coord_to_name[(x, y)]
                    if st.button(str(name), key=(x, y), use_container_width=True):
                        st.session_state.solve_date.add(name)
                        st.session_state.omitted_vars.add((x, y))

    st.write(f"Solve for {st.session_state.solve_date}")

    ### solve button
    game_board = Graph('X', st.session_state.omitted_vars, {
                (0,6),(1,6),(2,6),(3,6),(4,6),(5,6),
                (0,5),(1,5),(2,5),(3,5),(4,5),(5,5),
                (0,4),(1,4),(2,4),(3,4),(4,4),(5,4),(6,4),
                (0,3),(1,3),(2,3),(3,3),(4,3),(5,3),(6,3),
                (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),
                (0,1),(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),
                (0,0),(1,0),(2,0)
                    }
                )

    if st.button("Solve", key = 'solve'):
        m = CalendarGameModel(game_board,pieces)        
        m.add_variables()
        m.add_constraints()

        m.set_objective()
        m.solve_model()

        #st.write("Solution:")
        #st.write(st.session_state.soln)

        st.session_state.omitted_vars = set()

    
    ### Color the game board
    assigned = {}

    for pt in game_board.verts:
        for key, verts in st.session_state.soln.items():
            if pt in verts:
                assigned[pt] = key

    print(assigned)


    for y in reversed(range(board_height)):
        cols = st.columns(board_width)

        for x in range(board_width):
            with cols[x]:
                if (x,y) in coord_to_name:
                    piece = assigned.get((x,y))

                    if piece:
                        color = piece_colors[piece]
                    else:
                        color = "#DDDDDD"

                    #st.write((x, y), piece, color)
                    st.markdown(
                        f"""
                        <div style="
                            background-color:{color};
                            color:black;
                            width:50px;
                            height:50px;
                            border-radius:10px;
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            ">
                            {coord_to_name[(x,y)]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    


if __name__ == "__main__":
    sys.exit(main())