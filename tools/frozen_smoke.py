"""Run the compiled game from an external folder, including an upstairs save."""
import json
import os
import subprocess
import sys
import tempfile
import struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from horror.saves import SaveStore
from horror.story import StorySession
from horror.inventory import ITEMS,PlacedItem
from horror.achievements import AchievementProfile
from horror.simulation import Session
from pygame import Vector2
from horror.narrative import document,speech
from horror.pixels import enable_native_dpi


def main():
    enable_native_dpi()
    root=Path(__file__).resolve().parents[1];exe=root/"dist/SetelahJamMalam.exe"
    report=[]
    with tempfile.TemporaryDirectory(prefix="its-frozen-qa-") as folder:
        s=StorySession();s.finish_cutscene();s.dialogue=[];s.stage=13;s.use_stairs("enter",5);s.use_stairs("up",5);s.health=37
        s.backpack.restore({key:1 for key in ITEMS});s.effects["quiet"]=12
        s.placed=[PlacedItem("alarm",s.player+Vector2(40,0),10,2)]
        earned=Session(42);earned.collect_item("medkit");earned.health=50;earned.use_item("medkit")
        profile=AchievementProfile(folder);profile.observe(earned);profile.save()
        store=SaveStore(folder);store.write("1",s.snapshot())
        s.open_dialogue([document("rak")]);store.write("2",s.snapshot())
        s.open_dialogue([speech("nara","Kali ini kita pulang berdua.")]);store.write("3",s.snapshot())
        for name,args in (("floor",["--load-slot","1"]),("story",["--story","--headless"]),("escape",["--seed","42","--headless"]),
                          ("paper",["--load-slot","2","--headless"]),("portrait",["--load-slot","3","--headless"]),
                          ("informatika",["--load-slot","2","--headless"]),
                          ("intro",["--load-slot","2","--headless"]),
                          ("ground",["--load-slot","2"]),("phone",["--load-slot","2","--headless"])):
            if name=="informatika":
                expanded=StorySession();expanded.finish_cutscene();expanded.use_stairs("enter",11);expanded.use_stairs("up",11)
                expanded.health=51;store.write("2",expanded.snapshot())
            if name=="intro":
                opening=StorySession();opening.cutscene["time"]=5.;store.write("2",opening.snapshot())
            if name=="ground":
                opening=StorySession();opening.finish_cutscene();store.write("2",opening.snapshot())
            if name=="phone":
                opening=StorySession();opening.cutscene["time"]=38.;store.write("2",opening.snapshot())
            shot=root/"docs/screenshots"/("compiled-"+name+".png")
            command=[str(exe),*args,"--frames","12","--data-dir",folder,"--screenshot",str(shot)]
            result=subprocess.run(command,cwd=folder,timeout=45,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            assert result.returncode==0 and shot.exists(),name
            entry={"mode":name,"exit_code":result.returncode,"screenshot":True,"external_working_directory":True}
            entry["pixels"]=list(struct.unpack(">II",shot.read_bytes()[16:24]))
            if name=="floor":
                import ctypes
                expected=[ctypes.windll.user32.GetSystemMetrics(i) for i in (0,1)]
                assert entry["pixels"]==expected,(entry["pixels"],expected)
                entry["native_dpi"]=True
                saved=store.read("auto");assert saved["level"]=="5:2" and saved["health"]==37
                assert saved["backpack"]=={key:1 for key in ITEMS} and saved["effects"]["quiet"]>0
                assert saved["layers"]["5:2"]["placed"][0]["kind"]=="alarm"
                entry.update(level=saved["level"],health=saved["health"],save_version=saved["version"])
                entry["backpack"]=True;entry["deployed_alarm"]=True
            if name=="intro":
                saved=store.read("auto");assert saved["cutscene"]["id"]=="intro" and saved["cutscene"]["time"]>5
                entry["cutscene_resume"]=True
            if name=="informatika":
                saved=store.read("auto");assert saved["level"]=="11:2" and saved["health"]==51
                entry["informatika_floor3"]=True
            if name=="portrait":
                saved=store.read("auto");assert saved["dialogue"][0]["speaker"]=="nara" and saved["dialogue_time"]>0
                entry["speech_typing_saved"]=True
            if name=="ground":
                saved=store.read("auto");assert saved["level"]=="11:0" and not saved["cutscene"]
                entry["new_ground_playable"]=True
            if name=="phone":
                saved=store.read("auto");assert saved["cutscene"]["time"]>38
                entry["phone_scene_resume"]=True
            assert store.read("1")["health"]==37,"New story changed manual save"
            assert "first_aid" in AchievementProfile(folder).unlocked,"Achievement was lost"
            entry["achievement_retained"]=True
            report.append(entry)
    (root/"docs/compiled-smoke.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(report)


if __name__=="__main__":main()
