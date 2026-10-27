"""One actionable next step; does not disclose puzzle answers or alter saved state."""
from dataclasses import dataclass
from pygame import Vector2


@dataclass
class Target:
    key: str
    point: Vector2
    label: str
    display: Vector2


def target(key,point,label,display=None):
    return Target(key,Vector2(point),label,Vector2(display if display is not None else point))


def story_targets(s):
    from .story import QUESTS
    objects=s.quest_objects()
    if s.stage==4:objects=[row for row in objects if int(row[0].split(":")[1]) in s.goal_rooms]
    if objects:
        return [target(key,p,label.removeprefix("E  "),getattr(s.layout,"phone_display",p) if key=="phone" else p) for key,p,label in objects]
    if s.level_key=="campus":
        if s.stage==3:return [target("fuse",p,"Ambil sekring") for p in s.fuses]
        if s.stage==22:return [target("panel",s.campus.panel,"Nyalakan panel rektorat")]
        if s.stage==24:return [target("exit",s.campus.exit,"Buka gerbang")]
    if s.stage in QUESTS:
        _,building,floor,_,_=QUESTS[s.stage]
    else:
        building,floor={10:(22,1),18:(21,1),22:(15,0),24:(6,0)}.get(s.stage,(s.goal_rooms[0] if s.goal_rooms else 11,0))
    destination=s.campus.room_names[building].title()+(f" · Lantai {floor+1}" if floor else "")
    required=f"{building}:{floor}" if floor or building==11 else "campus"
    if s.level_key=="campus":
        if required=="campus":return [target("destination",s.campus.center(s.campus.centers[building]),destination)]
        if building==11:
            return [target("building_enter",p,"Masuk Informatika") for _,_,p,_ in s.building_options()]
        return [target("stairs",s.campus.stairs[building],"Naik ke "+destination)]
    if s.level_key=="11:0" and building!=11:
        return [target("building_exit",p,"Keluar Informatika · ke "+destination) for p in s.layout.exit_points.values()]
    direction="up" if s.layout.building==building and s.layout.floor<floor else "down"
    label=(f"Naik ke lantai {s.layout.floor+2}" if direction=="up" else
           "Turun ke lantai "+str(s.layout.floor))+" · "+destination
    return [target("stairs",p,label) for d,_,p,_ in s.stair_options() if d==direction]


def interaction_point(s,interaction):
    action,key,_=interaction
    if action in ("story","shutdown"):
        for name,p,_ in s.quest_objects():
            if name==key:return Vector2(getattr(s.layout,"phone_display",p) if key=="phone" else p)
        if key=="nara_hint":return s.point(19)
    if action=="stairs":
        return next((Vector2(p) for d,b,p,_ in s.stair_options() if (d,b)==key),None)
    if action in ("building_enter","building_exit"):
        return next((Vector2(p) for a,k,p,_ in s.building_options() if a==action and k==key),None)
    if action in ("fuse","bottle","medkit"):return Vector2({"fuse":s.fuses,"bottle":s.pickups,"medkit":s.medkits}[action][key])
    if action=="loot":return s.loot[key].pos.copy()
    if action=="door":return Vector2(s.layout.center(key))
    if action in ("panel","panel_done","missing"):return Vector2(s.layout.panel)
    if action=="exit":return Vector2(s.layout.exit)
    return None
