"""Issue #17 review prototype. Not imported by the shipped game.

Default: write repeatable comparisons to docs/reviews/minimap.
--interactive [--story]: play a disposable session; I toggles the prototype.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pygame
from pygame import Vector2
from horror.app import App
from horror.config import HEIGHT, TEAL, AMBER, PAPER


class MiniMapPrototype:
    radius=9

    def __init__(self):
        self.enabled=False;self.session=None;self.seen={};self.sample_key=None

    def toggle(self):self.enabled=not self.enabled

    @staticmethod
    def level_key(session):
        return session.mode_key,getattr(session,"level_key",str(session.seed))

    def observe(self,session):
        if not self.enabled:return
        if session is not self.session:
            self.session=session;self.seen={};self.sample_key=None
        layout=session.layout;level=self.level_key(session);cx,cy=layout.tile(session.player)
        stamp=(level,cx,cy,round(session.facing.x*8),round(session.facing.y*8),session.flashlight,layout.revision)
        if stamp==self.sample_key:return
        self.sample_key=stamp;known=self.seen.setdefault(level,{})
        for y in range(max(0,cy-self.radius),min(layout.height,cy+self.radius+1)):
            for x in range(max(0,cx-self.radius),min(layout.width,cx+self.radius+1)):
                point=Vector2(layout.center((x,y)));delta=point-session.player;distance=delta.length()
                nearby=distance<(95 if session.flashlight else 70)
                beam=session.flashlight and 0<distance<355 and delta.normalize().dot(session.facing)>.88
                if not (nearby or beam):continue
                end=point
                if layout.blocks_sight((x,y)) and distance>22:end-=delta.normalize()*22
                if not layout.line_clear(session.player,end):continue
                door=layout.doors.get((x,y))
                known[(x,y)]=3 if door and not door.opened else layout.grid[y][x]

    def panel_bounds(self,app):
        r=app.renderer;p=r.marker_position(app.session.player)
        avoid=[pygame.Rect(p.x-54,p.y-132,108,144),*getattr(r,"marker_boxes",()),*getattr(r,"guidance_avoid",())]
        for x,y in ((app.width-224,HEIGHT-316),(app.width-224,174),(24,HEIGHT-316),(24,174)):
            box=pygame.Rect(x,y,200,196)
            if all(not box.inflate(8,8).colliderect(other) for other in avoid):return box
        return None

    def draw(self,app):
        if (not self.enabled or app.mode!="playing" or app.map_open or getattr(app,"wave_slide",0)>.001
                or getattr(app.session,"modal",False)):return None
        self.observe(app.session);box=self.panel_bounds(app)
        if box is None:return None
        r,s,session=app.renderer,app.screen,app.session
        r.panel(s,box,(6,16,21),(52,79,79),4)
        r.text(s,"I · Peta kecil",(box.x+10,box.y+9),12,TEAL)
        location=session.location if session.mode_key=="story" else "Escape"
        if getattr(session,"level_key",None)=="campus":location="Kampus"
        parts=location.split(" · ")
        if len(parts)>1:location=parts[-1]+" · "+parts[0]
        while len(location)>1 and r.font(11).size(location)[0]>178:location=location[:-2]+"…"
        r.text(s,location,(box.x+10,box.y+28),11,PAPER)
        cx,cy=session.layout.tile(session.player);cell=7
        center=Vector2(box.centerx,box.y+50+(self.radius+.5)*cell)
        known=self.seen[self.level_key(session)]
        colors={0:(24,44,48),1:(89,108,105),2:(65,72,61),3:(179,134,72)}
        for (x,y),value in known.items():
            dx,dy=x-cx,y-cy
            if abs(dx)>self.radius or abs(dy)>self.radius:continue
            r.draw.rect(s,colors.get(value,(24,44,48)),(center.x+dx*cell-cell/2,center.y+dy*cell-cell/2,cell-1,cell-1))
        if session.mode_key=="story":
            info=r.guidance(session)
            if info and session.layout.tile(info[1]) in known:
                x,y=session.layout.tile(info[1]);dx,dy=x-cx,y-cy
                if abs(dx)<=self.radius and abs(dy)<=self.radius:
                    r.draw.circle(s,AMBER,center+Vector2(dx*cell,dy*cell),3,1)
        facing=session.facing;normal=Vector2(-facing.y,facing.x)
        r.draw.polygon(s,TEAL,[center+facing*5,center-facing*3+normal*3,center-facing*3-normal*3])
        return box


def interactive(story):
    with tempfile.TemporaryDirectory(prefix="its-minimap-prototype-") as folder:
        a=App(folder);a.start_story() if story else a.start(42)
        prototype=MiniMapPrototype();clock=pygame.time.Clock()
        print("Prototype only: I toggles minimap; normal controls and M still work. Profile is temporary.")
        while a.running:
            dt=min(.05,clock.tick(60)/1000);events=[]
            for event in pygame.event.get():
                if event.type==pygame.KEYDOWN and event.key==pygame.K_i and not getattr(event,"repeat",False):prototype.toggle()
                else:events.append(event)
            a.events(events);a.update(dt);a.draw();prototype.draw(a);a.present()
        pygame.quit()


def captures(output):
    output.mkdir(parents=True,exist_ok=True);report=[]
    with tempfile.TemporaryDirectory() as folder:
        a=App(folder,audio=False)
        for name,level,cell,stage in (("campus","campus",(73,50),1),("interior","22:1",(6,19),1),("escape",None,None,None)):
            if level is None:a.start(42)
            else:
                a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[]
                layout=s.get_layout(level);s.switch_level(level,layout.center(cell));s.stage=stage
            s=a.session;s.monsters=[];s.transition=s.message_time=s.encounter_timer=0.;s.elapsed=60.
            a.sync_scene();a.renderer.update_camera(s,snap=True);a.map_open=False;a.draw()
            pygame.image.save(a.screen,str(output/(name+"-hud.png")))
            a.map_open=True;a.draw();pygame.image.save(a.screen,str(output/(name+"-map.png")))
            a.map_open=False;a.draw();prototype=MiniMapPrototype();prototype.toggle()
            before=json.dumps(s.snapshot(),sort_keys=True) if s.mode_key=="story" else (list(s.player),s.health,s.elapsed)
            box=prototype.draw(a);pygame.image.save(a.screen,str(output/(name+"-minimap.png")))
            begin=time.perf_counter()
            for _ in range(120):prototype.draw(a)
            cost=(time.perf_counter()-begin)*1000/120
            after=json.dumps(s.snapshot(),sort_keys=True) if s.mode_key=="story" else (list(s.player),s.health,s.elapsed)
            report.append({"case":name,"known_cells":len(prototype.seen[prototype.level_key(s)]),
                           "layout_cells":s.layout.width*s.layout.height,"mean_overlay_ms":round(cost,3),
                           "read_only":before==after,"panel":list(box) if box else None,
                           "scope":"one orientation at spawn; overlay only, no human playtest"})
        pygame.quit()
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(report)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive",action="store_true");parser.add_argument("--story",action="store_true")
    parser.add_argument("--output",type=Path,default=ROOT/"docs/reviews/minimap");args=parser.parse_args()
    if args.interactive:interactive(args.story)
    else:
        os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
        captures(args.output)


if __name__=="__main__":main()
