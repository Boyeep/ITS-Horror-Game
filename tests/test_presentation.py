"""Regressions for native text, upright poses, occlusion and persistent readers."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import json
import tempfile
import unittest
import pygame
from horror.app import App
from horror.story import StorySession, NOTES
from horror.narrative import speech, document, DOCUMENT_KINDS, DOCUMENT_TEXT
from horror.reader import StoryReader
from horror.saves import SaveStore


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.a=App(self.folder.name,audio=False)
    def tearDown(self):
        pygame.quit();self.folder.cleanup()

    def test_button_ink_center_at_native_and_windows_125_percent_resolution(self):
        a=self.a
        for dimensions in ((1280,800),(1920,1200),(960,700)):
            a.window=pygame.display.set_mode(dimensions);a.resize_canvas()
            self.assertEqual(a.screen.get_size(),dimensions)
            for label in ("Simpan","Lanjut cerita","Kembali","Pengaturan"):
                target=(100,240,220,44)
                ink=a.renderer.centered_text(a.screen,label,target,18)
                box=a.renderer.draw.box(a.screen,target)
                self.assertLessEqual(abs(ink.centerx-box.centerx),1)
                self.assertLessEqual(abs(ink.centery-box.centery),1)
                native_center=a.renderer.draw.point(a.screen,pygame.Rect(target).center)
                self.assertLess(a.to_canvas(native_center).distance_to(pygame.Rect(target).center),1)

    def test_four_directions_keep_head_above_feet(self):
        art=self.a.renderer.art
        for kind in ("player","nara"):
            poses=[art.student_frame(kind,0,d) for d in ((1,0),(0,1),(-1,0),(0,-1))]
            for pose in poses:
                self.assertEqual(pose.get_size(),(48,64))
                bounds=pose.get_bounding_rect()
                self.assertGreater(bounds.height,bounds.width*1.5)
                self.assertGreaterEqual(bounds.bottom,61)
            self.assertEqual(len({pygame.image.tobytes(p,"RGBA") for p in poses}),4)
        self.assertNotEqual(pygame.image.tobytes(art.portrait("arga",(180,210)),"RGBA"),pygame.image.tobytes(art.portrait("nara",(180,210)),"RGBA"))

    def test_flashlight_ray_stops_at_closed_door_and_passes_when_open(self):
        a=self.a;a.start_story();s=a.session;r=a.renderer
        for cell,door in s.layout.doors.items():
            if door.passage:continue
            direction=pygame.Vector2(1,0) if door.vertical else pygame.Vector2(0,1)
            origin=pygame.Vector2(s.layout.center(cell))-direction*60
            if not s.layout.blocks_sight(s.layout.tile(origin)) and not s.layout.blocks_sight(s.layout.tile(origin+direction*100)):break
        else:self.fail("No test door")
        door.opened=False;closed=r.ray_end(s.layout,origin,direction,140).length()
        door.opened=True;opened=r.ray_end(s.layout,origin,direction,140).length()
        self.assertLess(closed,60);self.assertGreater(opened,80)
        hand,lens=r.torch_position(s)
        self.assertGreater(hand.distance_to(s.player),10)
        self.assertGreater((lens-hand).dot(s.facing),0)
        beam=r.beam_glow
        self.assertGreater(beam.get_at((80,170)).r,beam.get_at((80,70)).r)
        self.assertGreater(beam.get_at((80,170)).r,beam.get_at((330,170)).r)

    def test_story_objects_choose_documents_and_real_speakers(self):
        s=StorySession();s.finish_cutscene();s.dialogue=[];s.handle_quest("phone")
        self.assertEqual(s.dialogue[0]["kind"],"message")
        self.assertEqual(s.dialogue[1]["speaker"],"arga")
        s.handle_quest("note");self.assertEqual(s.dialogue[0]["kind"],"paper")
        s.stage=6;s.handle_quest("log");self.assertEqual(s.dialogue[0]["kind"],"book")
        s.stage=15;s.handle_quest("nara")
        self.assertEqual(s.dialogue[-2]["speaker"],"nara")
        self.assertEqual(s.dialogue[-1]["document"],"nara")

    def test_save_reader_survives_new_and_legacy_dialogue_formats(self):
        s=StorySession();s.open_dialogue([document("rak"),speech("nara","Jangan jawab ponselnya.")])
        store=SaveStore(self.folder.name);store.write("1",s.snapshot())
        r=StorySession(checkpoint=store.read("1"));self.assertEqual(r.dialogue,s.dialogue)
        old=json.loads(json.dumps(s.snapshot()));old["version"]=3
        old["dialogue"]=[["Buku jaga",NOTES["jaga"][1]],["Nara","Aku di SCC."]]
        store.write("2",old);restored=StorySession(checkpoint=store.read("2"))
        self.assertEqual(restored.dialogue,[document("jaga"),speech("nara","Aku di SCC.")])

    def test_all_evidence_readers_render_and_pause_with_working_continue(self):
        a=self.a;a.start_story();s=a.session;s.finish_cutscene()
        for key in DOCUMENT_KINDS:
            s.open_dialogue([document(key)]);before=s.player.copy();seconds=s.elapsed
            a.update(.05,{});a.draw()
            self.assertEqual(s.player,before);self.assertEqual(s.elapsed,seconds)
            a.events([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_e,unicode="e",mod=0)])
            self.assertFalse(s.dialogue)
        s.journal=list(NOTES);s.journal_open=True
        for i in range(len(s.journal)):
            s.journal_page=i;a.draw();self.assertEqual(s.journal_page,i)

    def test_paper_text_fits_small_layout_without_losing_clues(self):
        a=self.a;reader=StoryReader(a.renderer)
        for key in ("rak","jalur","nara","insiden","foto"):
            rect=(50,200,385 if key=="foto" else 471,390)
            bottom=reader.fitted(a.screen,DOCUMENT_TEXT[key],rect,21,"georgia")
            self.assertLessEqual(bottom,rect[1]+rect[3])
        self.assertIn("2, 4, 1, 3",DOCUMENT_TEXT["rak"])
        self.assertIn("A, C, B",DOCUMENT_TEXT["insiden"])


if __name__=="__main__":unittest.main()
