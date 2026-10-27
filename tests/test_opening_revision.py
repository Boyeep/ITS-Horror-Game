"""Opening navigation, old saves and the cause/effect of the prologue."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import json
import unittest
import pygame
from horror.story import StorySession
from horror.cinematics import INTRO_LINES,CUTSCENES
from horror.saves import SaveStore
from horror.achievements import AchievementProfile
from tools.campaign_driver import CampaignDriver


class OpeningRevisionTests(unittest.TestCase):
    def test_starting_lab_is_spacious_with_one_exit_and_a_reachable_phone(self):
        s=StorySession();f=s.layout
        self.assertEqual(s.level_key,"11:0");self.assertEqual(f.validate(),[])
        x,y,w,h=f.lab_bounds
        self.assertGreaterEqual(w*h,200)
        boundary={(xx,yy) for xx in range(x-1,x+w+1) for yy in range(y-1,y+h+1)
                  if xx in (x-1,x+w) or yy in (y-1,y+h)}
        exits=[cell for cell in boundary if f.walkable(cell,True)]
        self.assertEqual(exits,[f.lab_door])
        reachable=f.reachable(f.tile(s.player))
        for p in [f.phone_interaction,*f.exit_points.values(),*f.stair_points.values()]:self.assertIn(f.tile(p),reachable)
        self.assertFalse(f.is_outdoor(s.player));self.assertEqual(f.surface_at(f.center((16,22))),"grass")
        for p in [*s.medkits,*s.pickups,*[drop.pos for drop in s.loot]]:self.assertGreater(s.player.distance_to(p),300)

    def test_phone_to_campus_then_back_and_stairs_use_real_inputs(self):
        s=StorySession();s.finish_cutscene();d=CampaignDriver(s)
        d.walk(s.point(11));d.press();d.dismiss();self.assertEqual(s.stage,1)
        d.navigate(22);self.assertEqual(s.level_key,"campus")
        d.navigate(11);self.assertEqual(s.level_key,"11:0")
        d.stairs_to("up",(11,"sw"),s.layout.stair_points["sw"])
        self.assertEqual(s.level_key,"11:1")
        d.stairs_to("down",(11,"sw"),s.layout.stair_points["sw"])
        self.assertEqual(s.level_key,"11:0")
        for entrance in ("main","south","courtyard"):
            d.walk(s.layout.exit_points[entrance]);d.press();self.assertEqual(s.level_key,"campus")
            d.press();self.assertEqual(s.level_key,"11:0")
            self.assertTrue(s.can_stand(s.player,11))

    def test_version6_ground_save_is_moved_without_resetting_progress_or_inventory(self):
        s=StorySession();s.finish_cutscene();s.use_building("building_exit","main")
        data=s.snapshot();data.update(version=6,player=[2940,1900],stage=8,health=39)
        data["layers"].pop("11:0",None)
        before=json.dumps(data,sort_keys=True);r=StorySession(checkpoint=data)
        self.assertEqual(json.dumps(data,sort_keys=True),before)
        self.assertEqual(r.level_key,"11:0");self.assertEqual(r.stage,8);self.assertEqual(r.health,39)
        self.assertEqual(r.backpack.items,s.backpack.items);self.assertIsNone(r.cutscene)
        self.assertTrue(r.can_stand(r.player,11));self.assertTrue(SaveStore.valid(r.snapshot()))
        data.update(stage=0,cutscene={"id":"intro","time":12.5})
        self.assertEqual(StorySession(checkpoint=data).cutscene,{"id":"intro","time":0.})

    def test_upper_floor_save_and_campus_save_keep_their_location(self):
        for level in ("11:2","campus"):
            s=StorySession();s.finish_cutscene();s.stage=12
            s.switch_level(level,s.get_layout(level).spawn);data=s.snapshot();data["version"]=6
            r=StorySession(checkpoint=data)
            self.assertEqual(r.level_key,level);self.assertEqual(r.player,s.player);self.assertEqual(r.stage,12)
        old={"version":1,"stage":6,"difficulty":"easy","player":[1420,4020],"collected":2,"journal":["pesan"]}
        r=StorySession(checkpoint=old)
        self.assertEqual(r.level_key,"campus");self.assertEqual(list(r.player),old["player"])

    def test_prologue_establishes_deadline_departure_phone_and_reaction_in_order(self):
        text=" ".join(line[3] for line in INTRO_LINES)
        self.assertIn("08.00",text);self.assertIn("buku log",text);self.assertIn("tinggal dicas",text)
        departure=next(start for start,end,speaker,body in INTRO_LINES if "tinggal dicas" in body)
        waiting=next(start for start,end,speaker,body in INTRO_LINES if "belum balik" in body)
        reaction=next(start for start,end,speaker,body in INTRO_LINES if "nomornya sendiri" in body)
        self.assertLess(departure,waiting);self.assertLess(waiting,35);self.assertGreater(reaction,35)
        self.assertGreaterEqual(CUTSCENES["intro"],reaction+5)

    def test_each_landing_offers_a_real_return_flight_and_ground_is_not_an_upper_floor(self):
        s=StorySession();s.finish_cutscene();d=CampaignDriver(s)
        self.assertEqual(AchievementProfile.measure(s)["floors"],0)
        for key in ("nw","ne","sw","se"):
            d.stairs_to("up",(11,key),s.layout.stair_points[key])
            self.assertEqual(s.level_key,"11:1")
            point=next(p for direction,k,p in s.layout.stair_portals if direction=="down" and k==key)
            d.stairs_to("down",(11,key),point)
            self.assertEqual(s.level_key,"11:0")
            self.assertLess(s.player.distance_to(s.layout.stair_points[key]),41)
        self.assertEqual(AchievementProfile.measure(s)["floors"],1)


if __name__=="__main__":unittest.main()
