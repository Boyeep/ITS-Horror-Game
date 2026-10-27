"""Persistent floors, independent saves, world materials and pose-driven shadows."""
import json
import os
import tempfile
import unittest
from pathlib import Path
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame
from horror.app import App
from horror.art import Art
from horror.audio import Audio
from horror.campus import CampusLayout,FLOOR_COUNTS
from horror.floors import BuildingLayout
from horror.saves import SaveStore
from horror.simulation import Monster
from horror.story import StorySession


def session():
    s=StorySession();s.finish_cutscene();s.dialogue=[];s.switch_level("campus",s.campus.spawn);s.interact_cooldown=0;return s


class ExpansionTests(unittest.TestCase):
    def test_all_floors_have_walkable_stairs_and_quest_rooms(self):
        for building,count in FLOOR_COUNTS.items():
            for floor in range(1,count):
                layout=BuildingLayout(building,floor)
                self.assertEqual(layout.validate(),[])
                reachable=layout.reachable(layout.tile(layout.spawn))
                for pos in [layout.down,*[layout.quest_point(i) for i in range(4)]]:
                    self.assertIn(layout.tile(pos),reachable)
                if layout.up:self.assertIn(layout.tile(layout.up),reachable)
        self.assertRaises(ValueError,BuildingLayout,5,4)

    def test_outdoor_materials_follow_geometry(self):
        layout=CampusLayout();self.assertTrue(layout.is_outdoor(layout.center((40,105))))
        self.assertTrue(layout.is_outdoor(layout.spawn))
        self.assertEqual(layout.surface_at(layout.center((35,100))),"asphalt")
        self.assertEqual(layout.surface_at(layout.center((12,108))),"grass")
        self.assertIn("concrete",{m for row in layout.materials for m in row})
        self.assertEqual(BuildingLayout(5,3).surface_at((200,200)),"metal")

    def test_floor_loot_doors_hp_and_pending_chase_survive_roundtrip(self):
        s=session();s.health=41;s.bottles=1;s.stage=9;s.panel_progress=1.4;s.exhausted=True
        s.use_stairs("enter",22);s.medkits=[]
        door=next(iter(s.layout.doors));s.layout.toggle_door(door)
        s.use_stairs("up",22);s.player=pygame.Vector2(s.layout.quest_point(3));s.stamina=23
        m=Monster("Pendengar",s.player+pygame.Vector2(90,0),pygame.Vector2(-1,0),state="search",memory=4)
        s.monsters=[m];s.sequences["catalog"]=[4];s.switches=[True,False,True]
        data=json.loads(json.dumps(s.snapshot()));r=StorySession(checkpoint=data)
        self.assertEqual(r.level_key,"22:2");self.assertEqual(r.health,41)
        self.assertEqual(r.bottles,1);self.assertEqual(r.stamina,23)
        self.assertEqual(r.panel_progress,1.4);self.assertTrue(r.exhausted)
        self.assertEqual(r.player,s.player);self.assertEqual(r.monsters[0].kind,"Pendengar")
        r.use_stairs("down",22)
        self.assertEqual(r.medkits,[]);self.assertTrue(r.layout.doors[door].opened)
        self.assertEqual(r.sequences["catalog"],[4])

    def test_pursuer_uses_delayed_stairs_and_cannot_hit_on_arrival(self):
        s=session();s.elapsed=20
        s.player=pygame.Vector2(s.campus.stairs[22])
        m=Monster("Penjaga",s.player+pygame.Vector2(-80,0),pygame.Vector2(1,0),state="chase")
        s.monsters=[m];s.use_stairs("enter",22)
        self.assertEqual(s.monsters,[]);self.assertEqual(len(s.followers),1)
        for _ in range(30):s.update(.05)
        self.assertEqual(s.health,100);self.assertEqual(s.monsters,[])
        for _ in range(30):s.update(.05)
        self.assertEqual(len(s.monsters),1);self.assertEqual(s.monsters[0].kind,"Penjaga")

    def test_new_puzzles_reject_errors_and_keep_progress_for_save(self):
        s=session();s.stage=10
        s.press_sequence("catalog",17);self.assertEqual(s.sequences["catalog"],[])
        for n in (4,17,9):s.press_sequence("catalog",n)
        self.assertEqual(s.stage,11)
        s.finish_cutscene();s.dialogue=[];s.stage=12;s.puzzle="circuit"
        self.assertFalse(s.puzzle_input("submit"));self.assertEqual(s.stage,12)
        s.puzzle_input("0");s.puzzle_input("2");self.assertTrue(s.puzzle_input("submit"))
        s.finish_cutscene();s.dialogue=[];s.puzzle="frequency";s.stage=13
        self.assertFalse(s.puzzle_input("submit"))
        for _ in range(3):s.puzzle_input("left")
        self.assertTrue(s.puzzle_input("submit"));self.assertEqual(s.stage,14)

    def test_gate_and_interior_stairs_cannot_skip_final_chapter(self):
        s=session();s.power=True;s.signal_off=True;s.stage=23;s.player=pygame.Vector2(s.campus.exit)
        s.update(.05);self.assertEqual(s.status,"playing")

    def test_nara_can_open_a_door_closed_behind_player(self):
        s=session();s.stage=24;s.elapsed=30
        cell=(s.campus.centers[19][0],s.campus.centers[19][1]+3)
        door=s.campus.doors[cell];center=pygame.Vector2(s.campus.center(cell))
        s.player=center+pygame.Vector2(0,130)
        start=center-pygame.Vector2(0,60)
        s.companion={"level":"campus","pos":list(start)}
        for _ in range(65):s.update(.05)
        self.assertTrue(door.opened)
        self.assertLess(pygame.Vector2(s.companion["pos"]).distance_to(s.player),start.distance_to(s.player))
        s.stage=24;s.use_stairs("enter",22);s.player=pygame.Vector2(s.layout.down)
        s.update(.05);self.assertEqual(s.status,"playing")

    def test_independent_slots_backup_and_legacy_migration(self):
        with tempfile.TemporaryDirectory() as folder:
            store=SaveStore(folder);s=session();saved=store.write("1",s.snapshot())
            s.terminals.append(7)
            self.assertEqual(saved["terminals"],[])
            s.stage=12;s.health=39;store.write("2",s.snapshot())
            self.assertEqual(store.read("1")["stage"],0)
            self.assertEqual(store.read("2")["health"],39)
            s.stage=14;store.write("2",s.snapshot())
            store.path("2").write_text("truncated",encoding="utf-8")
            self.assertEqual(store.read("2")["stage"],12);self.assertTrue(store.recovered)
            old={"version":1,"stage":6,"difficulty":"easy","player":[2900,1700],"collected":2,"journal":["pesan"]}
            Path(folder,"story.json").write_text(json.dumps(old),encoding="utf-8")
            store.migrate(folder);self.assertEqual(store.read("auto")["version"],1)
            migrated=StorySession("easy",store.read("auto"));self.assertEqual(migrated.stage,6)
            self.assertIn("pesan",migrated.journal)
            self.assertTrue(Path(folder,"story.json").exists())


class ExpansionAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.app=App(self.tmp.name,audio=False)
    def tearDown(self):pygame.quit();self.tmp.cleanup()
    def key(self,key,unicode=""):
        self.app.events([pygame.event.Event(pygame.KEYDOWN,key=key,unicode=unicode,mod=0)])

    def test_manual_save_menu_loads_exact_floor_and_health(self):
        a=self.app;a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[];s.stage=13;s.use_stairs("enter",5);s.use_stairs("up",5)
        s.health=37;s.bottles=1
        self.key(pygame.K_F5);self.assertEqual(a.mode,"save");a.draw()
        a.action("save_slot:1");a.action("back_saves")
        s.health=99;a.action("load_menu");a.action("load_slot:1")
        self.assertEqual(a.mode,"playing");self.assertEqual(a.session.health,37)
        self.assertEqual(a.session.level_key,"5:2");self.assertEqual(a.session.bottles,1)
        a.draw();self.assertEqual(a.renderer.seed,a.session.layout.seed)
        self.assertLessEqual(a.renderer.camera.x+a.renderer.view_size.x,a.session.layout.width*40)

    def test_escape_seed_cannot_reuse_campus_render_cache(self):
        a=self.app;a.start_story();a.draw()
        a.start(1960);a.draw()
        self.assertEqual(a.renderer.world.get_size(),(a.session.layout.width*40,a.session.layout.height*40))
        self.assertFalse(getattr(a.session.layout,"campus",False))

    def test_ultrawide_floor_camera_stays_inside_world_and_aim_roundtrips(self):
        a=self.app;a.start_story();a.session.finish_cutscene();a.session.dialogue=[];a.session.use_stairs("enter",22)
        a.window=pygame.display.set_mode((3200,800));a.resize_canvas();a.sync_scene()
        r=a.renderer;s=a.session
        self.assertLessEqual(r.camera.x+r.view_size.x,s.layout.width*40)
        self.assertLessEqual(r.camera.y+r.view_size.y,s.layout.height*40)
        local=r.world_to_screen(s.player)
        canvas=(local.x*a.width/r.view_size.x,local.y*800/r.view_size.y)
        self.assertLess(r.screen_to_world(canvas).distance_to(s.player),.001)

    def test_puzzle_keyboard_and_reading_journal_preserve_switches(self):
        a=self.app;a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[];s.stage=12;s.puzzle="circuit"
        self.key(pygame.K_1,"1");self.key(pygame.K_3,"3");a.draw()
        self.key(pygame.K_j);self.assertTrue(s.journal_open);self.assertEqual(s.switches,[True,False,True])
        self.key(pygame.K_ESCAPE);s.puzzle="circuit";self.key(pygame.K_RETURN)
        self.assertEqual(s.stage,13)

    def test_shadow_rotates_with_pose_and_character_palette_is_distinct(self):
        art=self.app.renderer.art;frame=art.student_frame("player",0)
        a=Art.actor_shadow(frame);b=Art.actor_shadow(pygame.transform.rotate(frame,90))
        unrotated=pygame.transform.rotate(b,-90)
        self.assertEqual(a.get_size(),unrotated.get_size())
        # A fixed oval would remain unchanged when the actor turns.
        self.assertNotEqual(pygame.image.tobytes(a,"RGBA"),pygame.image.tobytes(b,"RGBA"))
        self.assertNotEqual(pygame.image.tobytes(frame,"RGBA"),pygame.image.tobytes(art.student_frame("nara",0),"RGBA"))

    def test_audio_has_environment_and_nonrepeating_monster_variants(self):
        audio=Audio();self.assertGreater(audio.night_music.get_length(),120)
        for kind in ("guard","listener","ambusher"):self.assertEqual(len(audio.banks["monster_"+kind]),4)
        for material in ("asphalt","metal"):self.assertEqual(len(audio.banks["step_"+material]),5)
        previous=None
        for _ in range(8):
            audio.play("monster_guard");index=audio.last_index["monster_guard"]
            self.assertNotEqual(index,previous);previous=index


if __name__=="__main__":unittest.main()
