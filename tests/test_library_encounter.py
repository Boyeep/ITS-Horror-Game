"""The library reveal is readable, persistent and idempotent across presentation and saves."""
import json
import unittest
from pygame import Vector2
from horror.story import StorySession
from horror.cinematics import CUTSCENES


def reading():
    s=StorySession();s.finish_cutscene();s.dialogue=[]
    s.use_stairs("enter",22);s.player=s.point(22,floor=1);s.stage=1;s.elapsed=30.
    s.handle_quest("note")
    return s


def reveal():
    s=reading()
    while s.dialogue:s.next_dialogue()
    return s


class LibraryEncounterTests(unittest.TestCase):
    def test_note_remains_readable_and_journal_keeps_the_clue(self):
        s=reading();position=s.player.copy()
        self.assertIn("rak",s.journal)
        self.assertTrue(s.dialogue)
        for _ in range(300):s.update(.05,(1,0),True)
        self.assertEqual(s.player,position);self.assertEqual(s.health,100)
        self.assertFalse(s.monsters);self.assertIsNone(s.cutscene)

    def test_natural_handoff_uses_the_planned_legal_reveal_once(self):
        s=reveal();position=s.player.copy();elapsed=s.elapsed
        planned=Vector2(s.library_reveal)
        self.assertTrue(s.can_stand(planned,12))
        self.assertTrue(s.layout.line_clear(s.player,planned))
        self.assertGreater(planned.distance_to(s.player),150)
        self.assertGreaterEqual(CUTSCENES["library"],12.)
        while s.cutscene:s.update(.05,(1,0),True)
        self.assertEqual(s.elapsed,elapsed);self.assertEqual(s.player,position)
        self.assertEqual(len(s.monsters),1)
        self.assertEqual(s.monsters[0].pos,planned)
        self.assertEqual(s.monsters[0].state,"chase")
        self.assertGreaterEqual(s.monsters[0].wait,2.)
        self.assertEqual(s.library_pressure,14.)
        self.assertEqual(s.encounter_count,1)
        self.assertEqual(sum(name=="stinger" for name,_,_ in s.audio_events),1)
        s.finish_cutscene();self.assertFalse(s.start_cutscene("library"))
        self.assertEqual(len(s.monsters),1)

    def test_save_after_stinger_resumes_without_replaying_or_respawning(self):
        s=reveal();s.cutscene["time"]=5.4
        r=StorySession(checkpoint=json.loads(json.dumps(s.snapshot())))
        self.assertEqual(r.library_reveal,s.library_reveal)
        for _ in range(20):r.update(.05)
        self.assertFalse(any(name=="stinger" for name,_,_ in r.audio_events))
        r.finish_cutscene();r.finish_cutscene()
        self.assertEqual(len(r.monsters),1)
        saved=StorySession(checkpoint=r.snapshot())
        self.assertIn("library",saved.seen_scenes)
        self.assertIsNone(saved.pending_encounter)
        self.assertEqual(len(saved.monsters),1)
        self.assertGreater(saved.library_pressure,0.)

    def test_journal_freezes_chase_pressure_and_player(self):
        s=reveal();s.finish_cutscene();s.journal_open=True
        point=s.monsters[0].pos.copy();remaining=s.library_pressure
        for _ in range(50):s.update(.05,(1,0),True)
        self.assertEqual(s.library_pressure,remaining)
        self.assertEqual(s.monsters[0].pos,point)
        self.assertEqual(s.health,100)

    def test_stairs_transfer_a_pursuer_instead_of_erasing_it(self):
        s=reveal();s.finish_cutscene()
        s.player=Vector2(s.layout.down)
        m=s.monsters[0];m.pos=Vector2(s.layout.nearest_floor(s.player+Vector2(80,0)))
        m.state="search";m.memory=12.
        s.use_stairs("down",22)
        self.assertEqual(len(s.followers),1)
        for _ in range(60):s.update(.05)
        self.assertFalse(s.followers)
        self.assertEqual(sum(m.kind=="Penjaga" for m in s.monsters),1)
        self.assertGreater(s.monsters[0].memory,8.)

    def test_optional_fields_do_not_replay_old_library_saves(self):
        s=reveal();s.finish_cutscene();data=s.snapshot()
        data.pop("library_reveal");data.pop("library_pressure")
        r=StorySession(checkpoint=data)
        self.assertEqual(r.library_pressure,0.)
        self.assertFalse(r.start_cutscene("library"))
