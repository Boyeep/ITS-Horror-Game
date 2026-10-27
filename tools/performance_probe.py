"""Bounded offscreen frame timings, including the new native-size UI."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from horror.app import App
from horror.config import VERSION

reports=[]
with tempfile.TemporaryDirectory() as folder:
    a=App(folder,audio=False)
    for mode in ("escape","ground"):
        if mode=="escape":a.start(42)
        else:a.start_story();a.session.finish_cutscene();a.session.transition=0
        for size in ((1280,800),(1920,1200)):
            a.window=pygame.display.set_mode(size);a.resize_canvas();a.draw()
            begin=time.perf_counter()
            for _ in range(180):a.update(1/60,{});a.draw();a.present()
            elapsed=time.perf_counter()-begin
            reports.append({"version":VERSION,"mode":mode,"pixels":size,"frames":180,"uncapped_fps":round(180/elapsed,1),"ai":len(a.session.monsters),"driver":"SDL dummy"})
    pygame.quit()
Path("docs/performance-review.json").write_text(json.dumps(reports,indent=2),encoding="utf-8")
print(reports)
