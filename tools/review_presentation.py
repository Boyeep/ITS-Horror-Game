"""Actual native captures of characters, architecture, story readers and cutscenes."""
import json
import os
import sys
import tempfile
from pathlib import Path
if "--headless" in sys.argv:
    os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from horror.app import App
from horror.narrative import speech,document
from horror.inventory import ITEMS


with tempfile.TemporaryDirectory() as folder:
    a=App(folder);out=Path("docs/screenshots");out.mkdir(parents=True,exist_ok=True);captures=[]
    def capture(name):
        a.draw();a.present();pygame.event.pump();pygame.image.save(a.screen,str(out/(name+".png")));captures.append(name)
    capture("menu")
    for seconds,name in ((0,"rektorat"),(9,"tower2"),(18,"informatika"),(8.3,"crossfade")):
        a.time=seconds;capture("menu-"+name)
    a.time=0
    a.start_story();s=a.session
    s.cutscene["time"]=1.75
    capture("story-prologue")
    for seconds,label in ((9.,"lab"),(15.,"arga"),(24.,"departure"),(30.,"waiting"),(32.5,"blackout"),(38.,"phone"),(48.,"handoff")):
        s.cutscene["time"]=seconds;capture("intro-"+label)
    s.finish_cutscene();s.message_time=0;a.sync_scene();capture("first-location");a.map_open=True;capture("informatika-map1");a.map_open=False
    position=s.player.copy();s.player=pygame.Vector2(s.layout.phone_interaction)
    s.facing=(pygame.Vector2(s.layout.phone_display)-s.player).normalize()
    a.renderer.update_camera(s,snap=True);capture("phone-action")
    s.player=position;a.renderer.update_camera(s,snap=True)
    for kind in ("arga","nara"):
        s.open_dialogue([speech(kind,"Jahitan tasmu lepas lagi. Aku yang menjahitnya. Bukan suara di ponsel itu." if kind=="nara" else "Ponsel Nara… menerima pesan dari nomornya sendiri?")])
        if kind=="nara":s.dialogue_time=.7;capture("dialogue-typing")
        s.reveal_dialogue()
        capture("dialogue-"+kind)
    for key in ("pesan","rak","jaga","film","foto","server","insiden","katalog"):
        s.open_dialogue([document(key)]);capture("reader-"+key)
    s.finish_cutscene();s.dialogue=[];s.journal=list(("rak","jaga","foto","insiden"));s.journal_open=True;s.journal_page=1
    capture("story-journal");s.journal_open=False
    a.save_story("1");a.action("save_menu");capture("story-save");a.action("back_saves");a.set_mode("playing")
    s.monsters=[];s.message_time=0;s.transition=0
    for direction,vector in (("east",(1,0)),("south",(0,1)),("west",(-1,0)),("north",(0,-1))):
        s.facing.update(vector);capture("torch-"+direction)
    s.flashlight=False;capture("torch-off")
    s.backpack.restore({key:1 for key in ITEMS});s.health=64
    s.story_items.update(("Ponsel","Kartu akses","Kartu asrama","Foto Nara","Kunci servis","Radio Nara"))
    a.action("backpack");a.action("bag_select:medkit");capture("backpack")
    a.action("bag_tab:keys");capture("backpack-keys");a.set_mode("playing")
    a.action("achievements");capture("achievements");a.set_mode("playing")
    s.stage=8;s.flashlight=True;s.player=pygame.Vector2(s.layout.center(s.layout.lab_door))+pygame.Vector2(0,65)
    s.facing.update(0,1);s.message_time=0;s.transition=0
    a.renderer.update_camera(s,snap=True)
    door=min(s.layout.doors.values(),key=lambda door:pygame.Vector2(s.layout.center(door.cell)).distance_to(s.player))
    for state in (False,True):
        door.opened=state;door.swing=float(state);capture("door-open" if state else "door-closed")
    for direction in ("down","up"):
        s.switch_level("22:1",s.get_layout("22:1").down if direction=="down" else s.get_layout("22:1").up)
        s.player+=pygame.Vector2(62,38) if direction=="down" else pygame.Vector2(-62,42)
        s.facing=pygame.Vector2(-62,-38).normalize() if direction=="down" else pygame.Vector2(62,-42).normalize()
        s.transition=0;s.message_time=0;a.renderer.update_camera(s,snap=True);capture("stairs-"+direction)
    for floor in (1,2):
        layout=s.get_layout(f"11:{floor}");s.switch_level(f"11:{floor}",layout.quest_point(0 if floor==1 else 2))
        s.transition=s.message_time=0;s.monsters=[];a.sync_scene();capture("informatika-floor"+str(floor+1))
        a.map_open=True;capture("informatika-map"+str(floor+1));a.map_open=False
    s.switch_level("11:1",s.get_layout("11:1").spawn);s.transition=s.message_time=0;a.sync_scene()
    for cell,name in (((5,18),"vertical"),((19,38),"horizontal")):
        door=s.layout.doors[cell];door.opened=False;door.swing=0
        normal=pygame.Vector2(1,0) if door.vertical else pygame.Vector2(0,1)
        s.player=pygame.Vector2(s.layout.center(cell))-normal*70;s.facing=normal
        a.renderer.update_camera(s,snap=True)
        for enabled in (False,True):
            s.flashlight=enabled;capture("door-"+name+("-lit" if enabled else "-unlit"))
    s.flashlight=True;s.switch_level("campus",s.campus.spawn);s.transition=s.message_time=0;a.sync_scene()
    a.renderer.zoom=1;a.renderer.resize(a.width)
    a.renderer.camera.update(pygame.Vector2(s.campus.center((74,42)))-a.renderer.view_size/2)
    capture("informatika-ground-overview")
    a.renderer.zoom=2;a.renderer.resize(a.width);a.renderer.update_camera(s,snap=True)
    a.map_open=True;capture("story-campus-map");a.map_open=False
    for key,level,point,stage in (("library","22:1",s.get_layout("22:1").quest_point(0),2),
                                 ("reunion","campus",s.point(19),16),
                                 ("shutdown","5:3",s.get_layout("5:3").quest_point(1),21),
                                 ("ending","campus",s.campus.exit,24)):
        s.switch_level(level,point);s.stage=stage;s.cutscene={"id":key,"time":3.2};s.transition=0
        capture("cutscene-"+key);s.cutscene=None
    sheet=pygame.Surface((960,640));sheet.fill((87,100,91))
    for row,kind in enumerate(("player","nara","Penjaga","Pendengar","Penyergap")):
        a.renderer.text(sheet,kind,(18,30+row*120),16)
        for col in range(4):a.renderer.art.actor(sheet,kind,(230+col*190,65+row*120),pygame.Vector2(1,0).rotate(col*90),0)
    pygame.image.save(sheet,str(out/"characters-and-shadows.png"))
    report={"display":a.window.get_size(),"canvas":a.screen.get_size(),"ui_scale":a.renderer.ui_scale,
            "save_version":s.snapshot()["version"],"captures":captures,"native_ui":a.screen.get_size()==a.window.get_size()}
    Path("docs/presentation-review.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(report);pygame.quit()
