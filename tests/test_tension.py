"""Atmosphere helpers: tension is read-only, builds fast, drains slowly, and cues respect cooldowns."""
import unittest
from types import SimpleNamespace

from horror.tension import CueGate, approach, light_dip, tension_level


class TensionTests(unittest.TestCase):
    def test_calm_session_has_no_tension(self):
        self.assertEqual(tension_level(SimpleNamespace(threat=0., encounter_timer=0., health=100, max_health=100)), 0.)

    def test_threat_and_encounter_raise_tension(self):
        self.assertAlmostEqual(tension_level(SimpleNamespace(threat=.6, encounter_timer=0., health=100, max_health=100)), .6)
        self.assertEqual(tension_level(SimpleNamespace(threat=0., encounter_timer=.65, health=100, max_health=100)), 1.)

    def test_low_health_adds_tension_only_below_half(self):
        make = lambda health: SimpleNamespace(threat=0., encounter_timer=0., health=health, max_health=100)
        self.assertEqual(tension_level(make(60)), 0.)
        self.assertGreater(tension_level(make(20)), tension_level(make(40)) )
        self.assertLessEqual(tension_level(make(0)), 1.)

    def test_missing_fields_do_not_break(self):
        self.assertEqual(tension_level(SimpleNamespace()), 0.)

    def test_tension_builds_faster_than_it_drains(self):
        up = approach(0., 1., .2)
        down = 1. - approach(1., 0., .2)
        self.assertGreater(up, down)
        self.assertLessEqual(approach(0., 1., 10.), 1.)

    def test_cue_gate_spaces_cues_and_honours_cooldown(self):
        gate = CueGate(gap=2.)
        self.assertTrue(gate.allow("breath", 5.))
        self.assertFalse(gate.allow("whisper", 1.))      # global gap blocks stacking
        gate.tick(2.1)
        self.assertTrue(gate.allow("whisper", 1.))       # gap over, different cue
        gate.tick(2.1)
        self.assertFalse(gate.allow("breath", 5.))       # own cooldown still running
        gate.tick(3.)
        self.assertTrue(gate.allow("breath", 5.))


class LightDipTests(unittest.TestCase):
    @staticmethod
    def sweep(level, seconds=120):
        """Return (share of time dipping, most dip onsets seen in any one second)."""
        steps, active, on, per_second = seconds * 60, 0, False, {}
        for i in range(steps):
            dipping = light_dip(i / 60, level) > 0
            active += dipping
            if dipping and not on:
                per_second[i // 60] = per_second.get(i // 60, 0) + 1
            on = dipping
        return active / steps, max(per_second.values(), default=0)

    def test_dip_stays_between_zero_and_one(self):
        for level in (0., .5, 1.):
            for i in range(600):
                self.assertTrue(0. <= light_dip(i / 10, level) <= 1.)

    def test_calm_is_almost_never_dipping(self):
        self.assertLess(self.sweep(0.)[0], .01)

    def test_more_tension_means_more_dipping(self):
        shares = [self.sweep(level)[0] for level in (0., .3, .6, 1.)]
        self.assertEqual(shares, sorted(shares))
        self.assertGreater(shares[-1], shares[0] + .1)

    def test_never_more_than_three_dips_in_a_second(self):
        """Photosensitivity guard: keep light changes within the common 3-per-second limit."""
        for level in (0., .3, .6, 1.):
            self.assertLessEqual(self.sweep(level)[1], 3)


if __name__ == "__main__":
    unittest.main()