"""Capture repeatable atmosphere comparisons and offscreen timings without personal saves.

Use the same script on the base and PR branches, with separate --output paths.
These are rendering probes, not evidence of a new-player playtest.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pygame
from horror.app import App


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build/atmosphere-review")
    parser.add_argument("--frames", type=int, default=120)
    args = parser.parse_args()
    if args.frames < 1:
        parser.error("--frames must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "driver": "SDL dummy", "size": [1280, 800], "frames": args.frames, "captures": [], "timings": []}
    with tempfile.TemporaryDirectory() as folder:
        a = App(folder, audio=False)
        try:
            a.window = pygame.display.set_mode((1280, 800))
            a.resize_canvas()
            for scene in ("campus", "library", "informatika", "escape"):
                if scene == "escape":
                    a.start(42)
                else:
                    a.start_story()
                    s = a.session
                    s.finish_cutscene()
                    s.dialogue = []
                    if scene == "campus":
                        s.switch_level("campus", s.campus.center((74, 42)))
                        s.stage = 1
                    else:
                        level = "22:1" if scene == "library" else "11:1"
                        layout = s.get_layout(level)
                        s.switch_level(level, layout.quest_point(0))
                        s.stage = 1 if scene == "library" else 8
                s = a.session
                s.monsters = []
                s.transition = s.message_time = s.encounter_timer = s.hit_flash = 0.
                s.elapsed = 12.3
                s.moving = False
                s.flashlight = True
                s.facing.update(1, 0)
                a.sync_scene()
                a.renderer.update_camera(s, snap=True)
                for tension, reduced, suffix in ((0., False, "calm"), (1., False, "tense"), (1., True, "reduced")):
                    s.threat = tension
                    a.settings["reduced_motion"] = reduced
                    a.draw()
                    name = f"{scene}-{suffix}.png"
                    pygame.image.save(a.screen, str(args.output / name))
                    report["captures"].append(name)
                a.settings["reduced_motion"] = False
                s.threat = 1.
                for _ in range(10):
                    s.elapsed += 1 / 60
                    a.draw()
                begin = time.perf_counter()
                for _ in range(args.frames):
                    s.elapsed += 1 / 60
                    a.draw()
                elapsed = time.perf_counter() - begin
                report["timings"].append({"scene": scene, "mean_draw_ms": round(elapsed * 1000 / args.frames, 3),
                                           "scope": "draw only; no AI/audio or frame cap"})
        finally:
            pygame.quit()
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
