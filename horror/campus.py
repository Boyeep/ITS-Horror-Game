"""Fixed Sukolilo-inspired geography, traced as original tiles rather than PDF imagery.

Relative landmarks/roads refer to the ITS International Student Guide, map on
PDF page 15 (printed 12), and the official 2021 topography in Campus Forests.
Building footprints, interiors and story access points are gameplay abstractions.
"""
import math
import random

from .config import TILE, OUTDOOR_KINDS
from .world import Layout, Door, Furniture, Candidate, AnnealingStats, graph_from, ROOM_FURNITURE
from .informatika import ground as build_informatika

LANDMARKS = [
    ("GRAHA SEPULUH NOPEMBER", "meeting", 19, 12),
    ("TELAGA", "garden", 14, 18),
    ("SISTEM INFORMASI", "computer", 28, 24),
    ("PENS", "computer", 46, 13),
    ("JALAN RAYA ITS", "walkway", 48, 5),
    ("PUSAT ROBOTIKA", "lab", 70, 24),
    ("GERBANG UTAMA", "gate", 7, 43),
    ("TEKNIK LINGKUNGAN", "lab", 30, 44),
    ("ARSITEKTUR", "studio", 34, 53),
    ("PERENCANAAN WILAYAH", "studio", 44, 46),
    ("DESAIN PRODUK", "studio", 61, 36),
    ("INFORMATIKA", "computer", 72, 42),
    ("HUTAN KAMPUS", "garden", 15, 62),
    ("HALAMAN MANARUL ILMI", "garden", 31, 65),
    ("TEKNIK SIPIL", "lab", 39, 61),
    ("REKTORAT", "admin", 47, 59),
    ("PASCASARJANA", "meeting", 55, 50),
    ("RESEARCH CENTER", "lab", 77, 56),
    ("STADION ITS", "garden", 20, 86),
    ("SCC / KANTIN", "canteen", 39, 80),
    ("TAMAN ALUMNI", "garden", 32, 73),
    ("TEKNIK MESIN", "workbench", 62, 89),
    ("PERPUSTAKAAN", "library", 60, 67),
    ("TEKNIK KIMIA", "lab", 71, 80),
    ("ASRAMA ITS", "lobby", 19, 106),
    ("JALAN TEKNIK ELEKTRO", "walkway", 35, 100),
    ("MATEMATIKA", "classroom", 46, 94),
    ("PLASA DR. ANGKA", "plaza", 49, 69),
    ("TEKNIK ELEKTRO", "lab", 61, 99),
    ("TEKNIK MATERIAL", "lab", 79, 96),
]

# Roads follow the west entrance, central spine, east road and southern loop.
ROADS = [
    [(7,43),(8,10),(48,5),(68,32),(82,52),(82,104),(35,110),(35,100)],
    [(7,43),(18,47),(32,59),(35,76),(35,100)],
    [(18,47),(27,35),(47,35),(68,32)],
    [(32,59),(48,69),(67,69),(82,61)],
    [(35,100),(62,104),(82,104)],
    [(48,69),(56,78),(62,89),(62,104)],
]

# Playable floors are fiction for this story, not claims about real floorplans.
FLOOR_COUNTS = {11: 3, 22: 3, 5: 4, 15: 2, 21: 2}


class CampusLayout(Layout):
    campus = True
    spawn_room, panel_room, exit_room = 11, 15, 6

    def __init__(self):
        self.seed = 1960
        self.width, self.height = 88, 118
        self.room_names = [n for n,_,_,_ in LANDMARKS]
        self.room_kinds = [k for _,k,_,_ in LANDMARKS]
        self.outdoors = {n for n,k in enumerate(self.room_kinds) if k in OUTDOOR_KINDS}
        self.centers = {n:(x,y) for n,(_,_,x,y) in enumerate(LANDMARKS)}
        self.origins = {n:(x-4,y-3) for n,(x,y) in self.centers.items()}
        self.grid = [[1 if x in (0,self.width-1) or y in (0,self.height-1) else 0
                      for x in range(self.width)] for y in range(self.height)]
        self.materials = [["grass" for _ in range(self.width)] for _ in range(self.height)]
        self.doors, self.glass, self.furniture = {}, set(), []
        self.revision = 0
        self.roads = ROADS
        self.water = set()
        self.buildings = {}
        for y in range(7,29):
            for x in range(2,12):
                if ((x-7)/4.5)**2+((y-18)/10)**2 < 1:
                    self.water.add((x,y));self.grid[y][x]=1
        for road in ROADS:
            for a,b in zip(road,road[1:]):
                self.paint_road(a,b,2,"asphalt")
        # Every location has an approach to the nearest road, with building access south.
        templates={"meeting":11,"admin":5,"computer":0,"lab":10,"studio":6,"workbench":2,
                   "library":9,"canteen":8,"lobby":8,"classroom":1}
        for n,(_,kind,x,y) in enumerate(LANDMARKS):
            approach=(x,y+4) if kind not in OUTDOOR_KINDS else (x,y)
            nearest=min((point for road in ROADS for point in self.road_points(road)),key=lambda p:math.dist(p,approach))
            self.paint_road(approach,nearest,1)
            if n in self.outdoors:
                self.paint_road((x-1,y),(x+1,y),2)
                continue
            if n==11:
                build_informatika(self);continue
            ox,oy=self.origins[n]
            self.buildings[n]=(ox,oy,9,7)
            for ty in range(oy,oy+7):
                for tx in range(ox,ox+9):
                    wall=tx in (ox,ox+8) or ty in (oy,oy+6)
                    self.grid[ty][tx]=1 if wall else 0
                    self.materials[ty][tx]="wood" if kind in ("meeting","admin","library") else "concrete"
            cell=(x,oy+6);self.grid[cell[1]][cell[0]]=0
            self.doors[cell]=Door(cell,False)
            # A small, hand-arranged interior leaves the center and entry free.
            base=ROOM_FURNITURE[templates.get(kind,1)]
            for index,(fkind,_,_,_,_) in enumerate(base[:3]):
                px,py=((ox+1,oy+1),(ox+6,oy+1),(ox+1,oy+4))[index]
                self.furniture.append(Furniture(fkind,px,py,2,1))
                for tx in range(px,px+2):self.grid[py][tx]=2
        # The entrance roundabout and the stadium preserve their recognizable shapes.
        self.roundabout=(13,44)
        self.stadium=(20,86)
        for y in range(42,47):
            for x in range(11,16):
                if math.dist((x,y),self.roundabout)<2.3:self.materials[y][x]="grass"
        for y in range(85,88):
            for x in range(17,24):self.materials[y][x]="grass"
        self.stairs={n:self.center((self.centers[n][0]+2,self.centers[n][1]+1)) for n in FLOOR_COUNTS}
        self.stairs[11]=self.informatika_stairs["sw"]
        self.decor=[]
        for n in (11,15,19,22,24):
            x,y=self.centers[n]
            places=((84,37),(75,51)) if n==11 else ((x+6,y+4),(x+7,y+6))
            for px,py in places:
                if all(self.walkable((tx,py),True) for tx in (px,px+1)) and self.is_outdoor(self.center((px,py))):
                    self.furniture.append(Furniture("motorbike",px,py,2,1))
                    for tx in (px,px+1):self.grid[py][tx]=2
        rng=random.Random(self.seed)
        for n in sorted(self.outdoors):
            x,y=self.centers[n]
            for dx,dy in ((-3,-2),(3,2)):
                px,py=x+dx,y+dy
                if self.walkable((px,py),True) and self.materials[py][px]=="grass":
                    self.furniture.append(Furniture("tree",px,py,1,1));self.grid[py][px]=2
        # Ground-level set dressing is tied to place, with explicit collision footprints.
        for room in (1,12,13,18,20,27):
            x,y=self.centers[room]
            for dx,dy in ((-4,3),(3,-3)):
                px,py=x+dx,y+dy
                if self.walkable((px,py),True) and self.materials[py][px]=="grass":
                    self.furniture.append(Furniture("bench",px,py,1,1));self.grid[py][px]=2
        for _ in range(180):
            x,y=rng.randrange(2,self.width-2),rng.randrange(2,self.height-2)
            if self.materials[y][x]=="grass" and self.walkable((x,y),True) and min(math.dist((x,y),p) for p in self.centers.values())>6:
                self.decor.append(("tree",x,y))
                self.grid[y][x]=2
        self.spawn=self.informatika_spawn
        self.intro_start=(self.spawn[0]+80,self.spawn[1]-40)
        self.panel=self.center(self.centers[self.panel_room])
        self.exit=self.center(self.centers[self.exit_room])
        self.fuses=[self.center(self.centers[n]) for n in (23,28)]
        self.monster_spawns=[self.center(self.centers[n]) for n in (15,20,26)]
        self.bottle_spawns=[self.nearest_floor(self.center((x+1,y-1) if n in FLOOR_COUNTS else (x+2,y+1))) for n,(_,_,x,y) in enumerate(LANDMARKS) if n!=self.spawn_room]
        self.sight_cells={(x,y) for _,x,y in self.decor}
        for item in self.furniture:
            if item.kind in ("tree","shelf","cabinet"):
                self.sight_cells.update((x,y) for y in range(item.y,item.y+item.height) for x in range(item.x,item.x+item.width))
        self.medkit_spawns=[self.nearest_floor(self.center((self.centers[n][0]+2,self.centers[n][1]))) for n in (11,22,15,19,6)]
        self.edges=self._landmark_edges()
        self.graph=graph_from(self.edges)
        self.tree=self.edges
        self.candidate=Candidate((23,28),(15,20,26),())
        self.stats=AnnealingStats(0,0,0,0,0,[0])
        if self.validate():
            raise ValueError(self.validate())

    def road_points(self,road):
        for a,b in zip(road,road[1:]):
            steps=max(abs(b[0]-a[0]),abs(b[1]-a[1]),1)
            for i in range(steps+1):
                yield (round(a[0]+(b[0]-a[0])*i/steps),round(a[1]+(b[1]-a[1])*i/steps))

    def paint_road(self,a,b,radius,material="concrete"):
        for x,y in self.road_points([a,b]):
            for ty in range(max(1,y-radius),min(self.height-1,y+radius+1)):
                for tx in range(max(1,x-radius),min(self.width-1,x+radius+1)):
                    if (tx,ty) not in self.water:
                        if material=="asphalt" or self.materials[ty][tx]!="asphalt":
                            self.materials[ty][tx]=material

    def _landmark_edges(self):
        # Schematic connections for the denah; physical navigation uses the real tile grid.
        edges=set()
        for n,a in self.centers.items():
            nearest=sorted((math.dist(a,b),m) for m,b in self.centers.items() if m!=n)[:3]
            for _,m in nearest:edges.add(tuple(sorted((n,m))))
        return tuple(sorted(edges))

    def room_origin(self,room):
        return self.origins[room]

    def room_center_cell(self,room):
        if room==11:return self.tile(self.informatika_spawn)
        return self.centers[room]

    def room_at(self,pos):
        x,y=pos[0]/TILE,pos[1]/TILE
        if 66<=x<83 and 35<=y<50:return 11
        return min(self.centers,key=lambda n:(self.centers[n][0]-x)**2+(self.centers[n][1]-y)**2)

    def surface_at(self,pos):
        x,y=self.tile(pos)
        return self.materials[max(0,min(self.height-1,y))][max(0,min(self.width-1,x))]

    def is_outdoor(self,pos):
        x,y=pos[0]/TILE,pos[1]/TILE
        if 66<=x<83 and 35<=y<50:return self.tile(pos) not in self.informatika_cells
        return not any(ox<x<ox+w and oy<y<oy+h for ox,oy,w,h in self.buildings.values())

    def blocks_sight(self,cell):return super().blocks_sight(cell) or cell in getattr(self,"sight_cells",set())
