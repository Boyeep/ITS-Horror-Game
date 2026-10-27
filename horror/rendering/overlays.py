"""Native-resolution objectives, HUD, maps and debugging overlays."""
import math
import pygame
from ..config import AMBER, COLS, HEIGHT, MUTED, PAPER, RED, ROOM_COUNT, ROOM_NAMES, TEAL, TILE
from ..guidance import story_targets, interaction_point


class OverlayRenderer:
    def marker_position(self,pos):
        p=self.world_to_screen(pos)
        return pygame.Vector2(p.x*self.width/self.scene.get_width(),p.y*HEIGHT/self.scene.get_height())

    @staticmethod
    def marker_visible(session,point):
        delta=pygame.Vector2(point)-session.player
        end=pygame.Vector2(point)-delta.normalize()*22 if delta.length_squared() else point
        return session.layout.line_clear(session.player,end)

    def guidance(self,session):
        targets=story_targets(session)
        if not targets:return None
        goal=min(targets,key=lambda t:t.point.distance_squared_to(session.player))
        key=(id(session),session.level_key,session.stage,session.layout.revision,session.layout.tile(session.player),
             goal.key,tuple(goal.point),goal.label)
        if self.route_cache is None or self.route_cache[0]!=key:
            path=session.layout.path(session.layout.tile(session.player),session.layout.tile(goal.point))
            self.route_cache=(key,path)
        path=self.route_cache[1];point=goal.point;hint=goal.label;kind=goal.key
        if not self.marker_visible(session,point):
            for cell in path:
                candidate=pygame.Vector2(session.layout.center(cell))
                if not self.marker_visible(session,candidate):break
                point=candidate
                door=session.layout.doors.get(cell)
                if door and not door.opened:
                    kind="door";hint="Buka pintu";break
                kind="route";hint="Ikuti koridor · "+goal.label
        return goal,point,hint,kind

    def action_marker(self,screen,point,label,available=False,progress=None,avoid=None):
        p=self.marker_position(point)
        if not (22<p.x<self.width-22 and 170<p.y<HEIGHT-92):return False
        color=AMBER if available else (209,202,159)
        self.draw.circle(screen,color,p,13,1)
        for dx,dy in ((-18,-18),(18,-18),(-18,18),(18,18)):
            self.draw.line(screen,color,p+(dx,dy),p+(dx-(6 if dx>0 else -6),dy),2)
        self.draw.line(screen,color,p+(0,-16),p+(0,-28))
        text=label.replace("E  ","").replace("Tahan E  ","")
        if available:text=("Tahan E · " if label.startswith("Tahan E") else "E · ")+text
        width=min(self.width-44,self.font(16).size(text)[0]+28)
        x=max(22,min(self.width-width-22,p.x-width/2));y=p.y-65
        if avoid is not None and pygame.Rect(x,y,width,31).colliderect(avoid):
            y=avoid.top-40 if avoid.top>205 else min(HEIGHT-130,avoid.bottom+12)
        self.panel(screen,(x,y,width,31),(10,22,27),(97,108,87),3)
        self.centered_text(screen,text,(x,y,width,31),16,PAPER)
        if progress is not None:self.draw.rect(screen,TEAL,(x,y+30,width*max(0,min(1,progress)),3))
        return True

    def draw_guidance(self,screen,session):
        info=self.guidance(session)
        if info is None:return False
        goal,point,hint,kind=info
        interaction=session.interaction()
        group=story_targets(session) if session.stage in (10,18) and len(session.quest_objects())>1 else []
        width=min(428,self.width-56)
        title=self.wrap_lines(session.objective,width-32,18)
        detail=[] if point==goal.point else self.wrap_lines(hint,width-32,14)
        if kind in ("building_exit","building_enter","stairs") and point==goal.point:
            detail=self.wrap_lines(hint,width-32,14)
        if interaction:
            focus_point=interaction_point(session,interaction)
            if focus_point is not None and (focus_point.distance_to(point)<60 or focus_point.distance_to(goal.display)<60):
                detail=[]
        if group:detail=self.wrap_lines("Urutan ada pada catatan.",width-32,14)
        height=45+len(title)*24+len(detail)*19
        self.panel(screen,(28,24,width,height),(10,21,26),(48,66,67),4)
        self.text(screen,"TUJUAN",(44,35),11,AMBER)
        for i,line in enumerate(title):self.text(screen,line,(44,55+i*24),18,PAPER)
        for i,line in enumerate(detail):self.text(screen,line,(44,60+len(title)*24+i*19),14,MUTED)
        shown=False;focus=None
        player=self.marker_position(session.player)
        avoid=pygame.Rect(round(player.x-48),round(player.y-120),96,132)
        if interaction:
            focus=interaction_point(session,interaction)
            progress=session.shutdown_progress/5 if interaction[0]=="shutdown" else session.panel_progress/3 if interaction[0]=="panel" else None
            if focus is not None:shown=self.action_marker(screen,focus,interaction[2],True,progress,avoid)
        direct=self.marker_visible(session,goal.point)
        p=self.marker_position(goal.display)
        if group:
            for member in group:
                if self.marker_visible(session,member.point) and (focus is None or focus.distance_to(member.display)>55):
                    self.action_marker(screen,member.display,member.label,avoid=avoid)
        elif direct and (focus is None or focus.distance_to(goal.display)>55):
            self.action_marker(screen,goal.display,"Ponsel Nara" if goal.key=="phone" else goal.label,avoid=avoid)
        if not group and (not direct or not (30<p.x<self.width-30 and 170<p.y<HEIGHT-100)) and not (shown and focus is not None and focus.distance_to(point)<60):
            p=self.marker_position(point);centre=pygame.Vector2(self.width/2,HEIGHT/2)
            direction=p-centre
            if direction.length_squared():
                direction.normalize_ip();normal=pygame.Vector2(-direction.y,direction.x)
                p.x=max(38,min(self.width-38,p.x));p.y=max(190,min(HEIGHT-150,p.y))
                self.draw.circle(screen,(12,27,32),p,16)
                self.draw.polygon(screen,AMBER,[p+direction*10,p-direction*6+normal*6,p-direction*6-normal*6])
        return shown

    def hud(self, screen, session):
        room = session.location if session.mode_key=="story" else session.layout.room_at(session.player)
        if getattr(self, 'last_room', None) != room:
            self.last_room = room
            self.room_until = session.elapsed + 3
        guided=session.mode_key=="story" and not session.modal
        marker_shown=self.draw_guidance(screen,session) if guided else False
        if session.mode_key!="story" and session.elapsed < getattr(self, 'room_until', 0):
            self.text(screen, room if session.mode_key=="story" else session.layout.room_names[room].title(), (28, 28), 17, PAPER)
        color = RED if session.health <= 30 else PAPER
        self.text(screen, 'HP', (28, HEIGHT-79), 11, MUTED, mono=True)
        self.text(screen, str(session.health), (188, HEIGHT-81), 15, color, align='right', mono=True)
        self.draw.rect(screen,(49,60,62),(28,HEIGHT-54,160,3))
        self.draw.rect(screen,color,(28,HEIGHT-54,160*session.health/session.max_health,3))
        if session.stamina<99:
            self.draw.rect(screen,(40,51,54),(28,HEIGHT-42,160,2))
            self.draw.rect(screen,(130,158,158),(28,HEIGHT-42,160*session.stamina/100,2))
        if session.noise_level>.02:
            for i in range(8):
                self.draw.rect(screen,MUTED if i<session.noise_level*8 else (38,46,47),(210+i*6,HEIGHT-54,3,3+i%3*2))
        active=[]
        if session.effects["quiet"]>0:active.append(f"Senyap {math.ceil(session.effects['quiet'])}s")
        if session.effects["energy"]>0:active.append(f"Energi {math.ceil(session.effects['energy'])}s")
        if active:self.text(screen," / ".join(active),(28,HEIGHT-111),13,TEAL)
        self.ui_item(screen,"backpack",32,(self.width-282,HEIGHT-81))
        self.text(screen,f"{session.backpack.used}/12",(self.width-244,HEIGHT-69),15,MUTED,mono=True)
        if session.mode_key!="story" or session.stage in (3,4):
            self.icon_fuse(screen,(self.width-158,HEIGHT-59),.65,PAPER)
            self.text(screen,f'{session.collected}/2',(self.width-141,HEIGHT-69),17,PAPER,mono=True)
        self.icon_bottle(screen,(self.width-69,HEIGHT-60),PAPER)
        self.text(screen,str(session.bottles),(self.width-50,HEIGHT-69),17,PAPER,mono=True)
        interaction = None if getattr(session,"modal",False) else session.interaction()
        if interaction and not marker_shown:
            label=interaction[2]
            width=self.font(16).size(label)[0]+32
            self.panel(screen,(self.width/2-width/2,HEIGHT-106,width,36),(14,23,27),(54,65,67),2)
            self.centered_text(screen,label,(self.width/2-width/2,HEIGHT-106,width,36),16,PAPER)
            if interaction[0]=='panel':
                self.draw.rect(screen,PAPER,(self.width/2-width/2,HEIGHT-72,width*session.panel_progress/3,2))
            elif interaction[0]=='shutdown':
                self.draw.rect(screen,PAPER,(self.width/2-width/2,HEIGHT-72,width*session.shutdown_progress/5,2))
        if session.message_time>0 and session.message!=getattr(session,"objective",None):
            self.text(screen,session.message,(self.width/2,76),17,PAPER,align='center')

    def draw_map(self, screen, session):
        if getattr(session.layout,"interior",False):
            self.draw_floor_map(screen,session)
            return
        if getattr(session.layout,"campus",False):
            self.draw_campus_map(screen,session)
            return
        shade=pygame.Surface(screen.get_size(),pygame.SRCALPHA);shade.fill((3,10,14,235));screen.blit(shade,(0,0))
        width=min(1120,self.width-80);left=(self.width-width)/2
        self.text(screen,'Denah',(left+24,132),30,PAPER)
        cellw=(width-48)/COLS;cellh=86
        nodes={n:(left+24+(n%COLS+.5)*cellw,237+(n//COLS)*cellh) for n in range(ROOM_COUNT)}
        for a,b in session.layout.edges:
            if a in session.visited or b in session.visited:
                self.draw.line(screen,(54,73,76),nodes[a],nodes[b],2)
        for n,pos in nodes.items():
            known=n in session.visited or n in (session.layout.panel_room,session.layout.exit_room)
            rect=pygame.Rect(pos[0]-cellw/2+5,pos[1]-29,cellw-10,58)
            self.panel(screen,rect,(22,34,39) if known else (12,22,27),(40,55,58),2)
            if known:
                self.wrapped(screen,ROOM_NAMES[n].title(),(rect.x+9,rect.y+10),rect.width-18,12,PAPER if n in session.visited else MUTED,1.2)
            else:
                self.text(screen,'·',(pos[0],pos[1]-10),16,MUTED,align='center')
            if n==session.layout.room_at(session.player):
                self.draw.circle(screen,TEAL,(rect.right-7,rect.y+7),3)

    def draw_floor_map(self,screen,session):
        screen.fill((5,13,18));layout=session.layout
        self.text(screen,session.location,(60,60),26,PAPER)
        scale=min(18,(HEIGHT-300)/layout.height,(self.width-120)/layout.width)
        left=(self.width-layout.width*scale)/2;top=130
        for y,row in enumerate(layout.grid):
            for x,value in enumerate(row):
                color=(9,24,24) if (x,y) in getattr(layout,"void_cells",set()) else (68,86,84) if value==1 else (30,49,51) if value==2 else (17,30,35)
                self.draw.rect(screen,color,(left+x*scale,top+y*scale,scale-1,scale-1))
        def p(pos):return pygame.Vector2(left+pos[0]/TILE*scale,top+pos[1]/TILE*scale)
        if layout.building==11:
            for name,pos in layout.labels:
                self.text(screen,name,p(pos),9 if name!="COURTYARD" else 12,MUTED)
        for direction,_,pos,_ in session.stair_options():
            point=p(pos);self.draw.circle(screen,AMBER,point,8,1)
            self.text(screen,"Turun" if direction=="down" else "Naik",(point.x+13,point.y-7),12,AMBER)
        for _,_,pos,_ in session.building_options():
            self.draw.circle(screen,TEAL,p(pos),7,2)
        for _,pos,_ in session.quest_objects():self.draw.circle(screen,AMBER,p(pos),7,2)
        self.draw.circle(screen,TEAL,p(session.player),5)
        self.text(screen,session.objective,(self.width/2,676),17,AMBER,align="center")
        self.text(screen,"Tangga: ganti lantai. Pintu bertanda KELUAR: kembali ke kampus.",(self.width/2,716),14,MUTED,align="center")

    def draw_campus_map(self,screen,session):
        screen.fill((5,13,18))
        left=(self.width-850)/2
        self.text(screen,"Denah kampus",(left,44),28,PAPER)
        scale=5.25
        origin=pygame.Vector2(self.width/2-220,112)
        def point(p):return origin+pygame.Vector2(p)*scale
        for road in session.layout.roads:
            self.draw.lines(screen,(47,67,67),False,[point(p) for p in road],9)
            self.draw.lines(screen,(68,85,80),False,[point(p) for p in road],1)
        self.draw.ellipse(screen,(32,63,70),(*point((2,7)),10*scale,22*scale))
        goals=set(session.goal_rooms)
        important={0:"Graha ITS",1:"Telaga",2:"Sistem Informasi",6:"Gerbang utama",7:"T. Lingkungan",
                   11:"Informatika",15:"Rektorat",18:"Stadion",20:"Taman Alumni",21:"T. Mesin",
                   22:"Perpustakaan",23:"T. Kimia",28:"T. Elektro"}
        occupied=[]
        for n,(x,y) in session.layout.centers.items():
            p=point((x,y));goal=n in goals
            color=AMBER if goal else PAPER if n in session.visited else MUTED
            if n==11:
                for ox,oy,ww,hh in ((66,35,17,5),(78,40,5,5),(66,45,17,5)):
                    q=point((ox,oy));self.draw.rect(screen,(24,38,42),(q.x,q.y,ww*scale,hh*scale))
                    self.draw.rect(screen,color,(q.x,q.y,ww*scale,hh*scale),1)
            else:
                self.draw.rect(screen,(24,38,42),(p.x-12,p.y-8,24,16))
                self.draw.rect(screen,color,(p.x-12,p.y-8,24,16),1)
            if goal:self.draw.circle(screen,AMBER,p,51 if n==11 else 19,1)
        for n in sorted(important,key=lambda k:(k not in goals,k)):
            p=point(session.layout.centers[n]);name=important[n]
            size=self.font(14).size(name)
            preferred_left=n in (0,1,2,6,7,18,20)
            candidates=[]
            for dy in (0,-24,24,-44,44,-64,64):
                for to_left in (preferred_left,not preferred_left):
                    px=p.x-20-size[0] if to_left else p.x+20
                    rect=pygame.Rect(px,p.y-9+dy,*size)
                    if all(not rect.inflate(12,8).colliderect(other) for other in occupied):
                        candidates.append((abs(dy),rect))
            rect=min(candidates,key=lambda pair:pair[0])[1] if candidates else pygame.Rect(p.x+20,p.y-9,*size)
            occupied.append(rect)
            self.draw.line(screen,(51,72,71),p,rect.midright if rect.right<p.x else rect.midleft,1)
            self.text(screen,name,rect.topleft,14,AMBER if n in goals else PAPER if n in session.visited else MUTED)
        player=point(session.player/ TILE)
        self.draw.circle(screen,TEAL,player,5)
        self.draw.line(screen,TEAL,player,player+session.facing*12,2)
        self.text(screen,session.objective,(self.width/2,748),16,AMBER,align="center")
        self.text(screen,"Posisi relatif kampus · interior disederhanakan",(self.width/2,778),11,MUTED,align="center")
        self.text(screen,"U",(left+825,108),13,MUTED,align="center")
        self.draw.line(screen,MUTED,(left+825,165),(left+825,134),1)
        self.draw.lines(screen,MUTED,False,[(left+820,141),(left+825,134),(left+830,141)],1)

    def draw_debug(self, screen, session, fps):
        for monster in session.monsters:
            points = [self.world_to_screen(monster.pos)] + [self.world_to_screen(session.layout.center(c)) for c in monster.path]
            if len(points) > 1:
                self.draw.lines(screen, RED, False, points, 1)
            self.text(screen, monster.kind + " / " + monster.state, self.world_to_screen(monster.pos) + (-35, -38), 12, RED, mono=True)
        self.panel(screen, (24, 190, 310, 100))
        stats = session.layout.stats
        for i, line in enumerate((f"DEBUG  {fps:.0f} FPS / seed {session.seed}", f"SA cost {stats.initial:.2f} -> {stats.best:.2f}",
                                  f"{stats.iterations} iter / {stats.worse_accepted} worse accepted", "F3 tutup / garis merah: path A*")):
            self.text(screen, line, (36, 202 + i * 20), 12, TEAL, mono=True)
