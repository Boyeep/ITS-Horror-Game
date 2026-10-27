"""Capture real game UI states and measure uncapped rendering, using dummy SDL."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from horror.app import App


def main():
    out = Path("docs/screenshots")
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        app = App(directory)
        def capture(name):
            app.draw()
            pygame.image.save(app.screen, str(out / (name + ".png")))
        capture("menu")
        app.action("help")
        capture("help")
        app.action("back")
        app.action("settings")
        capture("settings")
        app.action("back")
        app.start(42)
        capture("gameplay")
        app.session.health = 38
        app.session.hit_flash = .2
        capture("hurt")
        app.session.hit_flash = 0
        app.session.player = app.session.medkits[0].copy()
        app.renderer.update_camera(app.session, snap=True)
        capture("medkit")
        app.session.interact()
        app.session.use_item("medkit")
        capture("healed")
        app.session.player = pygame.Vector2(app.session.layout.center(app.session.layout.room_center_cell(6)))
        app.renderer.update_camera(app.session, snap=True)
        app.session.facing.update(-.7, -.7)
        app.session.facing.normalize_ip()
        app.session.message_time = 0
        capture("library")
        app.start(42)
        app.map_open = True
        capture("map")
        app.map_open = False
        app.set_mode("pause")
        capture("pause")
        app.previous_mode = "pause"
        app.action("settings")
        capture("settings-paused")
        app.set_mode("playing")
        app.session.elapsed = 25
        # Capture all three human-authored monster sprites in an unobstructed room.
        for i, monster in enumerate(app.session.monsters):
            monster.pos = app.session.player + pygame.Vector2(80 + i * 60, -50)
        app.session.facing.update(1, 0)
        app.session.message_time = 0
        capture("encounter")
        app.session.status, app.session.last_attacker = "lost", "Pendengar"
        app.set_mode("result")
        capture("lost")
        app.session.status = "won"
        app.session.collected = 2
        app.session.elapsed = 381
        capture("won")
        # Real simulation + lighting + all HUD draws, not an empty-window FPS counter.
        app.start(735)
        app.session.elapsed = 25
        start = time.perf_counter()
        frames = 180
        for frame in range(frames):
            app.update(1 / 60, {})
            if app.mode != "playing":
                app.start(735)
            app.draw()
        elapsed = time.perf_counter() - start
        print(f"Render + simulation: {frames} frames / {elapsed:.3f}s = {frames / elapsed:.1f} FPS uncapped, dummy SDL")
        pygame.quit()


if __name__ == "__main__":
    main()
