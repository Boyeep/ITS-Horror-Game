"""All four terminal routes, with frozen gameplay and idempotent result bookkeeping."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy");os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import tempfile
import unittest
import pygame
from horror.app import App
from horror.audio import Audio


class OutcomeTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.a=App(self.folder.name,audio=False);self.addCleanup(pygame.quit)

    def key(self,key,repeat=False):
        return pygame.event.Event(pygame.KEYDOWN,key=key,unicode="",mod=0,repeat=repeat)

    def terminal(self,story=False,won=False):
        a=self.a
        if story:
            a.start_story();a.session.finish_cutscene();a.session.dialogue=[]
        else:a.start(42)
        a.session.status="won" if won else "lost"
        if not won:a.session.health=0;a.session.last_attacker="Penjaga"
        a.begin_result()
        return a.session

    def test_story_and_escape_death_freeze_the_session_then_show_results(self):
        for story in (False,True):
            with self.subTest(story=story):
                s=self.terminal(story);a=self.a
                self.assertEqual(a.mode,"outcome")
                before=(list(s.player),s.elapsed,s.health,dict(s.backpack.items))
                for _ in range(120):a.update(.05,{pygame.K_d:True,pygame.K_LSHIFT:True})
                self.assertEqual(a.mode,"result")
                self.assertEqual((list(s.player),s.elapsed,s.health,dict(s.backpack.items)),before)
                self.assertIsNone(a.outcome)

    def test_escape_success_is_presented_and_counted_only_once(self):
        a=self.a;s=self.terminal(won=True)
        self.assertEqual(a.mode,"outcome");self.assertTrue(a.outcome.won)
        wins=a.settings["wins"];a.begin_result();a.begin_result()
        self.assertEqual(a.settings["wins"],wins)
        for _ in range(140):a.update(.05,{})
        self.assertEqual(a.mode,"result")
        a.begin_result();self.assertEqual(a.settings["wins"],wins)

    def test_story_success_reuses_its_existing_ending(self):
        a=self.a;a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[]
        s.stage=24;s.status="won";s.wrap_ending()
        while s.dialogue:s.next_dialogue()
        self.assertEqual(s.cutscene["id"],"ending")
        s.finish_cutscene();a.update(.05,{})
        self.assertEqual(a.mode,"result");self.assertIsNone(a.outcome)
        self.assertIn("ending",s.seen_scenes)

    def test_pause_and_resume_preserve_time_and_do_not_expose_dead_saves(self):
        a=self.a;self.terminal(story=True);a.update(.05,{})
        seconds=a.outcome.time
        a.events([self.key(pygame.K_ESCAPE)])
        self.assertEqual(a.mode,"pause")
        for _ in range(10):a.update(.05,{})
        self.assertEqual(a.outcome.time,seconds)
        a.draw();actions={b.action for b in a.buttons}
        self.assertIn("cutscene_skip",actions);self.assertNotIn("save_menu",actions);self.assertNotIn("backpack",actions)
        a.action("resume");self.assertEqual(a.mode,"outcome")
        a.action("cutscene_skip");self.assertEqual(a.mode,"result")

    def test_confirm_skip_does_not_retry_from_the_same_event_batch_or_repeat(self):
        a=self.a;self.terminal();a.draw();original=a.session
        a.events([self.key(pygame.K_RETURN),self.key(pygame.K_RETURN),self.key(pygame.K_e)])
        a.draw();self.assertEqual(a.mode,"result");self.assertIs(a.session,original)
        a.events([self.key(pygame.K_RETURN,repeat=True)])
        self.assertIs(a.session,original)
        a.events([pygame.event.Event(pygame.KEYUP,key=pygame.K_RETURN),self.key(pygame.K_RETURN)])
        self.assertEqual(a.mode,"playing");self.assertIsNot(a.session,original)
        self.assertIsNone(a.outcome)

    def test_mouse_skip_and_retry_start_a_fresh_presentation_lifecycle(self):
        a=self.a;self.terminal();a.draw()
        button=next(b for b in a.buttons if b.action=="outcome_skip")
        a.events([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=button.rect.center)])
        self.assertEqual(a.mode,"result")
        a.action("retry");self.assertEqual(a.mode,"playing")
        self.assertIsNone(a.result_session);self.assertIsNone(a.outcome)
        a.session.status="lost";a.begin_result();self.assertEqual(a.mode,"outcome")

    def test_story_death_preserves_the_previous_checkpoint_on_retry(self):
        a=self.a;a.start_story();a.session.finish_cutscene();a.session.dialogue=[];a.session.stage=3
        a.save_story();checkpoint=a.save_store.read("auto")
        a.session.status="lost";a.session.health=0;a.begin_result();a.finish_outcome()
        self.assertFalse(a.save_story())
        self.assertEqual(a.save_store.read("auto"),checkpoint)
        a.action("retry");self.assertEqual(a.session.stage,3);self.assertEqual(a.session.health,100)
        self.assertIsNone(a.outcome)

    def test_drawing_and_resizing_either_outcome_does_not_mutate_gameplay(self):
        a=self.a
        for won in (False,True):
            s=self.terminal(won=won)
            before=(list(s.player),s.health,s.elapsed,s.status)
            for reduced in (False,True):
                a.settings["reduced_motion"]=reduced
                for size in ((960,700),(1920,1200)):
                    a.window=pygame.display.set_mode(size);a.resize_canvas()
                    for t in (0.,2.,4.5):a.outcome.time=t;a.draw()
            self.assertEqual((list(s.player),s.health,s.elapsed,s.status),before)

    def test_pause_and_skip_end_transient_audio_without_stopping_music_loops(self):
        a=self.a;a.audio=Audio();self.terminal()
        a.audio.play("caught");a.set_mode("pause")
        for index in range(5,pygame.mixer.get_num_channels()):
            if index==6 and hasattr(a.audio,"heart_channel"):
                self.assertEqual(pygame.mixer.Channel(index).get_volume(),0.)
            else:self.assertFalse(pygame.mixer.Channel(index).get_busy())
        self.assertTrue(a.audio.music_channels[0].get_busy())
        a.action("resume");a.audio.play("caught");a.finish_outcome()
        self.assertEqual(a.mode,"result")
