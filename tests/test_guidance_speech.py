"""Actionable navigation and original character blips follow actual visible text."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy");os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import json
import tempfile
import unittest
import pygame
from horror.app import App
from horror.audio import Audio
from horror.narrative import speech,document
from horror.story import StorySession
from horror.guidance import story_targets,interaction_point
from horror.speech import visible_count,duration,pulses


class SpeechTests(unittest.TestCase):
    def test_typing_freezes_world_and_resume_does_not_replay_letters(self):
        s=StorySession();s.finish_cutscene();s.open_dialogue([speech("nara","Arga, kamu dengar suara itu?")])
        before=s.player.copy();s.audio_events=[]
        for _ in range(16):s.update(.05,(1,0),True)
        self.assertEqual(s.player,before);self.assertEqual(s.play_seconds,0);self.assertEqual(s.health,100)
        self.assertTrue(s.typing);self.assertTrue(any(e[0]=="voice_nara" for e in s.audio_events))
        count=visible_count(s.dialogue[0]["body"],s.dialogue_time)
        self.assertGreater(count,0);self.assertLess(count,len(s.dialogue[0]["body"]))
        saved=json.loads(json.dumps(s.snapshot()));r=StorySession(checkpoint=saved)
        self.assertEqual(r.dialogue_time,s.dialogue_time)
        r.audio_events=[];r.update(.001)
        expected=bool(pulses(r.dialogue[0]["body"],s.dialogue_time,r.dialogue_time))
        self.assertEqual(bool(r.audio_events),expected)
        r.reveal_dialogue();r.audio_events=[];r.update(.05)
        self.assertFalse(r.typing);self.assertFalse(r.audio_events)

    def test_narration_and_documents_are_silent(self):
        s=StorySession();s.finish_cutscene()
        for page in ({"kind":"narration","title":"Malam","body":"Tidak ada suara."},document("rak")):
            s.open_dialogue([page]);s.audio_events=[]
            for _ in range(20):s.update(.05)
            self.assertFalse(s.typing);self.assertFalse(s.audio_events)

    def test_cutscene_blips_only_when_a_character_is_speaking(self):
        s=StorySession();s.audio_events=[]
        s.cutscene["time"]=1.
        for _ in range(12):s.update(.05)
        self.assertFalse(any(e[0].startswith("voice_") for e in s.audio_events))
        s.cutscene["time"]=6.;s.audio_events=[]
        for _ in range(12):s.update(.05)
        self.assertTrue(any(e[0]=="voice_nara" for e in s.audio_events))


class GuidanceTests(unittest.TestCase):
    def test_phone_marker_matches_physical_phone_and_next_goal_leads_outside(self):
        s=StorySession();s.finish_cutscene()
        goal=story_targets(s)[0]
        self.assertEqual(goal.display,pygame.Vector2(s.layout.phone_display))
        self.assertEqual(goal.point,pygame.Vector2(s.layout.phone_interaction))
        s.player=goal.point.copy();s.interact_cooldown=0
        interaction=s.interaction();self.assertIn("Periksa ponsel",interaction[2])
        self.assertEqual(interaction_point(s,interaction),goal.display)
        s.handle_quest("phone");s.dialogue=[]
        goals=story_targets(s)
        self.assertEqual({goal.key for goal in goals},{"building_exit"})
        self.assertTrue(all("Perpustakaan" in goal.label and "Lantai 2" in goal.label for goal in goals))

    def test_floor_guidance_chooses_correct_direction_without_giving_puzzle_answers(self):
        s=StorySession();s.finish_cutscene();s.stage=8
        self.assertTrue(all("Naik" in goal.label for goal in story_targets(s)))
        s.use_stairs("up",(11,"sw"));s.stage=1
        self.assertTrue(all("Turun" in goal.label for goal in story_targets(s)))
        s.use_stairs("enter",22);s.stage=10
        goals=story_targets(s)
        self.assertEqual(len(goals),3)
        self.assertEqual({goal.key for goal in goals},{"catalog:9","catalog:4","catalog:17"})

    def test_power_route_follows_the_current_goal_instead_of_a_nearer_wrong_terminal(self):
        s=StorySession();s.finish_cutscene();s.stage=4;s.switch_level("campus",s.campus.center(s.campus.centers[2]))
        self.assertEqual([goal.key for goal in story_targets(s)],["terminal:7"])
        s.terminals=[7]
        self.assertEqual([goal.key for goal in story_targets(s)],["terminal:21"])
        s.terminals=[7,21]
        self.assertEqual([goal.key for goal in story_targets(s)],["terminal:2"])


class SpeechAppTests(unittest.TestCase):
    def setUp(self):self.folder=tempfile.TemporaryDirectory();self.a=App(self.folder.name,audio=False);self.a.start_story();self.a.session.finish_cutscene()
    def tearDown(self):pygame.quit();self.folder.cleanup()
    def key(self,key):self.a.events([pygame.event.Event(pygame.KEYDOWN,key=key,unicode="",mod=0)])

    def test_first_press_reveals_second_advances_and_pause_freezes_typing(self):
        a=self.a;s=a.session;s.open_dialogue([speech("arga","Kamu masih di sana?"),speech("nara","Jangan buka pintunya.")])
        a.update(.05,{});self.key(pygame.K_ESCAPE);time=s.dialogue_time;a.update(.05,{})
        self.assertEqual(s.dialogue_time,time)
        a.action("resume");self.key(pygame.K_e)
        self.assertEqual(len(s.dialogue),2);self.assertFalse(s.typing)
        self.key(pygame.K_e);self.assertEqual(s.dialogue[0]["speaker"],"nara");self.assertTrue(s.typing)

    def test_native_hud_is_persistent_read_only_and_has_no_baked_world_copy(self):
        a=self.a;s=a.session;s.elapsed=120;s.message_time=0
        a.window=pygame.display.set_mode((1920,1200));a.resize_canvas()
        captured=[];real=a.renderer.text
        def record(surface,body,*args,**kwargs):
            captured.append((surface,str(body)))
            return real(surface,body,*args,**kwargs)
        a.renderer.text=record
        before=json.dumps(s.snapshot(),sort_keys=True);a.draw()
        self.assertEqual(json.dumps(s.snapshot(),sort_keys=True),before)
        self.assertTrue(any(surface==a.screen and body==s.objective for surface,body in captured))
        self.assertFalse(any(surface==a.renderer.world for surface,body in captured))
        self.assertFalse(any("DEMO BESOK" in body or "LOBI / KELUAR" in body for _,body in captured))

    def test_voice_banks_are_original_short_distinct_and_obey_effects_volume(self):
        audio=Audio();self.assertTrue(audio.available)
        for speaker in ("arga","nara"):
            self.assertEqual(len(audio.banks["voice_"+speaker]),3)
            self.assertTrue(all(.03<clip.get_length()<.06 for clip in audio.banks["voice_"+speaker]))
        self.assertNotEqual(audio.banks["voice_arga"][0].get_raw(),audio.banks["voice_nara"][0].get_raw())
        audio.set_volume(0);audio.play("voice_nara")
        self.assertEqual(audio.voice_channel.get_volume(),0)
        audio.stop_voice();self.assertFalse(audio.voice_channel.get_busy())

    def test_door_lighting_never_interpolates_a_one_pixel_source_axis(self):
        a=self.a;s=a.session
        a.window=pygame.display.set_mode((1920,1200));a.resize_canvas()
        original=pygame.transform.smoothscale;seen=[]
        def checked(source,size,*args,**kwargs):
            self.assertGreaterEqual(min(source.get_size()),2)
            if 2 in source.get_size():seen.append(source.get_size())
            return original(source,size,*args,**kwargs)
        pygame.transform.smoothscale=checked
        try:
            for point in (s.layout.spawn,s.layout.phone_interaction):
                s.player=pygame.Vector2(point);a.renderer.update_camera(s,snap=True);a.draw()
        finally:pygame.transform.smoothscale=original
        self.assertTrue(seen)


if __name__=="__main__":unittest.main()
