"""Capture the campaign's actual UI and measure rendering with three active AI."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from horror.app import App
from horror.story import NOTES


def main():
    out=Path("docs/screenshots");out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as folder:
        app=App(folder)
        def capture(name):
            app.draw();pygame.image.save(app.screen,str(out/(name+".png")))
        capture("menu")
        app.start_story();app.session.cutscene["time"]=1.75;capture("story-prologue")
        s=app.session
        while s.dialogue or s.cutscene:
            if s.cutscene:s.finish_cutscene()
            else:s.next_dialogue()
        s.interact();capture("story-message")
        while s.dialogue or s.cutscene:
            if s.cutscene:s.finish_cutscene()
            else:s.next_dialogue()
        s.stage=2;s.journal=["pesan","rak"];s.player=s.point(15)
        app.renderer.update_camera(s,snap=True)
        s.keypad=True;s.code="24";capture("story-locker")
        s.keypad=False;s.journal=[*NOTES];s.journal_page=2;s.journal_open=True
        capture("story-journal")
        s.journal_open=False;s.stage=4;s.terminals=[7]
        s.message_time=0
        app.map_open=True;capture("story-campus-map");app.map_open=False
        s.player=s.point(20,(0,0));s.facing.update(1,0)
        app.renderer.update_camera(s,snap=True)
        s.stage=6;s.elapsed=65;s.message_time=0
        s.spawn_encounter("Penjaga");s.spawn_encounter("Pendengar");s.spawn_encounter("Penyergap")
        s.threat=.95;s.encounter_timer=.42;capture("story-chase")
        s.encounter_timer=0;s.threat=0;capture("story-campus-night")
        s.monsters[0].pos=s.player+pygame.Vector2(190,0)
        start=time.perf_counter()
        for _ in range(180):app.update(1/60,{});app.draw()
        duration=time.perf_counter()-start
        report={"frames":180,"uncapped_fps":round(180/duration,1),"three_ai":len(s.monsters),
                "campus_units":[s.layout.width*40,s.layout.height*40],"exploration_seconds":app.audio.music[0].get_length(),
                "chase_loop_seconds":app.audio.music[1].get_length(),"stinger_seconds":app.audio.sounds["stinger"].get_length(),
                "alternate_music_seconds":app.audio.night_music.get_length()}
        s.monsters=[];s.followers=[];s.threat=0;s.encounter_timer=0;s.elapsed=100
        s.player=s.point(20,(-120,80));s.facing.update(.8,-.6)
        app.renderer.update_camera(s,snap=True);capture("story-outdoor-grass")
        s.player=pygame.Vector2(s.campus.center((35,100)));s.facing.update(0,-1)
        app.renderer.update_camera(s,snap=True);capture("story-outdoor-asphalt")
        s.switch_level("22:1",s.get_layout("22:1").quest_point(0));s.stage=1;s.transition=0
        capture("story-library-floor");app.map_open=True;capture("story-floor-map");app.map_open=False
        s.switch_level("5:1",s.get_layout("5:1").quest_point(0));s.stage=12;s.transition=0
        s.puzzle="circuit";s.switches=[True,False,True];capture("story-circuit");s.puzzle=None
        s.switch_level("5:2",s.get_layout("5:2").quest_point(2));s.stage=13;s.transition=0
        s.puzzle="frequency";s.frequency=1076;capture("story-frequency");s.puzzle=None
        s.switch_level("5:3",s.get_layout("5:3").quest_point(1));s.stage=20;s.transition=0
        s.facing.update(.8,-.6);capture("story-rooftop")
        app.save_story("1");s.stage=21;app.save_story("2");s.stage=22;app.save_story("3");app.save_story()
        app.action("save_menu");capture("story-save");app.action("back_saves")
        app.action("load_menu");capture("story-load");app.action("back_saves")
        app.set_mode("playing");s.switch_level("campus",s.point(19));s.stage=15;s.transition=0
        s.player+=pygame.Vector2(-80,25);s.facing.update(1,0);capture("story-nara")
        sheet=pygame.Surface((960,640));sheet.fill((87,100,91))
        for row,kind in enumerate(("player","nara","Penjaga","Pendengar","Penyergap")):
            app.renderer.text(sheet,kind,(18,30+row*120),16)
            for col in range(4):
                facing=pygame.Vector2(1,0).rotate(col*90)
                app.renderer.art.actor(sheet,kind,(230+col*190,65+row*120),facing,0)
        pygame.image.save(sheet,str(out/"characters-and-shadows.png"))
        Path("docs/story-review.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(report)
        pygame.quit()


if __name__=="__main__":main()
