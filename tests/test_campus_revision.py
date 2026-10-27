"""Door lighting/alignment, researched Informatika geometry and the three-image menu."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy");os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import json
import math
import tempfile
import unittest
import pygame
from horror.app import App
from horror.architecture import door_geometry,DOOR_ANCHOR
from horror.campus import CampusLayout
from horror.floors import BuildingLayout
from horror.story import StorySession
from horror.backdrop import SCENES


class CampusRevisionTests(unittest.TestCase):
    def test_ground_has_larger_wings_courtyard_and_connected_entrances(self):
        c=CampusLayout();self.assertEqual(c.validate(),[])
        self.assertEqual(c.buildings[11],(66,35,17,15))
        self.assertGreater(17*15,9*7*4)
        self.assertTrue(c.is_outdoor(c.center((72,42))))
        self.assertTrue(c.is_outdoor(c.spawn))
        reachable=c.reachable(c.tile(c.spawn))
        for cell in c.informatika_entrances:self.assertIn(cell,reachable)
        for point in c.informatika_stairs.values():self.assertIn(c.tile(point),reachable)
        self.assertIn(c.tile(c.informatika_phone),reachable)

    def test_floor3_topology_has_named_labs_and_no_walkable_courtyard(self):
        f=BuildingLayout(11,2);self.assertEqual(f.validate(),[])
        self.assertEqual((f.width,f.height),(38,44))
        self.assertTrue({"PEMROGRAMAN 1","PEMROGRAMAN 2","NETICS"}.issubset({name for name,_ in f.labels}))
        self.assertFalse(f.walkable((19,20),True))
        reachable=f.reachable(f.tile(f.spawn))
        for point in [*f.stair_points.values(),*[f.quest_point(i) for i in range(5)]]:self.assertIn(f.tile(point),reachable)

    def test_each_stair_returns_to_its_corresponding_landing(self):
        for key in ("nw","ne","sw","se"):
            s=StorySession();s.finish_cutscene();s.use_stairs("enter",(11,key))
            self.assertEqual(s.level_key,"11:1")
            point=next(p for d,k,p in s.layout.stair_portals if d=="down" and k==key)
            self.assertLess(s.player.distance_to(point),41)
            s.use_stairs("down",(11,key));self.assertEqual(s.level_key,"11:0")
            self.assertLess(s.player.distance_to(s.layout.stair_points[key]),41)
        s.use_stairs("enter",11);s.use_stairs("up",(11,"se"))
        self.assertEqual(s.level_key,"11:2");self.assertLess(s.player.distance_to(s.layout.stair_points["se"]),41)

    def test_old_informatika_save_translates_entities_and_preserves_progress(self):
        s=StorySession();s.finish_cutscene();data=s.snapshot();data["version"]=5
        data["stage"]=8;data["level"]="11:1";data["player"]=[340,260];data["health"]=41
        data["layers"]["11:1"]={"fuses":[],"pickups":[[340,340]],"medkits":[[980,740]],
            "doors":[[15,6]],"monsters":[],"loot":[{"item":"tape","pos":[340,300],"quantity":1}],"placed":[]}
        before=json.dumps(data,sort_keys=True);r=StorySession(checkpoint=data)
        self.assertEqual(json.dumps(data,sort_keys=True),before)
        self.assertEqual(r.stage,8);self.assertEqual(r.health,41)
        self.assertTrue(r.can_stand(r.player,11));self.assertLess(r.player.distance_to(r.layout.quest_point(0)),1)
        self.assertEqual(r.loot[0].item,"tape");self.assertTrue(r.layout.walkable(r.layout.tile(r.loot[0].pos),True))
        self.assertTrue(any(door.opened for door in r.layout.doors.values()))

    def test_door_hinge_and_closed_leaf_share_the_tile_plane_in_both_orientations(self):
        for vertical in (False,True):
            hinge,tip=door_geometry(vertical,0)
            expected=(pygame.Vector2(0,-18),pygame.Vector2(0,18)) if vertical else (pygame.Vector2(-18,0),pygame.Vector2(18,0))
            self.assertLess(hinge.distance_to(expected[0]),.00001);self.assertLess(tip.distance_to(expected[1]),.00001)
            for swing in (0,.25,.5,1):
                other,end=door_geometry(vertical,swing)
                self.assertEqual(hinge,other);self.assertAlmostEqual(end.distance_to(hinge),36)
        self.assertEqual(DOOR_ANCHOR,(48,48))


class DoorLightingTests(unittest.TestCase):
    def setUp(self):self.folder=tempfile.TemporaryDirectory();self.a=App(self.folder.name,audio=False)
    def tearDown(self):pygame.quit();self.folder.cleanup()

    def test_flashlight_brightens_the_wood_but_does_not_light_the_room_behind_it(self):
        a=self.a;a.start_story();s=a.session;s.finish_cutscene()
        s.use_stairs("enter",11);s.monsters=[];s.transition=s.message_time=0
        for cell in ((5,18),(19,38)):
            door=s.layout.doors[cell];door.opened=False;door.swing=0
            normal=pygame.Vector2(1,0) if door.vertical else pygame.Vector2(0,1)
            centre=pygame.Vector2(s.layout.center(cell));s.player=centre-normal*70;s.facing=normal
            a.renderer.update_camera(s,snap=True)
            means=[];behind=[]
            for enabled in (False,True):
                s.flashlight=enabled;a.draw();p=a.renderer.world_to_screen(centre)
                sx=a.screen.get_width()/a.renderer.scene.get_width();sy=a.screen.get_height()/a.renderer.scene.get_height()
                roi=pygame.Rect(round((p.x-4)*sx),round((p.y-4)*sy),round(8*sx),round(8*sy))
                means.append(sum(pygame.transform.average_color(a.screen.subsurface(roi))[:3]) / 3)
                q=a.renderer.world_to_screen(centre+normal*35)
                behind.append(sum(a.renderer.lightmap.get_at((round(q.x),round(q.y)))) )
            self.assertGreater(means[1],means[0]*1.35,(cell,means))
            self.assertLessEqual(abs(behind[1]-behind[0]),5)

    def test_menu_rotates_three_distinct_images_and_fades_at_the_boundary(self):
        r=self.a.renderer
        self.assertEqual(SCENES,("rektorat","tower2","informatika"))
        self.assertEqual([r.backdrop_phase(t)[0] for t in (0,9,18,27)],[0,1,2,0])
        self.assertAlmostEqual(r.backdrop_phase(8.3)[2],.5)
        self.assertEqual(len({pygame.image.tobytes(image,"RGB") for image in r.menu_images}),3)
        r.backdrop(self.a.screen,9,reduced=True)


if __name__=="__main__":unittest.main()
