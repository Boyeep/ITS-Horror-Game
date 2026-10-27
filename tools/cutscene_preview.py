"""Render actual opening frames; --assemble uses Pillow only for the preview GIF."""
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FRAMES=ROOT/"build/cutscene-preview"


def main():
    if "--assemble" in sys.argv:
        from PIL import Image
        frames=[Image.open(path).convert("RGB") for path in sorted(FRAMES.glob("frame-*.png"))]
        destination=ROOT/"docs/screenshots/opening-preview.gif"
        frames[0].save(destination,save_all=True,append_images=frames[1:],duration=200,loop=0,optimize=True,disposal=2)
        for frame in frames:frame.close()
        print({"gif":str(destination.relative_to(ROOT)),"frames":len(frames),"bytes":destination.stat().st_size})
        return
    import tempfile
    os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
    sys.path.insert(0,str(ROOT))
    import pygame
    from horror.app import App
    from horror.cinematics import CUTSCENES
    FRAMES.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        a=App(folder,audio=False);a.start_story()
        for i in range(round((CUTSCENES["intro"]+1.6)*5)):
            a.draw();frame=pygame.transform.smoothscale(a.screen,(720,450))
            pygame.image.save(frame,str(FRAMES/f"frame-{i:03}.png"))
            for _ in range(4):a.update(.05,{})
        assert a.session.cutscene is None
        (ROOT/"docs/cutscene-review.json").write_text(json.dumps({"opening_seconds":CUTSCENES["intro"],"frames":i+1,"sample_fps":5,"handoff":True,"player_control":not a.session.modal},indent=2),encoding="utf-8")
        pygame.quit()
    print({"frames":i+1,"folder":str(FRAMES.relative_to(ROOT))})


if __name__=="__main__":main()
