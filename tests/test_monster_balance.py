"""Fair reaction windows, persistent attacks and difficulty pressure on real movement."""
import unittest
from pygame import Vector2
from horror.simulation import Session, Monster
from horror.story import StorySession


def arena(difficulty="normal", kind="Penjaga", distance=20):
    s=Session(42,difficulty);w,h=s.layout.width,s.layout.height
    s.layout.grid=[[int(x in (0,w-1) or y in (0,h-1)) for x in range(w)] for y in range(h)]
    s.layout.doors={};s.layout.glass=set();s.layout.ensure_hill_map(force=True)
    s.player=Vector2(s.layout.center((12,12)))
    m=Monster(kind,s.player-Vector2(distance,0),Vector2(1,0))
    s.monsters=[m];s.elapsed=20.;s.audio_events=[]
    return s,m


class MonsterBalanceTests(unittest.TestCase):
    def test_contact_gives_a_cue_before_damage(self):
        for difficulty in ("easy","normal","hard"):
            for kind in ("Penjaga","Pendengar"):
                with self.subTest(difficulty=difficulty,kind=kind):
                    s,m=arena(difficulty,kind)
                    s.update(.05)
                    self.assertEqual(s.health,100)
                    self.assertEqual(m.state,"attack")
                    self.assertGreaterEqual(m.timer,.45)
                    self.assertTrue(any(name in ("heavy","whisper") for name,_,_ in s.audio_events))
                    for _ in range(20):s.update(.05)
                    self.assertLess(s.health,100)
                    self.assertEqual(s.hits_taken,1)

    def test_moving_out_of_windup_evades_damage(self):
        s,m=arena();s.update(.05)
        for _ in range(15):s.update(.05,(1,0),sprint=True)
        self.assertEqual(s.health,100)
        self.assertGreater(m.cooldown,0)

    def test_passive_walking_is_not_an_automatic_melee_dodge(self):
        s,m=arena();s.update(.05)
        for _ in range(15):s.update(.05,(1,0))
        self.assertLess(s.health,100)

    def test_attack_cannot_hit_through_a_door_or_wall(self):
        s,m=arena();s.update(.05)
        s.layout.grid[12][11]=1
        m.pos=Vector2(s.layout.center((10,12)))
        for _ in range(15):s.update(.05)
        self.assertEqual(s.health,100)

    def test_normal_and_hard_close_distance_faster_without_teleporting(self):
        distances=[]
        for difficulty in ("easy","normal","hard"):
            s,m=arena(difficulty,distance=240)
            initial=m.pos.copy()
            for _ in range(15):
                before=m.pos.copy();s._update_monster(m,.05)
                self.assertLessEqual(m.pos.distance_to(before),11.)
                self.assertTrue(s.can_stand(m.pos,12))
            distances.append(m.pos.distance_to(initial))
        self.assertLess(distances[0],distances[1])
        self.assertLess(distances[1],distances[2])

    def test_easy_spawn_grace_prevents_windup_and_damage(self):
        s,m=arena("easy");s.elapsed=0.
        for _ in range(30):s.update(.05)
        self.assertEqual(s.health,100)
        self.assertNotEqual(m.state,"attack")

    def test_hidden_quiet_player_is_not_acquired_through_walls(self):
        s,m=arena("hard",distance=160)
        s.layout.grid[12][10]=1
        s.last_mode="crouch";s.moving=True;s.flashlight=False
        self.assertFalse(s.sees_player(m))
        self.assertEqual(s.neighborhood_signature(m),0.)

    def test_save_load_preserves_partial_melee_windup(self):
        s=StorySession();s.finish_cutscene();s.dialogue=[]
        m=Monster("Penjaga",s.player-Vector2(20,0),Vector2(1,0),state="attack",timer=.3)
        s.monsters=[m]
        restored=StorySession(checkpoint=s.snapshot())
        self.assertEqual(restored.monsters[0].state,"attack")
        self.assertAlmostEqual(restored.monsters[0].timer,.3)
