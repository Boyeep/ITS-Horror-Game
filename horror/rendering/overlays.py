"""Native-resolution objectives, HUD, maps and debugging overlays."""
import math
import pygame
from ..config import AMBER, COLS, HEIGHT, MUTED, PAPER, RED, ROOM_COUNT, ROOM_NAMES, TEAL, TILE
from ..guidance import story_targets, interaction_point


class OverlayRenderer:
    def marker_position(self,pos):
        p=self.world_to_screen(pos)
        return pygame.Vector2(p.x*self.width/self.scene.get_width()+getattr(self,"wave_shift",0.),p.y*HEIGHT/self.scene.get_height())

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
        gx=28+round(getattr(self,"wave_shift",0.)*2)
        width=min(428 if gx==28 else 340,self.width-gx-32)
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
        self.panel(screen,(gx,24,width,height),(10,21,26),(48,66,67),4)
        self.text(screen,"TUJUAN",(gx+16,35),11,AMBER)
        for i,line in enumerate(title):self.text(screen,line,(gx+16,55+i*24),18,PAPER)
        for i,line in enumerate(detail):self.text(screen,line,(gx+16,60+len(title)*24+i*19),14,MUTED)
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
            rx_room = 28 + round(getattr(self, "wave_shift", 0.) * 2)
            self.text(screen, room if session.mode_key=="story" else session.layout.room_names[room].title(), (rx_room, 28), 17, PAPER)
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
            label = f"{monster.kind} / {monster.state} T={monster.temp:.2f} {monster.last_decision}"
            self.text(screen, label, self.world_to_screen(monster.pos) + (-35, -38), 11, RED, mono=True)
        self.panel(screen, (24, 190, 330, 100))
        stats = session.layout.stats
        for i, line in enumerate((f"DEBUG  {fps:.0f} FPS / seed {session.seed}", f"SA cost {stats.initial:.2f} -> {stats.best:.2f}",
                                  f"{stats.iterations} iter / {stats.worse_accepted} worse accepted", "F3 tutup / merah: langkah HC+SA")):
            self.text(screen, line, (36, 202 + i * 20), 12, TEAL, mono=True)

    def draw_wave_map(self, screen, session, settings=None, fps=60., slide=1.):
        if slide <= .001:
            self.wave_shift = 0.
            return
        ease = slide * slide * (3. - 2. * slide)
        target_w = round(self.width * .48)
        split_x = max(1, round(target_w * ease))
        offset_x = split_x - target_w
        self.wave_shift = split_x * .5
        sx_scale, _ = self.ui_scale
        shift_px = round(self.wave_shift * sx_scale)
        split_px = max(1, round(split_x * sx_scale))
        if shift_px > 0:
            gameplay = screen.copy()
            screen.blit(gameplay, (shift_px, 0))
        pane = pygame.Surface((split_px, screen.get_height()), pygame.SRCALPHA)
        pane.fill((4, 11, 16, 234))
        screen.blit(pane, (0, 0))
        prev_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(0, 0, split_px, screen.get_height()))

        layout = session.layout
        layout.ensure_hill_map()
        cols, rows = min(31, layout.width), min(27, layout.height)
        ptx, pty = layout.tile(session.player)
        x0 = max(0, min(layout.width - cols, ptx - cols // 2))
        y0 = max(0, min(layout.height - rows, pty - rows // 2))
        reduced = (settings or {}).get("reduced_motion", False)
        theta = -.05 + (0. if reduced else .025 * math.sin(session.elapsed * .42))
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        cos_phi = .76
        scale_xy = min(14.2, (target_w - 92) / max(1, cols + 2))
        scale_z = 32.
        cx_scr, cy_scr = offset_x + target_w * .50, HEIGHT * .54
        px_f, py_f = session.player.x / TILE - .5, session.player.y / TILE - .5
        p_amp = 1.65 * (1.22 if session.last_mode == "sprint" and session.moving else .58 if session.last_mode == "crouch" else .92)
        if session.flashlight:
            p_amp *= 1.06
        p_sig = 2.05 if session.last_mode != "crouch" else 1.4

        def proj(gx, gy, z):
            u, v = gx - (cols - 1) * .5, gy - (rows - 1) * .5
            rx = u * cos_t - v * sin_t
            ry = u * sin_t + v * cos_t
            return (cx_scr + rx * scale_xy, cy_scr + ry * scale_xy * cos_phi - z * scale_z), ry

        def eval_tile(tx, ty):
            if not layout.walkable((tx, ty), True):
                return -.26, 0., 0., 0., True
            b = session.base_score((tx, ty))
            wave = 0. if reduced else .045 * math.sin(session.elapsed * 2.5 + .45 * tx) * math.cos(session.elapsed * 2.0 + .45 * ty)
            sig = max((session.player_signature(m, (tx, ty)) for m in session.monsters), default=0.)
            d_sq = (tx - px_f) ** 2 + (ty - py_f) ** 2
            vis_spike = p_amp * math.exp(-d_sq / (2. * p_sig * p_sig))
            heat = max((m.visit_heat.get((tx, ty), 0.) for m in session.monsters), default=0.)
            t_pull = 0.
            for m in session.monsters:
                if m.target is not None:
                    td = (tx - (m.target.x / TILE - .5)) ** 2 + (ty - (m.target.y / TILE - .5)) ** 2
                    t_pull = max(t_pull, .36 * math.exp(-td / 12.))
            z = max(-.18, min(2.65, b + wave + max(sig, vis_spike * .78) + t_pull - .16 * min(2.5, heat)))
            return z, sig, vis_spike, heat, False

        # Draw 3D base frame axes inside left pane
        base_corners = [proj(0, 0, -.26)[0], proj(cols - 1, 0, -.26)[0],
                        proj(cols - 1, rows - 1, -.26)[0], proj(0, rows - 1, -.26)[0]]
        self.draw.lines(screen, (38, 68, 78), True, base_corners, 1)
        z_axis_bottom, _ = proj(0, rows - 1, -.26)
        z_axis_top, _ = proj(0, rows - 1, 2.1)
        self.draw.line(screen, (52, 96, 110), z_axis_bottom, z_axis_top, 1)
        self.text(screen, "Z", (z_axis_top[0] - 14, z_axis_top[1] - 16), 11, TEAL, mono=True)

        # Precompute grid vertices
        verts = [[None] * cols for _ in range(rows)]
        for iy in range(rows):
            ty = y0 + iy
            for ix in range(cols):
                tx = x0 + ix
                z, sig, vis_spike, heat, is_wall = eval_tile(tx, ty)
                pt, ry = proj(ix, iy, z)
                verts[iy][ix] = (pt, ry, z, sig, vis_spike, heat, is_wall)

        # Painter's algorithm: sort quads back-to-front by average depth ry
        quads = []
        for iy in range(rows - 1):
            for ix in range(cols - 1):
                v00, v10, v11, v01 = verts[iy][ix], verts[iy][ix + 1], verts[iy + 1][ix + 1], verts[iy + 1][ix]
                avg_ry = (v00[1] + v10[1] + v11[1] + v01[1]) * .25
                quads.append((avg_ry, ix, iy, v00, v10, v11, v01))
        quads.sort(key=lambda q: q[0])

        for _, ix, iy, v00, v10, v11, v01 in quads:
            pts = (v00[0], v10[0], v11[0], v01[0])
            walls = v00[6] + v10[6] + v11[6] + v01[6]
            if walls >= 3:
                fill, stroke = (11, 20, 26), (26, 42, 50)
            else:
                avg_z = (v00[2] + v10[2] + v11[2] + v01[2]) * .25
                max_sig = max(v00[3], v10[3], v11[3], v01[3])
                max_vis = max(v00[4], v10[4], v11[4], v01[4])
                max_heat = max(v00[5], v10[5], v11[5], v01[5])
                chk = 6 if (ix + iy) & 1 else 0
                t = max(0., min(1., (avg_z + .1) / 1.4))
                r = round(16 + t * 38 + chk)
                g = round(50 + t * 102 + chk)
                b_col = round(68 + t * 88 + chk)
                stroke = (38, round(112 + t * 75), round(122 + t * 70))
                if max_heat > .22:
                    hk = min(1., max_heat / 2.2)
                    r = round(r * (1 - hk) + 155 * hk)
                    g = round(g * (1 - hk) + 52 * hk)
                    b_col = round(b_col * (1 - hk) + 46 * hk)
                    stroke = (210, 86, 72)
                if max_sig >= .42:
                    sk = min(1., (max_sig - .3) / 1.4)
                    r = round(r * (1 - sk) + 46 * sk)
                    g = round(g * (1 - sk) + 206 * sk)
                    b_col = round(b_col * (1 - sk) + 124 * sk)
                    stroke = (98, 245, 168)
                elif max_vis > .35:
                    vk = min(1., (max_vis - .25) / 1.3)
                    r = round(r * (1 - vk) + 42 * vk)
                    g = round(g * (1 - vk) + 172 * vk)
                    b_col = round(b_col * (1 - vk) + 190 * vk)
                    stroke = (88, 218, 228)
                fill = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b_col)))
            self.draw.polygon(screen, fill, pts)
            self.draw.polygon(screen, stroke, pts, 1)

        # Highlight static ambiguous peaks inside the window
        for px_p, py_p, _, _ in layout.hill_peaks:
            if x0 <= px_p <= x0 + cols - 1 and y0 <= py_p <= y0 + rows - 1:
                z_p, _, _, _, _ = eval_tile(round(px_p), round(py_p))
                pt_p, _ = proj(px_p - x0, py_p - y0, z_p + .05)
                self.draw.circle(screen, AMBER, pt_p, 8, 2)
                self.draw.circle(screen, AMBER, pt_p, 3)

        # Draw Player narrow peak stem & threshold marker
        pgx, pgy = max(0., min(cols - 1., px_f - x0)), max(0., min(rows - 1., py_f - y0))
        pz, psig, _, _, _ = eval_tile(ptx, pty)
        p_base, _ = proj(pgx, pgy, 0.)
        p_thresh, _ = proj(pgx, pgy, max(.42, session.base_score((ptx, pty)) + .42))
        p_top, _ = proj(pgx, pgy, pz + .1)
        p_color = (78, 242, 148) if psig >= .42 else (88, 218, 228)
        self.draw.line(screen, p_color, p_base, p_top, 2)
        self.draw.circle(screen, AMBER, p_thresh, 6, 1)
        self.draw.circle(screen, p_color, p_top, 10, 2)
        self.draw.circle(screen, p_color, p_top, 4)
        self.text(screen, f"PLAYER PEAK ({max(psig, p_amp * .78):.2f})", (p_top[0] + 12, p_top[1] - 9), 11, p_color, mono=True)

        # Draw Monsters, their 4 neighbor probes, visited trails, and target markers on the 3D surface
        rx_mesh = (cols - 1) * .5 * scale_xy + 24.
        ry_mesh = (rows - 1) * .5 * scale_xy * cos_phi + 22.
        for monster in session.monsters:
            mtx, mty = layout.tile(monster.pos)
            raw_gx = monster.pos.x / TILE - .5 - x0
            raw_gy = monster.pos.y / TILE - .5 - y0
            dist_tiles = monster.pos.distance_to(session.player) / TILE
            in_window = 0. <= raw_gx <= cols - 1. and 0. <= raw_gy <= rows - 1.
            if not in_window:
                # Monster is outside the local 3D wave mesh: draw an outer perimeter compass arrow outside the mesh.
                dx_w = monster.pos.x - session.player.x
                dy_w = monster.pos.y - session.player.y
                d_len = max(1., math.hypot(dx_w, dy_w))
                ux, uy = dx_w / d_len, dy_w / d_len
                t_edge = 1. / max(abs(ux) / rx_mesh, abs(uy) / ry_mesh, .001)
                ind_x = max(offset_x + 48., min(offset_x + target_w - 48., cx_scr + ux * t_edge))
                ind_y = max(126., min(HEIGHT - 108., cy_scr + uy * t_edge))
                nx, ny = -uy, ux
                tip = (ind_x + ux * 9., ind_y + uy * 9.)
                b1 = (ind_x - ux * 5. + nx * 5., ind_y - uy * 5. + ny * 5.)
                b2 = (ind_x - ux * 5. - nx * 5., ind_y - uy * 5. - ny * 5.)
                self.draw.circle(screen, (14, 26, 32), (round(ind_x), round(ind_y)), 12)
                self.draw.circle(screen, (195, 84, 72), (round(ind_x), round(ind_y)), 12, 1)
                self.draw.polygon(screen, (225, 96, 82), [tip, b1, b2])
                lbl = f"{monster.kind} ({dist_tiles:.0f}m)"
                tw_lbl = self.font(10, mono=True).size(lbl)[0]
                lx = max(offset_x + 12, min(offset_x + target_w - tw_lbl - 12, round(ind_x - tw_lbl * .5)))
                ly = round(ind_y - 25) if uy <= 0 else round(ind_y + 14)
                self.text(screen, lbl, (lx, ly), 10, (215, 118, 102), mono=True)
                continue
            mgx, mgy = raw_gx, raw_gy
            mz, _, _, _, _ = eval_tile(mtx, mty)
            if len(monster.visited_cells) >= 2:
                trail_pts = []
                for cx_c, cy_c in monster.visited_cells[-8:]:
                    if x0 <= cx_c < x0 + cols and y0 <= cy_c < y0 + rows:
                        tz, _, _, _, _ = eval_tile(cx_c, cy_c)
                        trail_pts.append(proj(cx_c - x0, cy_c - y0, tz + .04)[0])
                if len(trail_pts) >= 2:
                    self.draw.lines(screen, (215, 78, 66), False, trail_pts, 2)
            if monster.target is not None:
                ttx, tty = layout.tile(monster.target)
                tgx = max(0., min(cols - 1., monster.target.x / TILE - .5 - x0))
                tgy = max(0., min(rows - 1., monster.target.y / TILE - .5 - y0))
                tz, _, _, _, _ = eval_tile(ttx, tty)
                t_pt, _ = proj(tgx, tgy, max(0., tz) + .06)
                m_surf, _ = proj(mgx, mgy, max(0., mz) + .06)
                self.draw.line(screen, AMBER, m_surf, t_pt, 1)
                self.draw.circle(screen, AMBER, t_pt, 6, 2)
            probe_col = (255, 145, 45) if "sa_" in monster.last_decision or "restart" in monster.last_decision else (248, 216, 76)
            for nx, ny in layout.neighbors((mtx, mty), True):
                if x0 <= nx < x0 + cols and y0 <= ny < y0 + rows:
                    nz, _, _, _, _ = eval_tile(nx, ny)
                    n_pt, _ = proj(nx - x0, ny - y0, nz + .06)
                    self.draw.circle(screen, probe_col, n_pt, 4)
            m_base, _ = proj(mgx, mgy, 0.)
            m_top, _ = proj(mgx, mgy, max(0., mz) + .14)
            self.draw.line(screen, RED, m_base, m_top, 2)
            self.draw.circle(screen, RED, m_top, 10, 2)
            self.draw.circle(screen, RED, m_top, 4)
            self.text(screen, f"{monster.kind} [{monster.state}] {dist_tiles:.0f}m", (m_top[0] - 44, m_top[1] - 22), 11, RED, mono=True)

        # Top-Left HUD Badge fitted cleanly inside the left pane
        max_sig_now = max((session.neighborhood_signature(m) for m in session.monsters), default=0.)
        detected = max_sig_now >= .42 or any(session.sees_player(m) for m in session.monsters)
        box_left = offset_x + 20
        box_w_left = max(260, target_w - 40)
        self.panel(screen, (box_left, 20, box_w_left, 88), (10, 20, 26), (48, 86, 94), 4)
        self.text(screen, "3D WAVE MAP · HILL CLIMBING + SA", (box_left + 14, 31), 13, AMBER, mono=True)
        self.text(screen, "V: tutup · Puncak Pemain · 4 Tetangga · Dinding (-1.0)", (box_left + 14, 54), 11, PAPER)
        status_txt = f"Postur: {session.last_mode.upper()} | Senter: {'ON' if session.flashlight else 'OFF'} | Sensor: {max_sig_now:.2f}/0.42 ({'TERDETEKSI' if detected else 'AMAN'})"
        self.text(screen, status_txt, (box_left + 14, 76), 11, (82, 238, 148) if detected else TEAL, mono=True)

        screen.set_clip(prev_clip)

        # Vertical split divider line between Left WaveMap and Right Gameplay
        self.draw.line(screen, (20, 44, 52), (split_x - 2, 0), (split_x - 2, HEIGHT), 2)
        self.draw.line(screen, (74, 148, 158), (split_x, 0), (split_x, HEIGHT), 2)

        # Top-Right Simulated Annealing Temperature HUD (slides in from right edge)
        if session.monsters:
            box_w = 336
            box_h = 44 + len(session.monsters) * 66
            rx = self.width - box_w - 24 + round((1. - ease) * (box_w + 32))
            self.panel(screen, (rx, 24, box_w, box_h), (10, 20, 26), (72, 52, 54), 4)
            self.text(screen, "Monster AI: Simulated Annealing", (rx + 16, 36), 14, RED, mono=True)
            for idx, m in enumerate(session.monsters):
                my = 64 + idx * 66
                dist_m = m.pos.distance_to(session.player) / TILE
                self.text(screen, f"{m.kind} · {m.state.upper()} · {dist_m:.0f}m ({m.last_decision})", (rx + 16, my), 12, PAPER, mono=True)
                bar_x, bar_y, bar_w, bar_h = rx + 16, my + 20, box_w - 32, 12
                self.draw.rect(screen, (32, 42, 46), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
                t_val = max(.05, min(1., m.temp))
                bar_col = (round(58 + 188 * t_val), round(148 - 22 * t_val), round(218 - 176 * t_val))
                self.draw.rect(screen, bar_col, (bar_x, bar_y, round(bar_w * t_val), bar_h), border_radius=2)
                self.draw.rect(screen, (92, 108, 112), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=2)
                stat_line = f"Temp={m.temp:.2f}  score={m.last_score:.2f}  SA={m.sa_accepted}  restart={m.restarts}"
                self.text(screen, stat_line, (rx + 16, my + 36), 11, MUTED, mono=True)
