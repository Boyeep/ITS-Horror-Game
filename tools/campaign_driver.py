"""Deterministic known-answer input driver; never teleports or bypasses stairs."""
import pygame
from horror.story import QUESTS
from horror.inventory import ITEMS


class CampaignDriver:
    def __init__(self,session,enemies=False):
        self.s=session;self.enemies=enemies;self.steps=0;self.stairs=0;self.stages=[]

    def dismiss(self):
        while self.s.dialogue or self.s.cutscene:
            if self.s.cutscene:self.s.finish_cutscene()
            else:self.s.next_dialogue()

    def tick(self,direction=(0,0),aim=None,holding=False):
        s=self.s;self.steps+=1
        if not self.enemies:
            s.monsters=[];s.followers=[]
            for state in s.level_states.values():state["monsters"]=[]
        else:
            if s.threat>.3 and s.bottles and s.monsters and s.throw_cooldown<=0:
                m=min(s.monsters,key=lambda m:m.pos.distance_to(s.player));away=s.player-m.pos
                if away.length_squared():s.throw(s.player+away.normalize()*270)
            interaction=s.interaction()
            item="medkit" if interaction and interaction[0]=="medkit" else s.loot[interaction[1]].item if interaction and interaction[0]=="loot" else None
            if item in ("medkit","bandage") and s.backpack.count(item)<ITEMS[item].stack and s.backpack.capacity-s.backpack.used>=ITEMS[item].space:
                if s.interact_cooldown>0:direction=(0,0)
                else:s.interact()
            if s.health<=60:
                if s.backpack.count("medkit"):s.use_item("medkit")
                elif s.backpack.count("bandage"):s.use_item("bandage")
        near=self.enemies and any(m.pos.distance_to(s.player)<380 for m in s.monsters)
        s.update(.05,direction,near,False,holding,aim);s.audio_events.clear()

    def press(self):
        for _ in range(15):
            if self.s.interact_cooldown<=0:break
            self.tick()
        self.s.interact()

    def walk(self,destination):
        s=self.s
        for _ in range(5):
            path=s.layout.path(s.layout.tile(s.player),s.layout.tile(destination));blocked=False
            for cell in path:
                point=pygame.Vector2(s.layout.center(cell))
                for _ in range(70):
                    if s.status!="playing":return s.status=="won"
                    if s.ending_pending:return True
                    delta=point-s.player
                    if delta.length()<7:break
                    door=s.layout.doors.get(cell)
                    if door and not door.opened and delta.length()<75:
                        interaction=s.interaction()
                        if interaction and interaction[:2]==("door",cell):self.press()
                    self.tick(delta,point)
                if s.player.distance_to(point)>8:blocked=True;break
            if not blocked:return True
        raise AssertionError(f"Route blocked: {s.level_key}, {s.stage}, {s.player}, {destination}, {s.interaction()}")

    def stairs_to(self,direction,building,pos):
        self.walk(pos);before=self.s.level_key;self.press()
        if before==self.s.level_key:raise AssertionError(f"Stair failed: {direction}, {self.s.interaction()}")
        self.stairs+=1

    def navigate(self,building,floor=0):
        s=self.s
        target=f"{building}:{floor}" if floor or building==11 else "campus"
        while s.level_key not in ("campus",target):
            if s.level_key=="11:0":
                if building==11:break
                self.walk(s.layout.exit_points["main"]);self.press();continue
            if s.layout.building==building and s.layout.floor<floor:break
            self.stairs_to("down",s.layout.building,s.layout.down)
        if building==11 and s.level_key=="campus":
            self.walk(pygame.Vector2(s.campus.center(s.campus.informatika_entrances[0]))+pygame.Vector2(40,0));self.press()
            if s.level_key!="11:0":raise AssertionError("Informatika entrance failed")
        if floor and s.level_key=="campus":self.stairs_to("enter",building,s.campus.stairs[building])
        while floor and s.layout.floor<floor:self.stairs_to("up",building,s.layout.up)

    def run(self):
        s=self.s;self.dismiss()
        for _ in range(80):
            if s.status!="playing":break
            stage=s.stage;self.stages.append(stage)
            if stage in QUESTS:
                key,building,floor,index,label=QUESTS[stage];self.navigate(building,floor)
                objects=s.quest_objects()
                self.walk(objects[0][1]);self.press()
                if s.keypad:
                    s.code="2413";s.submit_code()
                if s.puzzle:
                    if s.puzzle=="frequency":
                        while s.frequency!=1078:s.puzzle_input("left" if s.frequency>1078 else "right")
                    else:
                        desired=[False,True,False] if s.puzzle=="isolation" else [True,False,True]
                        for i,value in enumerate(desired):
                            if s.switches[i]!=value:s.puzzle_input(str(i))
                    if not s.puzzle_input("submit"):raise AssertionError("Puzzle rejected valid solution")
                if stage==20:
                    for _ in range(120):
                        self.tick(holding=True)
                        if s.stage!=20 or s.status!="playing":break
                self.dismiss()
            elif stage==3:
                self.navigate(23)
                self.walk(s.fuses[0]);self.press();self.dismiss()
            elif stage==4:
                self.navigate(7);room=[7,21,2][len(s.terminals)]
                self.walk(s.point(room));self.press();self.dismiss()
            elif stage in (10,18):
                name,building,floor,expected=("catalog",22,1,[4,17,9]) if stage==10 else ("generator",21,1,[0,2,1])
                self.navigate(building,floor)
                for value in expected:
                    obj=next(obj for obj in s.quest_objects() if obj[0]==f"{name}:{value}")
                    self.walk(obj[1]);self.press()
                self.dismiss()
            elif stage==22:
                self.navigate(15);self.walk(s.campus.panel)
                for _ in range(75):
                    self.tick(holding=True)
                    if s.stage!=22 or s.status!="playing":break
            elif stage==24:
                self.navigate(6);self.walk(s.campus.exit);self.dismiss()
            else:raise AssertionError(f"Unhandled stage {stage}")
            if s.status=="lost":break
        if s.status=="playing":raise AssertionError(f"No progression: {s.stage}, {s.interaction()}")
        return {"status":s.status,"stage":s.stage,"seconds":round(s.play_seconds,2),"steps":self.steps,
                "stairs":self.stairs,"floors":sorted(s.visited_floors),"health":s.health,"hits":s.hits_taken,
                "stages":self.stages,"encounters":s.encounter_count,"reason":s.death_reason}
