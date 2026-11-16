"""Real mixer checks for optional cues, lifecycle transitions and independent sliders."""
import os
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import unittest
from types import SimpleNamespace
import pygame
from horror.audio import Audio


class AtmosphereAudioTests(unittest.TestCase):
    def setUp(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.addCleanup(pygame.quit)
        self.audio = Audio()
        self.session = SimpleNamespace(threat=1., encounter_timer=0., health=100, max_health=100,
                                       modal=False, chase_active=True, cutscene=None, status="playing",
                                       layout=SimpleNamespace(is_outdoor=lambda point: True), player=pygame.Vector2())
        self.audio.atmosphere(.5, self.session, 1.)

    def test_pause_and_modal_stop_optional_cues_and_heartbeat(self):
        a = self.audio
        for session in (None, self.session):
            with self.subTest(paused=session is None):
                a.play_atmosphere("breath_heavy", .6)
                self.assertTrue(a.atmosphere_channel.get_busy())
                self.session.modal = True
                a.atmosphere(.1, session, 1.)
                self.assertFalse(a.atmosphere_channel.get_busy())
                self.assertEqual(a.heart_channel.get_volume(), 0.)

    def test_new_session_does_not_inherit_previous_tension_or_breath(self):
        a = self.audio
        a.play_atmosphere("breath_heavy", .6)
        fresh = SimpleNamespace(threat=0., health=100, max_health=100)
        a.atmosphere(.01, fresh, 1.)
        self.assertEqual(a.tension, 0.)
        self.assertEqual(a.heart_channel.get_volume(), 0.)
        self.assertFalse(a.atmosphere_channel.get_busy())

    def test_stinger_interrupts_breath_and_defers_optional_cues(self):
        a = self.audio
        a.play_atmosphere("breath_heavy", .6)
        a.play("stinger")
        self.assertFalse(a.atmosphere_channel.get_busy())
        self.assertFalse(a.gate.allow("enter", 45.))
        a.gate.tick(3.)
        self.assertTrue(a.gate.allow("enter", 45.))

    def test_sound_before_first_context_keeps_its_priority_gap(self):
        a = self.audio
        a.play("stinger")
        a.watched = None
        a.atmosphere(.01, self.session, 1.)
        self.assertFalse(a.gate.allow("enter", 45.))

    def test_effects_mute_is_immediate_and_music_is_independent(self):
        a = self.audio
        a.play_atmosphere("breath_heavy", .6)
        a.set_volume(0.)
        self.assertFalse(a.atmosphere_channel.get_busy())
        self.assertEqual(a.heart_channel.get_volume(), 0.)
        a.update_context(.5, self.session, "playing", music_volume=.7)
        self.assertGreater(a.music_channels[1].get_volume(), 0.)
        self.assertEqual(a.heart_channel.get_volume(), 0.)
        a.set_volume(.65)
        a.update_context(.1, self.session, "playing", music_volume=0.)
        self.assertEqual(a.music_channels[1].get_volume(), 0.)
        self.assertGreater(a.heart_channel.get_volume(), 0.)

    def test_relief_waits_for_chase_and_does_not_repeat(self):
        a, s = self.audio, self.session
        a.breath_wait = 100.
        for _ in range(4):
            a.atmosphere(1., s, 1.)
        s.chase_active = False
        a.atmosphere(.1, s, 1.)
        self.assertEqual(a.counters.get("breath_heavy"), 1)
        self.assertGreater(a.release, 0.)
        a.atmosphere_channel.stop()
        for _ in range(10):
            a.atmosphere(.1, s, 1.)
        self.assertEqual(a.counters.get("breath_heavy"), 1)

    def test_room_entry_does_not_stack_on_a_gameplay_cue(self):
        a = self.audio
        self.session.threat = 0.
        a.tension = 0.
        a.atmosphere(.1, self.session, 1., indoor=False)
        a.play("stinger")
        a.atmosphere(.1, self.session, 1., indoor=True)
        self.assertEqual(a.counters.get("distant", 0), 0)

    def test_new_recordings_are_loaded_and_radio_does_not_repeat(self):
        a = self.audio
        self.assertEqual(len(a.banks["radio"]), 3)
        self.assertEqual(len(a.banks["book"]), 1)
        previous = None
        for _ in range(6):
            a.play("radio")
            self.assertNotEqual(a.last_index["radio"], previous)
            previous = a.last_index["radio"]


if __name__ == "__main__":
    unittest.main()
