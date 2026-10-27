"""Separate, navigable building floors with stairs, rooms and persistent doors."""
from .campus import LANDMARKS, FLOOR_COUNTS
from .config import TILE
from .world import Layout, Door, Furniture, AnnealingStats
from .informatika import upper as build_informatika


class BuildingLayout(Layout):
    interior=True
    campus=False
    width,height=32,24

    def __init__(self,building,floor):
        if building not in FLOOR_COUNTS or not 1<=floor<FLOOR_COUNTS[building]:
            raise ValueError("Unknown floor")
        self.building,self.floor=building,floor
        self.rooftop=building==5 and floor==3
        self.seed=100000+building*10+floor
        self.room_names=[name for name,_,_,_ in LANDMARKS]
        label="Atap pemancar" if self.rooftop else f"Lantai {floor+1}"
        self.room_names[building]+= " · "+label.upper()
        self.outdoors={building} if self.rooftop else set()
        self.room_kinds=[kind for _,kind,_,_ in LANDMARKS]
        self.grid=[[1 if x in (0,31) or y in (0,23) else 0 for x in range(32)] for y in range(24)]
        self.doors={};self.glass=set();self.furniture=[];self.revision=0;self.sight_cells=set()
        if building==11:
            build_informatika(self,floor)
            errors=self.validate()
            if errors:raise ValueError(errors)
            return
        self.down=self.center((5,19));self.up=self.center((26,5)) if floor+1<FLOOR_COUNTS[building] else None
        self.stairs=[("down",self.down)]+([("up",self.up)] if self.up else [])
        self.zones=[(8,6),(23,6),(8,16),(23,16),(16,12)]
        self.labels=[]
        if not self.rooftop:
            for y in range(1,23):
                if y not in (11,12,13):self.grid[y][15]=1
            for x in range(1,31):
                if x not in (14,15,16):self.grid[11][x]=1
            for cell,vertical in (((8,11),False),((23,11),False),((15,6),True),((15,18),True)):
                self.grid[cell[1]][cell[0]]=0;self.doors[cell]=Door(cell,vertical)
            kinds={22:("shelf","table","shelf","cabinet"),11:("computer","computer","cabinet","desk"),
                   5:("workbench","cabinet","computer","boxes"),15:("desk","cabinet","table","sofa"),
                   21:("workbench","boxes","cabinet","workbench")}[building]
            if building==22 and floor==2:kinds=("cabinet","computer","shelf","desk")
            if building==5 and floor==2:kinds=("computer","workbench","cabinet","computer")
            for i,(cx,cy) in enumerate(self.zones[:4]):
                for dx,dy in ((-4,-3),(3,-3),(-4,2)):
                    # Stair approaches and all four room centers stay clear.
                    x,y=cx+dx,cy+dy
                    if abs(x-5)<3 and abs(y-19)<3 or abs(x-26)<3 and abs(y-5)<3:continue
                    self.add_furniture(kinds[i],x,y,2,1)
            names={22:("ARSIP","KATALOG","RUANG BACA","MIKROFILM"),11:("SERVER","LAB MALAM","ARSIP DATA","RUANG ASISTEN"),
                   5:("DISTRIBUSI","KONTROL","PEMANCAR","SERVIS"),15:("RUANG RAPAT","ARSIP INSIDEN","OPERASIONAL","ADMINISTRASI"),
                   21:("GENERATOR A","GENERATOR B","PANEL BEBAN","BENGKEL")}[building]
            self.labels=[(name,self.center((cx-3,cy-4))) for name,(cx,cy) in zip(names,self.zones)]
            if building==5 and floor==2:
                self.labels=[(name,self.center((cx-3,cy-4))) for name,(cx,cy) in zip(("TELEMETRI","ARSIP RADIO","PENERIMA","ISOLASI"),self.zones)]
        else:
            for x,y,w,h in ((11,4,4,3),(21,13,5,2),(9,17,2,2)):
                self.add_furniture("workbench",x,y,w,h)
            self.labels=[("ANTENA 03",self.center((20,8))),("ATAP · AREA SERVIS",self.center((3,2)))]
        self.spawn=self.center((6,19));self.panel=self.center((23,16));self.exit=self.down
        self.spawn_room=self.panel_room=self.exit_room=building
        self.fuses=[];self.monster_spawns=[self.center(p) for p in self.zones[:3]]
        self.bottle_spawns=[self.nearest_floor(self.center((x,y))) for x,y in ((8,8),(24,8),(10,17))]
        self.medkit_spawns=[self.center((24,18))]
        self.stats=AnnealingStats(0,0,0,0,0,[0]);self.edges=()
        errors=self.validate()
        if errors:raise ValueError(errors)

    def add_furniture(self,kind,x,y,w,h):
        self.furniture.append(Furniture(kind,x,y,w,h))
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                self.grid[yy][xx]=2
                if kind in ("shelf","cabinet"):self.sight_cells.add((xx,yy))

    def room_at(self,pos):return self.building
    def room_center_cell(self,room):return self.zones[room%len(self.zones)]
    def room_origin(self,room):return (1,1)
    def is_outdoor(self,pos):return self.rooftop
    def surface_at(self,pos):return "metal" if self.rooftop else "wood" if self.building==22 else "concrete"
    def quest_point(self,index=0):return self.center(self.zones[index%len(self.zones)])
    def blocks_sight(self,cell):return super().blocks_sight(cell) or cell in self.sight_cells
