"""Repeatable HUD/map captures and route metadata; no new-player assertions."""
import argparse
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
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("build/guidance-review"));args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True);report=[]
    with tempfile.TemporaryDirectory() as folder:
        a=App(folder,audio=False)
        for name,level,cell,stage in (("phone","11:0",(22,41),0),("paired-stairs","11:1",(3,5),9),
                                      ("catalog","22:1",(15,12),10),("campus","campus",(73,50),1)):
            a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[]
            layout=s.get_layout(level);s.switch_level(level,layout.center(cell));s.stage=stage
            s.monsters=[];s.transition=s.message_time=s.encounter_timer=0.;s.elapsed=60.
            a.sync_scene();a.renderer.update_camera(s,snap=True)
            info=a.renderer.guidance(s)
            report.append({"case":name,"level":level,"stage":stage,
                           "goal":list(info[0].point) if info else None,"next":list(info[1]) if info else None,
                           "kind":info[3] if info else None,"interaction":s.interaction()[2] if s.interaction() else None})
            a.map_open=False;a.draw();pygame.image.save(a.screen,str(args.output/(name+".png")))
            a.map_open=True;a.draw();pygame.image.save(a.screen,str(args.output/(name+"-map.png")))
            a.map_open=False
        pygame.quit()
    (args.output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(report)


if __name__=="__main__":main()
