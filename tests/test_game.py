"""Behavioral checks: reachability, sensory fairness, real movement and UI flows."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import tempfile
import unittest
from pathlib import Path

import pygame

from horror.app import App
from horror.simulation import (
    LOCAL_SEARCH_BUDGET,
    PLATEAU_EPS,
    SIGNATURE_THRESHOLD,
    TEMP_REHEAT,
    Session,
)
from horror.story import StorySession
from horror.world import Layout
from horror.config import ROOM_COUNT, ROOM_W, ROOM_H, TILE, COLS, ROWS, MONSTER_RADIUS
from horror.audio import Audio


class GenerationTests(unittest.TestCase):
    def test_one_hundred_seeds_valid_and_optimizer_keeps_best(self):
        improvements = 0
        for seed in range(100):
            layout = Layout(seed)
            self.assertEqual(layout.validate(), [], f"seed {seed}")
            self.assertLessEqual(layout.stats.best, layout.stats.initial)
            improvements += layout.stats.best < layout.stats.initial
            for position in layout.fuses + [layout.panel, layout.exit]:
                route = layout.path(layout.tile(layout.spawn), layout.tile(position))
                self.assertTrue(route, f"no route seed {seed}")
        self.assertGreater(improvements, 50)

    def test_seed_reproduces_layout(self):
        a, b = Layout(735), Layout(735)
        self.assertEqual(a.edges, b.edges)
        self.assertEqual(a.candidate, b.candidate)
        self.assertEqual(a.grid, b.grid)
        self.assertEqual(a.glass, b.glass)
        self.assertNotEqual(a.candidate, Layout(736).candidate)


class GameplayTests(unittest.TestCase):
    def test_difficulty_changes_actual_hearing(self):
        states = []
        for difficulty in ("easy", "hard"):
            session = Session(42, difficulty)
            session.elapsed = 20
            listener = session.monsters[1]
            listener.pos = pygame.Vector2(session.layout.center((9, 22)))
            session.emit_noise(session.layout.center((5, 22)), 3, "langkah")
            states.append(listener.state)
        self.assertEqual(states, ["patrol", "investigate"])

    def test_closed_door_attenuates_sound(self):
        layout = Layout(42)
        cell, door = next(iter(layout.doors.items()))
        x, y = cell
        a, b = ((x - 1, y), (x + 1, y)) if door.vertical else ((x, y - 1), (x, y + 1))
        self.assertNotIn(b, layout.sound_field(layout.center(a), 2.5))
        layout.toggle_door(cell)
        self.assertIn(b, layout.sound_field(layout.center(a), 2.5))

    def test_collision_does_not_tunnel_through_boundary(self):
        session = Session(12)
        session.player.update(60, 900)
        session.move(session.player, pygame.Vector2(-300, 0), 11)
        self.assertGreaterEqual(session.player.x, 51)
        self.assertTrue(session.can_stand(session.player, 11))

    def test_monsters_follow_long_routes_and_open_doors(self):
        for seed in (0, 1, 2, 4, 5, 6):
            session = Session(seed)
            session.layout.path = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("A* path must not be used by monster"))
            monster = session.monsters[0]
            monster.pos = pygame.Vector2(session.layout.spawn)
            monster.target = pygame.Vector2(session.layout.exit)
            for _ in range(1800):
                monster.wait = max(0, monster.wait - .05)
                if monster.wait <= 0:
                    session._follow(monster, 142, .05)
                if monster.pos.distance_to(monster.target) < 10:
                    break
            self.assertLess(monster.pos.distance_to(monster.target), 10, f"stuck seed {seed}: {monster.pos}")
            self.assertTrue(any(door.opened for door in session.layout.doors.values()))

    def test_local_search_opens_and_crosses_doors_from_both_sides(self):
        for seed in (1, 42):
            for vertical in (False, True):
                for side in (-1, 1):
                    for queued_current_cell in (False, True):
                        with self.subTest(seed=seed, vertical=vertical, side=side,
                                          queued_current_cell=queued_current_cell):
                            session = Session(seed)
                            session.layout.path = lambda *args, **kwargs: self.fail("Monster used A*")
                            cell = next(c for c, d in session.layout.doors.items()
                                        if not d.passage and d.vertical == vertical)
                            door = session.layout.doors[cell]
                            door.opened = False
                            center = pygame.Vector2(session.layout.center(cell))
                            normal = pygame.Vector2(1, 0) if vertical else pygame.Vector2(0, 1)
                            monster = session.monsters[0]
                            monster.pos = center + normal * side * TILE
                            monster.facing = -normal * side
                            monster.target = center - normal * side * TILE
                            monster.state = "search"
                            monster.path = [session.layout.tile(monster.pos)] if queued_current_cell else []
                            before = monster.pos.copy()

                            session._follow(monster, 142, .05)
                            self.assertTrue(door.opened)
                            self.assertEqual(monster.pos, before)
                            self.assertGreater(monster.wait, 0)
                            self.assertEqual(monster.trace[-1]["to"], cell)
                            for _ in range(120):
                                monster.wait = max(0, monster.wait - .05)
                                if monster.wait <= 0:
                                    session._follow(monster, 142, .05)
                                self.assertTrue(session.can_stand(monster.pos, MONSTER_RADIUS))
                                if monster.pos.distance_to(monster.target) < 4:
                                    break
                            self.assertLess(monster.pos.distance_to(monster.target), 4)
                            self.assertTrue(all(abs(step["to"][0] - step["from"][0]) +
                                                abs(step["to"][1] - step["from"][1]) == 1
                                                for step in monster.trace))

    def test_base_hill_landscape_and_floor_walls(self):
        a, b = Layout(735), Layout(735)
        self.assertEqual(a.base_hill, b.base_hill)
        self.assertEqual(a.hill_peaks, b.hill_peaks)
        self.assertGreaterEqual(len(a.hill_peaks), 4)
        self.assertTrue(a.floor_cells)
        for y in range(a.height):
            for x in range(a.width):
                h = a.hill_height((x, y))
                if a.walkable((x, y), True):
                    self.assertGreaterEqual(h, 0.)
                    self.assertLessEqual(h, 2.0)
                else:
                    self.assertEqual(h, -1.)
        s1, s2 = Session(735), Session(735)
        sample = a.floor_cells[10]
        self.assertEqual(s1.base_score(sample), s2.base_score(sample))
        self.assertEqual(s1.base_score((0, 0)), -1.)

    def test_player_signature_peak_and_sensor_rules(self):
        session = Session(42)
        guard, listener, ambusher = session.monsters
        player_cell = session.layout.tile(session.player)
        # Grace period suppresses player signature peak.
        session.elapsed = 1.0
        self.assertEqual(session.player_signature(guard, player_cell), 0.)
        session.elapsed = 20.0
        # Visible player produces a steep narrow peak above SIGNATURE_THRESHOLD.
        guard.pos = session.player - pygame.Vector2(TILE * 2, 0)
        guard.facing = pygame.Vector2(1, 0)
        self.assertTrue(session.sees_player(guard))
        peak = session.player_signature(guard, player_cell)
        far = session.player_signature(guard, (player_cell[0] + 8, player_cell[1] + 8))
        self.assertGreater(peak, SIGNATURE_THRESHOLD * 3)
        self.assertGreater(peak, far * 5)
        self.assertGreaterEqual(session.neighborhood_signature(guard), SIGNATURE_THRESHOLD)
        # Crouch vs Sprint modifies signature amplitude and spread when not in direct sight.
        listener.pos = session.player + pygame.Vector2(TILE * 2, 0)
        listener.facing = pygame.Vector2(1, 0)
        self.assertFalse(session.sees_player(listener))
        session.moving, session.last_mode = True, "sprint"
        sprint_sig = session.neighborhood_signature(listener)
        session.moving, session.last_mode = True, "crouch"
        crouch_sig = session.neighborhood_signature(listener)
        self.assertGreater(sprint_sig, crouch_sig)
        # Distant hidden player has zero signature (no global coordinate leak).
        ambusher.pos = pygame.Vector2(session.layout.exit)
        self.assertEqual(session.neighborhood_signature(ambusher), 0.)

    def test_monster_detect_chase_lose_reheat_explore_and_redetect(self):
        session = Session(42)
        session.elapsed = 20.0
        monster = session.monsters[0]
        monster.pos = session.player - pygame.Vector2(TILE * 2, 0)
        monster.facing = pygame.Vector2(1, 0)
        monster.temp = .65
        # 1. Detect player signature peak and enter chase, cooling temperature.
        session._update_monster(monster, .05)
        self.assertEqual(monster.state, "chase")
        self.assertIsNone(monster.explore_target)
        self.assertLessEqual(monster.temp, .16)
        # 2. Player moves far away out of sight; monster loses track and reaches local optimum at last known peak.
        last_known = monster.target.copy()
        session.player = pygame.Vector2(session.layout.exit)
        for _ in range(90):
            session._update_monster(monster, .05)
            if monster.explore_target is not None and monster.restarts >= 1:
                break
        self.assertIn(monster.state, ("search", "patrol"))
        self.assertNotEqual(monster.target, session.player)
        self.assertGreaterEqual(monster.temp, TEMP_REHEAT * .5)
        self.assertTrue(monster.restarts >= 1 or monster.sa_accepted >= 1 or monster.explore_target is not None)
        # Force an active random floor exploration target and verify immediate re-detection when player returns.
        monster.explore_target = session._random_floor_target(monster)
        monster.target = monster.explore_target.copy()
        monster.state = "patrol"
        session.player = monster.pos + monster.facing * TILE
        session.moving, session.last_mode = True, "sprint"
        self.assertGreaterEqual(session.neighborhood_signature(monster), SIGNATURE_THRESHOLD)
        session._update_monster(monster, .05)
        self.assertIsNone(monster.explore_target)
        self.assertEqual(monster.target, session.player)
        self.assertIn(monster.state, ("chase", "search"))
        self.assertNotEqual(last_known, monster.target)

    def test_local_search_scenarios_u_wall_plateau_and_spanning_tree_limit(self):
        # Scenario A: U-shaped wall dead-end pocket recovery without oscillation freeze.
        session = Session(42)
        session.elapsed = 20.0
        session.player = pygame.Vector2(session.layout.exit)
        monster = session.monsters[0]
        cx, cy = session.layout.room_center_cell(session.layout.spawn_room)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                session.layout.grid[cy + dy][cx + dx] = 0
        for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0)):
            session.layout.grid[cy + dy][cx + dx] = 1
        session.layout.ensure_hill_map(force=True)
        monster.pos = pygame.Vector2(session.layout.center((cx, cy)))
        monster.target = pygame.Vector2(session.layout.center((cx, cy - 3)))
        monster.state = "search"
        visited = set()
        for _ in range(90):
            monster.wait = 0
            session._follow(monster, 142, .05)
            visited.add(session.layout.tile(monster.pos))
        # Monster escapes the dead-end pocket (cx, cy) downward and routes around the U-wall.
        self.assertIn((cx, cy + 1), visited)
        self.assertGreaterEqual(len(visited), 4)
        # Scenario B: Flat plateau triggers SA reheat and downhill/plateau exploration.
        flat_session = Session(42)
        flat_session.layout.ensure_hill_map()
        flat_session.layout._base_hill = tuple(
            tuple(.5 if v >= 0 else -1. for v in row) for row in flat_session.layout.base_hill
        )
        flat_session.hill_phase = (0., 0., 0.)
        m_flat = flat_session.monsters[0]
        m_flat.target = None
        m_flat.temp = .1
        flat_session._local_search_step(m_flat)
        self.assertGreaterEqual(m_flat.temp, TEMP_REHEAT)
        self.assertIn(m_flat.last_decision, ("plateau", "sa_downhill", "sa_uphill", "local_optimum"))
        # Scenario C: Documented spanning-tree wall barrier in seed 3 recovers via SA/random floor without freezing.
        barrier_session = Session(3)
        barrier_session.elapsed = 20.0
        m_bar = barrier_session.monsters[0]
        m_bar.pos = pygame.Vector2(barrier_session.layout.center(barrier_session.layout.room_center_cell(11)))
        m_bar.state = "patrol"
        m_bar.explore_target = pygame.Vector2(barrier_session.layout.exit)
        m_bar.target = m_bar.explore_target.copy()
        visited_rooms = set()
        for _ in range(250):
            barrier_session._update_monster(m_bar, .05)
            visited_rooms.add(barrier_session.layout.room_at(m_bar.pos))
        self.assertGreaterEqual(m_bar.sa_accepted, 1)
        self.assertGreaterEqual(len(visited_rooms), 2)

    def test_local_search_seed_trace_determinism_and_story_mode_integration(self):
        def run_trace(seed):
            s = Session(seed, "normal")
            s.elapsed = 20.0
            m = s.monsters[0]
            for _ in range(60):
                s._update_monster(m, .05)
            return list(m.trace), tuple( round(v, 3) for v in (m.pos.x, m.pos.y, m.temp) ), m.sa_accepted, m.restarts

        t1, p1, sa1, r1 = run_trace(108)
        t2, p2, sa2, r2 = run_trace(108)
        self.assertEqual(t1, t2)
        self.assertEqual(p1, p2)
        self.assertEqual(sa1, sa2)
        self.assertEqual(r1, r2)
        self.assertTrue(t1)
        self.assertLessEqual(len(t1), 40)
        # Story mode integration check: monsters on story maps use HC+SA and build valid base hills.
        story = StorySession("normal")
        story.spawn_encounter("Penjaga")
        story.elapsed = 20.0
        self.assertTrue(story.monsters)
        self.assertTrue(story.layout.base_hill)
        sm = story.monsters[0]
        sm.wait = 0
        for _ in range(25):
            story._update_monster(sm, .05)
        self.assertTrue(sm.trace)
        self.assertLessEqual(len(sm.path), 1)

    def test_hidden_player_does_not_update_monster_target(self):
        session = Session(42)
        session.elapsed = 20
        monster = session.monsters[0]
        monster.pos = pygame.Vector2(session.layout.center(session.layout.room_center_cell(0)))
        monster.target = monster.pos + pygame.Vector2(100, 0)
        known = monster.target.copy()
        monster.state, monster.memory = "chase", 7
        self.assertFalse(session.sees_player(monster))
        session._update_monster(monster, .05)
        self.assertEqual(monster.target, known)
        self.assertEqual(monster.state, "search")

    def test_bottle_redirects_listener_to_impact_not_player(self):
        session = Session(42)
        session.elapsed = 20
        monster = session.monsters[1]
        monster.pos = session.player + pygame.Vector2(100, 0)
        session.throw(session.player + pygame.Vector2(250, 0))
        self.assertEqual(session.bottles, 3)
        self.assertEqual(monster.state, "investigate")
        self.assertGreater(monster.target.distance_to(session.player), 100)

    def test_door_cannot_close_on_actor(self):
        session = Session(42)
        cell = next(cell for cell,door in session.layout.doors.items() if not door.passage)
        session.layout.toggle_door(cell)
        session.player = pygame.Vector2(session.layout.center(cell))
        session.interact()
        self.assertTrue(session.layout.doors[cell].opened)

    def test_open_door_offcenter_and_corner_turn_passage_both_directions(self):
        from horror.story import StorySession
        for seed in (1, 7, 19, 42, 73):
            session = Session(seed)
            session.monsters = []
            h_cell = next(c for c, d in session.layout.doors.items() if not d.passage and not d.vertical)
            v_cell = next(c for c, d in session.layout.doors.items() if not d.passage and d.vertical)
            for cell in (h_cell, v_cell):
                door = session.layout.doors[cell]
                door.opened = True
                door.swing = 1.
                center = pygame.Vector2(session.layout.center(cell))
                for side in (-1, 1):
                    for offset in (-17, 0, 17, 22):
                        if door.vertical:
                            session.player = center + pygame.Vector2(side * 42, offset)
                            move_dir = (-side, 0)
                        else:
                            session.player = center + pygame.Vector2(offset, side * 42)
                            move_dir = (0, -side)
                        self.assertTrue(session.can_stand(session.player, 11))
                        for _ in range(24):
                            session.update(.03, move_dir, sprint=True)
                        passed = (session.player.x - center.x) * (-side) > 18 if door.vertical else (session.player.y - center.y) * (-side) > 18
                        self.assertTrue(passed, f"seed {seed} cell {cell} side {side} offset {offset} pos {session.player}")
        story = StorySession()
        story.finish_cutscene()
        story.monsters = []
        for level_key, door_cells in (("11:0", ((17, 35), (48, 24))), ("11:1", ((5, 18), (32, 18), (19, 38))), ("22:1", ((8, 11), (15, 6)))):
            story.switch_level(level_key, story.get_layout(level_key).spawn)
            story.transition = 0
            for cell in door_cells:
                door = story.layout.doors[cell]
                door.opened = True
                door.swing = 1.
                center = pygame.Vector2(story.layout.center(cell))
                for side in (-1, 1):
                    if door.vertical:
                        story.player = center + pygame.Vector2(side * 38, 16)
                        move_dir = (-side, 0)
                    else:
                        story.player = center + pygame.Vector2(16, side * 38)
                        move_dir = (0, -side)
                    for _ in range(22):
                        story.update(.03, move_dir, sprint=True)
                    passed = (story.player.x - center.x) * (-side) > 15 if door.vertical else (story.player.y - center.y) * (-side) > 15
                    self.assertTrue(passed, f"story {level_key} door {cell} side {side}")

    def test_door_prompt_e_range_and_diagonal_two_sided_interaction(self):
        from horror.story import StorySession
        session = Session(42)
        session.monsters = []
        h_cell = next(c for c, d in session.layout.doors.items() if not d.passage and not d.vertical)
        v_cell = next(c for c, d in session.layout.doors.items() if not d.passage and d.vertical)
        for cell in (h_cell, v_cell):
            door = session.layout.doors[cell]
            center = pygame.Vector2(session.layout.center(cell))
            for side in (-1, 1):
                # Diagonal approach along wall and extended range up to ~82px
                for lat, norm in ((0, 80), (-42, 24), (42, 24)):
                    session.player = center + (pygame.Vector2(side * norm, lat) if door.vertical else pygame.Vector2(lat, side * norm))
                    inter = session.interaction()
                    self.assertIsNotNone(inter, f"missing prompt cell {cell} side {side} lat {lat} norm {norm}")
                    self.assertEqual(inter[0], "door")
                    self.assertEqual(inter[1], cell)
            # Threshold close assist at 22px from door center (previously blocked under 34px)
            door.opened = True
            session.interact_cooldown = 0
            session.player = center + (pygame.Vector2(22, 0) if door.vertical else pygame.Vector2(0, 22))
            session.interact()
            self.assertFalse(door.opened)
            self.assertTrue(session.can_stand(session.player, 11))
        story = StorySession()
        story.finish_cutscene()
        # Diagonal approach to building exit on 11:0 and building entrance on campus
        exit_pt = pygame.Vector2(story.layout.exit_points["south"])
        story.player = exit_pt + pygame.Vector2(38, -22)
        inter = story.interaction()
        self.assertIsNotNone(inter)
        self.assertEqual(inter[0], "building_exit")
        story.switch_level("campus", story.campus.spawn)
        ent_pt = pygame.Vector2(story.campus.center(story.campus.informatika_entrances[1]))
        story.player = ent_pt + pygame.Vector2(42, 26)
        inter = story.interaction()
        self.assertIsNotNone(inter)
        self.assertEqual(inter[0], "building_enter")

    def test_closed_door_blocks_completely_without_wall_gaps(self):
        session = Session(42)
        session.monsters = []
        for cell, door in session.layout.doors.items():
            if door.passage:
                continue
            door.opened = False
            door.swing = 0.
            center = pygame.Vector2(session.layout.center(cell))
            for offset in range(-36, 37, 4):
                if door.vertical:
                    session.player = center + pygame.Vector2(-34, offset)
                    if not session.can_stand(session.player, 11):
                        continue
                    session.move(session.player, pygame.Vector2(80, 0), 11)
                    self.assertLessEqual(session.player.x, center.x - 30.9, f"leaked vertical door {cell} offset {offset}")
                else:
                    session.player = center + pygame.Vector2(offset, -34)
                    if not session.can_stand(session.player, 11):
                        continue
                    session.move(session.player, pygame.Vector2(0, 80), 11)
                    self.assertLessEqual(session.player.y, center.y - 30.9, f"leaked horizontal door {cell} offset {offset}")

    def test_attack_telegraphs_and_does_not_dash_through_wall(self):
        session = Session(42)
        session.elapsed = 20
        monster = session.monsters[2]
        monster.pos = pygame.Vector2(session.layout.center((3, 22)))
        session.player = monster.pos + pygame.Vector2(120, 0)
        monster.facing = pygame.Vector2(1, 0)
        session._update_monster(monster, .05)
        self.assertEqual(monster.state, "windup")
        initial = monster.pos.copy()
        for _ in range(10):
            session._update_monster(monster, .05)
        self.assertEqual(initial, monster.pos)
        monster.state, monster.timer = "dash", .6
        monster.pos.update(60, 900)
        monster.dash.update(-1, 0)
        for _ in range(15):
            session._update_monster(monster, .05)
        self.assertGreaterEqual(monster.pos.x, 52)
        self.assertEqual(monster.state, "recovery")

    def test_distinct_door_events_and_floor_foley(self):
        session = Session(42)
        session.monsters = []
        cell,door = next((cell,door) for cell,door in session.layout.doors.items() if not door.passage)
        direction = pygame.Vector2(-55,0) if door.vertical else pygame.Vector2(0,-55)
        session.player = pygame.Vector2(session.layout.center(cell)) + direction
        session.interact()
        self.assertEqual(session.audio_events[-1][0], "door_open")
        session.interact_cooldown = 0
        session.interact()
        self.assertEqual(session.audio_events[-1][0], "door_close")
        for room, expected in ((session.layout.spawn_room,"concrete"),(6,"wood")):
            session.player=pygame.Vector2(session.layout.center(session.layout.room_center_cell(room)))
            session.audio_events.clear()
            for _ in range(20):
                session.update(.05,(1,0))
            steps=[event[0] for event in session.audio_events if event[0].startswith("step_")]
            self.assertTrue(steps)
            self.assertTrue(all(name=="step_"+expected for name in steps), steps)
        garden_origin = session.layout.room_origin(13)
        self.assertEqual(session.layout.surface_at(session.layout.center((garden_origin[0]+3,garden_origin[1]+2))),"grass")

    def test_larger_campus_has_indoor_and_outdoor_objectives(self):
        layout=Layout(42)
        self.assertEqual(ROOM_COUNT,30)
        self.assertEqual(len(layout.graph),30)
        self.assertGreater(len(layout.outdoors),5)
        self.assertGreater(layout.width*layout.height, 2*45*28)
        self.assertTrue(any(door.passage for door in layout.doors.values()))

    def test_capture_and_terminal_states(self):
        session = Session(42)
        session.elapsed = 20
        session.health = 20
        session.monsters[0].pos = session.player.copy()
        session.update(.02)
        self.assertEqual(session.status, "lost")
        self.assertIn("Penjaga", session.death_reason)
        elapsed = session.elapsed
        session.update(.05, (1, 0))
        self.assertEqual(session.elapsed, elapsed)

    def test_health_survives_first_hit_and_contact_does_not_stack(self):
        session = Session(42)
        session.elapsed = 20
        for monster in session.monsters:
            monster.pos = session.player.copy()
        session.update(.02)
        self.assertEqual(session.health, 72)
        self.assertEqual(session.status, "playing")
        self.assertEqual(session.hits_taken, 1)
        self.assertGreater(session.invulnerable, 1)
        self.assertTrue(session.can_stand(session.player, 11))
        for _ in range(35):
            for monster in session.monsters:
                monster.pos = session.player.copy()
            session.update(.02)
        self.assertEqual(session.health, 72)
        self.assertEqual(session.hits_taken, 1)

    def test_invulnerability_expires_and_damage_scales_with_difficulty(self):
        results = []
        for difficulty in ("easy", "normal", "hard"):
            session = Session(42, difficulty)
            monster = session.monsters[0]
            session.take_hit(monster)
            first_health = session.health
            self.assertFalse(session.take_hit(monster))
            session.monsters = []
            for _ in range(34):
                session.update(.05)
            self.assertTrue(session.take_hit(monster))
            self.assertLess(session.health, first_health)
            results.append(100 - first_health)
        self.assertLess(results[0], results[1])
        self.assertLess(results[1], results[2])

    def test_medkit_is_carried_and_heals_only_when_used(self):
        session = Session(42)
        session.player = session.medkits[0].copy()
        count = len(session.medkits)
        session.interact()
        self.assertEqual(len(session.medkits),count-1)
        self.assertEqual(session.backpack.count("medkit"),1)
        self.assertFalse(session.use_item("medkit"))
        self.assertEqual(session.backpack.count("medkit"),1)
        session.health = 83
        session.interact_cooldown = 0
        self.assertTrue(session.use_item("medkit"))
        self.assertEqual(session.health, 100)
        self.assertEqual(len(session.medkits), count - 1)
        session.health = 32
        session.player = session.medkits[0].copy()
        session.interact_cooldown = 0
        session.interact()
        session.item_cooldown=0
        session.use_item("medkit")
        self.assertEqual(session.health, 72)

    def test_complete_run_by_walking_interacting_and_powering_panel(self):
        session = Session(208)
        # Isolate progression from adversarial encounters; enemy routing is tested above.
        session.monsters = []

        def walk_to(destination):
            path = session.layout.path(session.layout.tile(session.player), session.layout.tile(destination))
            for cell in path:
                waypoint = pygame.Vector2(session.layout.center(cell))
                for _ in range(130):
                    delta = waypoint - session.player
                    if session.status == "won":
                        return
                    if delta.length() < 4:
                        break
                    door = session.layout.doors.get(cell)
                    if door and not door.opened and session.player.distance_to(waypoint) < 75:
                        session.interact()
                    session.update(min(.03, delta.length() / 125), delta, aim=waypoint)
                self.assertLess(session.player.distance_to(waypoint), 5, f"player stuck at {cell}")

        for fuse in list(session.fuses):
            walk_to(fuse)
            session.interact_cooldown = 0
            session.interact()
        self.assertEqual(session.collected, 2)
        self.assertEqual(len(session.fuses), 0)
        walk_to(session.layout.panel)
        for _ in range(110):
            session.update(.03, holding=True)
        self.assertTrue(session.power)
        walk_to(session.layout.exit)
        self.assertEqual(session.status, "won")


class AppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = App(self.directory.name, audio=False)

    def tearDown(self):
        pygame.quit()
        self.directory.cleanup()

    def key(self, key, unicode=""):
        self.app.events([pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode, mod=0)])
        self.app.draw()

    def test_keyboard_menu_pause_and_resume(self):
        self.app.focus=next(i for i,b in enumerate(self.app.buttons) if b.action=="start")
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.mode, "playing")
        self.key(pygame.K_ESCAPE)
        elapsed = self.app.session.elapsed
        self.app.session.invulnerable = 1.2
        self.app.update(.05, {pygame.K_d: True})
        self.assertEqual(self.app.session.elapsed, elapsed)
        self.assertEqual(self.app.session.invulnerable, 1.2)
        self.key(pygame.K_RETURN)
        self.assertEqual(self.app.mode, "playing")
        self.app.update(.05, {pygame.K_d: True})
        self.assertGreater(self.app.session.elapsed, elapsed)

    def test_toggle_key_v_renders_live_3d_wave_map(self):
        self.app.start(42)
        self.assertFalse(self.app.wave_open)
        self.assertEqual(self.app.wave_slide, 0.)
        self.key(pygame.K_v)
        self.assertTrue(self.app.wave_open)
        self.assertFalse(self.app.map_open)
        self.assertGreater(self.app.wave_slide, 0.)
        for _ in range(10):
            self.app.update(.05, {pygame.K_d: True})
        self.app.draw()
        self.assertEqual(self.app.wave_slide, 1.)
        self.assertGreater(self.app.renderer.wave_shift, 100.)
        # Toggle close V -> swipes left back to normal gameplay (wave_slide -> 0, wave_shift -> 0)
        self.key(pygame.K_v)
        self.assertFalse(self.app.wave_open)
        self.assertLess(self.app.wave_slide, 1.)
        for _ in range(10):
            self.app.update(.05, {})
        self.app.draw()
        self.assertEqual(self.app.wave_slide, 0.)
        self.assertEqual(self.app.renderer.wave_shift, 0.)
        # Mutual exclusion with M (map)
        self.key(pygame.K_v)
        self.assertTrue(self.app.wave_open)
        self.key(pygame.K_m)
        self.assertTrue(self.app.map_open)
        self.assertFalse(self.app.wave_open)
        self.assertEqual(self.app.wave_slide, 0.)

    def test_help_settings_return_and_persistence(self):
        self.app.action("help")
        self.app.draw()
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.mode, "menu")
        self.app.action("settings")
        self.app.action("volume:-0.1")
        self.app.draw()
        self.key(pygame.K_ESCAPE)
        self.assertEqual(self.app.mode, "menu")
        self.app.load_settings()
        self.assertAlmostEqual(self.app.settings["volume"], .55)

    def test_mouse_navigation_and_invalid_settings_recover(self):
        help_button = next(b for b in self.app.buttons if b.action == "help")
        self.app.events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=help_button.rect.center)])
        self.assertEqual(self.app.mode, "help")
        path = Path(self.directory.name) / "settings.json"
        for contents in ("not json", "[]", '{"volume": "invalid", "difficulty": "impossible"}'):
            path.write_text(contents, encoding="utf-8")
            self.app.load_settings()
            self.assertEqual(self.app.settings["difficulty"], "normal")
            self.assertEqual(self.app.settings["volume"], .65)

    def test_seed_entry_retry_new_map_and_result(self):
        self.app.action("seed")
        for char in "1234":
            self.key(ord(char), char)
        self.key(pygame.K_RETURN)
        self.app.action("start")
        self.assertEqual(self.app.session.seed, 1234)
        self.app.session.status = "won"
        self.app.update(.01, {})
        self.app.draw()
        self.assertEqual(self.app.mode, "result")
        self.assertEqual(self.app.settings["wins"], 1)
        self.app.action("retry")
        self.assertEqual(self.app.session.seed, 1234)
        self.assertEqual(self.app.session.collected, 0)
        self.assertFalse(self.app.session.power)
        self.assertEqual(self.app.session.health, 100)
        self.app.action("new")
        self.assertNotEqual(self.app.session.seed, 1234)

    def test_close_camera_follows_and_coordinate_roundtrip_is_correct(self):
        self.app.start(42)
        renderer, session = self.app.renderer, self.app.session
        center = pygame.Vector2(640, 400)
        self.assertLess(renderer.screen_to_world(center).distance_to(session.player), .001)
        self.assertEqual(renderer.scene.get_size(), (640, 400))
        self.assertEqual(renderer.zoom, 2)
        before = renderer.camera.copy()
        session.player.x += 100
        renderer.update_camera(session, .1)
        self.assertGreater(renderer.camera.x, before.x)
        self.assertLess(renderer.camera.x, before.x + 100)
        point = session.player + pygame.Vector2(71, -35)
        rendered = renderer.world_to_screen(point) * renderer.zoom
        self.assertLess(renderer.screen_to_world(rendered).distance_to(point), .001)
        renderer.update_camera(session, snap=True)
        self.assertLess((renderer.world_to_screen(session.player) * renderer.zoom).distance_to(center), .001)

    def test_mouse_aim_and_throw_use_zoomed_world_coordinates(self):
        self.app.start(42)
        session = self.app.session
        self.app.events([pygame.event.Event(pygame.MOUSEMOTION, pos=(640, 200), rel=(0, -200), buttons=(0, 0, 0))])
        self.app.update(.02, {})
        self.assertLess(session.facing.y, -.99)
        self.assertAlmostEqual(session.facing.x, 0, places=3)
        count = session.bottles
        self.key(pygame.K_q)
        self.assertEqual(session.bottles, count - 1)
        noise = session.noises[-1]
        self.assertAlmostEqual(noise.pos.x, session.player.x, places=2)
        self.assertLess(noise.pos.y, session.player.y - 40)

    def test_window_to_canvas_coordinates_preserve_center(self):
        self.app.start(42)
        self.app.window = pygame.display.set_mode((960, 700))
        canvas = self.app.to_canvas((480, 350))
        self.assertLess(canvas.distance_to((640, 400)), .001)
        self.assertLess(self.app.renderer.screen_to_world(canvas).distance_to(self.app.session.player), .001)

    def test_canvas_fills_wide_and_narrow_windows_without_bars(self):
        self.app.start(42)
        for dimensions in ((960,700),(1600,900),(1920,800)):
            self.app.window=pygame.display.set_mode(dimensions)
            self.app.resize_canvas()
            self.assertEqual(self.app.screen.get_size(),dimensions)
            self.assertAlmostEqual(self.app.width/800,dimensions[0]/dimensions[1],delta=.002)
            color=(79,113,157)
            self.app.screen.fill(color)
            self.app.present()
            for point in ((0,0),(dimensions[0]-1,0),(0,dimensions[1]-1),(dimensions[0]-1,dimensions[1]-1)):
                actual=tuple(self.app.window.get_at(point))[:3]
                self.assertLessEqual(max(abs(a-b) for a,b in zip(actual,color)),3)
            self.assertLess(self.app.renderer.screen_to_world(self.app.to_canvas((dimensions[0]/2,dimensions[1]/2))).distance_to(self.app.session.player),.001)

    def test_camera_keeps_world_edges_inside_view(self):
        self.app.start(42)
        session,renderer=self.app.session,self.app.renderer
        for position in ((60,60),((session.layout.width-2)*TILE,(session.layout.height-2)*TILE)):
            session.player.update(position)
            renderer.update_camera(session,snap=True)
            self.assertGreaterEqual(renderer.camera.x,0)
            self.assertGreaterEqual(renderer.camera.y,0)
            self.assertLessEqual(renderer.camera.x+renderer.view_size.x,session.layout.width*TILE)
            self.assertLessEqual(renderer.camera.y+renderer.view_size.y,session.layout.height*TILE)

    def test_recorded_audio_banks_decode_and_vary(self):
        audio=Audio()
        self.assertTrue(audio.available)
        for name in ("door_open","door_close","step_concrete","step_wood","step_grass"):
            self.assertIn(name,audio.banks)
            self.assertGreater(audio.banks[name][0].get_length(),.03)
        self.assertEqual(len(audio.banks["step_concrete"]),5)
        self.assertNotEqual(audio.banks["door_open"][0].get_raw(),audio.banks["door_close"][0].get_raw())


if __name__ == "__main__":
    unittest.main()
