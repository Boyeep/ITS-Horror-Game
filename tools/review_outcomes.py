"""Capture the four result routes with disposable profiles and frozen gameplay."""
import json
import os
from pathlib import Path
import sys
import tempfile
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pygame
from horror.app import App


def main():
    out=ROOT/"docs/reviews/outcomes";out.mkdir(parents=True,exist_ok=True);report=[]
    with tempfile.TemporaryDirectory() as folder:
        a=App(folder,audio=False)
        for story,won in ((True,False),(False,False),(False,True),(True,True)):
            if story:
                a.start_story();a.session.finish_cutscene();a.session.dialogue=[]
            else:a.start(42)
            s=a.session;s.status="won" if won else "lost"
            if not won:s.health=0;s.last_attacker="Penjaga"
            if won and story:
                s.stage=24;s.wrap_ending()
                while s.dialogue:s.next_dialogue()
                s.cutscene["time"]=4.;a.draw()
                pygame.image.save(a.screen,str(out/"story-ending.png"));s.finish_cutscene()
            a.begin_result();name=("story" if story else "escape")+("-won" if won else "-lost")
            before=(list(s.player),s.health,s.elapsed)
            if a.outcome:
                a.outcome.time=3.;a.draw();pygame.image.save(a.screen,str(out/(name+".png")))
                for _ in range(140):a.update(.05,{pygame.K_d:True})
            report.append({"case":name,"mode":a.mode,"status":s.status,
                           "frozen":before==(list(s.player),s.health,s.elapsed),"extra_scene":not(story and won)})
            a.draw();pygame.image.save(a.screen,str(out/(name+"-result.png")))
        pygame.quit()
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(report)


if __name__=="__main__":main()
