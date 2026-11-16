"""Cosmetic interior dressing plans: wall fixtures and floor wear.

These are pure grid calculations. The renderer draws the plans into the baked world picture and never
writes them back to layout.grid, so navigation, line of sight, puzzles and monster paths are untouched.
"""
import random

WALL_FIXTURES = ("board", "poster", "extinguisher", "vent", "clock")
WEAR_VARIANTS = ("scuff", "stain", "crack")


def is_open(grid, cell, doors=(), skip=()):
    """True for a plain walkable floor cell: inside the grid, empty, not a door and not skipped."""
    x, y = cell
    return 0 <= y < len(grid) and 0 <= x < len(grid[y]) and grid[y][x] == 0 and cell not in doors and cell not in skip


def stair_zone(stairs, tile, reach=2):
    """Cells around every stair point. Stairs are props about 2x3 cells in size that are not part of the grid,
    so dressing has to keep clear of them explicitly."""
    zone = set()
    for _, point in stairs:
        cx, cy = int(point[0] // tile), int(point[1] // tile)
        zone |= {(x, y) for x in range(cx - reach, cx + reach + 1) for y in range(cy - reach, cy + reach + 1)}
    return zone


def wall_fixtures(grid, doors=(), skip=(), density=.16, spacing=3, seed=11):
    """(kind, x, y) for wall cells that face open floor to the south; never on the top border or beside a door."""
    plan, last = [], {}
    for y, row in enumerate(grid):
        if y == 0:
            continue  # the top border carries the room banners
        for x, value in enumerate(row):
            if value != 1 or (x, y) in skip or not is_open(grid, (x, y + 1), doors, skip):
                continue
            if any((x + dx, y + dy) in doors for dx in (-1, 0, 1) for dy in (0, 1)):
                continue
            if x - last.get(y, -spacing) < spacing:
                continue
            rng = random.Random(f"fixture{seed}:{x}:{y}")
            if rng.random() < density:
                plan.append((rng.choice(WALL_FIXTURES), x, y))
                last[y] = x
    return plan


def floor_wear(grid, doors=(), skip=(), density=.09, seed=3):
    """(variant, x, y) scuffs, stains and cracks on plain floor cells."""
    plan = []
    for y, row in enumerate(grid):
        for x in range(len(row)):
            if not is_open(grid, (x, y), doors, skip):
                continue
            rng = random.Random(f"wear{seed}:{x}:{y}")
            if rng.random() < density:
                plan.append((rng.choice(WEAR_VARIANTS), x, y))
    return plan