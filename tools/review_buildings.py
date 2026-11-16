"""Capture authored building/stair geometry, with both bake overviews and lit gameplay."""
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
from horror import architecture


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("build/building-review"));args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True);report=[]
    with tempfile.TemporaryDirectory() as folder:
        a=App(folder,audio=False);a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[]
        for key in ("campus","11:1","22:1","5:2"):
            layout=s.get_layout(key)
            point=layout.spawn if key!="campus" else layout.center((73,50))
            s.switch_level(key,point);s.monsters=[];s.transition=s.message_time=0
            a.renderer.build_world(layout);world=a.renderer.world.copy()
            if key=="campus":crop=pygame.Rect(65*40,34*40,19*40,18*40)
            else:
                crop=world.get_rect();size=getattr(architecture,"STAIR_SIZE",(88,112))
                for direction,point in layout.stairs:
                    image=a.renderer.art.architecture(direction,size)
                    world.blit(image,image.get_rect(center=point))
            name=key.replace(":","-")
            pygame.image.save(world.subsurface(crop),str(args.output/(name+"-overview.png")))
            report.append({"level":key,"size":[layout.width,layout.height],"stairs":[[d,list(p)] for d,p in (layout.stairs if key!="campus" else [])]})
        s.switch_level("11:1",s.get_layout("11:1").center((3,8)));s.facing.update(0,-1)
        s.monsters=[];s.transition=s.message_time=0;a.sync_scene();a.renderer.update_camera(s,snap=True);a.draw()
        pygame.image.save(a.screen,str(args.output/"paired-stairs-gameplay.png"))
        pygame.quit()
    (args.output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(report)


if __name__=="__main__":main()
