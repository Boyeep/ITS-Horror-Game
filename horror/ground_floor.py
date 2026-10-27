"""Authored ground-floor play space: C wings, courtyard and a single-exit project lab.

The building's wings follow the public site reference. Room use, scale and story
props are an adaptation, not a surveyed plan of private university interiors.
"""
from .world import Layout, Door, Furniture, AnnealingStats


class InformatikaGround(Layout):
    interior=True
    campus=False
    rooftop=False
    building=11
    floor=0
    width,height=64,48

    def __init__(self,names,kinds):
        self.seed=110000
        self.room_names=list(names);self.room_names[11]="INFORMATIKA · LANTAI 1"
        self.room_kinds=list(kinds);self.outdoors=set()
        self.grid=[[int(x in (0,63) or y in (0,47)) for x in range(64)] for y in range(48)]
        self.doors={};self.glass=set();self.furniture=[];self.sight_cells=set();self.revision=0
        self.outdoor_cells={(x,y) for y in range(15,32) for x in range(1,48)}
        # Exterior walls separate the open garden from the three occupied wings.
        for x in range(1,49):
            self.grid[14][x]=1;self.grid[32][x]=1
        for y in range(14,33):self.grid[y][48]=1
        for cell,vertical in (((22,14),False),((36,32),False),((48,24),True)):
            self.door(cell,vertical)
        # North corridor, rooms and landing. South corridor serves the project lab.
        for x in range(1,49):self.grid[10][x]=1;self.grid[35][x]=1
        for x in (12,30,48):
            for y in range(1,11):self.grid[y][x]=1
        for x in (7,28,45):
            for y in range(35,47):self.grid[y][x]=1
        for x in (5,20,39):self.door((x,10),False)
        for x in (5,17,36,53):self.door((x,35),False)
        for y in range(1,14):self.grid[y][53]=1
        self.door((53,10),True)
        self.spawn=self.center((18,39));self.phone_interaction=self.center((23,41))
        self.phone_display=(23.8*40,42.35*40)
        self.nara_position=self.center((23,41));self.nara_exit=self.center((17,34))
        self.lab_bounds=(8,36,20,11);self.lab_door=(17,35)
        self.stair_points={key:self.center(cell) for key,cell in
                           (("nw",(7,7)),("ne",(58,7)),("sw",(4,41)),("se",(57,41)))}
        self.stair_portals=[("up",key,point) for key,point in self.stair_points.items()]
        self.stairs=[("up",p) for p in self.stair_points.values()];self.down=None;self.up=self.stair_points["se"]
        self.exit_points={"main":self.center((62,24)),"south":self.center((36,46)),"courtyard":self.center((1,24))}
        self.entry_spawns={"main":self.center((60,24)),"south":self.center((36,44)),"courtyard":self.center((3,24))}
        for cell,vertical in (((63,24),True),((36,47),False),((0,24),True)):
            self.door(cell,vertical);self.doors[cell].opened=True;self.doors[cell].swing=1
        # Workstations form two rows, with broad aisles and no props on the exit lane.
        for x in (10,16,22):
            for y in (38,42):self.add("computer",x,y,3,1)
        self.add("shelf",9,45,4,1);self.add("cabinet",25,45,2,1)
        for x in (16,22,34,40):self.add("computer",x,4,3,1)
        for x in (32,39):self.add("table",x,40,3,2)
        for y in (17,29):
            self.add("sofa",57,y,3,1);self.add("plant",52,y,1,1)
        self.add("desk",54,26,3,1)
        for x,y in ((10,19),(39,19),(10,28),(39,28)):
            self.add("tree",x,y,2,2)
        for x,y in ((17,18),(28,28)):self.add("bench",x,y,3,1)
        self.labels=[(name,self.center(cell)) for name,cell in (
            ("LAB PROYEK",(9,36)),("RUANG DISKUSI",(31,36)),("SELASAR SELATAN",(9,33)),
            ("LAB KOMPUTER",(15,2)),("RUANG ASISTEN",(33,2)),("LOBI UTAMA",(51,20)),
            ("COURTYARD",(21,23)),("KELUAR",(58,23)),("KELUAR",(34,45)))]
        self.zones=[(18,39),(54,24),(21,7),(37,40),(22,24)]
        self.panel=self.center((54,22));self.exit=self.exit_points["main"]
        self.spawn_room=self.panel_room=self.exit_room=11
        self.fuses=[];self.monster_spawns=[self.center((50,30)),self.center((36,12)),self.center((35,43))]
        self.bottle_spawns=[];self.medkit_spawns=[self.center((54,25))]
        self.stats=AnnealingStats(0,0,0,0,0,[0]);self.edges=()
        errors=self.validate()
        if errors:raise ValueError(errors)

    def door(self,cell,vertical):
        self.grid[cell[1]][cell[0]]=0;self.doors[cell]=Door(cell,vertical)

    def add(self,kind,x,y,w,h):
        self.furniture.append(Furniture(kind,x,y,w,h))
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                self.grid[yy][xx]=2
                if kind in ("shelf","cabinet","tree"):self.sight_cells.add((xx,yy))

    def room_at(self,pos):return 11
    def room_origin(self,room):return (1,1)
    def room_center_cell(self,room):return (54,24)
    def is_outdoor(self,pos):return self.tile(pos) in self.outdoor_cells
    def surface_at(self,pos):
        x,y=self.tile(pos)
        if (x,y) in self.outdoor_cells:return "concrete" if 21<=x<=24 or 23<=y<=25 or x>=44 else "grass"
        return "concrete"
    def quest_point(self,index=0):return self.phone_interaction if index==0 else self.center(self.zones[index%len(self.zones)])
    def blocks_sight(self,cell):return super().blocks_sight(cell) or cell in self.sight_cells
    def location_name(self,pos):
        x,y=self.tile(pos)
        zone="Courtyard" if self.is_outdoor(pos) else "Lab proyek" if 8<=x<28 and y>=36 else "Selasar selatan" if y>=32 and x<48 else "Lobi utama" if x>=48 else "Sayap utara"
        return "Informatika · "+zone
