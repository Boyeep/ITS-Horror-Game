"""Authored, timed story shots. Rendering uses a copy; gameplay state stays frozen."""
import copy
import math
import pygame
from .config import AMBER,PAPER,MUTED,HEIGHT
from .simulation import Monster
from .backdrop import cover_image
from .speech import visible_count

CUTSCENES={"intro":50.,"library":5.5,"reunion":6.,"shutdown":5.,"ending":8.5}
STAGE_SCENES={2:"library",16:"reunion",21:"shutdown"}
CUES={"intro":((23.5,"step_concrete",.25),(24.3,"step_concrete",.25),(25.1,"step_concrete",.25),
                (26.2,"door_open",.55),(27.9,"door_close",.4),(32.,"panel",.55),
                (35.6,"phone_vibrate",.7),(37.,"phone_vibrate",.5)),
      "library":((2.3,"monster_guard",.22),),"reunion":((1.,"step_concrete",.25),),
      "shutdown":((.3,"power",.35),(2.,"panel",.35)),"ending":((1.,"door_open",.55),(3.,"step_asphalt",.3),(3.6,"step_asphalt",.25))}

# Time, speaker and text are shared by previews and the live opening.
INTRO_LINES=(
    (0.,6.,None,"Besok pukul 08.00, Arga dan Nara harus menunjukkan demo peta suara kampus."),
    (6.,12.,"nara","Peta suaranya sudah jadi. Tinggal cocokkan hasilnya dengan buku log di perpustakaan."),
    (12.,18.,"arga","Kita selesaikan malam ini. Besok jam delapan dosen sudah menunggu."),
    (18.,21.,None,"Beberapa jam kemudian. Demo selesai; buku log belum diambil."),
    (21.,28.,"nara","Aku ambil buku log di arsip lantai dua. Ponselku tinggal dicas. Tunggu aku di sini."),
    (28.,32.,"arga","Sudah setengah jam… Nara belum balik."),
    (43.,47.,"arga","Ini ponsel Nara. Pesan dari nomornya sendiri?"),
    (47.,50.,None,"Periksa ponsel di meja Nara."),
)


def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)


class CinematicRenderer:
    def __init__(self,renderer):self.r=renderer

    def shade(self,s,color,alpha):
        layer=pygame.Surface(s.get_size(),pygame.SRCALPHA);layer.fill((*color,round(max(0,min(255,alpha)))));s.blit(layer,(0,0))

    def world(self,s,session,settings,t,kind):
        r=self.r;v=copy.copy(session)
        v.player=session.player.copy();v.facing=session.facing.copy();v.elapsed=t;v.monsters=[];v.moving=False
        v.threat=v.encounter_timer=v.hit_flash=v.transition=0;v.invulnerable=0;v.health=100
        v.noises=[];v.message_time=0;v.placed=list(session.placed)
        pan=pygame.Vector2()
        if kind=="intro":
            v.layout=session.get_layout("11:0");v.level_key="11:0";v.player=pygame.Vector2(v.layout.spawn)
            state=session.state_for("11:0");v.loot=state["loot"];v.medkits=state["medkits"];v.pickups=[];v.fuses=[];v.placed=[]
            v.stage=0;v.flashlight=t>=34.;v.facing=pygame.Vector2(v.layout.phone_interaction)-v.player;v.facing.normalize_ip()
            v.cinematic_light=175 if t<32 else 18
            if t<28:
                p=pygame.Vector2(v.layout.nara_position)
                if t>=23:
                    route=[p,pygame.Vector2(v.layout.center((20,40))),pygame.Vector2(v.layout.center((20,37))),
                           pygame.Vector2(v.layout.center((17,37))),pygame.Vector2(v.layout.nara_exit)]
                    progress=min(3.999,(t-23)/5*4);index=int(progress);p=route[index].lerp(route[index+1],ease(progress-index))
                    v.cinematic_nara_facing=(route[index+1]-route[index]).normalize()
                    v.layout=copy.copy(v.layout);v.layout.doors=dict(v.layout.doors)
                    door=copy.copy(v.layout.doors[v.layout.lab_door]);door.opened=True;door.swing=1
                    v.layout.doors[v.layout.lab_door]=door
                v.companion={"level":"11:0","pos":list(p)}
                v.cinematic_nara_moving=t>=23
            else:v.companion=None
            pan.update(55 if t<28 else 18,5)
        elif kind=="library":
            v.facing.update(1,0);v.flashlight=True;pan.update(50*ease(t/5.5),-12)
            if t>2.2:
                v.monsters=[Monster("Penjaga",v.player+pygame.Vector2(165,0),pygame.Vector2(-1,0))]
        elif kind=="reunion":
            v.stage=24;v.facing.update(1,0)
            v.player=session.player+pygame.Vector2(-30*(1-ease(t/3)),18)
            v.moving=t<3
            v.companion={"level":v.level_key,"pos":list(session.player+pygame.Vector2(62,8))}
            pan.update(20*ease(t/6),-12)
        elif kind=="shutdown":
            pan.update(15,-40*ease(t/5));v.facing.update(0,-1)
        elif kind=="ending":
            v.player+=pygame.Vector2(-70*ease(t/6),0);v.facing.update(-1,0);v.moving=t<6
            v.companion={"level":v.level_key,"pos":list(v.player+pygame.Vector2(55,15))}
            pan.update(-20*ease(t/8.5),-15)
        camera=r.camera.copy()
        try:
            focus=session.player if settings.get("reduced_motion",False) else v.player+pan
            r.camera.update(focus-r.view_size/2)
            maximum=pygame.Vector2(v.layout.width*40,v.layout.height*40)-r.view_size
            r.camera.x=max(0,min(maximum.x,r.camera.x));r.camera.y=max(0,min(maximum.y,r.camera.y))
            r.draw_session(s,v,settings,cinematic=True)
        finally:r.camera.update(camera)
        if kind=="intro" and 32<=t<34:
            self.shade(s,(3,8,12),195*(1-ease((t-32)/2)))
        if kind=="shutdown":self.shade(s,(2,7,13),90*ease((t-1)/3))
        if kind=="ending":self.shade(s,(182,181,150),80*ease((t-2)/6))

    def phone(self,s,t,reduced=False):
        r=self.r;cx=r.width/2;motion=math.sin(t*38)*1.5 if not reduced and (35.6<t<36.2 or 37<t<37.6) else 0
        s.fill((24,28,29))
        # Desk, abandoned notebook and the lit phone are drawn in native UI pixels.
        r.draw.rect(s,(71,55,40),(cx-600,100,1200,640))
        for i in range(8):r.draw.line(s,(79,61,43),(cx-600,140+i*76),(cx+600,140+i*76),2)
        r.draw.polygon(s,(20,27,29),[(cx+150,209),(cx+429,229),(cx+407,605),(cx+129,586)])
        r.draw.polygon(s,(168,161,135),[(cx+160,199),(cx+413,219),(cx+392,590),(cx+139,571)])
        for i in range(7):r.draw.line(s,(126,127,110),(cx+191,274+i*34),(cx+363,287+i*34))
        x=cx-159+motion;y=137
        r.panel(s,(x-11,y-8,306,527),(13,20,23),(73,86,87),24)
        r.panel(s,(x,y,284,510),(25,43,51),(58,78,83),17)
        r.draw.rect(s,(10,19,23),(x+104,y+13,76,6),border_radius=3)
        r.text(s,"23.47",(x+142,y+58),42,PAPER,align="center")
        if t>35.6:
            r.panel(s,(x+15,y+127,254,295),(46,67,73),(89,108,107),9)
            sx,sy=r.draw.scale(s)
            r.ui_image(s,r.art.face_icon("nara",(round(43*sx),round(59*sy))),(x+29,y+165))
            r.text(s,"Nara",(x+88,y+170),23,PAPER)
            r.text(s,"Sekarang",(x+88,y+204),13,MUTED)
            r.wrapped(s,"Arga, aku masih di perpustakaan. Catatanku di arsip lantai 2. Kalau lampu mati, jangan lewat bundaran.",(x+29,y+248),225,18,PAPER,1.35)
        r.draw.line(s,(139,158,158),(x+100,y+488),(x+184,y+488),3)
        r.draw.lines(s,(155,163,145),False,[(x+142,y+510),(x+142,y+560),(cx+340,y+560),(cx+340,y+480)],4)
        r.text(s,"Ponsel Nara · masih tersambung ke pengisi daya",(cx,705),17,MUTED,align="center")

    def intro_caption(self,s,t):
        r=self.r
        for start,end,speaker,body in INTRO_LINES:
            if start<=t<end:
                width=min(1000,r.width-100);left=(r.width-width)/2
                r.panel(s,(left,HEIGHT-201,width,128),(9,20,26),(60,82,86),5)
                x=left+27
                if speaker:
                    sx,sy=r.draw.scale(s)
                    r.ui_image(s,r.art.face_icon(speaker,(round(63*sx),round(87*sy))),(x,HEIGHT-184))
                    x+=87;r.text(s,speaker.title(),(x,HEIGHT-185),18,AMBER)
                    r.wrapped(s,body,(x,HEIGHT-155),width-145,23,PAPER,1.3,visible=visible_count(body,t-start))
                else:
                    lines=r.wrap_lines(body,width-58,23)
                    for i,line in enumerate(lines):r.text(s,line,(r.width/2,HEIGHT-174+i*31),23,PAPER,align="center")
                break

    def draw(self,s,session,settings):
        r=self.r;scene=session.cutscene;kind=scene["id"];t=scene["time"];duration=CUTSCENES[kind]
        reduced=settings.get("reduced_motion",False)
        if kind=="intro" and t<6:
            image=r.art.menu_scene("informatika",look="dusk")
            bar=round(s.get_height()*66/HEIGHT)
            size=(s.get_width(),s.get_height()-bar*2)
            key=("intro_cover",size)
            if key not in r.art.cache:r.art.cache[key]=cover_image(image,size)
            s.fill((3,8,12));s.blit(r.art.cache[key],(0,bar))
            r.campus_atmosphere.draw(s,t,reduced,dusk=True)
            r.text(s,"18.10 · INFORMATIKA",(r.width/2,84),23,PAPER,align="center")
        elif kind=="intro" and 35<=t<43:self.phone(s,t,reduced)
        else:self.world(s,session,settings,t,kind)
        # A hard cut is softened at the boundary of each opening shot.
        boundaries=(0,6,18,21,28,35,43,duration) if kind=="intro" else (0,duration)
        fade=max(max(0,1-abs(t-boundary)/.38) for boundary in boundaries)
        if fade:self.shade(s,(3,8,12),255*fade)
        r.draw.rect(s,(3,8,12),(0,0,r.width,66));r.draw.rect(s,(3,8,12),(0,HEIGHT-66,r.width,66))
        if kind=="intro":
            if 6<=t<35 or t>=43:
                clock="18.16" if t<18 else "23.10" if t<28 else "23.47"
                r.text(s,clock+" · LAB PROYEK",(55,84),20,PAPER)
            self.intro_caption(s,t)
        caption={"reunion":"Nara.","shutdown":"Sinyal terputus.","ending":"23.48"}.get(kind)
        if caption and 1.4<t<duration-.7:r.text(s,caption,(r.width/2,HEIGHT-110),24,PAPER,align="center")
