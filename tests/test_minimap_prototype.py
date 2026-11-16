"""Review-only minimap keeps discoveries local, hides secrets and leaves saves untouched."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy");os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import json
import tempfile
import unittest
import pygame
from pygame import Vector2
from horror.app import App
from horror.simulation import Session
from tools.minimap_prototype import MiniMapPrototype


class MiniMapPrototypeTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.a=App(self.folder.name,audio=False);self.addCleanup(pygame.quit)
        self.a.start(42);self.a.session.elapsed=60.;self.a.draw()
        self.p=MiniMapPrototype()

    def test_default_off_never_discovers_or_draws(self):
        self.p.observe(self.a.session)
        self.assertFalse(self.p.enabled);self.assertEqual(self.p.seen,{})
        self.assertIsNone(self.p.draw(self.a))

    def test_wall_blocks_discovery_of_the_room_behind_it(self):
        s=Session(42);w,h=s.layout.width,s.layout.height
        s.layout.grid=[[int(x in (0,w-1) or y in (0,h-1)) for x in range(w)] for y in range(h)]
        s.layout.doors={};s.player=Vector2(s.layout.center((12,12)));s.facing.update(1,0)
        for y in range(1,h-1):s.layout.grid[y][13]=1
        self.p.toggle();self.p.observe(s);known=self.p.seen[self.p.level_key(s)]
        self.assertIn((13,12),known);self.assertNotIn((14,12),known)

    def test_hidden_monsters_and_items_cannot_change_minimap_pixels(self):
        a=self.a;self.p.toggle();box=self.p.draw(a)
        before=pygame.image.tobytes(a.screen.subsurface(box),"RGB")
        a.session.monsters[0].pos.update(9999,9999)
        a.session.fuses=[Vector2(8888,8888)];a.session.pickups=[Vector2(7777,7777)]
        self.p.draw(a)
        self.assertEqual(pygame.image.tobytes(a.screen.subsurface(box),"RGB"),before)

    def test_reading_and_drawing_does_not_modify_story_save(self):
        a=self.a;a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[];a.draw()
        before=json.dumps(s.snapshot(),sort_keys=True);self.p.toggle()
        for _ in range(5):self.p.draw(a)
        self.assertEqual(json.dumps(s.snapshot(),sort_keys=True),before)

    def test_floor_discoveries_are_kept_separate(self):
        a=self.a;a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[]
        self.p.toggle();self.p.observe(s);old_key=self.p.level_key(s);old=dict(self.p.seen[old_key])
        layout=s.get_layout("22:1");s.switch_level("22:1",layout.spawn);self.p.observe(s)
        self.assertNotEqual(self.p.level_key(s),old_key)
        self.assertEqual(self.p.seen[old_key],old);self.assertEqual(len(self.p.seen),2)

    def test_new_run_does_not_inherit_discoveries_even_for_the_same_seed(self):
        self.p.toggle();self.p.observe(self.a.session)
        key=self.p.level_key(self.a.session);self.p.seen[key][(999,999)]=1
        self.p.observe(Session(42));self.assertNotIn((999,999),self.p.seen[key])

    def test_panel_fits_native_resolutions_and_avoids_the_actor(self):
        a=self.a;self.p.toggle()
        for size in ((960,700),(1920,1200)):
            a.window=pygame.display.set_mode(size);a.resize_canvas();a.draw();box=self.p.draw(a)
            self.assertIsNotNone(box)
            native=a.renderer.draw.box(a.screen,box)
            self.assertTrue(a.screen.get_rect().contains(native))
            point=a.renderer.marker_position(a.session.player)
            self.assertFalse(box.colliderect(pygame.Rect(point.x-54,point.y-132,108,144)))

    def test_full_map_wave_map_and_modal_hide_the_prototype(self):
        a=self.a;self.p.toggle();a.map_open=True;self.assertIsNone(self.p.draw(a))
        a.map_open=False;a.wave_slide=1.;self.assertIsNone(self.p.draw(a))
        a.wave_slide=0.;a.session.modal=True;self.assertIsNone(self.p.draw(a))
