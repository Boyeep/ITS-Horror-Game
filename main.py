"""Run the game, validate maps, or capture deterministic review screenshots."""
import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Setelah Jam Malam — ITS Horror Game")
    parser.add_argument("--seed", type=int, help="Start a repeatable map immediately")
    parser.add_argument("--story", action="store_true", help="Start the story campaign")
    parser.add_argument("--load-slot", choices=("auto","1","2","3"), help="Load a story save slot")
    parser.add_argument("--difficulty", choices=("easy", "normal", "hard"))
    parser.add_argument("--validate", type=int, metavar="COUNT", help="Validate COUNT map seeds, without opening a window")
    parser.add_argument("--headless", action="store_true", help="Use SDL dummy video/audio for automated verification")
    parser.add_argument("--frames", type=int, help="Exit after a bounded number of frames")
    parser.add_argument("--screenshot", type=Path, help="Save the initial screen as a PNG")
    parser.add_argument("--data-dir", type=Path, help="Override the user settings directory")
    args = parser.parse_args()
    if args.validate is not None:
        import time
        from horror.world import Layout
        start = time.perf_counter()
        improved = 0
        for seed in range(args.validate):
            layout = Layout(seed)
            assert not layout.validate(), f"Invalid seed {seed}"
            improved += layout.stats.best < layout.stats.initial
        print(f"PASS: {args.validate} connected, completable maps; SA improved {improved}; {time.perf_counter() - start:.2f}s")
        return
    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    from horror.app import App
    app = App(args.data_dir)
    if args.difficulty:
        app.settings["difficulty"] = args.difficulty
        app.draw()
    if args.load_slot:
        data=app.save_store.read(args.load_slot)
        if data is None:parser.error("Save slot is empty or invalid")
        app.start_story(data=data)
        app.draw()
        app.present()
    elif args.story:
        app.start_story()
        app.draw()
        app.present()
    elif args.seed is not None:
        app.start(args.seed)
        app.draw()
        app.present()
    if args.screenshot:
        import pygame
        args.screenshot.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(app.screen, str(args.screenshot))
    app.run(args.frames)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        import tempfile
        path = Path(tempfile.gettempdir()) / "ITS-Horror-Game-error.log"
        path.write_text(traceback.format_exc(), encoding="utf-8")
        # Windowed builds have no console; show a useful, persistent error location.
        if os.name == "nt" and not getattr(__import__("sys"), "stderr", None):
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Game gagal dijalankan. Detail tersimpan di:\n{path}", "Setelah Jam Malam", 0x10)
        raise
