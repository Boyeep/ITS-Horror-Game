"""Staged captures of actual item art, backpack UI, rewards and deployed light."""
import json
import os
import sys
import tempfile
from pathlib import Path
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from horror.app import App
from horror.inventory import ITEMS,Loot


def main():
    out=Path("docs/screenshots");out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        a=App(directory);a.start_story();s=a.session;s.finish_cutscene();s.dialogue=[];s.stage=12
        s.backpack.restore({key:1 for key in ITEMS});s.health=64;s.stamina=14
        s.story_items.update(("Ponsel","Kartu akses","Kartu asrama","Foto Nara","Kunci servis","Radio Nara"));s.collected=2
        def capture(name):a.draw();pygame.image.save(a.screen,str(out/(name+".png")))
        a.action("backpack");a.action("bag_select:medkit");capture("backpack")
        a.action("bag_tab:keys");capture("backpack-keys");a.action("bag_tab:supplies")
        a.action("bag_use");a.update(.05,{})
        a.achievement_queue=[];a.achievement_toast="first_aid";a.toast_time=4
        capture("achievement-toast")
        a.action("achievements");capture("achievements");a.action("achievement_page:1");capture("achievements-page2")
        a.action("achievements_back");a.achievement_toast=None;a.achievement_queue=[]
        s.switch_level("5:2",s.get_layout("5:2").quest_point(2));s.stage=13;s.transition=0;s.message_time=0
        s.player+=pygame.Vector2(-40,40);s.facing.update(1,0);s.monsters=[]
        s.backpack.add("glow");s.item_cooldown=0;s.use_item("glow");s.flashlight=False
        for i,key in enumerate(("medkit","energy","tape","alarm")):
            pos=s.layout.nearest_floor(s.player+pygame.Vector2(80+(i%2)*60,-40+(i//2)*80))
            s.loot.append(Loot(key,pygame.Vector2(pos)))
        capture("field-supplies")
        sheet=pygame.Surface((1100,460));sheet.fill((20,34,41))
        for i,(key,item) in enumerate(ITEMS.items()):
            x=54+(i%4)*266;y=26+(i//4)*216
            sheet.blit(a.renderer.art.item_icon(key,150),(x+32,y))
            a.renderer.text(sheet,item.name,(x+108,y+160),19,align="center")
        pygame.image.save(sheet,str(out/"item-art.png"))
        a.achievements.save()
        print({"items":len(ITEMS),"capacity":s.backpack.capacity,"save_version":s.snapshot()["version"],"profile":len(a.achievements.unlocked)})
        pygame.quit()


if __name__=="__main__":main()
