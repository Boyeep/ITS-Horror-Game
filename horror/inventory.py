"""Item definitions, bounded storage and deterministic, reachable field supplies."""
import math
import random
from dataclasses import dataclass
from pygame import Vector2


@dataclass(frozen=True)
class Item:
    name: str
    description: str
    space: int
    stack: int
    shortcut: str = ""


ITEMS={
    "bottle":Item("Botol kaca","Lempar sebagai umpan. Monster yang mendengar akan memeriksa tempat pecahnya.",1,8,"Q"),
    "medkit":Item("P3K","Pulihkan 40 HP. Tidak habis jika HP sudah penuh.",2,3,"1"),
    "bandage":Item("Perban","Pulihkan 20 HP. Bekal ringan untuk luka kecil.",1,5),
    "energy":Item("Minuman energi","Pulihkan 45 stamina. Selama 9 detik, lari lebih hemat stamina dan pemulihan lebih cepat.",1,3,"2"),
    "tape":Item("Lakban kain","Redam suara langkah selama 20 detik. Pintu, kaca dan penglihatan monster tetap perlu diwaspadai.",1,2),
    "alarm":Item("Alarm saku","Letakkan umpan. Berbunyi setelah 3 detik, lalu berulang selama 10 detik.",2,2,"3"),
    "glow":Item("Lampu kimia","Terangi dan tandai jalan selama 45 detik. Tidak menghasilkan noise.",1,4,"4"),
}


class Backpack:
    capacity=12

    def __init__(self):self.items={key:0 for key in ITEMS}
    @property
    def used(self):return sum(ITEMS[key].space*count for key,count in self.items.items())
    def count(self,key):return self.items.get(key,0)
    def add(self,key,count=1):
        if key not in ITEMS:return 0
        item=ITEMS[key]
        amount=max(0,min(int(count),item.stack-self.count(key),(self.capacity-self.used)//item.space))
        self.items[key]+=amount;return amount
    def remove(self,key,count=1):
        if count<=0 or self.count(key)<count:return False
        self.items[key]-=count;return True
    def restore(self,data):
        self.items={key:0 for key in ITEMS}
        if not isinstance(data,dict):return
        for key in ITEMS:
            value=data.get(key,0)
            if type(value) is int:self.add(key,max(0,value))


@dataclass
class Loot:
    item: str
    pos: Vector2
    quantity: int=1
    natural: bool=True

    def pack(self):return {"item":self.item,"pos":list(self.pos),"quantity":self.quantity,"natural":self.natural}


@dataclass
class PlacedItem:
    kind: str
    pos: Vector2
    life: float
    delay: float=0.
    pulse: float=0.

    def pack(self):return {"kind":self.kind,"pos":list(self.pos),"life":self.life,"delay":self.delay,"pulse":self.pulse}


def restore_loot(records):
    result=[]
    for raw in records:
        if raw.get("item") not in ITEMS:continue
        pos=Vector2(raw["pos"])
        if all(math.isfinite(n) for n in pos):result.append(Loot(raw["item"],pos,max(1,min(8,int(raw.get("quantity",1)))),bool(raw.get("natural",True))))
    return result


def restore_placed(records):
    result=[]
    for raw in records:
        if raw.get("kind") not in ("alarm","glow"):continue
        pos=Vector2(raw["pos"])
        values=[float(raw.get(k,0)) for k in ("life","delay","pulse")]
        if all(math.isfinite(n) for n in [*pos,*values]) and values[0]>0:
            result.append(PlacedItem(raw["kind"],pos,min(45,values[0]),max(0,min(3,values[1])),max(0,min(2,values[2]))))
    return result


def seed_supplies(layout):
    if getattr(layout,"building",None)==11 and getattr(layout,"floor",None)==0:
        return [Loot(item,Vector2(layout.center(cell))) for item,cell in
                (("bandage",(54,27)),("energy",(37,43)),("glow",(39,8)))]
    rng=random.Random(layout.seed^0xBACA)
    if getattr(layout,"interior",False):
        common=("bandage","energy","tape","alarm","glow")
        plan=[(common[(layout.building+layout.floor)%5],0),(common[(layout.building+layout.floor+2)%5],2),("glow",3)]
    else:
        plan=[("bandage",0),("bandage",19),("bandage",24),("energy",11),("energy",18),("energy",21),
              ("tape",7),("tape",28),("alarm",5),("alarm",17),("glow",22),("glow",12),("glow",26)]
    occupied={layout.tile(p) for p in [layout.spawn,layout.panel,layout.exit,*layout.fuses,*layout.medkit_spawns,*layout.bottle_spawns]}
    stairs=getattr(layout,"stairs",None)
    if isinstance(stairs,dict):occupied.update(layout.tile(p) for p in stairs.values())
    elif isinstance(stairs,list):occupied.update(layout.tile(p) for _,p in stairs)
    drops=[]
    for item,room in plan:
        cx,cy=layout.room_center_cell(room)
        offsets=[(-1,1),(1,-1),(-2,0),(2,0),(0,2),(0,-2),(-2,2),(2,-2)]
        rng.shuffle(offsets)
        for dx,dy in offsets:
            cell=(cx+dx,cy+dy)
            if cell not in occupied and cell not in layout.doors and layout.walkable(cell,True):
                drops.append(Loot(item,Vector2(layout.center(cell))));occupied.add(cell);break
    return drops


def new_stats():
    return {"items_found":0,"found_types":[],"heals_used":0,"low_stamina_drinks":0,
            "quiet_seconds":0.,"lures_worked":0,"glow_areas":[],"sprint_seconds":0.,"items_used":{}}


def restore_stats(data):
    stats=new_stats()
    if not isinstance(data,dict):return stats
    for key,value in stats.items():
        raw=data.get(key)
        if type(value) in (int,float) and type(raw) in (int,float) and math.isfinite(raw):stats[key]=max(0,min(10000000,raw))
    for key in ("found_types","glow_areas"):
        raw=data.get(key,[])
        if isinstance(raw,list):stats[key]=list(dict.fromkeys(v for v in raw if isinstance(v,str) and (key!="found_types" or v in ITEMS)))[:128]
    used=data.get("items_used",{})
    if isinstance(used,dict):stats["items_used"]={k:max(0,min(100000,int(v))) for k,v in used.items() if k in ITEMS and type(v) is int}
    return stats
