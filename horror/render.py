"""Procedural environment art, occluded lighting, and a readable diegetic HUD."""
import math
import random
from collections import OrderedDict

import pygame

from .config import (AMBER, HEIGHT, MUTED, PAPER, TEAL, TILE, WIDTH,
                     VIEW_WIDTH, VIEW_HEIGHT, VERSION)
from .rendering.world import WorldRenderer
from .rendering.overlays import OverlayRenderer
from .art import Art
from .pixels import ScaledDraw
from .backdrop import SCENES, NAMES
from .backdrop import CampusAtmosphere,cover_image


class Renderer(WorldRenderer, OverlayRenderer):
    width = WIDTH

    def __init__(self):
        self.ui_target=None;self.ui_layers=set();self.ui_scale=(1.,1.);self.draw=ScaledDraw(self)
        self.fonts = {}
        self.world = None
        self.world_cache=OrderedDict()
        self.current_world_key=None
        self.seed = None
        self.camera = pygame.Vector2()
        self.view_size = pygame.Vector2(VIEW_WIDTH, VIEW_HEIGHT)
        self.zoom = self.width / VIEW_WIDTH
        self.scene = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT)).convert()
        self.lightmap = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT)).convert()
        self.occlusion = pygame.Surface((VIEW_WIDTH, VIEW_HEIGHT)).convert()
        self.torch_layer=pygame.Surface(self.scene.get_size()).convert()
        self.torch_mask=pygame.Surface(self.scene.get_size()).convert()
        self.ambient_glow = self.radial_glow(100, (195, 199, 182))
        self.beam_glow = self.flashlight_cone()
        self.chemical_glow=self.radial_glow(175,(85,211,153))
        self.art = Art()
        self.menu_images=[self.art.menu_scene(kind) for kind in SCENES]
        self.menu_scaled={}
        self.campus_atmosphere=CampusAtmosphere()
        self.route_cache=None
        self.grain = pygame.Surface((self.width, HEIGHT), pygame.SRCALPHA)
        rng = random.Random(17)
        for _ in range(1700):
            x, y = rng.randrange(self.width), rng.randrange(HEIGHT)
            self.grain.set_at((x, y), (150, 175, 160, rng.randrange(2, 5)))

    def resize(self, width):
        self.width = width
        self.view_size.update(round(width / self.zoom), round(HEIGHT/self.zoom))
        size = tuple(map(int, self.view_size))
        self.scene = pygame.Surface(size).convert()
        self.lightmap = pygame.Surface(size).convert()
        self.occlusion = pygame.Surface(size).convert()
        self.torch_layer=pygame.Surface(size).convert();self.torch_mask=pygame.Surface(size).convert()

    @staticmethod
    def flashlight_cone():
        cone=pygame.Surface((340,340)).convert();cone.fill((0,0,0))
        for x in range(340):
            spread=4+x*.55
            along=(1-x/340)**.65*min(1,(x+20)/30)
            for offset in range(-math.ceil(spread),math.ceil(spread)+1):
                y=170+offset
                if not 0<=y<340:continue
                lateral=max(0,1-(offset/spread)**2)**1.5
                value=along*lateral
                cone.set_at((x,y),(round(242*value),round(237*value),round(210*value)))
        return cone

    @staticmethod
    def ray_end(layout,origin,direction,maximum):
        distance=8.
        while distance<maximum:
            if layout.blocks_sight(layout.tile(origin+direction*distance)):
                low,high=max(0,distance-8),distance
                for _ in range(5):
                    mid=(low+high)/2
                    if layout.blocks_sight(layout.tile(origin+direction*mid)):high=mid
                    else:low=mid
                return direction*high
            distance+=8
        return direction*maximum

    def torch_position(self,session):
        hand=session.player+self.art.torch_grip(session.facing)
        lens=hand+session.facing*9
        if session.layout.blocks_sight(session.layout.tile(lens)):lens=session.player.copy()
        return hand,lens

    def bind_ui(self,surface):
        self.ui_target=surface;self.ui_layers={surface}
        self.ui_scale=(surface.get_width()/self.width,surface.get_height()/HEIGHT)
        if self.grain.get_size()!=surface.get_size():
            self.grain=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
            rng=random.Random(17)
            for _ in range(1700):self.grain.set_at((rng.randrange(surface.get_width()),rng.randrange(surface.get_height())),(150,175,160,rng.randrange(2,5)))

    def ui_image(self,surface,image,pos,anchor="topleft"):
        rect=image.get_rect();setattr(rect,anchor,self.draw.point(surface,pos));surface.blit(image,rect);return rect

    def ui_item(self,surface,key,size,pos,anchor="topleft",alpha=255):
        image=self.art.item_icon(key,round(size*min(self.draw.scale(surface))))
        if alpha<255:image=image.copy();image.set_alpha(alpha)
        return self.ui_image(surface,image,pos,anchor)

    def ui_key_item(self,surface,label,size,pos):
        return self.ui_image(surface,self.art.key_item_icon(label,round(size*min(self.draw.scale(surface)))),pos)

    def ui_badge(self,surface,key,size,pos,unlocked=True):
        return self.ui_image(surface,self.art.achievement_badge(key,round(size*min(self.draw.scale(surface))),unlocked),pos)

    @staticmethod
    def radial_glow(radius, color):
        glow = pygame.Surface((radius * 2, radius * 2)).convert()
        glow.fill((0, 0, 0))
        for r in range(radius, 0, -1):
            intensity = (1 - (r / radius) ** 1.65) ** 1.2
            pygame.draw.circle(glow, tuple(int(c * intensity) for c in color), (radius, radius), r)
        return glow

    def font(self, size, bold=False, mono=False, family=None):
        key = size, bold, mono, family
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont(family or ("consolas" if mono else "bahnschrift,arial"), size, bold=bold)
        return self.fonts[key]

    def text(self, surface, text, pos, size=20, color=PAPER, bold=False, align="left", mono=False, family=None):
        image = self.font(round(size*self.draw.scale(surface)[1]), bold, mono, family).render(str(text), True, color)
        rect = image.get_rect()
        setattr(rect, "midtop" if align == "center" else "topright" if align == "right" else "topleft", self.draw.point(surface,pos))
        surface.blit(image, rect)
        return rect

    def centered_text(self,surface,text,rect,size=18,color=PAPER,bold=False):
        target=self.draw.box(surface,rect)
        image=self.font(round(size*self.draw.scale(surface)[1]),bold).render(str(text),True,color)
        ink=image.get_bounding_rect()
        position=(target.centerx-ink.centerx,target.centery-ink.centery)
        surface.blit(image,position)
        return ink.move(position)

    def wrap_lines(self,text,max_width,size=20,family=None):
        lines=[]
        for paragraph in str(text).split("\n"):
            line=""
            for word in paragraph.split():
                trial=f"{line} {word}".strip()
                if self.font(size,family=family).size(trial)[0]>max_width and line:
                    lines.append(line);line=word
                else:line=trial
            lines.append(line)
        return lines

    def wrapped(self, surface, text, pos, max_width, size=20, color=MUTED, spacing=1.4, family=None,visible=None):
        x, y = pos
        for line in self.wrap_lines(text,max_width,size,family):
            shown=line if visible is None else line[:max(0,visible)]
            if shown:self.text(surface,shown,(x,y),size,color,family=family)
            if visible is not None:visible-=len(line)+1
            y+=round(size*spacing)
        return y

    def panel(self,surface, rect, color=(13, 23, 27), border=(48, 65, 66), radius=4):
        self.draw.rect(surface, color, rect, border_radius=radius)
        self.draw.rect(surface, border, rect, 1, border_radius=radius)


    def world_to_screen(self, pos):
        return pygame.Vector2(pos) - self.camera

    def screen_to_world(self, pos):
        return pygame.Vector2(pos[0]*self.view_size.x/self.width,pos[1]*self.view_size.y/HEIGHT)+self.camera

    def update_camera(self, session, dt=0, *, snap=False):
        fit=max(2.,self.width/(session.layout.width*TILE),HEIGHT/(session.layout.height*TILE))
        if abs(fit-self.zoom)>.0001:
            self.zoom=fit;self.resize(self.width)
        target = session.player - self.view_size / 2
        maximum = pygame.Vector2(session.layout.width * TILE, session.layout.height * TILE) - self.view_size
        target.x = max(0, min(maximum.x, target.x))
        target.y = max(0, min(maximum.y, target.y))
        if snap:
            self.camera.update(target)
        else:
            self.camera += (target - self.camera) * (1 - math.exp(-10 * max(0, dt)))
        self.camera.x = max(0, min(maximum.x, self.camera.x))
        self.camera.y = max(0, min(maximum.y, self.camera.y))

    def icon_medkit(self, surface, pos):
        x, y = map(int, pos)
        self.draw.rect(surface, (57, 66, 58), (x - 13, y - 11, 26, 22), border_radius=3)
        self.draw.rect(surface, (203, 203, 179), (x - 12, y - 12, 24, 20), border_radius=3)
        self.draw.rect(surface, (151, 67, 58), (x - 2, y - 8, 4, 12))
        self.draw.rect(surface, (151, 67, 58), (x - 6, y - 4, 12, 4))

    def icon_fuse(self, surface, pos, scale=1, color=AMBER):
        x, y = map(int, pos)
        w, h = int(12 * scale), int(23 * scale)
        self.draw.rect(surface, color, (x - w // 2, y - h // 2, w, h), 2, border_radius=2)
        self.draw.rect(surface, color, (x - w // 2 - 2, y - h // 2 - 2, w + 4, 4))
        self.draw.rect(surface, color, (x - w // 2 - 2, y + h // 2 - 2, w + 4, 4))
        self.draw.line(surface, color, (x - 2, y - 6), (x + 2, y + 5), 2)

    def icon_bottle(self, surface, pos, color=TEAL):
        x, y = map(int, pos)
        self.draw.rect(surface, color, (x - 5, y - 3, 11, 18), 2, border_radius=3)
        self.draw.rect(surface, color, (x - 2, y - 10, 5, 9), 2)
        self.draw.line(surface, color, (x - 1, y - 10), (x + 3, y - 10), 2)

    def draw_monster(self, screen, monster, time):
        p = self.world_to_screen(monster.pos)
        moving = monster.target is not None and monster.wait <= 0 and monster.state not in ("windup", "recovery")
        self.art.actor(screen, monster.kind, p, monster.facing, time, moving)
        if monster.state == "windup":
            self.draw.line(screen, (146,94,83), p + monster.dash * 28, p + monster.dash * 90, 1)

    def draw_player(self, screen, session):
        self.draw_human(screen,"player",session.player,session.facing,session.elapsed,session.moving,session.invulnerable>0)

    def draw_human(self,screen,kind,pos,facing,time,moving=False,invulnerable=False):
        self.art.actor(screen,kind,self.world_to_screen(pos),facing,time,moving,shadow_only=True)
        self.humans.append((kind,pygame.Vector2(pos),pygame.Vector2(facing),time,moving,invulnerable))

    @staticmethod
    def lit_image(target,image,rect,light,minimum=0,local_light=None):
        clipped=rect.clip(target.get_rect())
        if not clipped:return
        local=clipped.move(-rect.x,-rect.y)
        fragment=image.subsurface(local).copy()
        illumination=local_light.subsurface(local) if local_light is not None else light.subsurface(clipped)
        if minimum:
            illumination=illumination.copy();illumination.fill((minimum,minimum,minimum),special_flags=pygame.BLEND_RGB_MAX)
        fragment.blit(illumination,(0,0),special_flags=pygame.BLEND_RGB_MULT)
        target.blit(fragment,clipped)

    def draw_native_entities(self,target,session):
        """Characters/architecture bypass the small world buffer, retaining their linework."""
        sx=target.get_width()/self.scene.get_width();sy=target.get_height()/self.scene.get_height()
        light=pygame.transform.smoothscale(self.lightmap,target.get_size())
        for kind,pos,size in self.native_items:
            p=self.world_to_screen(pos)
            pixels=max(1,round(size*min(sx,sy)))
            image=self.art.item_icon(kind,pixels)
            rect=image.get_rect(center=(round(p.x*sx),round(p.y*sy)))
            if target.get_rect().colliderect(rect):self.lit_image(target,image,rect,light)
        for kind,pos,vertical,swing in self.props:
            w,h=(96,96) if kind=="door" else (88,112)
            anchor=(48,48) if kind=="door" else (44,56)
            p=self.world_to_screen(pos)
            rect=pygame.Rect(round((p.x-anchor[0])*sx),round((p.y-anchor[1])*sy),round(w*sx),round(h*sy))
            if not target.get_rect().colliderect(rect):continue
            image=self.art.architecture(kind,rect.size,vertical,swing)
            illumination=None
            door=session.layout.doors.get(session.layout.tile(pos)) if kind=="door" else None
            if door and not door.opened:
                # A blocked tile has no interior light. Sample its near face, where the beam hits,
                # then project that strip onto the wood rather than sampling behind the blocker.
                delta=session.player-pygame.Vector2(pos)
                if vertical:
                    side=1 if delta.x>=0 else -1
                    strip=pygame.Surface((1,96)).convert()
                    sample_origin=(-round(p.x+side*21),-round(p.y-48))
                else:
                    side=1 if delta.y>=0 else -1
                    strip=pygame.Surface((96,1)).convert()
                    sample_origin=(-round(p.x-48),-round(p.y+side*21))
                strip.blit(self.lightmap,sample_origin)
                if session.flashlight:
                    reflection=pygame.Surface(strip.get_size()).convert()
                    reflection.blit(self.torch_layer,sample_origin)
                    reflection.fill((112,105,89),special_flags=pygame.BLEND_RGB_MULT)
                    strip.blit(reflection,(0,0),special_flags=pygame.BLEND_RGB_ADD)
                # One-pixel source axes caused a native scaler access violation.
                # Duplicate that axis before interpolation, preserving the sampled light.
                strip=pygame.transform.scale(strip,(max(2,strip.get_width()),max(2,strip.get_height())))
                illumination=pygame.transform.smoothscale(strip,rect.size)
            self.lit_image(target,image,rect,light,local_light=illumination)
        for kind,pos,facing,time,moving,invulnerable in sorted(self.humans,key=lambda row:row[1].y):
            p=self.world_to_screen(pos);frame=int(time*(12 if moving else 2))%12 if moving else 0
            image=self.art.student_frame(kind,frame,facing,(round(48*sx),round(64*sy))).copy()
            rect=image.get_rect(midbottom=(round(p.x*sx),round((p.y+5)*sy)))
            if kind=="player":
                hand=p+self.art.torch_grip(facing);tip=hand+facing*9
                def point(v):return (round(v.x*sx-rect.x),round(v.y*sy-rect.y))
                pygame.draw.line(image,(29,39,42),point(hand-facing*3),point(tip),max(1,round(4*sx)))
                pygame.draw.line(image,(144,152,137),point(hand+facing*5),point(tip),max(1,round(3*sx)))
                pygame.draw.circle(image,(238,228,179) if session.flashlight else (75,91,88),point(tip),max(1,round(1.5*sx)))
            if invulnerable and int(time*12)%2:image.set_alpha(150)
            self.lit_image(target,image,rect,light)

    def lighting(self, screen, session, brightness):
        if getattr(session,"cinematic_light",0)>=150:
            self.lightmap.fill((211,208,186))
            screen.blit(self.lightmap,(0,0),special_flags=pygame.BLEND_RGB_MULT)
            return
        origin = self.world_to_screen(session.player)
        self.lightmap.fill((0, 0, 0))
        self.lightmap.blit(self.static_light, -self.camera)
        glows=[item for item in session.placed if item.kind=="glow" and item.pos.distance_to(session.player)<600]
        for item in glows:
            glow=self.chemical_glow
            if item.life<5:
                glow=glow.copy();gain=int(255*item.life/5);glow.fill((gain,gain,gain),special_flags=pygame.BLEND_RGB_MULT)
            self.lightmap.blit(glow,glow.get_rect(center=self.world_to_screen(item.pos)),special_flags=pygame.BLEND_RGB_MAX)
        ambient = self.ambient_glow if session.flashlight else pygame.transform.smoothscale(self.ambient_glow, (140, 140))
        self.lightmap.blit(ambient, ambient.get_rect(center=origin), special_flags=pygame.BLEND_RGB_MAX)
        rays = []
        maximum=355 if session.flashlight else 85
        if glows:maximum=max(maximum,min(450,max(session.player.distance_to(p.pos)+175 for p in glows)))
        for i in range(144):
            angle = math.tau * i / 144
            direction = pygame.Vector2(math.cos(angle), math.sin(angle))
            rays.append(self.ray_end(session.layout,session.player,direction,maximum))
        self.occlusion.fill((0, 0, 0))
        self.draw.polygon(self.occlusion, (255, 255, 255), [origin + ray for ray in rays])
        self.lightmap.blit(self.occlusion, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if session.flashlight:
            _,lens=self.torch_position(session);tip=self.world_to_screen(lens)
            angle=math.atan2(session.facing.y,session.facing.x)
            beam=pygame.transform.rotate(self.beam_glow,-math.degrees(angle))
            self.torch_layer.fill((0,0,0))
            self.torch_layer.blit(beam,beam.get_rect(center=tip+session.facing*170))
            self.torch_mask.fill((0,0,0))
            points=[tip]
            for i in range(65):
                a=angle-math.radians(30)+math.radians(60)*i/64
                direction=pygame.Vector2(math.cos(a),math.sin(a))
                points.append(tip+self.ray_end(session.layout,lens,direction,340))
            self.draw.polygon(self.torch_mask,(255,255,255),points)
            self.torch_layer.blit(self.torch_mask,(0,0),special_flags=pygame.BLEND_RGB_MULT)
            self.torch_layer.blit(self.occlusion,(0,0),special_flags=pygame.BLEND_RGB_MULT)
            self.lightmap.blit(self.torch_layer,(0,0),special_flags=pygame.BLEND_RGB_MAX)
        outside = session.layout.is_outdoor(session.player) if hasattr(session.layout,"is_outdoor") else session.layout.room_at(session.player) in session.layout.outdoors
        base = int((30 if outside else 17) + brightness * 16 + (5 if session.power else 0))
        base=max(base,getattr(session,"cinematic_light",0))
        if getattr(session.layout,"lab_bounds",None) and not outside:base=max(base,46)
        self.lightmap.fill((base, base + 1, base), special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(self.lightmap, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def draw_session(self, screen, session, settings, debug=False, map_open=False, fps=60,cinematic=False):
        key=(type(session.layout).__name__,session.layout.seed)
        if self.seed is None or self.current_world_key!=key or self.world is None:
            if key in self.world_cache:
                self.world,self.static_light=self.world_cache[key];self.seed=session.layout.seed;self.last_room=None
                self.world_cache.move_to_end(key)
            else:
                self.build_world(session.layout)
                self.world_cache[key]=(self.world,self.static_light)
                while len(self.world_cache)>3:self.world_cache.popitem(last=False)
            self.current_world_key=key
        ui_screen = screen
        screen = self.scene
        self.humans=[];self.props=[];self.native_items=[]
        screen.fill((5, 8, 9))
        screen.blit(self.world, -self.camera)
        for cell, door in session.layout.doors.items():
            if door.passage:
                continue
            self.props.append(("door",session.layout.center(cell),door.vertical,door.swing))
        if not getattr(session.layout,"interior",False):
            panel = self.world_to_screen(session.layout.panel)
            self.draw.rect(screen, (21, 32, 35), (panel.x - 23, panel.y - 25, 46, 50), border_radius=3)
            self.draw.rect(screen, TEAL if session.power else AMBER, (panel.x - 19, panel.y - 21, 38, 12), 2)
            for offset in (-9, 9):
                self.icon_fuse(screen, (panel.x + offset, panel.y + 8), .65, TEAL if session.power else (126, 133, 108))
            exit_pos = self.world_to_screen(session.layout.exit)
            self.draw.rect(screen, (27, 69, 56) if session.exit_ready else (65, 58, 43), (exit_pos.x - 28, exit_pos.y - 30, 56, 60), border_radius=3)
        for pos in session.fuses:
            self.native_items.append(("fuse",pos,31))
        for pos in session.pickups:
            self.native_items.append(("bottle",pos,30))
        for pos in session.medkits:
            self.native_items.append(("medkit",pos,36))
        for drop in session.loot:
            p=self.world_to_screen(drop.pos);self.native_items.append((drop.item,drop.pos,32))
            if drop.pos.distance_to(session.player)<160 and session.layout.line_clear(session.player,drop.pos):
                self.draw.circle(screen,(196,207,174),(p.x,p.y-21),1)
        for item in session.placed:
            p=self.world_to_screen(item.pos);self.native_items.append((item.kind,item.pos,30))
            if item.kind=="alarm" and item.delay<=0:
                self.draw.circle(screen,(191,133,69),p,int(18+(2-item.pulse)*9),1)
        if session.mode_key=="story":
            for direction,building,pos,label in session.stair_options():
                self.props.append(("down" if direction=="down" else "up",pos,False,0))
            for key,pos,_ in session.quest_objects():
                p=self.world_to_screen(pos)
                if key=="nara":
                    direction=session.player-pos
                    facing=direction.normalize() if direction.length_squared() else pygame.Vector2(1,0)
                    self.draw_human(screen,"nara",pos,facing,session.elapsed)
                elif key=="phone":
                    display=pygame.Vector2(getattr(session.layout,"phone_display",pos));p=self.world_to_screen(display)
                    self.native_items.append(("phone",display,34))
                elif key in ("note","photo","film","incident","log") or key.startswith("catalog:"):
                    self.native_items.append(("photo" if key=="photo" else "note",pos,38))
                elif key.startswith("generator:"):
                    self.draw.circle(screen,(125,141,132),p,18,3)
                    self.draw.line(screen,(180,147,81),(p.x-17,p.y),(p.x+17,p.y),4)
                    self.draw.line(screen,(180,147,81),(p.x,p.y-17),(p.x,p.y+17),4)
                elif key in ("radio","frequency","antenna","shutdown"):
                    self.draw.rect(screen,(49,65,66),(p.x-24,p.y-15,48,30),border_radius=3)
                    self.draw.rect(screen,(129,162,142),(p.x-17,p.y-10,20,11),1)
                    for i in range(3):self.draw.circle(screen,(165,162,125),(p.x+9+i*4,p.y+6),2)
                    self.draw.line(screen,(166,176,155),(p.x+18,p.y-15),(p.x+27,p.y-46),2)
                elif key=="server":
                    self.draw.rect(screen,(34,47,53),(p.x-20,p.y-26,40,52),border_radius=2)
                    for dy in (-16,-3,10):
                        self.draw.rect(screen,(75,100,103),(p.x-16,p.y+dy,32,8),1)
                        self.draw.circle(screen,TEAL,(p.x+11,p.y+dy+4),2)
                else:
                    self.draw.rect(screen,(63,75,70),(p.x-17,p.y-20,34,40),border_radius=2)
                    self.draw.rect(screen,AMBER,(p.x-11,p.y-13,22,10),1)
                    self.draw.circle(screen,TEAL if key.startswith("terminal:") and int(key.split(":")[1]) in session.terminals else AMBER,(p.x+8,p.y+10),2)
            if session.companion and session.companion["level"]==session.level_key:
                pos=pygame.Vector2(session.companion["pos"]);delta=session.player-pos
                facing=delta.normalize() if delta.length_squared() else session.facing
                facing=getattr(session,"cinematic_nara_facing",facing)
                self.draw_human(screen,"nara",pos,facing,session.elapsed,getattr(session,"cinematic_nara_moving",delta.length()>85))
            elif session.level_key=="campus" and 16<=session.stage<23:
                pos=session.point(19);delta=session.player-pos
                facing=delta.normalize() if delta.length_squared() else pygame.Vector2(1,0)
                self.draw_human(screen,"nara",pos,facing,session.elapsed)
        for noise in session.noises:
            if noise.label in ("botol pecah","alarm saku") and session.layout.line_clear(session.player, noise.pos):
                p = self.world_to_screen(noise.pos)
                self.draw.circle(screen, (112, 173, 160), p, int(18 + noise.age * 40), 1)
        for monster in session.monsters:
            if debug or session.player_can_see(monster):
                self.draw_monster(screen, monster, session.elapsed)
        self.draw_player(screen, session)
        self.lighting(screen, session, settings["brightness"])
        if debug:
            self.draw_debug(screen, session, fps)
        pygame.transform.scale(screen,ui_screen.get_size(),ui_screen)
        self.draw_native_entities(ui_screen,session)
        if cinematic:return
        screen = ui_screen
        if getattr(session,"transition",0)>0:
            fade=pygame.Surface(screen.get_size(),pygame.SRCALPHA);fade.fill((4,9,12,int(160*session.transition/.45)));screen.blit(fade,(0,0))
        reduced=settings.get("reduced_motion",False)
        if session.encounter_timer>0 and not reduced:
            amount=session.encounter_timer/.65
            # Zoom/crop stays filled at every edge; HUD is drawn afterwards.
            pixel_scale=min(self.ui_scale);extra=round(18*amount*pixel_scale)
            enlarged=pygame.transform.scale(screen,(screen.get_width()+extra*2,screen.get_height()+extra*2))
            shake=round(math.sin(session.elapsed*61)*5*amount*pixel_scale)
            screen.blit(enlarged,(-extra+shake,-extra))
        if session.threat>.05 or session.encounter_timer>0:
            strength=max(session.threat*.65,session.encounter_timer/.65)
            pulse=1 if reduced else .85+.15*math.sin(session.elapsed*4)
            shade=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
            self.ui_layers.add(shade)
            for inset in range(0,100,5):
                alpha=int(145*strength*pulse*(1-inset/100)**1.5)
                self.draw.rect(shade,(72,8,12,alpha),(inset,inset,self.width-inset*2,HEIGHT-inset*2),5)
            screen.blit(shade,(0,0))
        screen.blit(self.grain, (0, 0))
        if session.threat > .2:
            self.draw.rect(screen, tuple(int(c * session.threat) for c in (135, 48, 42)), (0, 0, self.width, HEIGHT), 3)
        if session.hit_flash > 0 or session.health <= 30:
            strength = min(1., session.hit_flash / .4) if session.hit_flash > 0 else .25
            self.draw.rect(screen, (int(180 * strength), 39, 34), (3, 3, self.width - 6, HEIGHT - 6), 8)
        self.hud(screen, session)
        if map_open:
            self.draw_map(screen, session)


    @staticmethod
    def backdrop_phase(time):
        time=max(0,time);index=int(time//9)%3;phase=time%9
        return index,(index+1)%3,max(0,min(1,(phase-7.6)/1.4))

    def backdrop(self, screen, time=0,reduced=False):
        w,h=screen.get_size()
        index,next_index,amount=self.backdrop_phase(time)
        if reduced:amount=0
        def scaled(n):
            key=(n,w,h)
            if key not in self.menu_scaled:
                source=self.menu_images[n]
                self.menu_scaled[key]=cover_image(source,(w,h))
                if len(self.menu_scaled)>9:
                    self.menu_scaled={k:v for k,v in self.menu_scaled.items() if k[1:]==(w,h)}
            return self.menu_scaled[key]
        art=scaled(index);size=art.get_size()
        screen.blit(art,((w-size[0])/2,(h-size[1])/2))
        if amount:
            following=scaled(next_index).copy();following.set_alpha(round(amount*255))
            screen.blit(following,((w-following.get_width())/2,(h-following.get_height())/2))
        self.campus_atmosphere.draw(screen,time,reduced)
        fade=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        for x in range(w):
            alpha=int(238*max(0,1-x/(w*.72))**1.4)
            self.draw.line(fade,(5,12,18,alpha),(x,0),(x,h))
        screen.blit(fade,(0,0))
        active=next_index if amount>.5 else index
        self.text(screen,NAMES[SCENES[active]],(self.width-30,26),14,(148,168,165),align="right")
        for i in range(3):self.draw.circle(screen,(190,204,188) if i==active else (62,87,91),(self.width-64+i*17,57),2.5)
        self.text(screen,'v'+VERSION,(self.width-28,HEIGHT-29),11,(92,111,120),align='right')
