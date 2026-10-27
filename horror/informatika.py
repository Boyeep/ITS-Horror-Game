"""Wing/courtyard topology from ITS UTBK 2026; L3 lab names follow the public plan.

The ground footprint follows the site diagram; L2 room use is a story adaptation.
Floorplan references and facade-photo credits are in docs/ITS_REFERENCES.md.
"""
from .config import TILE
from .world import Door,Furniture,AnnealingStats


def ground(layout):
    ox,oy,w,h=66,35,17,15
    layout.origins[11]=(ox,oy);layout.buildings[11]=(ox,oy,w,h)
    cells={(x,y) for y in range(oy,oy+h) for x in range(ox,ox+w)
           if y<oy+5 or y>=oy+h-5 or x>=ox+w-5}
    layout.informatika_cells=cells
    # Campus shows the exterior footprint; the full interior is a separate level.
    for x,y in cells:
        layout.grid[y][x]=1;layout.materials[y][x]="concrete"
    layout.informatika_entrances=((82,43),(73,49),(78,42))
    for cell in layout.informatika_entrances:
        layout.grid[cell[1]][cell[0]]=0
    layout.informatika_stairs={"sw":layout.center((73,50))}
    layout.informatika_spawn=layout.center((73,50))
    layout.informatika_phone=layout.informatika_spawn
    layout.paint_road((83,43),(85,51),1,"asphalt")
    layout.paint_road((73,50),(82,52),1,"asphalt")
    for x in range(67,78):
        for y in range(40,45):layout.materials[y][x]="grass"


def upper(layout,floor):
    """Two long wings, bottom cross-corridor and central NETICS, matching the L3 sheet."""
    layout.width,layout.height=38,44
    layout.grid=[[1]*38 for _ in range(44)];layout.void_cells=set();layout.furniture=[];layout.doors={}
    for y in range(1,43):
        for x in range(1,37):
            if 9<=x<=28 and y<35:
                layout.void_cells.add((x,y));continue
            boundary=x in (1,36) or y in (1,42) or (x in (8,29) and y<35) or (y==35 and 8<=x<=29)
            layout.grid[y][x]=int(boundary)
    for y in range(2,35):
        for x in (5,32):layout.grid[y][x]=1
    for y in (12,24):
        for x in (*range(1,6),*range(32,37)):layout.grid[y][x]=1
    for x in range(8,30):layout.grid[38][x]=1
    for x in (14,24):
        for y in range(38,43):layout.grid[y][x]=1
    for y in (8,18,29):
        for x in (5,32):layout.grid[y][x]=0;layout.doors[(x,y)]=Door((x,y),True)
    for x in (11,19,26):layout.grid[38][x]=0;layout.doors[(x,38)]=Door((x,38),False)
    layout.stair_points={"nw":layout.center((3,6)),"ne":layout.center((34,6)),
                         "sw":layout.center((11,40)),"se":layout.center((26,40))}
    layout.down=layout.stair_points["sw"];layout.up=layout.stair_points["se"] if floor==1 else None
    layout.stair_portals=[("down",key,point) for key,point in layout.stair_points.items() if key in ("sw","ne") or floor==2]
    if floor==1:layout.stair_portals.extend(("up",key,layout.stair_points[key]) for key in ("se","nw"))
    if floor==1:
        # Each landing has a separate flight in both directions, with no shared E target.
        layout.stair_portals.extend((direction,key,layout.center(cell)) for direction,key,cell in (
            ("down","nw",(3,4)),("up","ne",(34,4)),("up","sw",(9,40)),("down","se",(28,40))))
    layout.stairs=[(direction,point) for direction,key,point in layout.stair_portals]
    layout.spawn=layout.center((11,39));layout.zones=[(3,18),(34,18),(19,40),(34,29),(3,29)]
    if floor==2:
        labels=(("PEMROGRAMAN 2",(2,26)),("PEMROGRAMAN 1",(33,26)),("NETICS",(17,39)),("RUANG KELAS",(2,15)),("RUANG KELAS",(33,15)))
    else:
        labels=(("SERVER / LAB MALAM",(2,15)),("LAB RISET",(33,15)),("RUANG BACA",(17,39)),("WORKSHOP",(33,26)),("RUANG DISKUSI",(2,26)))
    layout.labels=[(name,layout.center(cell)) for name,cell in labels]
    layout.labels.append(("COURTYARD",layout.center((16,21))))
    for x in (2,33):
        for y in (15,21,27,32):
            if y not in (18,29):layout.add_furniture("computer",x,y,2,1)
    for x in (16,21):layout.add_furniture("computer" if floor==2 else "shelf",x,41,2,1)
    layout.panel=layout.center((19,40));layout.exit=layout.down
    layout.spawn_room=layout.panel_room=layout.exit_room=11
    layout.fuses=[];layout.monster_spawns=[layout.center(p) for p in ((6,17),(31,17),(19,36))]
    layout.bottle_spawns=[layout.center(p) for p in ((4,20),(33,20),(22,40))]
    layout.medkit_spawns=[layout.center((12,40)),layout.center((34,33))]
    layout.stats=AnnealingStats(0,0,0,0,0,[0]);layout.edges=()


def _migrate_v6(data,campus,get_layout):
    """Translate entities in the replaced Informatika geometry; other campuses/floors stay put."""
    if data.get("version",1)>=6:return data
    import copy
    import math
    from pygame import Vector2
    data=copy.deepcopy(data)
    def position(raw,key):
        p=Vector2(raw)
        if key=="11:1":
            layout=get_layout(key)
            if p.distance_to((260,780))<100:return list(layout.spawn)
            old=((8,6),(23,6),(8,16),(23,16))
            index=min(range(4),key=lambda n:p.distance_to(((old[n][0]+.5)*TILE,(old[n][1]+.5)*TILE)))
            centre=Vector2((old[index][0]+.5)*TILE,(old[index][1]+.5)*TILE)
            delta=p-centre
            if delta.length()>80:delta.scale_to_length(80)
            return list(layout.nearest_floor(Vector2(layout.quest_point(index))+delta))
        if key=="campus" and 68*TILE<=p.x<77*TILE and 39*TILE<=p.y<46*TILE:
            delta=p-Vector2((72.5*TILE,42.5*TILE))
            if delta.length()>80:delta.scale_to_length(80)
            return list(campus.nearest_floor(Vector2(campus.informatika_spawn)+delta))
        return list(p)
    current=data.get("level","campus")
    if "player" in data:data["player"]=position(data["player"],current)
    for key,layer in data.get("layers",{}).items():
        for kind in ("fuses","pickups","medkits"):layer[kind]=[position(p,key) for p in layer.get(kind,[])]
        for kind in ("loot","placed","monsters"):
            for item in layer.get(kind,[]):
                item["pos"]=position(item["pos"],key)
                if item.get("target") is not None:item["target"]=position(item["target"],key)
        doors=[]
        for cell in layer.get("doors",[]):
            if key=="11:1":
                layout=get_layout(key);point=position(((cell[0]+.5)*TILE,(cell[1]+.5)*TILE),key)
                cell=min(layout.doors,key=lambda d:math.dist(point,layout.center(d)))
            elif key=="campus" and tuple(cell)==(72,45):cell=(73,49)
            doors.append(list(cell))
        layer["doors"]=doors
    for follower in data.get("followers",[]):follower["point"]=position(follower["point"],follower["level"])
    if data.get("companion"):
        companion=data["companion"];companion["pos"]=position(companion["pos"],companion["level"])
    return data


def migrate_save(data,campus,get_layout):
    """Keep old progress, moving only the retired ground interior to its new level."""
    if data.get("version",1)>=7:return data
    import copy
    from pygame import Vector2
    data=copy.deepcopy(_migrate_v6(data,campus,get_layout))
    current=data.get("level","campus")
    p=Vector2(data.get("player",campus.spawn))
    was_inside=current=="campus" and campus.tile(p) in campus.informatika_cells
    if current=="campus" and (was_inside or data.get("stage",0)==0):
        target=get_layout("11:0")
        data["level"]="11:0";data["player"]=list(target.spawn)
    layer=data.get("layers",{}).get("campus",{})
    def safe(raw):return list(campus.nearest_floor(raw)) if not campus.walkable(campus.tile(raw),True) else raw
    for kind in ("fuses","pickups","medkits"):layer[kind]=[safe(p) for p in layer.get(kind,[])]
    for kind in ("loot","placed","monsters"):
        for item in layer.get(kind,[]):
            item["pos"]=safe(item["pos"])
            if item.get("target") is not None:item["target"]=safe(item["target"])
    if isinstance(data.get("cutscene"),dict) and data["cutscene"].get("id")=="intro":
        data["cutscene"]["time"]=0.
    return data
