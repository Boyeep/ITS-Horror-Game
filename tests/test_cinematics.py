"""Timed cinematics freeze real simulation and survive saves without replaying cues."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import json
import tempfile
import unittest
import pygame
from horror.app import App
from horror.story import StorySession
from horror.cinematics import CUTSCENES
from horror.saves import SaveStore


class CinematicTests(unittest.TestCase):
    def test_intro_has_timed_handoff_without_moving_or_damaging_real_player(self):
        s=StorySession();position=s.player.copy();items=dict(s.backpack.items)
        self.assertEqual(s.cutscene["id"],"intro")
        for _ in range(110):s.update(.05,(1,0),True,False,True,s.player+pygame.Vector2(100,0))
        self.assertEqual(s.player,position);self.assertEqual(s.health,100)
        self.assertEqual(s.elapsed,0);self.assertEqual(s.play_seconds,0);self.assertEqual(s.backpack.items,items)
        self.assertTrue(s.cutscene)
        for _ in range(round(CUTSCENES["intro"]/.05)-109):s.update(.05)
        self.assertIsNone(s.cutscene);self.assertFalse(s.modal);self.assertIn("intro",s.seen_scenes)
        s.update(.05,(1,0));self.assertGreater(s.player.x,position.x)

    def test_scene_and_pending_reveal_roundtrip_and_audio_does_not_repeat(self):
        s=StorySession();s.cutscene["time"]=36.5;s.audio_events=[]
        with tempfile.TemporaryDirectory() as folder:
            store=SaveStore(folder);store.write("1",s.snapshot());saved=store.read("1")
            r=StorySession(checkpoint=saved)
            self.assertEqual(r.cutscene,{"id":"intro","time":36.5})
            r.update(.05);self.assertFalse(any(event[0]=="phone_vibrate" for event in r.audio_events))
            for _ in range(12):r.update(.05)
            self.assertEqual(sum(e[0]=="phone_vibrate" for e in r.audio_events),1)
        s.finish_cutscene();s.use_stairs("enter",22);s.player=s.point(22,floor=1);s.stage=1
        s.handle_quest("note")
        while s.dialogue:s.next_dialogue()
        self.assertEqual(s.cutscene["id"],"library");self.assertFalse(s.monsters)
        r=StorySession(checkpoint=json.loads(json.dumps(s.snapshot())))
        r.finish_cutscene();self.assertEqual(len(r.monsters),1)
        self.assertGreater(r.monsters[0].pos.distance_to(r.player),130)
        r.finish_cutscene();self.assertEqual(len(r.monsters),1)

    def test_old_save_continues_without_replaying_intro(self):
        s=StorySession();data=s.snapshot();data["version"]=4
        for key in ("cutscene","pending_scene","seen_scenes"):data.pop(key)
        restored=StorySession(checkpoint=data)
        self.assertIsNone(restored.cutscene);self.assertIn("intro",restored.seen_scenes)

    def test_ending_cutscene_completes_before_result_and_cannot_award_twice(self):
        s=StorySession();s.finish_cutscene();s.stage=24;s.status="won";s.wrap_ending()
        while s.dialogue:s.next_dialogue()
        self.assertEqual(s.status,"playing");self.assertEqual(s.cutscene["id"],"ending")
        s.audio_events=[];s.finish_cutscene();s.finish_cutscene()
        self.assertEqual(s.status,"won");self.assertEqual(sum(e[0]=="win" for e in s.audio_events),1)


class CinematicAppTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.a=App(self.folder.name,audio=False);self.a.start_story()
    def tearDown(self):pygame.quit();self.folder.cleanup()
    def key(self,key):self.a.events([pygame.event.Event(pygame.KEYDOWN,key=key,unicode="",mod=0)])

    def test_pause_save_load_and_skip_have_working_inputs(self):
        a=self.a;s=a.session;a.update(.05,{});seconds=s.cutscene["time"]
        self.key(pygame.K_ESCAPE);a.update(.05,{})
        self.assertEqual(s.cutscene["time"],seconds);self.assertEqual(a.mode,"pause")
        a.save_story("1");a.start_story(data=a.save_store.read("1"));self.assertEqual(a.session.cutscene["time"],seconds)
        self.key(pygame.K_b);self.key(pygame.K_e);self.assertTrue(a.session.cutscene)
        a.draw();self.assertEqual(a.buttons,[])
        self.key(pygame.K_ESCAPE);a.draw();button=next(b for b in a.buttons if b.action=="cutscene_skip")
        a.events([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=button.rect.center)])
        self.assertIsNone(a.session.cutscene);self.assertFalse(a.session.modal);self.assertEqual(a.mode,"playing")
        a.start_story();self.key(pygame.K_RETURN);self.assertIsNone(a.session.cutscene)

    def test_all_shots_draw_without_mutating_saved_state_or_camera(self):
        a=self.a;s=a.session
        for kind,duration in CUTSCENES.items():
            for seconds in ((2.,9.,15.,19.,24.,30.,32.5,38.,44.,48.) if kind=="intro" else (duration/2,)):
                s.cutscene={"id":kind,"time":seconds}
                before=json.dumps(s.snapshot(),sort_keys=True);camera=a.renderer.camera.copy()
                a.draw()
                self.assertEqual(json.dumps(s.snapshot(),sort_keys=True),before)
                self.assertEqual(a.renderer.camera,camera)
                self.assertEqual(a.buttons,[])

    def test_characters_and_architecture_have_native_antialiased_images(self):
        a=self.a;a.session.finish_cutscene();a.window=pygame.display.set_mode((1920,1200));a.resize_canvas();a.draw()
        art=a.renderer.art;image=art.student_frame("player",0,(-1,0),(144,192))
        # A nearest enlargement of a 48x64 sprite has identical 3-pixel blocks.
        # Native curves have coverage within those blocks, retaining fine facial lines.
        blocks_differ=any(image.get_at((x,y))!=image.get_at((x+1,y)) for y in range(190) for x in range(0,141,3))
        self.assertTrue(blocks_differ)
        closed=art.architecture("door",(192,228),False,0)
        opened=art.architecture("door",(192,228),False,1)
        self.assertNotEqual(pygame.image.tobytes(closed,"RGBA"),pygame.image.tobytes(opened,"RGBA"))
        up=art.architecture("up",(264,336));down=art.architecture("down",(264,336))
        self.assertNotEqual(pygame.image.tobytes(up,"RGBA"),pygame.image.tobytes(down,"RGBA"))


if __name__=="__main__":unittest.main()
