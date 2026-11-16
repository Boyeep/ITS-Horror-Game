"""Bounded captures of reading, reveal and gameplay handoff using a temporary profile."""
import json
import os
from pathlib import Path
import sys
import tempfile
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pygame
from horror.app import App
from horror.cinematics import CUTSCENES


def main():
    out=ROOT/"docs/reviews/library";out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        a=App(folder,audio=False);a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[]
        s.use_stairs("enter",22);s.stage=1;s.player=s.point(22,floor=1);s.elapsed=30.
        s.handle_quest("note");a.sync_scene();a.renderer.update_camera(s,snap=True)
        def capture(name):
            a.draw();pygame.image.save(a.screen,str(out/(name+".png")))
        capture("note")
        while s.dialogue:s.next_dialogue()
        for seconds,name in ((1.5,"anticipation"),(4.5,"reveal"),(7.8,"threat"),(10.5,"route")):
            s.cutscene["time"]=seconds;capture(name)
        a.settings["reduced_motion"]=True;capture("reduced")
        s.finish_cutscene();capture("handoff")
        report={"duration":CUTSCENES["library"],"planned":s.library_reveal,
                "runtime":list(s.monsters[0].pos),"reaction_seconds":s.monsters[0].wait,
                "search_pressure_seconds":s.library_pressure,"journal":s.journal,"monsters":len(s.monsters),
                "scope":"scripted presentation captures, not a human playtest"}
        (out/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print(report);pygame.quit()


if __name__=="__main__":main()
