"""Story snapshot serialization and backwards-compatible restoration."""
import math
from pygame import Vector2
from .simulation import Monster
from .inventory import restore_loot, restore_placed, restore_stats
from .narrative import coerce_page
from .cinematics import CUTSCENES
from .informatika import migrate_save
from .story_data import NOTES


class StoryState:
    @staticmethod
    def pack_monster(m):
        return {"kind":m.kind,"pos":list(m.pos),"facing":list(m.facing),"state":m.state,
                "target":list(m.target) if m.target is not None else None,"memory":m.memory,"timer":m.timer,
                "cooldown":m.cooldown,"dash":list(m.dash),"wait":m.wait,"vocal_timer":m.vocal_timer}

    def snapshot(self):
        self.stash();layers={}
        for key,state in self.level_states.items():
            layout=self.get_layout(key)
            layers[key]={k:[list(p) for p in state[k]] for k in ("fuses","pickups","medkits")}
            layers[key]["monsters"]=[self.pack_monster(m) for m in state["monsters"]]
            layers[key]["doors"]=[list(cell) for cell,d in layout.doors.items() if d.opened]
            layers[key]["loot"]=[drop.pack() for drop in state["loot"]]
            layers[key]["placed"]=[item.pack() for item in state["placed"]]
        return {"version":7,"stage":self.stage,"act":self.act,"difficulty":self.difficulty_key,"level":self.level_key,
                "cutscene":dict(self.cutscene) if self.cutscene else None,"pending_scene":self.pending_scene,"seen_scenes":sorted(self.seen_scenes),
                "backpack":dict(self.backpack.items),"effects":dict(self.effects),"run_stats":self.run_stats,
                "location":self.location,"layers":layers,"player":list(self.player),"facing":list(self.facing),
                "health":self.health,"stamina":self.stamina,"exhausted":self.exhausted,"flashlight":self.flashlight,"collected":self.collected,
                "panel_progress":self.panel_progress,
                "bottles":self.bottles,"power":self.power,"signal_off":self.signal_off,"shutdown":self.shutdown_progress,
                "terminals":self.terminals,"sequences":self.sequences,"switches":self.switches,"frequency":self.frequency,
                "items":sorted(self.story_items),"journal":self.journal,"triggered":sorted(self.triggered),
                "visited":sorted(self.visited),"visited_floors":sorted(self.visited_floors),"seconds":self.play_seconds,"elapsed":self.elapsed,
                "dialogue":self.dialogue,"dialogue_time":self.dialogue_time,"pending_encounter":self.pending_encounter,"ending_pending":self.ending_pending,
                "followers":self.followers,"companion":self.companion,"completed":self.status=="won"}

    def restore(self,data):
        data=migrate_save(data,self.campus,self.get_layout)
        legacy=data.get("version",1)==1
        self.cutscene=None;self.pending_scene=None;self.seen_scenes={key for key in data.get("seen_scenes",["intro"]) if key in CUTSCENES}
        raw=data.get("cutscene")
        if isinstance(raw,dict) and raw.get("id") in CUTSCENES:
            key=raw["id"];seconds=float(raw.get("time",0))
            if not math.isfinite(seconds):raise ValueError("Invalid cutscene time")
            self.cutscene={"id":key,"time":max(0,min(CUTSCENES[key],seconds))}
        if data.get("pending_scene") in CUTSCENES:self.pending_scene=data["pending_scene"]
        self.stage=max(0,min(24,int(data.get("stage",0))))
        if legacy and self.stage>=6:self.stage=6
        self.dialogue=[] if legacy else [coerce_page(page) for page in data.get("dialogue",[])]
        seconds=data.get("dialogue_time",0.)
        self.dialogue_time=max(0,float(seconds)) if type(seconds) in (int,float) and math.isfinite(seconds) else 0.
        self.keypad=False;self.puzzle=None;self.ending_pending=bool(data.get("ending_pending",False))
        self.collected=max(0,min(2,int(data.get("collected",0))))
        self.terminals=list(data.get("terminals",[]))
        if self.terminals!=[7,21,2][:len(self.terminals)] or self.stage==4 and len(self.terminals)>2:self.terminals=[]
        self.story_items=set(data.get("items",[]));self.journal=[k for k in data.get("journal",[]) if k in NOTES]
        self.triggered=set(data.get("triggered",[]));self.visited=set(data.get("visited",[]));self.visited_floors=set(data.get("visited_floors",[]))
        self.bottles=max(0,min(8,int(data.get("bottles",4))));self.play_seconds=max(0,float(data.get("seconds",0)))
        if not math.isfinite(self.play_seconds):raise ValueError("Invalid play time")
        self.elapsed=max(0,float(data.get("elapsed",self.play_seconds)))
        self.health=max(1,min(100,int(data.get("health",100))));self.stamina=max(0,min(100,float(data.get("stamina",100))))
        self.exhausted=bool(data.get("exhausted",False));self.panel_progress=max(0,min(3,float(data.get("panel_progress",0))))
        self.flashlight=bool(data.get("flashlight",True));self.power=not legacy and bool(data.get("power",False))
        self.signal_off=bool(data.get("signal_off",False));self.shutdown_progress=max(0,min(5,float(data.get("shutdown",0))))
        self.frequency=max(1060,min(1090,int(data.get("frequency",1084))));self.switches=[bool(n) for n in data.get("switches",[False]*3)]
        if len(self.switches)!=3:self.switches=[False]*3
        self.sequences={k:list(data.get("sequences",{}).get(k,[])) for k in ("catalog","generator")}
        for name,expected in (("catalog",[4,17,9]),("generator",[0,2,1])):
            seq=self.sequences[name]
            if seq!=expected[:len(seq)] or len(seq)>2 and self.stage in (10,18):self.sequences[name]=[]
        if legacy:
            self.state_for("campus")["fuses"]=[Vector2(p) for p in data.get("fuses",[])]
            key=data.get("level","campus");self.layout=self.get_layout(key);self.level_key=key;self.seed=self.layout.seed
            state=self.state_for(key)
            self.fuses,self.pickups,self.medkits,self.monsters=(state[k] for k in ("fuses","pickups","medkits","monsters"))
            self.loot,self.placed=state["loot"],state["placed"]
            for cell in data.get("open_doors",[]):
                door=self.campus.doors.get(tuple(cell))
                if door:door.opened=True;door.swing=1
        else:
            self.level_states={}
            for key,raw in data.get("layers",{}).items():
                layout=self.get_layout(key);state=self.state_for(key)
                for name in ("fuses","pickups","medkits"):state[name]=[Vector2(p) for p in raw.get(name,[])]
                if "loot" in raw:state["loot"]=restore_loot(raw["loot"])
                state["placed"]=restore_placed(raw.get("placed",[]))
                for cell in raw.get("doors",[]):
                    door=layout.doors.get(tuple(cell))
                    if door:door.opened=True;door.swing=1
                state["monsters"]=[]
                for record in raw.get("monsters",[]):
                    if record["kind"] not in ("Penjaga","Pendengar","Penyergap"):continue
                    m=Monster(record["kind"],Vector2(record["pos"]),Vector2(record["facing"]))
                    m.state=record.get("state","patrol");m.target=Vector2(record["target"]) if record.get("target") is not None else None
                    for name in ("memory","timer","cooldown","wait","vocal_timer"):setattr(m,name,float(record.get(name,0)))
                    m.dash=Vector2(record.get("dash",[0,0]));state["monsters"].append(m)
            key=data.get("level","campus");self.layout=self.get_layout(key);self.level_key=key;self.seed=self.layout.seed
            state=self.state_for(key);self.fuses,self.pickups,self.medkits,self.monsters=(state[k] for k in ("fuses","pickups","medkits","monsters"))
            self.loot,self.placed=state["loot"],state["placed"]
        self.player=Vector2(data.get("player",self.layout.spawn))
        if not all(math.isfinite(v) for v in self.player):raise ValueError("Invalid position")
        if not self.can_stand(self.player,11):
            cell=self.layout.tile(self.player);door=self.layout.doors.get(cell)
            if door:door.opened=True;door.swing=1
            else:self.player=Vector2(self.layout.nearest_floor(self.player))
        self.facing=Vector2(data.get("facing",[1,0]))
        if self.facing.length_squared():self.facing.normalize_ip()
        else:self.facing.update(1,0)
        self.pending_encounter=data.get("pending_encounter");self.followers=list(data.get("followers",[]));self.companion=data.get("companion")
        if "backpack" in data:self.backpack.restore(data["backpack"])
        raw_effects=data.get("effects",{})
        for key,limit in (("energy",9),("quiet",20)):
            value=raw_effects.get(key,0)
            if type(value) in (int,float) and math.isfinite(value):self.effects[key]=max(0,min(limit,value))
        self.run_stats=restore_stats(data.get("run_stats",{}))
        self.invulnerable=.75;self.scene_changed=True
        if data.get("completed"):self.status="won";self.ending_pending=True
        self.notify(self.objective,4)
