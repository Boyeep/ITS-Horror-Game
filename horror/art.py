"""Human-authored Kenney sprites, arranged as recognizable campus interiors.

Sprites are bundled CC0 files, not generated images. Placement, night tint,
shadows and small campus-specific details are rendered locally by pygame.
"""
import math
import random

import pygame

from .config import TILE, ROOM_KINDS, ROOM_W, ROOM_H, OUTDOOR_KINDS
from .characters import portrait_original, student_original
from .architecture import door_original, stair_original
from .backdrop import campus_grade
from .resources import asset_path

ASSET_DIR = asset_path("kenney")


class Art:
    def __init__(self):
        self.originals = {}
        self.cache = {}

    def portrait(self,kind,size):
        size=tuple(map(int,size));key=("portrait_v17",kind,size)
        if key not in self.cache:
            base_key=("portrait_original_v17",kind)
            if base_key not in self.cache:self.cache[base_key]=portrait_original(kind)
            self.cache[key]=pygame.transform.smoothscale(self.cache[base_key],size)
        return self.cache[key]

    def face_icon(self,kind,size):
        size=tuple(map(int,size));key=("face_v17",kind,size)
        if key not in self.cache:
            self.portrait(kind,(300,360))
            base=self.cache[("portrait_original_v17",kind)]
            head=base.subsurface((80*3,31*3,145*3,200*3))
            self.cache[key]=pygame.transform.smoothscale(head,size)
        return self.cache[key]

    def architecture(self,kind,size,vertical=False,swing=0):
        step=round(max(0,min(1,swing))*20);size=tuple(map(int,size))
        original=("architecture_v18",kind,vertical,step)
        if original not in self.cache:
            self.cache[original]=door_original(vertical,step/20) if kind=="door" else stair_original(kind)
        key=(*original,size)
        if key not in self.cache:self.cache[key]=pygame.transform.smoothscale(self.cache[original],size)
        return self.cache[key]

    def image(self, name, size, *, crop=False, tint=(224, 222, 210)):
        name = f"tile_{name:02}" if isinstance(name, int) else name
        size = tuple(max(1, int(n)) for n in size)
        key = name, size, crop, tint
        if key not in self.cache:
            if name not in self.originals:
                self.originals[name] = pygame.image.load(str(ASSET_DIR / (name + ".png"))).convert_alpha()
            image = self.originals[name]
            if crop:
                image = image.subsurface(image.get_bounding_rect())
            image = pygame.transform.smoothscale(image, size)
            image.fill((*tint, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.cache[key] = image
        return self.cache[key]

    def place(self, surface, name, rect, *, crop=True, tint=(224, 222, 210), angle=0):
        rect = pygame.Rect(rect)
        image = self.image(name, rect.size, crop=crop, tint=tint)
        if angle:
            image = pygame.transform.rotate(image, angle)
        surface.blit(image, image.get_rect(center=rect.center))

    def floor(self, room, x, y):
        # Matching wood, linoleum and stone materials replace independent noisy tiles.
        kind = ROOM_KINDS[room]
        if kind in OUTDOOR_KINDS:
            grass = kind == "garden" and abs(x % ROOM_W - ROOM_W // 2) > 1 and abs(y % ROOM_H - ROOM_H // 2) > 1
            key = ("campus_floor", grass, (x * 7 + y * 13) % 4)
            if key not in self.cache:
                tile = pygame.Surface((TILE, TILE)).convert()
                tile.fill((57, 72, 54) if grass else (106, 112, 105))
                if grass:
                    rng = random.Random(x % 4 + y % 4 * 4)
                    for _ in range(14):
                        px, py = rng.randrange(TILE), rng.randrange(TILE)
                        pygame.draw.line(tile, (69, 83, 61), (px, py), (px + 1, py - 3))
                else:
                    pygame.draw.rect(tile, (88, 96, 90), (0, 0, TILE, TILE), 1)
                    pygame.draw.line(tile, (122, 126, 115), (2, 1), (TILE - 2, 1))
                self.cache[key] = tile
            return self.cache[key]
        if kind in ("admin", "library", "meeting", "archive"):
            tile = 96 + ((x + y * 3) % 4)
            tint = (193, 196, 191)
        elif kind in ("power", "storage", "lab", "workbench"):
            tile = (7, 8, 9, 10)[(x * 13 + y * 7) % 4]
            tint = (183, 191, 185)
        else:
            tile = 12
            tint = (190, 195, 184)
        return self.image(tile, (TILE, TILE), tint=tint)

    def furniture(self, surface, item):
        r = pygame.Rect(item.x * TILE, item.y * TILE, item.width * TILE, item.height * TILE)
        # The footprint shadow stays below furniture and does not claim walkable tiles.
        pygame.draw.rect(surface, (30, 34, 32), r.move(2, 4).inflate(-1, -2), border_radius=4)
        kind = item.kind
        if kind in ("desk", "computer", "workbench", "table"):
            top = r.inflate(-4, -4)
            if kind != "table":
                top.height = max(24, int(r.height * .74))
                self.place(surface, 528, (r.centerx - 11, r.bottom - 18, 22, 17))
            self.place(surface, 506 if kind == "table" else 484, top)
            if kind == "computer":
                pygame.draw.rect(surface, (23, 30, 32), (top.x + 10, top.y + 4, 26, 16), border_radius=2)
                pygame.draw.rect(surface, (65, 89, 86), (top.x + 13, top.y + 7, 20, 9))
                pygame.draw.line(surface, (123, 146, 132), (top.x + 16, top.y + 10), (top.x + 25, top.y + 10))
                pygame.draw.rect(surface, (138, 137, 119), (top.x + 10, top.y + 23, 24, 5), border_radius=1)
                self.place(surface, 263, (top.right - 21, top.y + 6, 12, 16), angle=7)
            elif kind == "workbench":
                self.place(surface, 321, (top.x + 4, top.y + 3, top.width - 8, top.height - 6))
                pygame.draw.rect(surface, (37, 43, 44), (top.x + 9, top.y + 7, 24, 14), border_radius=2)
                for index in range(3):
                    pygame.draw.circle(surface, (125, 154, 125), (top.x + 13 + index * 6, top.y + 11), 1)
                pygame.draw.line(surface, (67, 65, 54), (top.right - 30, top.centery - 4), (top.right - 12, top.centery + 5), 3)
            else:
                self.place(surface, 263, (top.x + 9, top.y + 5, 12, 15), angle=-8)
                self.place(surface, 317, (top.right - 24, top.y + 6, 12, 12))
        elif kind == "sofa":
            part_width = r.width / 3
            for i, tile in enumerate((447, 448, 449)):
                self.place(surface, tile, (r.x + i * part_width, r.y, part_width + 1, r.height), crop=False, tint=(169, 174, 162))
        elif kind == "shelf":
            self.place(surface, 484, r)
            colors = [(105, 72, 63), (84, 100, 90), (138, 130, 99), (73, 84, 103), (135, 119, 97)]
            for y in range(r.y + 7, r.bottom - 7, 26):
                pygame.draw.rect(surface, (59, 48, 36), (r.x + 6, y - 1, r.width - 12, 20))
                for x in range(r.x + 8, r.right - 11, 7):
                    color = colors[(x // 7 + y // 26) % len(colors)]
                    pygame.draw.rect(surface, color, (x, y, 5, 16 - (x % 3)))
                    pygame.draw.line(surface, (169, 156, 122), (x, y + 4), (x + 3, y + 4))
        elif kind == "cabinet":
            pygame.draw.rect(surface, (111, 119, 110), r.inflate(-2, -2), border_radius=2)
            for x in range(r.x + 2, r.right - 4, TILE):
                pygame.draw.rect(surface, (90, 98, 91), (x, r.y + 4, TILE - 3, r.height - 7), 1)
                pygame.draw.line(surface, (188, 188, 163), (x + 28, r.centery - 4), (x + 28, r.centery + 4), 2)
                for y in (r.y + 9, r.y + 13):
                    pygame.draw.line(surface, (69, 77, 72), (x + 6, y), (x + 22, y))
        elif kind == "boxes":
            for iy in range(item.height):
                for ix in range(item.width):
                    box = (r.x + ix * TILE + 3, r.y + iy * TILE + 3, TILE - 5, TILE - 5)
                    self.place(surface, 156 if (ix + iy) % 2 else 130, box)
                    pygame.draw.rect(surface, (155, 140, 107), (box[0] + 13, box[1] + 4, 8, 25))
        elif kind == "plant":
            self.place(surface, 316, (r.centerx - 12, r.centery - 8, 24, 24))
            self.place(surface, 134, (r.x + 1, r.y - 2, r.width - 2, r.height - 1), tint=(162, 164, 141), angle=15)
        elif kind == "tree":
            pygame.draw.ellipse(surface, (29, 38, 30), r.move(7, 10))
            pygame.draw.rect(surface, (81, 70, 49), (r.centerx - 6, r.centery - 3, 12, 25))
            for dx, dy, radius in ((-13, 2, 24), (14, 4, 22), (0, -16, 26), (-20, -16, 18)):
                pygame.draw.circle(surface, (46 + dy // 3, 67 + dx // 4, 46), (r.centerx + dx, r.centery + dy), radius)
        elif kind == "bench":
            pygame.draw.rect(surface, (39, 47, 43), r.inflate(-3, -3), border_radius=3)
            for dy in (7, 15, 23):
                pygame.draw.rect(surface, (118, 105, 76), (r.x + 4, r.y + dy, r.width - 8, 5), border_radius=1)
            pygame.draw.line(surface, (156, 143, 111), (r.x + 5, r.y + 6), (r.right - 5, r.y + 6), 2)
        elif kind == "motorbike":
            for x in (r.x+14,r.right-13):
                pygame.draw.ellipse(surface,(24,29,29),(x-9,r.centery-9,18,18))
                pygame.draw.ellipse(surface,(112,121,113),(x-5,r.centery-5,10,10),2)
            pygame.draw.line(surface,(129,138,129),(r.x+14,r.centery),(r.right-13,r.centery),4)
            pygame.draw.ellipse(surface,(68,91,98),r.inflate(-27,-15))
            pygame.draw.rect(surface,(27,38,40),(r.x+17,r.centery-6,24,12),border_radius=4)
            pygame.draw.line(surface,(171,173,155),(r.right-17,r.y+8),(r.right-17,r.bottom-8),2)
            pygame.draw.circle(surface,(213,202,151),(r.right-9,r.centery),3)

    def actor(self, surface, kind, pos, facing, time, moving=False, invulnerable=False,shadow_only=False):
        frame=int(time*(12 if moving else 2))%12
        if kind in ("player","nara"):
            image=self.student_frame(kind,frame if moving else 0,facing)
            p=pygame.Vector2(pos)
            shadow=pygame.transform.smoothscale(self.actor_shadow(image),(36,15))
            surface.blit(shadow,shadow.get_rect(center=p+pygame.Vector2(4,3)))
            if shadow_only:return
            if invulnerable and int(time*12)%2:image=image.copy();image.set_alpha(150)
            surface.blit(image,image.get_rect(midbottom=(round(p.x),round(p.y+5))))
            return
        image=self.monster_frame(kind,frame)
        angle=-math.degrees(math.atan2(facing.y,facing.x))
        rotated=pygame.transform.rotozoom(image,angle,1)
        p=pygame.Vector2(pos)
        shadow=self.actor_shadow(rotated)
        surface.blit(shadow,shadow.get_rect(center=p+pygame.Vector2(3,5)))
        if invulnerable and int(time * 12) % 2:
            rotated = rotated.copy()
            rotated.set_alpha(150)
        surface.blit(rotated, rotated.get_rect(center=p))

    def item_icon(self,kind,size=72):
        key=("item_v15",kind,int(size))
        if key in self.cache:return self.cache[key]
        s=pygame.Surface((220,220),pygame.SRCALPHA)
        ink=(25,35,38);paper=(222,216,184);silver=(154,174,174)
        def box(color,r,radius=0,width=0):pygame.draw.rect(s,color,r,width,border_radius=radius)
        def ellipse(color,r,width=0):pygame.draw.ellipse(s,color,r,width)
        def line(color,points,width=3):pygame.draw.lines(s,color,False,points,width)
        def poly(color,points):pygame.draw.polygon(s,color,points)
        ellipse((5,12,15,65),(35,164,154,25))
        if kind=="bottle":
            poly(ink,[(84,27),(132,27),(132,65),(151,88),(153,174),(141,187),(75,187),(64,174),(66,88),(84,65)])
            poly((50,104,87),[(89,43),(127,43),(127,68),(145,91),(145,171),(137,179),(80,179),(73,171),(74,91),(89,68)])
            line((120,173,141),[(84,85),(80,104),(80,164)],6)
            box((128,145,137),(83,25,51,18),4);line((195,202,182),[(88,29),(129,29)],3)
            poly(paper,[(75,113),(144,109),(144,152),(73,157)])
            box((77,108,95),(87,121,45,5),1);box((133,143,118),(87,133,35,4),1)
        elif kind=="backpack":
            box(ink,(79,29,63,42),11);box((128,99,46),(87,36,47,25),5)
            box((95,75,42),(40,63,141,122),21);box((208,165,61),(46,57,129,118),18)
            box((235,195,81),(51,62,119,47),14);line((145,104,43),[(55,111),(165,111)],4)
            box((183,136,45),(64,122,92,45),8);line((236,203,108),[(72,129),(148,129)],3)
            for x in (65,145):box((104,88,52),(x,100,12,25),3)
            line((241,222,149),[(98,141),(117,148),(104,157)],3)
        elif kind=="medkit":
            box(ink,(74,40,73,39),10);box((141,134,106),(82,47,57,26),5)
            box(ink,(29,67,162,112),17);box((205,202,173),(34,69,151,104),13)
            box((232,226,195),(39,74,141,29),9);line((132,132,107),[(39,107),(179,107)],3)
            box((167,69,57),(97,116,25,44),3);box((167,69,57),(87,126,45,23),3)
            for x in (50,163):box(silver,(x,94,10,20),2)
            line((244,236,205),[(42,154),(42,166),(65,166)],3)
        elif kind=="bandage":
            poly((179,169,136),[(88,122),(132,109),(186,143),(172,179),(109,161)])
            poly(paper,[(89,119),(133,107),(187,139),(172,171),(105,152)])
            ellipse((173,164,134),(32,54,125,108));ellipse((231,221,182),(29,48,125,103))
            ellipse((134,112,92),(61,68,61,58));ellipse((54,58,52),(77,81,31,32))
            ellipse((246,234,200),(40,57,102,86),3)
            for x in (133,144,155):line((191,177,143),[(x,132),(x-8,151)],2)
        elif kind=="energy":
            box(ink,(66,39,89,142),16);box((47,101,99),(72,43,77,129),11)
            box((69,131,124),(77,54,15,110),6)
            ellipse(silver,(68,31,86,26));ellipse((208,214,196),(73,34,76,17));ellipse((66,91,89),(101,37,25,11),3)
            ellipse(silver,(70,162,83,18));line((182,193,170),[(75,164),(145,164)],3)
            poly((235,184,75),[(117,72),(94,111),(110,111),(101,147),(135,100),(117,101)])
            for y in (66,150):line((165,196,177),[(82,y),(140,y)],2)
        elif kind=="tape":
            poly((84,104,83),[(122,130),(170,123),(189,166),(163,180),(132,154)])
            ellipse((54,72,62),(35,52,139,119));ellipse((110,133,102),(33,42,139,117))
            ellipse((186,178,140),(64,64,77,70));ellipse((41,54,46),(77,76,52,47))
            ellipse((151,165,130),(43,49,118,100),3)
            for y in range(142,163,6):line((145,157,123),[(153,y),(171,y-8)],2)
        elif kind=="radio":
            line(silver,[(151,54),(170,16)],6)
            box(ink,(60,48,104,141),16);box((72,103,93),(66,53,92,128),11)
            box((143,177,146),(77,69,70,34),4);line((41,71,62),[(85,81),(135,81)],4)
            for y in range(118,158,9):line((31,54,50),[(79,y),(144,y)],4)
            box(silver,(82,36,25,17),4);pygame.draw.circle(s,(189,142,70),(139,169),7)
        elif kind=="alarm":
            line(silver,[(158,75),(179,26)],5);box(ink,(83,29,54,24),7);box(silver,(89,24,42,16),4)
            box(ink,(44,56,131,126),18);box((193,123,62),(50,60,119,115),14)
            box((219,154,84),(57,68,105,18),7);ellipse(ink,(65,84,91,78));ellipse((203,211,187),(71,90,79,66),2)
            for dx,dy in ((0,-23),(25,0),(0,23),(-25,0)):
                pygame.draw.circle(s,(183,194,176),(110+dx,123+dy),3)
            line(paper,[(110,100),(110,123),(128,130)],4)
            pygame.draw.circle(s,(211,72,56),(148,74),4)
        elif kind=="glow":
            tube=pygame.Surface((220,220),pygame.SRCALPHA)
            pygame.draw.rect(tube,(17,47,46),(92,35,35,144),border_radius=13)
            pygame.draw.rect(tube,(83,187,155),(96,39,27,129),border_radius=10)
            pygame.draw.rect(tube,(180,239,172),(101,46,8,110),border_radius=4)
            pygame.draw.rect(tube,(39,92,86),(92,155,35,25),border_radius=4)
            pygame.draw.circle(tube,silver,(110,184),9,4)
            tube=pygame.transform.rotate(tube,-28);s.blit(tube,tube.get_rect(center=(110,110)))
        elif kind=="fuse":
            box((75,81,73),(85,44,53,135),8);box((207,171,88),(92,66,39,87),4)
            for y in (41,156):box(silver,(79,y,65,25),5)
            line((255,220,131),[(110,75),(100,93),(121,111),(102,132),(113,146)],4)
            line((231,222,177),[(96,73),(96,145)],3)
        elif kind=="key":
            pygame.draw.circle(s,ink,(86,78),43);pygame.draw.circle(s,(199,157,71),(83,75),38)
            pygame.draw.circle(s,(107,90,52),(83,75),18);pygame.draw.circle(s,(46,50,43),(83,75),12)
            poly((213,175,86),[(104,93),(117,89),(174,151),(174,172),(158,169),(154,158),(141,158),(139,144),(128,145)])
            line((239,205,119),[(60,60),(73,48),(91,47)],4)
        elif kind in ("card","photo","folder","phone"):
            if kind=="phone":
                box(ink,(62,26,96,166),14);box((83,113,115),(69,35,82,144),9)
                box((140,175,163),(76,57,68,99),3);line((32,53,57),[(86,83),(127,83)],4)
                line((205,215,194),[(91,39),(129,39)],3);pygame.draw.circle(s,silver,(110,184),3)
            elif kind=="photo":
                box((98,86,59),(37,47,152,145),4);box(paper,(31,40,152,145),4)
                box((66,101,113),(41,50,132,105),2)
                box((130,149,141),(49,67,114,31),2)
                for x in range(57,155,17):box((44,73,89),(x,72,9,16))
                for x,color in ((82,(44,104,136)),(133,(159,78,63))):
                    pygame.draw.circle(s,(180,143,107),(x,111),14);box(color,(x-18,126,36,29),8)
                line((128,130,108),[(66,169),(146,169)],3)
            else:
                box((98,86,59),(38,57,150,129),5);box(paper,(33,48,149,126),5)
                if kind=="folder":box((182,158,98),(40,35,68,27),5)
                box((53,101,124),(39,56,137,24),3)
                pygame.draw.circle(s,(150,123,87),(74,112),15)
                box((52,104,134),(54,129,40,22),7)
                for y,w in ((99,55),(112,45),(129,50),(142,31)):box((142,149,124),(108,y,w,4),1)
        else:
            box(paper,(52,47,120,131),8);box((69,114,135),(62,58,100,26),3)
            for y in (104,123,142):line((134,143,118),[(69,y),(150,y)],4)
        result=pygame.transform.smoothscale(s,(int(size),int(size)));self.cache[key]=result;return result

    def key_item_icon(self,label,size=64):
        text=label.lower()
        kind="fuse" if "sekring" in text else "phone" if "ponsel" in text else "key" if "kunci" in text else "photo" if "foto" in text else "radio" if "radio" in text else "card" if "kartu" in text or "akses" in text else "folder"
        return self.item_icon(kind,size)

    def achievement_badge(self,kind,size=64,unlocked=True):
        key=("badge",kind,int(size),unlocked)
        if key in self.cache:return self.cache[key]
        s=pygame.Surface((160,160),pygame.SRCALPHA)
        pygame.draw.polygon(s,(56,101,113),[(42,75),(76,84),(62,147),(47,130),(29,133)])
        pygame.draw.polygon(s,(43,79,98),[(85,82),(117,72),(135,133),(116,130),(100,148)])
        pygame.draw.circle(s,(38,45,43),(80,67),56)
        pygame.draw.circle(s,(200,165,90),(80,64),52)
        pygame.draw.circle(s,(237,213,145),(80,64),45,3)
        pygame.draw.circle(s,(39,61,62),(80,64),38)
        icon={"heal":"medkit","energy":"energy","alarm":"alarm","glow":"glow","book":"folder","map":"photo","stairs":"card","bag":"backpack"}.get(kind)
        if icon:s.blit(self.item_icon(icon,59),(51,34))
        else:
            points=[]
            for i in range(10):
                angle=-math.pi/2+i*math.pi/5;radius=27 if i%2==0 else 12
                points.append((80+math.cos(angle)*radius,64+math.sin(angle)*radius))
            pygame.draw.polygon(s,(226,213,168),points)
        if not unlocked:s.fill((112,130,132,255),special_flags=pygame.BLEND_RGBA_MULT)
        result=pygame.transform.smoothscale(s,(int(size),int(size)));self.cache[key]=result;return result

    @staticmethod
    def actor_shadow(rotated):
        # Pose is rotated FIRST. A fixed light offset is then applied in world space.
        silhouette=pygame.mask.from_surface(rotated,30).to_surface(setcolor=(7,12,15,125),unsetcolor=(0,0,0,0))
        size=silhouette.get_size()
        soft=pygame.transform.smoothscale(silhouette,(max(1,size[0]//3),max(1,size[1]//3)))
        return pygame.transform.smoothscale(soft,size)

    @staticmethod
    def pose_direction(facing):
        if abs(facing[0])>abs(facing[1]):return "east" if facing[0]>=0 else "west"
        return "south" if facing[1]>=0 else "north"

    @staticmethod
    def torch_grip(facing):
        return pygame.Vector2({"east":(12,-17),"west":(-12,-17),"south":(10,-12),"north":(14,-23)}[Art.pose_direction(facing)])

    def student_frame(self,kind,frame,facing=(1,0),size=(48,64)):
        direction=self.pose_direction(facing);size=tuple(map(int,size))
        original=("student_original_v17",kind,frame,direction)
        key=(*original,size)
        if original not in self.cache:self.cache[original]=student_original(kind,frame,direction)
        if key not in self.cache:self.cache[key]=pygame.transform.smoothscale(self.cache[original],size)
        return self.cache[key]

    def monster_frame(self, kind, frame):
        key = ("monster_rig", kind, frame)
        if key in self.cache:
            return self.cache[key]
        sprite = pygame.Surface((216, 216), pygame.SRCALPHA)
        def p(x, y):
            return (108 + x * 3, 108 + y * 3)
        def line(color, points, width=2):
            pygame.draw.lines(sprite, color, False, [p(x, y) for x, y in points], max(1, round(width * 3)))
        def ellipse(color, rect):
            x,y,w,h = rect
            pygame.draw.ellipse(sprite, color, (108 + x*3,108+y*3,w*3,h*3))
        def polygon(color, points):
            pygame.draw.polygon(sprite, color, [p(x,y) for x,y in points])
        wave = math.sin(frame / 12 * math.tau)
        bone, skin, shadow = (180, 180, 156), (111, 125, 111), (27, 33, 33)
        if kind == "Penjaga":
            polygon(shadow, [(-30,-12),(-12,-9),(5,-10),(13,0),(5,10),(-13,9),(-32,15),(-25,5),(-34,1)])
            for side in (-1,1):
                line((69, 78, 72), [(4,side*8),(-7,side*(21+wave*2)),(17+wave*3,side*28)], 3)
                for finger in range(3):
                    line(bone, [(16+wave*3,side*(26+finger*2)),(23+wave*3,side*(26+finger*2))], .8)
                line((63, 68, 61), [(-13,side*4),(-23,side*(11-wave*2)),(-31,side*19)], 2)
            line((120,128,114), [(-15,0),(-3,-1),(8,0)], 1)
            ellipse((172,177,159),(9,-8,20,16))
            ellipse((35,44,41),(17,-5,8,10))
            line((202,199,174),[(12,-5),(15,-6),(14,4)],1)
            # Juru Malam: a torn red neck ribbon and an ivory, eyeless faceplate.
            polygon((139,55,46),[(7,-9),(11,-8),(9,9),(5,10),(1,21),(-2,18),(5,3)])
            line((222,214,183),[(23,-5),(24,0),(22,5)],2)
            line((56,55,49),[(20,-3),(22,-1),(20,1),(23,4)],1)
        elif kind == "Pendengar":
            ellipse((62,74,67),(-18,-10,30,20))
            for side in (-1,1):
                line(skin,[(0,side*7),(-12,side*(23+wave*2)),(11-wave*3,side*31)],3)
                line(bone,[(10-wave*3,side*30),(20-wave*3,side*33)],1)
                polygon((107,122,105),[(9,side*6),(8,side*20),(18,side*24),(23,side*13)])
                line((53,64,56),[(13,side*11),(14,side*19),(18,side*18)],1)
                for rib in range(4):
                    line((151,158,139),[(-12+rib*5,0),(-10+rib*5,side*7)],1)
            ellipse((181,184,161),(6,-13,22,26))
            ellipse((38,42,35),(19,-8,7,16))
            for y in range(-6,8,3):
                line((212,205,174),[(20,y),(24,y+1)],.7)
            line((102,163,160),[(-11,-7),(-7,0),(-11,7)],2)
            for side in (-1,1):line((189,170,114),[(12,side*15),(17,side*22),(19,side*15)],1)
        else:
            ellipse((58,68,61),(-17,-9,34,18))
            for side in (-1,1):
                for leg in (-1,1):
                    stride = wave * leg * 4
                    line((102,117,100),[(leg*10,side*6),(leg*20+stride,side*20),(leg*29-stride,side*29)],2.4)
                    line(bone,[(leg*27-stride,side*27),(leg*33-stride,side*29)],1)
            for x in range(-12,11,5):
                polygon((157,160,135),[(x,-4),(x+3,0),(x,4),(x-2,0)])
            polygon((178,179,153),[(10,-9),(24,-10),(31,-3),(27,0),(31,4),(24,10),(10,9)])
            ellipse((28,36,31),(21,-7,5,4))
            ellipse((28,36,31),(21,3,5,4))
            line((63,63,51),[(27,-2),(19,0),(27,2)],1)
            line((232,219,188),[(26,-9),(21,-3),(25,1),(20,8)],1)
            line((135,53,47),[(-16,0),(-24,4),(-31,2)],2)
        image = pygame.transform.smoothscale(sprite, (72,72))
        self.cache[key] = image
        return image

    def menu_scene(self,kind="rektorat",look="night"):
        key=("campus_atmosphere_v191",kind,look)
        if key not in self.cache:
            path=ASSET_DIR.parent/"campus"/"photos"/(kind+".jpg")
            self.cache[key]=campus_grade(pygame.image.load(str(path)).convert(),kind,look)
        return self.cache[key]

    def crest(self,size):
        key=("official_its_crest",tuple(size))
        if key not in self.cache:
            base=pygame.image.load(str(ASSET_DIR.parent/"branding"/"its-crest.png")).convert_alpha()
            self.cache[key]=pygame.transform.smoothscale(base,size)
        return self.cache[key]
