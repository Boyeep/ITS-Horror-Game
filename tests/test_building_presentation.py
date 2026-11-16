"""Stair bays, window spans and cosmetic roofs agree with navigable geometry."""
import copy
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy");os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import tempfile
import unittest
import pygame
from horror.architecture import stair_bounds, top_window_columns
from horror.campus import CampusLayout,FLOOR_COUNTS
from horror.floors import BuildingLayout
from horror.ground_floor import InformatikaGround
from horror.story import StorySession
from horror.app import App


def interiors():
    c=CampusLayout()
    yield InformatikaGround(c.room_names,c.room_kinds)
    for b,count in FLOOR_COUNTS.items():
        for floor in range(1,count):yield BuildingLayout(b,floor)


class BuildingPresentationTests(unittest.TestCase):
    def test_every_paired_stair_has_separate_visible_bounds(self):
        for layout in interiors():
            boxes=[stair_bounds(point) for _,point in layout.stairs]
            for i,box in enumerate(boxes):
                self.assertTrue(pygame.Rect(0,0,layout.width*40,layout.height*40).contains(box))
                for other in boxes[i+1:]:self.assertFalse(box.colliderect(other),(layout.building,layout.floor,box,other))

    def test_windows_never_span_unoccupied_courtyard(self):
        for layout in interiors():
            for x in top_window_columns(layout):
                for column in range(x,x+3):
                    self.assertNotIn((column,1),getattr(layout,"void_cells",()))
                    self.assertEqual(layout.grid[0][column],1)
        layout=BuildingLayout(11,1)
        self.assertEqual(len(top_window_columns(layout)),2)

    def test_generic_flights_share_a_bay_and_transfers_remain_reachable(self):
        for building,count in FLOOR_COUNTS.items():
            if building==11:continue
            s=StorySession();s.finish_cutscene();s.dialogue=[];s.use_stairs("enter",building)
            for floor in range(1,count-1):
                old=s.layout
                self.assertLess(pygame.Vector2(old.up).distance_to(old.down),150)
                s.player=pygame.Vector2(old.up);s.use_stairs("up",building)
                self.assertTrue(s.can_stand(s.player,11))
                self.assertLess(s.player.distance_to(s.layout.down),60)
                s.use_stairs("down",building)
                self.assertLess(s.player.distance_to(old.up),60)
                s.use_stairs("up",building)

    def test_all_objectives_and_landings_still_have_routes(self):
        for layout in interiors():
            self.assertEqual(layout.validate(),[])
            reachable=layout.reachable(layout.tile(layout.spawn))
            for point in [*[p for _,p in layout.stairs],*[layout.quest_point(i) for i in range(5)]]:
                self.assertIn(layout.tile(point),reachable,(layout.building,layout.floor,point))

    def test_prior_save_near_old_stair_bay_keeps_progress_and_legal_position(self):
        s=StorySession();s.finish_cutscene();s.dialogue=[];s.use_stairs("enter",22)
        s.stage=10;s.health=37;s.player=pygame.Vector2(s.layout.center((26,3)))
        r=StorySession(checkpoint=s.snapshot())
        self.assertTrue(r.can_stand(r.player,11));self.assertEqual(r.health,37);self.assertEqual(r.stage,10)
        self.assertTrue(r.layout.path(r.layout.tile(r.player),r.layout.tile(r.layout.up)))

    def test_cosmetic_roof_cannot_change_collision_or_close_an_entrance(self):
        with tempfile.TemporaryDirectory() as folder:
            a=App(folder,audio=False)
            try:
                c=CampusLayout();before=copy.deepcopy(c.grid)
                a.renderer.build_world(c)
                self.assertEqual(c.grid,before)
                for cell in c.informatika_entrances:self.assertTrue(c.walkable(cell))
            finally:pygame.quit()
