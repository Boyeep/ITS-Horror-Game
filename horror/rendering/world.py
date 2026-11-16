"""Static world surfaces and location-specific decoration."""
import random
import pygame
from ..config import INK, ROOM_H, ROOM_KINDS, ROOM_W, TILE
from ..architecture import top_window_columns
from ..world import Furniture
from ..decor import floor_wear, stair_zone, wall_fixtures


class WorldRenderer:
    def exterior_roof_cell(self,rect,cell,solid):
        """Continuous exterior roof with edge trim; gaps use the collision footprint."""
        self.draw.rect(self.world,(60,79,87),rect)
        x,y=cell
        if y%3==0:self.draw.line(self.world,(69,88,95),rect.topleft,rect.topright)
        if x%5==0 and y%4==2 and all((x+dx,y+dy) in solid for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))):
            self.draw.rect(self.world,(36,51,58),(rect.x+4,rect.y+7,31,22))
            for offset in (11,16,21):self.draw.line(self.world,(98,120,123),(rect.x+8,rect.y+offset),(rect.right-8,rect.y+offset),2)
        if (x,y-1) not in solid:self.draw.line(self.world,(143,155,147),rect.topleft,rect.topright,3)
        if (x-1,y) not in solid:self.draw.line(self.world,(101,122,123),rect.topleft,rect.bottomleft,3)
        if (x+1,y) not in solid:self.draw.line(self.world,(35,49,57),rect.topright,rect.bottomright,4)
        if (x,y+1) not in solid:
            self.draw.line(self.world,(28,42,48),rect.bottomleft,rect.bottomright,5)
            self.draw.rect(self.world,(76,113,123),(rect.x+5,rect.bottom-14,30,8))
            self.draw.line(self.world,(160,180,168),(rect.x+20,rect.bottom-14),(rect.x+20,rect.bottom-6))

    def build_world(self, layout):
        self.seed = layout.seed
        self.last_room = None
        self.world = pygame.Surface((layout.width * TILE, layout.height * TILE)).convert()
        self.static_light = pygame.Surface(self.world.get_size()).convert()
        self.static_light.fill((0, 0, 0))
        self.world.fill(INK)
        if getattr(layout,"interior",False):
            self.build_floor_world(layout)
            return
        if getattr(layout, "campus", False):
            self.build_campus_world(layout)
            return
        rng = random.Random(layout.seed)
        for y, row in enumerate(layout.grid):
            for x, value in enumerate(row):
                rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                if value == 1:
                    outdoor = layout.room_at(layout.center((x,y))) in layout.outdoors
                    if outdoor:
                        self.draw.rect(self.world, (36, 51, 38), rect)
                        for dx,dy in ((8,12),(23,7),(29,27),(12,31)):
                            self.draw.circle(self.world,(44+dx//4,63,43),(rect.x+dx,rect.y+dy),12)
                    else:
                        self.draw.rect(self.world, (92, 102, 94), rect)
                        self.draw.rect(self.world, (60, 72, 67), rect.inflate(-2, -2), 1)
                        self.draw.line(self.world, (145, 146, 127), rect.topleft, rect.topright, 2)
                        self.draw.line(self.world, (36, 47, 44), rect.bottomleft, rect.bottomright, 4)
                    continue
                room = layout.room_at(layout.center((x, y)))
                self.world.blit(self.art.floor(room, x, y), rect)
                if (x, y) in layout.glass:
                    self.art.place(self.world, 264, rect.inflate(-9, -9))
        for item in layout.furniture:
            self.art.furniture(self.world, item)
        for room, name in enumerate(layout.room_names):
            x, y = layout.room_origin(room)
            if room in layout.outdoors:
                lx,ly = x*TILE+8*TILE, y*TILE+TILE+14
                self.draw.line(self.world,(58,65,59),(lx,ly),(lx,ly+19),3)
                self.draw.circle(self.world,(190,183,141),(lx,ly),4)
                glow=self.radial_glow(110,(121,130,111))
                self.static_light.set_clip((x*TILE+TILE,y*TILE+TILE,(ROOM_W-1)*TILE,(ROOM_H-1)*TILE))
                self.static_light.blit(glow,glow.get_rect(center=(lx,ly+25)),special_flags=pygame.BLEND_RGB_MAX)
                self.static_light.set_clip(None)
                if ROOM_KINDS[room] in ("parking","gate"):
                    for dx in (80,300):
                        self.draw.line(self.world,(155,159,131),(x*TILE+dx,y*TILE+110),(x*TILE+dx,y*TILE+145),2)
                continue
            # Notice boards and whiteboards are wall-mounted, not floating floor labels.
            bx, by = x * TILE + 275, y * TILE + 42
            self.draw.rect(self.world, (89, 76, 56), (bx, by, 110, 30), border_radius=2)
            self.draw.rect(self.world, (166, 170, 151) if ROOM_KINDS[room] in ("computer", "classroom", "lab", "studio") else (125, 107, 76), (bx + 3, by + 2, 104, 24))
            if ROOM_KINDS[room] in ("computer", "classroom", "lab", "studio"):
                for line in range(3):
                    self.draw.line(self.world, (80, 99, 91), (bx + 10, by + 8 + line * 5), (bx + 50 + line * 9, by + 8 + line * 5))
            else:
                for i in range(4):
                    self.art.place(self.world, 263, (bx + 7 + i * 24, by + 5, 15, 19), angle=(i - 2) * 3)
            # Small debris belongs beside furniture, rather than carpeting every room.
            for item in [p for p in layout.furniture if layout.room_at(layout.center((p.x, p.y))) == room][:2]:
                px, py = item.x * TILE - 15, (item.y + item.height) * TILE + 10
                if layout.walkable(layout.tile((px, py)), True):
                    self.art.place(self.world, 263, (px, py, 11, 15), angle=rng.randrange(-18, 19))

    def build_campus_world(self, layout):
        exterior={cell for cell in getattr(layout,"informatika_cells",()) if layout.grid[cell[1]][cell[0]]==1}
        grass = pygame.Surface((TILE,TILE)).convert()
        grass.fill((54,69,50))
        rng=random.Random(1960)
        for _ in range(18):
            x,y=rng.randrange(TILE),rng.randrange(TILE)
            self.draw.line(grass,(64,79,55),(x,y),(x+1,y-3))
        for y,row in enumerate(layout.grid):
            for x,value in enumerate(row):
                rect=pygame.Rect(x*TILE,y*TILE,TILE,TILE)
                material=layout.materials[y][x]
                if (x,y) in layout.water:
                    self.draw.rect(self.world,(37,65,65),rect)
                    self.draw.line(self.world,(47,77,75),(rect.x+8,rect.y+16),(rect.x+29,rect.y+16))
                elif value==1:
                    if (x,y) in exterior:
                        self.exterior_roof_cell(rect,(x,y),exterior)
                        continue
                    self.draw.rect(self.world,(90,100,93),rect)
                    self.draw.rect(self.world,(62,72,66),rect.inflate(-2,-2),1)
                    self.draw.line(self.world,(144,143,125),rect.topleft,rect.topright,2)
                    self.draw.line(self.world,(35,45,41),rect.bottomleft,rect.bottomright,4)
                elif material=="grass":self.world.blit(self.ground_tile("grass",x,y),rect)
                elif material in ("asphalt","concrete"):self.world.blit(self.ground_tile(material,x,y),rect)
                else:
                    tile=96+(x+y*3)%4 if material=="wood" else 12
                    self.world.blit(self.art.image(tile,(TILE,TILE),tint=(185,192,180)),rect)
        # Familiar silhouettes: west roundabout, lake, stadium, blue campus signs.
        rx,ry=layout.center(layout.roundabout)
        self.draw.circle(self.world,(113,119,105),(rx,ry),115,14)
        self.draw.circle(self.world,(69,85,57),(rx,ry),94)
        self.draw.circle(self.world,(164,164,139),(rx,ry),19,3)
        sx,sy=layout.center(layout.stadium)
        self.draw.ellipse(self.world,(127,100,77),(sx-160,sy-90,320,180),16)
        self.draw.rect(self.world,(82,103,63),(sx-118,sy-58,236,116))
        self.draw.rect(self.world,(147,159,124),(sx-118,sy-58,236,116),2)
        self.draw.line(self.world,(147,159,124),(sx,sy-58),(sx,sy+58),2)
        self.draw.circle(self.world,(147,159,124),(sx,sy),26,2)
        for road in layout.roads:
            points=list(layout.road_points(road))
            for i in range(0,len(points)-1,5):
                x,y=points[i]
                if layout.materials[y][x]=="asphalt" and layout.grid[y][x]==0:
                    a=pygame.Vector2(layout.center((x,y)));delta=pygame.Vector2(points[i+1])-pygame.Vector2((x,y))
                    if delta.length_squared():self.draw.line(self.world,(145,146,119),a-delta.normalize()*12,a+delta.normalize()*12,2)
        for item in layout.furniture:self.art.furniture(self.world,item)
        for kind,x,y in layout.decor:self.art.furniture(self.world,Furniture(kind,x,y,1,1))
        glow=self.radial_glow(115,(131,139,117))
        for room,name in enumerate(layout.room_names):
            cx,cy=layout.center(layout.centers[room])
            if room in layout.buildings:
                ox,oy,_,_=layout.buildings[room]
                px,py=ox*TILE+12,oy*TILE+8
            else:px,py=cx-95,cy-86
            lx,ly=cx+100,cy+115
            if not layout.blocks_sight(layout.tile((lx,ly))):
                self.draw.line(self.world,(29,35,32),(lx,ly+9),(lx,ly-17),5)
                self.draw.line(self.world,(66,76,68),(lx,ly+9),(lx,ly-17),3)
                self.draw.rect(self.world,(41,48,44),(lx-6,ly+7,13,4))
                self.draw.line(self.world,(66,76,68),(lx,ly-17),(lx+8,ly-21),3)
                self.draw.rect(self.world,(52,60,55),(lx+3,ly-25,11,4))
                self.draw.circle(self.world,(226,214,160),(lx+9,ly-20),3)
                self.draw.circle(self.world,(150,142,104),(lx+9,ly-20),7,1)
                self.static_light.blit(glow,glow.get_rect(center=(lx,ly)),special_flags=pygame.BLEND_RGB_MAX)

    GROUND_BASE = {"grass": (50, 70, 47), "asphalt": (55, 64, 66), "concrete": (111, 119, 111)}

    def ground_tile(self,material,x,y):
        """Night ground with small, low-contrast wear so wide areas stop reading as one repeated tile."""
        key=("terrain_v2",material,x%5,y%5)
        if key not in self.art.cache:
            rng=random.Random(x%5+y%5*11+{"grass":0,"asphalt":100,"concrete":200}[material])
            shift=rng.randrange(-4,5)
            tile=pygame.Surface((TILE,TILE)).convert()
            tile.fill(tuple(max(0,min(255,c+shift)) for c in self.GROUND_BASE[material]))
            getattr(self,"wear_"+material)(tile,rng)
            self.art.cache[key]=tile
        return self.art.cache[key]

    def wear_grass(self,tile,rng):
        if rng.random()<.3:
            self.draw.ellipse(tile,(44,62,42),(rng.randrange(4,TILE-22),rng.randrange(4,TILE-14),rng.randrange(12,20),rng.randrange(7,11)))
        for shade,count in (((65,85,54),14),((42,58,40),8)):
            for _ in range(count):
                px,py=rng.randrange(2,TILE-2),rng.randrange(4,TILE)
                self.draw.line(tile,shade,(px,py),(px+1,py-3))
        if rng.random()<.25:
            px,py=rng.randrange(5,TILE-8),rng.randrange(5,TILE-8)
            self.draw.line(tile,(92,84,50),(px,py),(px+3,py+1),2)

    def wear_asphalt(self,tile,rng):
        for shade,count in (((72,79,77),22),((44,52,54),10)):
            for _ in range(count):tile.set_at((rng.randrange(TILE),rng.randrange(TILE)),shade)
        if rng.random()<.2:
            self.draw.ellipse(tile,(48,56,58),(rng.randrange(4,TILE-22),rng.randrange(6,TILE-14),rng.randrange(12,20),rng.randrange(8,12)))
        if rng.random()<.3:
            px,py=rng.randrange(6,TILE-6),rng.randrange(6,TILE-6)
            for _ in range(rng.randrange(3,6)):
                nx,ny=max(3,min(TILE-3,px+rng.randrange(-8,9))),max(3,min(TILE-3,py+rng.randrange(-8,9)))
                self.draw.line(tile,(36,43,45),(px,py),(nx,ny))
                px,py=nx,ny
        if rng.random()<.07:
            px,py=rng.randrange(6,TILE-22),rng.randrange(8,TILE-14)
            self.draw.ellipse(tile,(40,57,66),(px,py,rng.randrange(14,20),rng.randrange(8,11)))
            self.draw.line(tile,(82,100,110),(px+4,py+2),(px+9,py+2))

    def wear_concrete(self,tile,rng):
        self.draw.rect(tile,(87,99,94),(0,0,TILE,TILE),1)
        self.draw.line(tile,(127,133,119),(2,1),(TILE-2,1))
        if rng.random()<.2:
            self.draw.ellipse(tile,(101,109,101),(rng.randrange(4,TILE-22),rng.randrange(5,TILE-14),rng.randrange(12,20),rng.randrange(7,11)))
        if rng.random()<.25:
            px,py=rng.randrange(6,TILE-14),rng.randrange(6,TILE-14)
            self.draw.line(tile,(84,94,90),(px,py),(px+rng.randrange(5,12),py+rng.randrange(4,12)))
        if rng.random()<.25:
            for _ in range(4):tile.set_at((rng.randrange(2,TILE-2),rng.choice((2,3,TILE-3))),(66,88,62))

    def dress_interior(self,layout):
        """Cosmetic dressing baked into the world picture; layout.grid is only read, never changed."""
        doors=getattr(layout,"doors",{})
        skip=set(getattr(layout,"void_cells",()))|set(getattr(layout,"outdoor_cells",()))|set(getattr(layout,"glass",()))
        skip|=stair_zone(getattr(layout,"stairs",()),TILE)
        for variant,x,y in floor_wear(layout.grid,doors,skip):
            self.world.blit(self.wear_overlay(variant,x,y),(x*TILE,y*TILE))
        for kind,x,y in wall_fixtures(layout.grid,doors,skip):
            self.draw_fixture(kind,pygame.Rect(x*TILE,y*TILE,TILE,TILE))

    def wear_overlay(self,variant,x,y):
        key=("wear_v1",variant,x%4,y%4)
        if key not in self.art.cache:
            tile=pygame.Surface((TILE,TILE),pygame.SRCALPHA);rng=random.Random(f"{variant}{x%4}{y%4}")
            if variant=="scuff":
                for _ in range(3):
                    px,py=rng.randrange(6,TILE-12),rng.randrange(6,TILE-12)
                    pygame.draw.line(tile,(0,0,0,34),(px,py),(px+rng.randrange(5,11),py+rng.randrange(-3,4)),2)
            elif variant=="stain":
                pygame.draw.ellipse(tile,(0,0,0,24),(rng.randrange(4,10),rng.randrange(5,12),rng.randrange(16,24),rng.randrange(10,16)))
            else:
                px,py=rng.randrange(8,TILE-8),rng.randrange(8,TILE-8)
                for _ in range(rng.randrange(3,6)):
                    nx,ny=max(3,min(TILE-3,px+rng.randrange(-9,10))),max(3,min(TILE-3,py+rng.randrange(-9,10)))
                    pygame.draw.line(tile,(0,0,0,46),(px,py),(nx,ny));px,py=nx,ny
            self.art.cache[key]=tile
        return self.art.cache[key]

    def draw_fixture(self,kind,rect):
        world,draw=self.world,self.draw
        if kind=="board":
            draw.rect(world,(64,54,42),(rect.x+7,rect.y+9,26,19),border_radius=1)
            draw.rect(world,(112,94,68),(rect.x+9,rect.y+11,22,15))
            for i,color in enumerate(((186,182,164),(146,168,166),(184,156,108))):
                draw.rect(world,color,(rect.x+11+i*7,rect.y+13+i%2*4,5,7))
        elif kind=="poster":
            draw.rect(world,(52,64,62),(rect.x+10,rect.y+7,20,26))
            draw.rect(world,(82,108,112),(rect.x+12,rect.y+9,16,22))
            draw.line(world,(150,160,140),(rect.x+14,rect.y+15),(rect.x+26,rect.y+15))
            draw.line(world,(150,160,140),(rect.x+14,rect.y+20),(rect.x+23,rect.y+20))
        elif kind=="extinguisher":
            draw.rect(world,(158,58,50),(rect.x+14,rect.y+12,11,18),border_radius=3)
            draw.rect(world,(48,52,50),(rect.x+16,rect.y+8,7,5))
        elif kind=="vent":
            draw.rect(world,(52,62,60),(rect.x+8,rect.y+12,24,16))
            for dy in (15,19,23):draw.line(world,(98,110,104),(rect.x+10,rect.y+dy),(rect.x+30,rect.y+dy))
        else:
            draw.circle(world,(170,170,152),rect.center,9);draw.circle(world,(50,58,56),rect.center,9,1)
            draw.line(world,(40,46,44),rect.center,(rect.centerx,rect.centery-6))
            draw.line(world,(40,46,44),rect.center,(rect.centerx+4,rect.centery))

    def build_floor_world(self,layout):
        wood=layout.building==22
        for y,row in enumerate(layout.grid):
            for x,value in enumerate(row):
                rect=pygame.Rect(x*TILE,y*TILE,TILE,TILE)
                if (x,y) in getattr(layout,"void_cells",set()):
                    self.draw.rect(self.world,(29,48,40),rect)
                elif value==1:
                    self.draw.rect(self.world,(87,99,96),rect)
                    self.draw.rect(self.world,(56,69,67),rect.inflate(-3,-3),1)
                    self.draw.line(self.world,(150,150,131),rect.topleft,rect.topright,2)
                elif hasattr(layout,"outdoor_cells") and (x,y) in layout.outdoor_cells:
                    self.world.blit(self.ground_tile(layout.surface_at(layout.center((x,y))),x,y),rect)
                elif layout.rooftop:
                    self.world.blit(self.ground_tile("asphalt",x,y),rect)
                    if x%5==0:self.draw.line(self.world,(92,104,99),rect.topleft,rect.bottomleft)
                else:
                    tint=(192,194,175) if wood else (161,184,181)
                    if hasattr(layout,"lab_bounds"):
                        tint=(189,188,168) if 11<=y<=13 or 33<=y<=34 or x>=49 else (170,182,175)
                    self.world.blit(self.art.image(96+(x+y)%4 if wood else 12,(TILE,TILE),tint=tint),rect)
        if not layout.rooftop:self.dress_interior(layout)
        for item in layout.furniture:self.art.furniture(self.world,item)
        if hasattr(layout,"lab_bounds"):self.project_lab(layout)
        for x in top_window_columns(layout):
            if not layout.rooftop:
                self.draw.rect(self.world,(37,63,74),(x*TILE+5,3,85,22))
                self.draw.line(self.world,(134,145,130),(x*TILE+45,3),(x*TILE+45,25),2)
        glow=self.radial_glow(160,(137,161,148))
        for cx,cy in layout.zones[:4]:
            pos=layout.center((cx,cy-3))
            if not layout.rooftop:self.draw.rect(self.world,(164,177,153),(pos[0]-24,pos[1]-3,48,6),border_radius=2)
            self.static_light.blit(glow,glow.get_rect(center=pos),special_flags=pygame.BLEND_RGB_MAX)
        if layout.rooftop:
            # Service mast, cable trays and red obstruction lamps, drawn as original geometry.
            x,y=layout.center((23,6))
            self.draw.circle(self.world,(89,106,105),(x,y),65,3)
            for dx,dy in ((-45,-45),(45,-45),(-45,45),(45,45)):
                self.draw.line(self.world,(125,144,138),(x,y),(x+dx,y+dy),4)
            self.draw.circle(self.world,(186,75,59),(x,y),7)
            self.draw.lines(self.world,(129,126,81),False,[(x,y+65),(x,12*TILE),(15*TILE,12*TILE),(15*TILE,20*TILE)],3)

    def project_lab(self,layout):
        # Keep physical details; navigation and story copy belong in the native HUD.
        phone=pygame.Vector2(layout.phone_display)
        self.draw.lines(self.world,(156,163,140),False,[phone+(0,11),phone+(0,26),phone+(40,26),phone+(40,16)],1)
        for x in range(9,28,4):
            self.draw.rect(self.world,(77,115,116),(x*TILE,46*TILE+19,3*TILE,12))
            self.draw.line(self.world,(146,167,155),(x*TILE,46*TILE+20),((x+3)*TILE,46*TILE+20),2)
        for y in (14,32):
            for x in (*range(8,20),*range(26,34),*range(39,45)):
                self.draw.rect(self.world,(45,79,82),(x*TILE,y*TILE+11,TILE,17))
                self.draw.line(self.world,(149,166,156),(x*TILE,y*TILE+11),(x*TILE+39,y*TILE+11),2)