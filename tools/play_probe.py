"""Deterministic mechanical play probe with all enemies enabled.

The bot knows the map and uses simple shortest routes, so this is NOT a human
playtest, a difficulty estimate, or a measurement of how frightening the game is.
"""
import json
import os
import sys
from pathlib import Path
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from horror.simulation import Session


def play(seed, difficulty):
    session = Session(seed, difficulty)
    steps = 0

    def tick(direction=(0, 0), aim=None, holding=False):
        nonlocal steps
        steps += 1
        if session.threat > .3 and session.bottles and session.throw_cooldown <= 0:
            nearest = min(session.monsters, key=lambda m: m.pos.distance_to(session.player))
            away = session.player - nearest.pos
            if away.length_squared():
                session.throw(session.player + away.normalize() * 280)
        session.update(.03, direction, session.threat > .2, False, holding, aim)
        session.audio_events.clear()

    def walk_to(destination):
        path = session.layout.path(session.layout.tile(session.player), session.layout.tile(destination))
        for cell in path:
            waypoint = pygame.Vector2(session.layout.center(cell))
            for _ in range(110):
                if session.status != "playing":
                    return False
                delta = waypoint - session.player
                if delta.length() < 5:
                    break
                door = session.layout.doors.get(cell)
                if door and not door.opened and delta.length() < 75:
                    session.interact()
                tick(delta, waypoint)
            if session.player.distance_to(waypoint) > 7:
                return False
        return True

    while session.fuses and session.status == "playing":
        target = min(session.fuses, key=lambda p: p.distance_to(session.player))
        if not walk_to(target):
            break
        session.interact_cooldown = 0
        session.interact()
    if session.status == "playing" and session.collected == 2 and walk_to(session.layout.panel):
        for _ in range(110):
            tick(holding=True)
            if session.status != "playing":
                break
        if session.power and session.status == "playing":
            walk_to(session.layout.exit)
    return {"seed": seed, "difficulty": difficulty, "status": session.status,
            "seconds": round(session.elapsed, 2), "fuses": session.collected,
            "reason": session.death_reason, "steps": steps}


if __name__ == "__main__":
    results = [play(seed, difficulty) for difficulty in ("easy", "normal", "hard") for seed in range(10)]
    path = Path("docs/play-probe.json")
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for difficulty in ("easy", "normal", "hard"):
        subset = [r for r in results if r["difficulty"] == difficulty]
        print(difficulty, {status: sum(r["status"] == status for r in subset) for status in ("won", "lost", "playing")})
    print("Probe recorded in", path)
