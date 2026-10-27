"""Read-only runtime asset audit. Never deletes files or contacts the network."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def audit():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    from horror.audio import Audio
    from horror.render import Renderer
    from horror.world import Layout, Furniture
    from horror.campus import CampusLayout, FLOOR_COUNTS
    from horror.config import ROOM_KINDS
    from horror.floors import BuildingLayout
    from horror.ground_floor import InformatikaGround
    from horror.asset_catalog import TILE_IDS
    from horror.version import VERSION

    assets = ROOT / "assets"
    used = set()
    image_load, sound_load = pygame.image.load, pygame.mixer.Sound

    def record(loader, value, *args, **kwargs):
        if isinstance(value, (str, os.PathLike)):
            path = Path(value).resolve()
            if path.is_relative_to(assets):
                used.add(path)
        return loader(value, *args, **kwargs)

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.display.set_mode((640, 400))
    try:
        with patch.object(pygame.image, "load", lambda v, *a, **k: record(image_load, v, *a, **k)), \
             patch.object(pygame.mixer, "Sound", lambda *a, **k: record(sound_load, *a, **k) if a else sound_load(**k)):
            renderer = Renderer()
            renderer.art.crest((144, 144))
            Audio()
            campus = CampusLayout()
            layouts = [Layout(42), campus, InformatikaGround(campus.room_names, campus.room_kinds)]
            layouts += [BuildingLayout(b, f) for b, count in FLOOR_COUNTS.items() for f in range(1, count)]
            for layout in layouts:
                renderer.build_world(layout)
            # Exercise procedural variants even if this seed does not happen to use them.
            for room in range(len(ROOM_KINDS)):
                for x in range(4):
                    for y in range(4):
                        renderer.art.floor(room, x, y)
            canvas = pygame.Surface((320, 320))
            for kind in ("desk", "computer", "workbench", "table", "sofa", "shelf", "cabinet", "boxes", "plant"):
                renderer.art.furniture(canvas, Furniture(kind, 1, 1, 3, 3))
    finally:
        pygame.quit()

    tile_ids = {int(p.stem.split("_")[1]) for p in used if p.parent.name == "kenney"}
    if tile_ids != set(TILE_IDS):
        raise AssertionError(f"Tile catalog differs from runtime: {tile_ids ^ set(TILE_IDS)}")
    # Match every imported file to its original recorded hash, including preserved licenses.
    for folder in ("kenney", "audio", "story_audio"):
        manifest = json.loads((assets / folder / "manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            path = assets / folder / entry["file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
                raise AssertionError(f"Asset hash mismatch: {path}")
    branding = json.loads((assets / "branding/source.json").read_text(encoding="utf-8"))
    if hashlib.sha256((assets / "branding/its-crest.png").read_bytes()).hexdigest() != branding["sha256"]:
        raise AssertionError("ITS crest differs from its recorded source")
    photos = json.loads((assets / "campus/photos/manifest.json").read_text(encoding="utf-8"))
    for entry in photos:
        path = assets / "campus/photos" / (entry["name"] + ".jpg")
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise AssertionError(f"ITS photo differs from recorded source: {path.name}")
    media = {p.resolve() for p in assets.rglob("*") if p.suffix.lower() in (".png", ".jpg", ".ogg", ".wav", ".mp3")}
    return {"version": VERSION, "coverage": "all layout types, procedural floor/furniture variants, menu photos/crest, every audio bank",
            "loaded_count": len(used), "loaded": sorted(p.relative_to(ROOT).as_posix() for p in used),
            "unused": sorted(p.relative_to(ROOT).as_posix() for p in media - used)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "docs/assets-audit.json")
    args = parser.parse_args()
    report = audit()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Loaded {report['loaded_count']} assets; {len(report['unused'])} unreferenced. Report: {args.report}")
    return bool(report["unused"])


if __name__ == "__main__":
    raise SystemExit(main())
