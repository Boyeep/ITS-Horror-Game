"""Static world surfaces and location-specific decoration."""
import random
import pygame
from ..config import INK, ROOM_H, ROOM_KINDS, ROOM_W, TILE
from ..world import Furniture


class WorldRenderer:
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
                self.draw.line(self.world,(53,62,53),(lx,ly-17),(lx,ly+9),3)
                self.draw.circle(self.world,(207,200,155),(lx,ly-17),4)
                self.static_light.blit(glow,glow.get_rect(center=(lx,ly)),special_flags=pygame.BLEND_RGB_MAX)

    def ground_tile(self,material,x,y):
        key=("terrain",material,x%3,y%3)
        if key not in self.art.cache:
            tile=pygame.Surface((TILE,TILE)).convert();rng=random.Random(x%3+y%3*7)
            tile.fill({"grass":(50,70,47),"asphalt":(55,64,66),"concrete":(111,119,111)}[material])
            for _ in range(22 if material=="asphalt" else 14):
                px,py=rng.randrange(TILE),rng.randrange(TILE)
                if material=="grass":self.draw.line(tile,(65,85,54),(px,py),(px+1,py-3))
                elif material=="asphalt":tile.set_at((px,py),(72,79,77))
            if material=="concrete":
                self.draw.rect(tile,(87,99,94),(0,0,TILE,TILE),1)
                self.draw.line(tile,(127,133,119),(2,1),(TILE-2,1))
            self.art.cache[key]=tile
        return self.art.cache[key]

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
        for item in layout.furniture:self.art.furniture(self.world,item)
        if hasattr(layout,"lab_bounds"):self.project_lab(layout)
        for x in range(3,layout.width-3,5):
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
