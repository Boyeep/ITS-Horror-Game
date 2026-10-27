"""Campaign progression, fair encounter cues and persistent UI flows."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import json
import tempfile
import unittest
from pathlib import Path

import pygame
from horror.app import App
from horror.audio import Audio
from horror.campus import CampusLayout
from horror.simulation import Monster, Session
from horror.story import StorySession
from tools.campaign_driver import CampaignDriver


def dismiss(session):
    while session.dialogue or session.cutscene:
        if session.cutscene:session.finish_cutscene()
        else:session.next_dialogue()


class StoryTests(unittest.TestCase):
    def test_geography_and_all_quest_sites_are_reachable(self):
        layout=CampusLayout()
        self.assertEqual(layout.validate(),[])
        r=layout.centers[15];i=layout.centers[11];p=layout.centers[22];g=layout.centers[6]
        self.assertTrue(i[0]>r[0] and i[1]<r[1])
        self.assertTrue(p[0]>r[0] and p[1]>r[1])
        self.assertLess(g[0],r[0])
        for n in range(30):
            if n!=layout.spawn_room:self.assertTrue(layout.path(layout.tile(layout.spawn),layout.centers[n]))
        self.assertEqual(layout.grid,CampusLayout().grid)

    def test_modal_freezes_motion_health_and_enemies(self):
        s=StorySession()
        s.monsters=[Monster("Penjaga",s.player.copy(),pygame.Vector2(1,0))]
        start=s.player.copy()
        s.update(.05,(1,0),True)
        self.assertEqual(s.elapsed,0)
        self.assertEqual(s.player,start)
        self.assertEqual(s.health,100)

    def test_code_and_terminal_errors_do_not_softlock(self):
        s=StorySession();dismiss(s);s.stage=2;s.keypad=True;s.code="1111"
        self.assertFalse(s.submit_code());self.assertTrue(s.keypad)
        s.code="2413";self.assertTrue(s.submit_code());dismiss(s)
        self.assertEqual(s.stage,3);self.assertEqual(len(s.fuses),2)
        s.stage=4;s.press_terminal(21);self.assertEqual(s.terminals,[])
        s.press_terminal(7);s.press_terminal(2);self.assertEqual(s.terminals,[])
        for room in (7,21,2):s.press_terminal(room)
        self.assertEqual(s.stage,5)
        self.assertTrue(s.dialogue)

    def test_complete_story_via_real_walks_doors_items_and_panel(self):
        s=StorySession("easy");report=CampaignDriver(s).run()
        self.assertEqual(report["status"],"won")
        self.assertEqual(set(report["stages"]),set(range(25)))
        self.assertEqual(report["stairs"],24)
        self.assertTrue(s.signal_off and s.power)
        self.assertGreater(report["steps"],10000)
        self.assertIn("5:3",report["floors"])
        self.assertIn("sunyi",s.journal)
        self.assertIsNotNone(s.companion)

    def test_scripted_reveal_has_safe_gap_and_checkpoint_preserves_puzzle(self):
        s=StorySession();dismiss(s)
        s.use_stairs("enter",22)
        s.player=s.point(22,floor=1);s.stage=1;s.interact_cooldown=0;s.interact();dismiss(s)
        self.assertEqual(len(s.monsters),1)
        self.assertGreater(s.monsters[0].pos.distance_to(s.player),130)
        self.assertTrue(s.player_can_see(s.monsters[0]))
        self.assertEqual(s.encounter_count,1)
        s.stage=4;s.collected=2;s.terminals=[7];s.bottles=3;s.play_seconds=94
        restored=StorySession("normal",json.loads(json.dumps(s.snapshot())))
        self.assertEqual(restored.stage,4);self.assertEqual(restored.terminals,[7])
        self.assertEqual(restored.goal_rooms,[21]);self.assertEqual(restored.play_seconds,94)
        self.assertEqual(restored.health,100);self.assertFalse(restored.modal)

    def test_stinger_requires_visibility_and_has_cooldown(self):
        s=StorySession();dismiss(s)
        m=Monster("Penjaga",s.player+pygame.Vector2(80,0),pygame.Vector2(-1,0))
        self.assertTrue(s.startle(m));self.assertFalse(s.startle(m))
        s.encounter_cooldown=0;m.pos=s.player+pygame.Vector2(600,0)
        self.assertFalse(s.startle(m))
        m.pos=s.player+pygame.Vector2(0,-200)
        self.assertFalse(s.startle(m))
        self.assertEqual(s.encounter_count,1)

    def test_continuously_visible_monster_does_not_repeat_stinger(self):
        s=StorySession();dismiss(s)
        m=Monster("Penjaga",s.player+pygame.Vector2(80,0),pygame.Vector2(-1,0),wait=100)
        s.monsters=[m]
        for _ in range(400):s.update(.05)
        self.assertEqual(s.encounter_count,1)
        self.assertTrue(s.chase_active)
        m.pos=s.player+pygame.Vector2(600,0);s.update(.05)
        self.assertFalse(s.chase_active)
        m.pos=s.player+pygame.Vector2(80,0);s.update(.05)
        self.assertEqual(s.encounter_count,2)


class StoryAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.app=App(self.tmp.name,audio=False)
    def tearDown(self):
        pygame.quit();self.tmp.cleanup()
    def key(self,key,unicode=""):
        self.app.events([pygame.event.Event(pygame.KEYDOWN,key=key,unicode=unicode,mod=0)])
    def test_both_modes_continue_keypad_journal_and_separate_stats(self):
        app=self.app
        self.assertTrue({"story","start"}.issubset({b.action for b in app.buttons}))
        app.action("story");s=app.session;dismiss(s)
        s.stage=2;s.note("rak");s.keypad=True
        app.update(.05,{pygame.K_d:True});self.assertEqual(s.elapsed,0)
        for c in "2413":self.key(ord(c),c)
        self.key(pygame.K_RETURN);dismiss(s);app.update(.05,{})
        self.assertEqual(s.stage,3)
        self.key(pygame.K_j);self.assertTrue(s.journal_open)
        app.draw();self.key(pygame.K_ESCAPE);self.assertFalse(s.journal_open)
        app.action("menu");app.draw()
        self.assertIn("continue_story",[b.action for b in app.buttons])
        app.action("continue_story");self.assertEqual(app.session.stage,3)
        app.session.status="won";app.session.ending_pending=True;app.update(.01,{})
        self.assertEqual(app.settings["wins"],0)
        self.assertIsNone(app.settings["best_seconds"])
        self.assertIsNone(app.story_checkpoint)
        app.action("start");self.assertIs(type(app.session),Session)
    def test_corrupt_checkpoint_falls_back_without_crash(self):
        app=self.app
        data={"version":1,"stage":4,"difficulty":"normal","player":None}
        Path(self.tmp.name,"story.json").write_text(json.dumps(data),encoding="utf-8")
        app.story_checkpoint=app.load_story();app.start_story(resume=True)
        self.assertEqual(app.session.stage,0)
        self.assertTrue(app.session.cutscene)
    def test_real_music_and_creature_audio_decode_and_crossfade(self):
        audio=Audio();s=StorySession();dismiss(s)
        self.assertGreater(audio.music[0].get_length(),30)
        self.assertGreater(audio.music[1].get_length(),4)
        self.assertLessEqual(audio.sounds["stinger"].get_length(),1.16)
        self.assertTrue(all(audio.banks["monster_"+k][0].get_length()>.1 for k in ("guard","listener","ambusher")))
        for _ in range(100):audio.update_context(.05,s,"playing",.6)
        self.assertLess(audio.chase_mix,.01)
        s.chase_active=True
        for _ in range(60):audio.update_context(.05,s,"playing",.6)
        self.assertGreater(audio.chase_mix,.99)
        self.assertGreater(audio.music_channels[1].get_volume(),0)
        audio.update_context(.05,s,"playing",0)
        self.assertEqual(audio.music_channels[0].get_volume(),0)
        self.assertEqual(audio.music_channels[1].get_volume(),0)


if __name__=="__main__":unittest.main()
