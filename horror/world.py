"""Seeded connected room graphs, simulated annealing, and grid navigation.

The annealing state contains objective/spawn rooms AND optional corridor edges.
Hard constraints are rejected, not merely traded against a fitness reward.
"""
import heapq
import math
import random
from collections import deque
from dataclasses import dataclass

from .config import (COLS, ROWS, ROOM_W, ROOM_H, TILE, ROOM_COUNT, ROOM_NAMES, ROOM_KINDS,
                     OUTDOOR_KINDS, SPAWN_ROOM, PANEL_ROOM, EXIT_ROOM)

Cell = tuple[int, int]
Edge = tuple[int, int]


def edge(a, b):
    return (min(a, b), max(a, b))


def distances(graph, source):
    out, queue = {source: 0}, deque([source])
    while queue:
        node = queue.popleft()
        for nxt in graph[node]:
            if nxt not in out:
                out[nxt] = out[node] + 1
                queue.append(nxt)
    return out


def graph_from(edges):
    graph = {i: [] for i in range(COLS * ROWS)}
    for a, b in edges:
        graph[a].append(b)
        graph[b].append(a)
    return graph


@dataclass(frozen=True)
class Candidate:
    fuses: tuple[int, int]
    monsters: tuple[int, int, int]
    loops: tuple[Edge, ...]


@dataclass
class Door:
    cell: Cell
    vertical: bool
    opened: bool = False
    passage: bool = False
    swing: float = 0.


@dataclass(frozen=True)
class Furniture:
    kind: str
    x: int
    y: int
    width: int
    height: int


# Authored arrangements keep the central door lanes clear. Furniture footprints
# drive BOTH visual placement and collision/navigation, rather than cosmetic clutter.
ROOM_FURNITURE = [
    [("computer", 2, 2, 2, 1), ("computer", 7, 2, 2, 1), ("computer", 2, 6, 2, 1), ("computer", 7, 6, 2, 1)],
    [("desk", 2, 2, 2, 1), ("desk", 7, 2, 2, 1), ("desk", 2, 6, 2, 1), ("desk", 7, 6, 2, 1)],
    [("workbench", 1, 2, 3, 1), ("cabinet", 7, 2, 2, 1), ("workbench", 7, 6, 3, 1)],
    [("cabinet", 2, 2, 2, 1), ("sofa", 1, 6, 3, 1), ("plant", 8, 6, 1, 1)],
    [("shelf", 2, 1, 2, 2), ("shelf", 7, 1, 2, 2), ("boxes", 2, 6, 2, 1), ("shelf", 7, 6, 3, 1)],
    [("desk", 1, 2, 3, 1), ("cabinet", 7, 2, 2, 1), ("sofa", 7, 6, 3, 1), ("desk", 2, 6, 2, 1)],
    [("table", 2, 1, 2, 2), ("workbench", 7, 6, 3, 1), ("cabinet", 7, 2, 2, 1)],
    [("boxes", 1, 1, 3, 2), ("boxes", 7, 2, 2, 2), ("boxes", 8, 6, 2, 1), ("cabinet", 2, 6, 2, 2)],
    [("sofa", 1, 6, 3, 1), ("sofa", 7, 6, 3, 1), ("table", 7, 2, 2, 1), ("plant", 2, 2, 1, 1)],
    [("shelf", 1, 1, 3, 2), ("shelf", 7, 1, 3, 2), ("table", 2, 6, 2, 2), ("table", 7, 6, 2, 2)],
    [("workbench", 1, 2, 3, 1), ("workbench", 7, 2, 3, 1), ("table", 7, 6, 2, 2)],
    [("table", 7, 1, 3, 2), ("shelf", 2, 2, 2, 1), ("sofa", 1, 6, 3, 1), ("cabinet", 7, 6, 3, 1)],
]


@dataclass
class AnnealingStats:
    initial: float
    best: float
    iterations: int
    accepted: int
    worse_accepted: int
    history: list[float]


class Layout:
    spawn_room, panel_room, exit_room = SPAWN_ROOM, PANEL_ROOM, EXIT_ROOM
    loop_count = 6

    def __init__(self, seed: int, iterations: int = 420):
        self.seed = seed
        self.room_names = list(ROOM_NAMES)
        self.room_kinds = list(ROOM_KINDS)
        rng = random.Random(seed)
        possible = []
        for row in range(ROWS):
            for col in range(COLS):
                n = row * COLS + col
                if col + 1 < COLS:
                    possible.append(edge(n, n + 1))
                if row + 1 < ROWS:
                    possible.append(edge(n, n + COLS))
        # Randomized depth-first spanning tree guarantees a connected foundation.
        visited, stack, tree = {self.spawn_room}, [self.spawn_room], []
        full = graph_from(possible)
        while stack:
            n = stack[-1]
            choices = [v for v in full[n] if v not in visited]
            if not choices:
                stack.pop()
                continue
            nxt = rng.choice(choices)
            tree.append(edge(n, nxt))
            visited.add(nxt)
            stack.append(nxt)
        self.tree = tuple(tree)
        optional = sorted(set(possible) - set(tree))
        candidates = [n for n in range(ROOM_COUNT) if n not in (SPAWN_ROOM, PANEL_ROOM, EXIT_ROOM)
                      and ROOM_KINDS[n] not in OUTDOOR_KINDS]
        loops = tuple(sorted(rng.sample(optional, self.loop_count)))
        graph = graph_from(self.tree + loops)
        safe_monsters = [n for n, d in distances(graph, SPAWN_ROOM).items() if d >= 3]
        current = Candidate(tuple(rng.sample(candidates, 2)),
                            tuple(rng.sample(safe_monsters, 3)), loops)
        current_score = self.evaluate(current)
        initial = current_score
        best, best_score = current, current_score
        temperature, accepted, worse = 2.5, 0, 0
        history = [best_score]
        for step in range(iterations):
            fs, ms, ls = list(current.fuses), list(current.monsters), list(current.loops)
            operation = rng.randrange(3)
            if operation == 0:
                fs[rng.randrange(2)] = rng.choice(candidates)
            elif operation == 1:
                ms[rng.randrange(3)] = rng.randrange(ROOM_COUNT)
            else:
                ls[rng.randrange(self.loop_count)] = rng.choice(optional)
            neighbor = Candidate(tuple(fs), tuple(ms), tuple(sorted(ls)))
            score = self.evaluate(neighbor)
            delta = score - current_score
            if math.isfinite(score) and (delta <= 0 or rng.random() < math.exp(-delta / temperature)):
                accepted += 1
                worse += delta > 0
                current, current_score = neighbor, score
                if score < best_score:
                    best, best_score = neighbor, score
            temperature = max(.025, temperature * .985)
            if (step + 1) % 20 == 0:
                history.append(best_score)
        self.candidate = best
        self.stats = AnnealingStats(initial, best_score, iterations, accepted, worse, history)
        self.edges = self.tree + best.loops
        self.graph = graph_from(self.edges)
        self.width, self.height = COLS * ROOM_W + 1, ROWS * ROOM_H + 1
        self.grid = [[1 for _ in range(self.width)] for _ in range(self.height)]
        self.doors: dict[Cell, Door] = {}
        self.glass: set[Cell] = set()
        self.furniture: list[Furniture] = []
        self.revision = 0
        templates = {"computer": 0, "classroom": 1, "power": 2, "workbench": 2, "archive": 4,
                     "admin": 5, "studio": 6, "storage": 7, "lobby": 8, "library": 9, "lab": 10, "meeting": 11, "canteen": 8}
        self.outdoors = {n for n, kind in enumerate(ROOM_KINDS) if kind in OUTDOOR_KINDS}
        for room in range(ROOM_COUNT):
            x, y = self.room_origin(room)
            for ty in range(y + 1, y + ROOM_H):
                for tx in range(x + 1, x + ROOM_W):
                    self.grid[ty][tx] = 0
            kind = ROOM_KINDS[room]
            furniture = ROOM_FURNITURE[templates[kind]] if kind in templates else [("tree", 1, 1, 2, 2), ("tree", 8, 6, 2, 2), ("bench", 7, 2, 2, 1)]
            for kind, ox, oy, width, height in furniture:
                self.furniture.append(Furniture(kind, x + ox, y + oy, width, height))
                for fy in range(y + oy, y + oy + height):
                    for fx in range(x + ox, x + ox + width):
                        self.grid[fy][fx] = 2
            for _ in range(2 if ROOM_KINDS[room] in ("storage", "power", "workbench") else 0):
                cell = (x + rng.randrange(2, ROOM_W - 1), y + rng.randrange(2, ROOM_H - 1))
                if self.grid[cell[1]][cell[0]] == 0 and cell != self.room_center_cell(room):
                    self.glass.add(cell)
        for a, b in self.edges:
            x, y = self.room_origin(a)
            vertical = b == a + 1
            cell = (x + ROOM_W, y + ROOM_H // 2) if vertical else (x + ROOM_W // 2, y + ROOM_H)
            self.grid[cell[1]][cell[0]] = 0
            passage = a in self.outdoors and b in self.outdoors
            self.doors[cell] = Door(cell, vertical, opened=passage, passage=passage, swing=float(passage))
            if passage:
                for delta in (-1, 1):
                    tx, ty = (cell[0], cell[1] + delta) if vertical else (cell[0] + delta, cell[1])
                    self.grid[ty][tx] = 0
        self.spawn = self.center(self.room_center_cell(SPAWN_ROOM))
        self.panel = self.center(self.room_center_cell(PANEL_ROOM))
        self.exit = self.center((self.width - 2, 2))
        self.fuses = [self.center(self.room_center_cell(n)) for n in best.fuses]
        self.monster_spawns = [self.center(self.room_center_cell(n)) for n in best.monsters]
        self.bottle_spawns = [self.nearest_floor(self.center((self.room_origin(n)[0] + 2,
                                                            self.room_origin(n)[1] + 6))) for n in range(ROOM_COUNT) if n != SPAWN_ROOM]
        self.medkit_spawns = [self.nearest_floor(self.center((self.room_origin(n)[0] + 9,
                                                            self.room_origin(n)[1] + 7))) for n in (SPAWN_ROOM, 6, 17, 23, 0)]
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid generated map {seed}: {errors}")

    def evaluate(self, state):
        if len(set(state.fuses)) != 2 or any(n in (SPAWN_ROOM, PANEL_ROOM, EXIT_ROOM) for n in state.fuses):
            return math.inf
        if len(set(state.monsters)) != 3 or len(set(state.loops)) != self.loop_count:
            return math.inf
        graph = graph_from(self.tree + state.loops)
        ds = {n: distances(graph, n) for n in range(ROOM_COUNT)}
        if any(ds[SPAWN_ROOM][n] < 3 for n in state.monsters):
            return math.inf
        a, b = state.fuses
        route = min(ds[SPAWN_ROOM][a] + ds[a][b] + ds[b][PANEL_ROOM], ds[SPAWN_ROOM][b] + ds[b][a] + ds[a][PANEL_ROOM]) + ds[PANEL_ROOM][EXIT_ROOM]
        # Lower is better: target exploration length, separated objectives, safe spawn.
        return (abs(route - 19) * 1.4 + max(0, 5 - ds[a][b]) * 2.0
                + sum(max(0, 5 - ds[SPAWN_ROOM][m]) for m in state.monsters) * .6
                + sum(max(0, 2 - ds[u][v]) for u, v in ((state.monsters[0], state.monsters[1]),
                                                         (state.monsters[1], state.monsters[2]))) * .4)

    @staticmethod
    def room_origin(room):
        return (room % COLS * ROOM_W, room // COLS * ROOM_H)

    @classmethod
    def room_center_cell(cls, room):
        x, y = cls.room_origin(room)
        return (x + ROOM_W // 2, y + ROOM_H // 2)

    @staticmethod
    def center(cell):
        return ((cell[0] + .5) * TILE, (cell[1] + .5) * TILE)

    @staticmethod
    def tile(pos):
        return (int(pos[0] // TILE), int(pos[1] // TILE))

    @staticmethod
    def room_at(pos):
        return max(0, min(ROWS - 1, int(pos[1] // (ROOM_H * TILE)))) * COLS + max(0, min(COLS - 1, int(pos[0] // (ROOM_W * TILE))))

    def surface_at(self, position):
        room = self.room_at(position)
        kind = ROOM_KINDS[room]
        x, y = self.tile(position)
        if kind == "garden" and abs(x % ROOM_W - ROOM_W // 2) > 1 and abs(y % ROOM_H - ROOM_H // 2) > 1:
            return "grass"
        return "wood" if kind in ("admin", "library", "meeting", "archive") else "concrete"

    def walkable(self, cell, doors_open=False):
        x, y = cell
        if not (0 <= x < self.width and 0 <= y < self.height) or self.grid[y][x] != 0:
            return False
        door = self.doors.get(cell)
        return doors_open or door is None or door.opened

    def blocks_sight(self, cell):
        # Desks block movement, not eye-level sight. Walls and shut doors occlude.
        x, y = cell
        return (not (0 <= x < self.width and 0 <= y < self.height)
                or self.grid[y][x] == 1 or (cell in self.doors and not self.doors[cell].opened))

    def neighbors(self, cell, doors_open=False):
        x, y = cell
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if self.walkable(nxt, doors_open):
                yield nxt

    def reachable(self, start):
        visited, queue = {start}, deque([start])
        while queue:
            for nxt in self.neighbors(queue.popleft(), True):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        return visited

    def validate(self):
        reachable = self.reachable(self.tile(self.spawn))
        errors = []
        for name, positions in (("objective", self.fuses + [self.panel, self.exit]),
                                ("monster", self.monster_spawns), ("bottle", self.bottle_spawns),
                                ("medkit", self.medkit_spawns)):
            if any(self.tile(p) not in reachable for p in positions):
                errors.append(f"unreachable {name}")
        if len(reachable) != sum(row.count(0) for row in self.grid):
            errors.append("disconnected floor")
        if self.stats.best > self.stats.initial:
            errors.append("annealing regressed")
        return errors

    def path(self, start, goal):
        if not self.walkable(goal, True):
            return []
        queue = [(0, start)]
        parent, costs = {start: None}, {start: 0}
        while queue:
            _, cur = heapq.heappop(queue)
            if cur == goal:
                out = []
                while cur != start:
                    out.append(cur)
                    cur = parent[cur]
                return out[::-1]
            for nxt in self.neighbors(cur, True):
                cost = costs[cur] + (2 if nxt in self.doors and not self.doors[nxt].opened else 1)
                if cost < costs.get(nxt, math.inf):
                    costs[nxt], parent[nxt] = cost, cur
                    h = abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1])
                    heapq.heappush(queue, (cost + h, nxt))
        return []

    def line_clear(self, a, b):
        distance = math.dist(a, b)
        steps = max(1, int(distance / 10))
        for i in range(1, steps + 1):
            t = i / steps
            if self.blocks_sight(self.tile((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))):
                return False
        return True

    def sound_field(self, position, budget):
        start = self.tile(position)
        queue, costs = [(0, start)], {start: 0}
        while queue:
            cost, cur = heapq.heappop(queue)
            if cost > costs[cur]:
                continue
            for nxt in self.neighbors(cur, True):
                added = 3.5 if nxt in self.doors and not self.doors[nxt].opened else 1
                total = cost + added
                if total <= budget and total < costs.get(nxt, math.inf):
                    costs[nxt] = total
                    heapq.heappush(queue, (total, nxt))
        return costs

    def toggle_door(self, cell):
        self.doors[cell].opened = not self.doors[cell].opened
        self.revision += 1

    def nearest_floor(self, position):
        cell = self.tile(position)
        if self.walkable(cell, True):
            return self.center(cell)
        candidates = [(math.dist(position, self.center((x, y))), (x, y))
                      for y in range(self.height) for x in range(self.width) if self.walkable((x, y), True)]
        return self.center(min(candidates)[1])
