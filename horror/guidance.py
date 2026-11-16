"""One actionable next step; does not disclose puzzle answers or alter saved state."""
from dataclasses import dataclass
from pygame import Vector2
import math
import pygame
from .config import PLAYER_RADIUS, TILE


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


def target_id(goal):
    return goal.key,tuple(goal.point)


def route_clear(session,point):
    """A centre ray alone can cut a corner that the player's body cannot pass."""
    delta=Vector2(point)-session.player;steps=max(1,math.ceil(delta.length()/10))
    return all(session.can_stand(session.player+delta*(i/steps),PLAYER_RADIUS) for i in range(1,steps+1))


def visible_face(session,point):
    delta=Vector2(point)-session.player
    end=Vector2(point)-delta.normalize()*22 if delta.length_squared() else point
    return session.layout.line_clear(session.player,end)


class RouteGuide:
    """HUD-only A* routes, with cost selection, short lookahead and waypoint hysteresis."""
    def __init__(self):
        self.context=None;self.cache_key=None;self.selected_id=None;self.waypoint=None
        self.paths={};self.current_path=[]

    def info(self,session,targets=None):
        targets=story_targets(session) if targets is None else targets
        if not targets:self.context=None;self.waypoint=None;self.current_path=[];return None
        layout=session.layout;start=layout.tile(session.player)
        signature=tuple(sorted((g.key,tuple(g.point),g.label,tuple(g.display)) for g in targets))
        doors=tuple(sorted((cell,door.opened) for cell,door in layout.doors.items()))
        context=(id(session),id(layout),getattr(session,"level_key","escape"),getattr(session,"stage",0),layout.revision,doors,signature)
        if context!=self.context:
            self.context=context;self.cache_key=None;self.selected_id=None;self.waypoint=None
        key=(context,start)
        if key!=self.cache_key:
            routes={}
            for goal in targets:
                path=layout.path(start,layout.tile(goal.point))
                if not path and start!=layout.tile(goal.point):continue
                cost=len(path)+sum(cell in layout.doors and not layout.doors[cell].opened for cell in path)
                routes[target_id(goal)]=(cost,goal,path)
            self.cache_key=key;self.paths=routes
            if not routes:self.selected_id=None;self.current_path=[];return None
            best=min(routes,key=lambda identity:(routes[identity][0],identity))
            # Keep an equivalent exit/landing until another route saves >3 cells.
            if self.selected_id in routes and routes[self.selected_id][0]<=routes[best][0]+3:best=self.selected_id
            if best!=self.selected_id:self.waypoint=None
            self.selected_id=best
        if self.selected_id not in self.paths:return None
        _,goal,path=self.paths[self.selected_id];self.current_path=path
        if self.waypoint is not None:
            point,hint,kind=self.waypoint
            if layout.tile(point) in path[:8] and point.distance_to(session.player)>55:
                valid=visible_face(session,point) if kind=="door" else route_clear(session,point)
                if valid:return goal,point.copy(),hint,kind
        point=Vector2(layout.center(start));hint="Ikuti koridor · "+goal.label;kind="route"
        if len(path)<=8 and route_clear(session,goal.point):
            point=goal.point.copy();hint=goal.label;kind=goal.key
        else:
            for cell in path[:8]:
                candidate=Vector2(layout.center(cell));door=layout.doors.get(cell)
                if door and not door.opened:
                    if visible_face(session,candidate):point=candidate;hint="Buka pintu";kind="door"
                    break
                if not route_clear(session,candidate):break
                point=candidate
        self.waypoint=(point.copy(),hint,kind)
        return goal,point,hint,kind


def place_label(anchor,size,bounds,avoid=()):
    """Deterministic positions in logical UI pixels, avoiding actor/HUD/other labels."""
    bounds=pygame.Rect(bounds);w,h=size;x,y=anchor
    candidates=[(x-w/2,y-65),(x-w/2,y+30),(x-w-28,y-h/2),(x+28,y-h/2)]
    for blocker in sorted(avoid,key=lambda box:Vector2(box.center).distance_squared_to(anchor)):
        candidates.extend(((x-w/2,blocker.top-h-12),(x-w/2,blocker.bottom+12)))
    candidates.extend(((x-w/2,bounds.bottom-h),(bounds.left,bounds.top),(bounds.right-w,bounds.top)))
    for left,top in candidates:
        rect=pygame.Rect(round(left),round(top),w,h);rect.clamp_ip(bounds)
        if bounds.contains(rect) and all(not rect.inflate(8,8).colliderect(other) for other in avoid):return rect
    return None


def arrow_position(origin,target,bounds):
    """Intersect the ray from the actual player with the safe HUD region."""
    bounds=pygame.Rect(bounds);origin=Vector2(origin);target=Vector2(target);delta=target-origin
    if not delta.length_squared():return None
    direction=delta.normalize()
    if bounds.collidepoint(target):return target,direction
    start=Vector2(max(bounds.left,min(bounds.right-1,origin.x)),max(bounds.top,min(bounds.bottom-1,origin.y)))
    limits=[]
    if direction.x>0:limits.append((bounds.right-1-start.x)/direction.x)
    elif direction.x<0:limits.append((bounds.left-start.x)/direction.x)
    if direction.y>0:limits.append((bounds.bottom-1-start.y)/direction.y)
    elif direction.y<0:limits.append((bounds.top-start.y)/direction.y)
    return start+direction*min(limits),direction
