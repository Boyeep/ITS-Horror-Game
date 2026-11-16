"""Reachable routes, stable exits, cache invalidation and collision-free HUD placement."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy");os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import tempfile
import unittest
import pygame
from pygame import Vector2
from horror.app import App
from horror.simulation import Session
from horror.world import Door
from horror.guidance import RouteGuide,target,route_clear,visible_face,place_label,arrow_position


def arena():
    s=Session(42);w,h=s.layout.width,s.layout.height
    s.layout.grid=[[int(x in (0,w-1) or y in (0,h-1)) for x in range(w)] for y in range(h)]
    s.layout.doors={};s.player=Vector2(s.layout.center((12,12)))
    return s


class WaypointRouteTests(unittest.TestCase):
    def test_route_cost_beats_nearer_target_behind_a_long_wall(self):
        s=arena()
        for y in range(1,20):s.layout.grid[y][13]=1
        near=target("near",s.layout.center((14,12)),"A")
        reachable=target("far",s.layout.center((12,18)),"B")
        info=RouteGuide().info(s,[near,reachable])
        self.assertEqual(info[0].key,"far")

    def test_unreachable_target_is_never_used_as_a_direction(self):
        s=arena()
        for x,y in ((13,12),(15,12),(14,11),(14,13)):s.layout.grid[y][x]=1
        guide=RouteGuide();goal=target("closed",s.layout.center((14,12)),"C")
        self.assertIsNone(guide.info(s,[goal]));self.assertEqual(guide.current_path,[])

    def test_equivalent_exit_selection_has_hysteresis(self):
        s=arena();guide=RouteGuide()
        goals=[target("left",s.layout.center((5,12)),"L"),target("right",s.layout.center((15,12)),"R")]
        s.player=Vector2(s.layout.center((9,12)));self.assertEqual(guide.info(s,goals)[0].key,"left")
        s.player=Vector2(s.layout.center((11,12)));self.assertEqual(guide.info(s,goals)[0].key,"left")
        s.player=Vector2(s.layout.center((13,12)));self.assertEqual(guide.info(s,goals)[0].key,"right")

    def test_opening_door_without_revision_still_invalidates_guidance(self):
        s=arena();s.layout.doors[(13,12)]=Door((13,12),True)
        guide=RouteGuide();goal=target("goal",s.layout.center((15,12)),"G")
        self.assertEqual(guide.info(s,[goal])[3],"door")
        s.layout.doors[(13,12)].opened=True
        self.assertEqual(guide.info(s,[goal])[3],"goal")
        self.assertEqual(guide.info(s,[goal])[1],goal.point)

    def test_changed_multiobject_progress_does_not_reuse_old_goal(self):
        s=arena();guide=RouteGuide()
        a=target("fuse",s.layout.center((13,12)),"Fuse")
        b=target("fuse",s.layout.center((18,12)),"Fuse")
        self.assertEqual(guide.info(s,[a,b])[0].point,a.point)
        self.assertEqual(guide.info(s,[b])[0].point,b.point)

    def test_centre_ray_cannot_suggest_a_corner_the_body_cannot_pass(self):
        s=arena();s.layout.grid[13][13]=1;s.player=Vector2(490,500)
        goal=target("g",(580,518),"G")
        self.assertTrue(visible_face(s,goal.point));self.assertFalse(route_clear(s,goal.point))
        info=RouteGuide().info(s,[goal])
        self.assertNotEqual(info[1],goal.point);self.assertTrue(route_clear(s,info[1]))

    def test_small_motion_in_one_tile_keeps_the_next_step(self):
        s=arena();guide=RouteGuide();goal=target("g",s.layout.center((25,18)),"G")
        point=guide.info(s,[goal])[1].copy()
        for dx in (-3,2,4,-1):
            s.player.x+=dx;self.assertEqual(guide.info(s,[goal])[1],point)

    def test_edge_arrow_uses_player_origin_instead_of_screen_center(self):
        bounds=pygame.Rect(38,190,1204,460);origin=Vector2(250,600);goal=Vector2(1300,300)
        point,direction=arrow_position(origin,goal,bounds)
        self.assertTrue(bounds.collidepoint(point))
        self.assertAlmostEqual(direction.dot((goal-origin).normalize()),1.)

    def test_label_boxes_fit_and_do_not_overlap_actor_hud_or_each_other(self):
        for width in (960,1280,1920):
            bounds=pygame.Rect(22,174,width-44,494)
            avoid=[pygame.Rect(width//2-48,280,96,132),pygame.Rect(28,24,428,110)]
            for offset in (0,20,-20):
                box=place_label((width/2+offset,400),(300,31),bounds,avoid)
                self.assertIsNotNone(box);self.assertTrue(bounds.contains(box))
                self.assertTrue(all(not box.colliderect(other) for other in avoid))
                avoid.append(box)


class WaypointAppTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.a=App(self.folder.name,audio=False);self.addCleanup(pygame.quit)
        self.a.start_story();self.a.session.finish_cutscene();self.a.session.dialogue=[]

    def test_paired_stair_prompt_follows_the_required_direction(self):
        s=self.a.session;layout=s.get_layout("11:1")
        s.switch_level("11:1",layout.center((3,5)));s.stage=9
        self.assertEqual(s.interaction()[0],"stairs")
        self.assertEqual(s.interaction()[1][0],"down")
        self.a.draw()
        for box in self.a.renderer.marker_boxes:
            self.assertTrue(pygame.Rect(0,0,self.a.width,800).contains(box))

    def test_map_and_hud_share_next_step_after_level_and_save_load_changes(self):
        a=self.a;s=a.session;s.stage=8
        before=a.renderer.guidance(s)
        s.use_stairs("up",(11,"sw"));a.sync_scene();a.draw()
        current=a.renderer.guidance(s)
        self.assertNotEqual(before[0].key,current[0].key)
        a.map_open=True;a.draw();self.assertEqual(a.renderer.guidance(s)[1],current[1])
        saved=s.snapshot();a.start_story(data=saved);a.draw()
        self.assertEqual(a.renderer.guidance(a.session)[1],current[1])
