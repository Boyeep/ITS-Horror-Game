"""Functional items, storage limits, save compatibility and permanent rewards."""
import json
import os
import tempfile
import unittest
from pathlib import Path
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame
from horror.achievements import AchievementProfile
from horror.app import App
from horror.campus import CampusLayout,FLOOR_COUNTS
from horror.floors import BuildingLayout
from horror.inventory import Backpack,ITEMS,Loot,PlacedItem,seed_supplies
from horror.simulation import Session,Monster
from horror.story import StorySession


def outdoor():
    s=StorySession();s.finish_cutscene();s.dialogue=[];s.switch_level("campus",s.campus.center((35,100)))
    s.interact_cooldown=0;s.elapsed=25
    return s


class ItemTests(unittest.TestCase):
    def test_capacity_stack_and_key_items_cannot_block_progress(self):
        bag=Backpack();self.assertEqual(bag.add("bottle",20),8)
        self.assertEqual(bag.add("medkit",9),2);self.assertEqual(bag.used,12)
        self.assertEqual(bag.add("glow"),0);self.assertFalse(bag.remove("medkit",3))
        self.assertEqual(bag.count("medkit"),2)
        s=outdoor();s.backpack=bag;s.stage=3;s.fuses=[s.player.copy()]
        s.interact();self.assertEqual(s.collected,1);self.assertEqual(s.backpack.used,12)

    def test_supplies_are_repeatable_reachable_and_not_on_door_tiles(self):
        layouts=[CampusLayout(),Session(11).layout]
        layouts += [BuildingLayout(b,f) for b,count in FLOOR_COUNTS.items() for f in range(1,count)]
        for layout in layouts:
            drops=seed_supplies(layout);reachable=layout.reachable(layout.tile(layout.spawn))
            self.assertTrue(drops)
            self.assertEqual([d.pack() for d in drops],[d.pack() for d in seed_supplies(layout)])
            cells=[layout.tile(d.pos) for d in drops]
            self.assertEqual(len(cells),len(set(cells)))
            for cell in cells:self.assertIn(cell,reachable);self.assertNotIn(cell,layout.doors)

    def test_heal_energy_and_failed_use_do_not_waste_items(self):
        s=Session(42);s.monsters=[];s.backpack.add("medkit")
        self.assertFalse(s.use_item("medkit"));self.assertEqual(s.backpack.count("medkit"),1)
        s.health=63;self.assertTrue(s.use_item("medkit"));self.assertEqual(s.health,100)
        self.assertEqual(s.run_stats["heals_used"],1)
        s.item_cooldown=0;s.health=50;s.use_item("bandage");self.assertEqual(s.health,70)
        s.item_cooldown=0;s.stamina=14;s.exhausted=True;s.use_item("energy")
        self.assertEqual(s.stamina,59);self.assertFalse(s.exhausted)
        self.assertEqual(s.run_stats["low_stamina_drinks"],1)
        s.backpack.add("energy");s.item_cooldown=0
        self.assertFalse(s.use_item("energy"));self.assertEqual(s.backpack.count("energy"),1)

    def test_tape_reduces_footsteps_not_door_noise(self):
        normal=outdoor();quiet=outdoor();quiet.backpack.add("tape");quiet.use_item("tape")
        for _ in range(12):normal.update(.05,(0,1));quiet.update(.05,(0,1))
        self.assertTrue(normal.noises and quiet.noises)
        self.assertLess(quiet.noises[-1].radius,normal.noises[-1].radius)
        self.assertGreater(quiet.run_stats["quiet_seconds"],0)
        quiet.emit_noise(quiet.player,4,"pintu")
        self.assertEqual(quiet.noises[-1].radius,4)

    def test_alarm_waits_then_gives_monster_source_evidence(self):
        s=outdoor();s.backpack.add("alarm");original=s.player.copy()
        listener=Monster("Pendengar",original+pygame.Vector2(200,0),pygame.Vector2(1,0),wait=100)
        s.monsters=[listener];self.assertTrue(s.use_item("alarm"));point=s.placed[0].pos.copy()
        s.player-=pygame.Vector2(150,0)
        for _ in range(50):s.update(.05)
        self.assertEqual(s.run_stats["lures_worked"],0)
        for _ in range(12):s.update(.05)
        self.assertEqual(listener.state,"investigate")
        self.assertLess(listener.target.distance_to(point),30)
        self.assertGreater(listener.target.distance_to(s.player),100)
        self.assertGreater(s.run_stats["lures_worked"],0)

    def test_glow_reveals_dark_area_but_not_through_wall(self):
        s=outdoor();s.flashlight=False
        monster=Monster("Penjaga",s.player+pygame.Vector2(200,0),pygame.Vector2(1,0))
        self.assertFalse(s.player_can_see(monster));self.assertTrue(s.use_item("glow"))
        self.assertTrue(s.player_can_see(monster))
        s.placed[0].life=.02;s.update(.05);self.assertFalse(s.player_can_see(monster))
        s.use_stairs("enter",5);s.flashlight=False
        s.player=pygame.Vector2(s.layout.center((14,6)));monster.pos=pygame.Vector2(s.layout.center((16,6)))
        s.placed=[PlacedItem("glow",monster.pos.copy(),45)]
        self.assertFalse(s.player_can_see(monster))

    def test_full_bag_leaves_world_item_and_dropped_item_is_not_farmed(self):
        s=outdoor();s.backpack.restore({"bottle":8,"medkit":2})
        s.loot=[Loot("energy",s.player.copy())]
        s.interact();self.assertEqual(len(s.loot),1);self.assertEqual(s.backpack.count("energy"),0)
        self.assertTrue(s.drop_item("bottle"));dropped=s.loot[-1]
        s.player=dropped.pos.copy();s.interact_cooldown=0;s.interact()
        self.assertEqual(s.bottles,8);self.assertEqual(s.run_stats["items_found"],0)

    def test_save_roundtrip_preserves_bag_effects_and_placed_items_on_both_floors(self):
        s=outdoor();s.backpack.add("tape");s.use_item("tape")
        s.item_cooldown=0;s.use_item("glow");campus_glow=s.placed[0].pos.copy()
        s.use_stairs("enter",22);s.backpack.add("alarm");s.item_cooldown=0;s.use_item("alarm")
        s.run_stats["quiet_seconds"]=7.2
        data=json.loads(json.dumps(s.snapshot()));self.assertEqual(data["version"],7)
        r=StorySession(checkpoint=data)
        self.assertEqual(r.backpack.items,s.backpack.items);self.assertEqual(r.effects,s.effects)
        self.assertEqual(r.placed[0].kind,"alarm");self.assertEqual(r.placed[0].delay,3)
        self.assertEqual(r.run_stats["quiet_seconds"],7.2)
        r.use_stairs("down",22)
        self.assertEqual(r.placed[0].kind,"glow");self.assertEqual(r.placed[0].pos,campus_glow)
        data["version"]=2
        for key in ("backpack","effects","run_stats"):data.pop(key,None)
        for state in data["layers"].values():state.pop("loot",None);state.pop("placed",None)
        old=StorySession(checkpoint=data)
        self.assertEqual(old.level_key,"22:1");self.assertTrue(old.loot)
        self.assertLessEqual(old.backpack.used,old.backpack.capacity)


class AchievementTests(unittest.TestCase):
    def test_real_conditions_duplicate_prevention_and_no_save_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            profile=AchievementProfile(folder);s=Session(42);s.monsters=[]
            self.assertEqual(profile.observe(s),[])
            s.collect_item("medkit");s.health=61;s.use_item("medkit")
            keys=profile.observe(s)
            self.assertIn("supplies",keys);self.assertIn("first_aid",keys)
            self.assertEqual(profile.observe(s),[]);self.assertTrue(profile.save())
            reloaded=AchievementProfile(folder);reloaded.observe(Session(42))
            self.assertIn("first_aid",reloaded.unlocked)
            self.assertEqual(reloaded.progress["first_aid"],1)

    def test_clean_and_no_sprint_awards_use_history_not_current_health(self):
        with tempfile.TemporaryDirectory() as folder:
            p=AchievementProfile(folder);s=Session(42,"hard");s.take_hit(s.monsters[0]);s.health=100
            s.run_stats["sprint_seconds"]=.1;s.status="won";keys=p.observe(s)
            self.assertIn("hard",keys);self.assertIn("escape",keys)
            self.assertNotIn("unhurt",keys);self.assertNotIn("walker",keys)
            story=outdoor();story.status="won";keys=p.observe(story)
            self.assertIn("story",keys);self.assertNotIn("unhurt",keys)

    def test_backup_recovers_and_quiet_progress_requires_moving(self):
        with tempfile.TemporaryDirectory() as folder:
            p=AchievementProfile(folder);s=outdoor();s.backpack.add("tape");s.use_item("tape")
            for _ in range(210):s.update(.05)
            self.assertNotIn("quiet_steps",p.observe(s))
            s.run_stats["quiet_seconds"]=10;p.observe(s);p.save()
            s.collect_item("energy");p.observe(s);p.save()
            Path(folder,"achievements.json").write_text("truncated",encoding="utf-8")
            r=AchievementProfile(folder);self.assertTrue(r.recovered);self.assertIn("quiet_steps",r.unlocked)


class BackpackAppTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.a=App(self.tmp.name,audio=False)
    def tearDown(self):pygame.quit();self.tmp.cleanup()
    def key(self,key,unicode=""):
        self.a.events([pygame.event.Event(pygame.KEYDOWN,key=key,unicode=unicode,mod=0)])

    def test_backpack_pauses_world_and_keyboard_use_returns_to_play(self):
        a=self.a;a.start(42);s=a.session;s.monsters=[];s.health=70
        self.key(pygame.K_b);self.assertEqual(a.mode,"backpack")
        elapsed=s.elapsed;position=s.player.copy();a.update(.5,{pygame.K_d:True})
        self.assertEqual(s.elapsed,elapsed);self.assertEqual(s.player,position)
        a.action("bag_select:bandage");self.key(pygame.K_RETURN)
        self.assertEqual(s.health,90);self.assertEqual(a.mode,"playing")
        self.assertIn("first_aid",a.achievements.unlocked)
        a.update(.02,{});self.assertIsNotNone(a.achievement_toast)
        self.assertEqual(a.mode,"playing")

    def test_story_dialogue_blocks_quick_use_and_bag_key_items_are_readonly(self):
        a=self.a;a.start_story();s=a.session;s.health=30;s.backpack.add("medkit")
        self.key(pygame.K_1,"1");self.assertEqual(s.health,30)
        self.key(pygame.K_b);self.assertEqual(a.mode,"playing")
        s.finish_cutscene();s.dialogue=[];s.story_items.add("Kunci servis");a.action("backpack");self.key(pygame.K_TAB)
        self.assertEqual(a.bag_tab,"keys");a.draw()
        self.key(pygame.K_x);self.assertIn("Kunci servis",s.story_items)
        self.key(pygame.K_ESCAPE);self.assertEqual(a.mode,"playing")

    def test_achievement_menu_paging_and_durable_profile(self):
        a=self.a;a.start(42);a.session.monsters=[];a.session.collect_item("medkit");a.update(.02,{})
        a.set_mode("pause");a.action("achievements");a.draw()
        self.assertEqual(a.mode,"achievements");self.key(pygame.K_RIGHT);a.draw()
        self.assertEqual(a.achievement_page,1);self.key(pygame.K_ESCAPE);self.assertEqual(a.mode,"pause")
        self.assertIn("supplies",AchievementProfile(self.tmp.name).unlocked)


if __name__=="__main__":unittest.main()
