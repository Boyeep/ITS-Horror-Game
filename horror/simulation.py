"""Gameplay rules. Sensors provide evidence; navigation never reads hidden players."""
import math
import random
from dataclasses import dataclass, field

from pygame import Vector2

from .config import DIFFICULTIES, TILE, ROOM_COUNT
from .world import Layout
from .inventory import Backpack, ITEMS, Loot, PlacedItem, seed_supplies, new_stats


@dataclass
class Monster:
    kind: str
    pos: Vector2
    facing: Vector2
    state: str = "patrol"
    target: Vector2 | None = None
    path: list = field(default_factory=list)
    repath: float = 0
    memory: float = 0
    timer: float = 0
    step: float = 0
    cooldown: float = 0
    dash: Vector2 = field(default_factory=Vector2)
    sound_cause: str = ""
    wait: float = 0
    goal_cell: tuple | None = None
    path_revision: int = -1
    vocal_timer: float = 8


@dataclass
class Noise:
    pos: Vector2
    radius: float
    age: float = 0
    label: str = ""


class Session:
    mode_key = "escape"

    @property
    def exit_ready(self):return self.power

    @property
    def bottles(self):return self.backpack.count("bottle")
    @bottles.setter
    def bottles(self,value):self.backpack.items["bottle"]=max(0,min(8,int(value)))

    def __init__(self, seed=1, difficulty="normal", layout=None):
        self.layout = layout or Layout(seed)
        self.seed, self.difficulty_key = seed, difficulty
        self.difficulty = DIFFICULTIES[difficulty]
        self.rng = random.Random(seed ^ 0xDEAD)
        self.backpack=Backpack()
        for key in ("bandage","energy","glow"):self.backpack.add(key)
        self.loot=seed_supplies(self.layout);self.placed=[]
        self.effects={"energy":0.,"quiet":0.};self.item_cooldown=0.
        self.run_stats=new_stats()
        self.player = Vector2(self.layout.spawn)
        self.facing = Vector2(1, 0)
        self.stamina, self.exhausted, self.flashlight = 100., False, True
        self.max_health, self.health = 100, 100
        self.invulnerable, self.hit_flash = 0., 0.
        self.last_attacker = ""
        self.hits_taken = 0
        self.medkits = [Vector2(p) for p in self.layout.medkit_spawns]
        self.fuses = [Vector2(p) for p in self.layout.fuses]
        self.collected = 0
        self.bottles = self.difficulty.bottles
        self.pickups = [Vector2(p) for p in self.rng.sample(self.layout.bottle_spawns, 9)]
        self.monsters = [Monster(kind, Vector2(pos), Vector2(1, 0).rotate(self.rng.randrange(360)))
                         for kind, pos in zip(("Penjaga", "Pendengar", "Penyergap"), self.layout.monster_spawns)]
        self.noises: list[Noise] = []
        self.audio_events = []
        self.elapsed, self.step_distance, self.noise_level = 0., 0., 0.
        self.power, self.panel_progress = False, 0.
        self.status, self.death_reason = "playing", ""
        self.visited = {self.layout.spawn_room}
        self.message = "Cari 2 sekring."
        self.message_time = 7.
        self.threat = 0.
        self.total_noises, self.chases = 0, 0
        self.throw_cooldown, self.interact_cooldown = 0., 0.
        self.last_mode = "walk"
        self.moving = False
        self.encounter_timer = self.encounter_cooldown = 0.
        self.chase_active = False
        self.encounter_count = 0
        self.visible_monsters = set()

    def player_can_see(self, monster):
        delta = monster.pos - self.player
        distance = delta.length()
        visible = distance < (95 if self.flashlight else 70)
        if self.flashlight and 0 < distance < 355:
            visible |= delta.normalize().dot(self.facing) > .88
        if distance<450:
            visible |= any(p.kind=="glow" and monster.pos.distance_to(p.pos)<170 and self.layout.line_clear(p.pos,monster.pos) for p in self.placed)
        return visible and self.layout.line_clear(self.player, monster.pos)

    def changed(self):
        if self.mode_key=="story":self.save_request=True

    def found_item(self,key,count=1):
        self.run_stats["items_found"]+=count
        if key not in self.run_stats["found_types"]:self.run_stats["found_types"].append(key)
        self.changed()

    def collect_item(self,key,natural=True):
        if not self.backpack.add(key):
            self.notify("Tas penuh / batas tumpukan. Buka B untuk mengatur bekal.",3)
            return False
        if natural:self.found_item(key)
        else:self.changed()
        self.sound("pickup");self.notify("+1 "+ITEMS[key].name,1.7);return True

    def placement(self):
        for distance in (40,60,20,0):
            point=Vector2(self.layout.center(self.layout.tile(self.player+self.facing*distance)))
            if self.layout.walkable(self.layout.tile(point)) and self.layout.line_clear(self.player,point):return point
        return None

    def drop_item(self,key):
        if self.status!="playing" or self.backpack.count(key)<=0:return False
        point=self.placement()
        if point is None:self.notify("Tidak ada tempat untuk meletakkan item.",2);return False
        self.backpack.remove(key);self.loot.append(Loot(key,point,natural=False));self.changed();self.sound("pickup",volume=.5)
        self.notify(ITEMS[key].name+" diletakkan",1.5);return True

    def use_item(self,key):
        if self.status!="playing" or key not in ITEMS:return False
        if self.item_cooldown>0:self.notify("Tunggu sebentar",1);return False
        if self.backpack.count(key)<=0:self.notify(ITEMS[key].name+" habis",1.5);return False
        if key=="bottle":return self.throw(self.player+self.facing*280)
        if key in ("medkit","bandage"):
            if self.health>=self.max_health:self.notify("HP penuh",1.5);return False
            restored=min(40 if key=="medkit" else 20,self.max_health-self.health)
            self.health+=restored;self.run_stats["heals_used"]+=1
            self.notify(f"+{restored} HP",1.5);self.sound("heal")
        elif key=="energy":
            if self.effects["energy"]>0:self.notify("Efek minuman masih aktif",1.5);return False
            if self.stamina<=25:self.run_stats["low_stamina_drinks"]+=1
            self.stamina=min(100,self.stamina+45);self.exhausted=False;self.effects["energy"]=9.
            self.notify("Stamina +45 · Energi 9 dtk",2);self.sound("drink")
        elif key=="tape":
            if self.effects["quiet"]>0:self.notify("Peredam masih aktif",1.5);return False
            self.effects["quiet"]=20.;self.notify("Langkah diredam · 20 dtk",2);self.sound("tape")
        else:
            point=self.placement()
            if point is None:self.notify("Tidak ada tempat untuk meletakkan item.",2);return False
            if key=="alarm":
                self.placed.append(PlacedItem("alarm",point,10.,3.));self.notify("Alarm aktif dalam 3 detik",2)
            else:
                glows=[p for p in self.placed if p.kind=="glow"]
                if len(glows)>=3:self.placed.remove(glows[0])
                self.placed.append(PlacedItem("glow",point,45.))
                area=f"{getattr(self,'level_key','escape')}:{self.layout.room_at(point)}"
                if area not in self.run_stats["glow_areas"]:self.run_stats["glow_areas"].append(area)
                self.notify("Lampu kimia · 45 dtk",2)
            self.sound("deploy",point,.6)
        self.backpack.remove(key);self.item_cooldown=.6
        used=self.run_stats["items_used"];used[key]=used.get(key,0)+1;self.changed();return True

    def update_equipment(self,dt):
        self.item_cooldown=max(0,self.item_cooldown-dt)
        for key in self.effects:self.effects[key]=max(0,self.effects[key]-dt)
        for item in self.placed[:]:
            if item.delay>0:
                item.delay=max(0,item.delay-dt)
                if item.delay>0:continue
            item.life-=dt
            if item.life<=0:self.placed.remove(item);continue
            if item.kind=="alarm":
                item.pulse-=dt
                if item.pulse<=0:
                    item.pulse=2.;self.emit_noise(item.pos,12,"alarm saku","alarm")

    def startle(self, monster, force=False):
        if self.encounter_cooldown > 0 or not self.player_can_see(monster):
            return False
        self.encounter_timer, self.encounter_cooldown = .65, 14.
        self.encounter_count += 1
        self.sound("stinger", volume=.72)
        self.sound("monster_" + {"Penjaga": "guard", "Pendengar": "listener", "Penyergap": "ambusher"}[monster.kind], monster.pos, .85)
        return True

    def take_hit(self, monster):
        if self.status != "playing" or self.invulnerable > 0:
            return False
        base = {"Penjaga": 28, "Pendengar": 22, "Penyergap": 38 if monster.state == "dash" else 24}[monster.kind]
        damage = round(base * self.difficulty.damage)
        self.health = max(0, self.health - damage)
        self.invulnerable, self.hit_flash = 1.6, .4
        self.last_attacker = monster.kind
        self.hits_taken += 1
        monster.wait = max(monster.wait, .85)
        self.stamina = max(self.stamina, 35)
        self.exhausted = False
        away = self.player - monster.pos
        if away.length_squared() < .1:
            away = -monster.facing if monster.facing.length_squared() else Vector2(-1, 0)
        self.move(self.player, away.normalize() * 65, 11)
        if monster.state == "dash":
            monster.state, monster.timer, monster.cooldown = "recovery", 2.5, 5
        if self.health > 0:
            self.sound("hurt")
            self.notify(f"-{damage} HP", 1.3)
        else:
            self.status = "lost"
            self.death_reason = monster.kind
            self.sound("caught")
        return True

    def notify(self, message, duration=4):
        self.message, self.message_time = message, duration

    def sound(self, name, position=None, volume=1.):
        self.audio_events.append((name, Vector2(position or self.player), volume))

    def emit_noise(self, position, radius, label, audible=None):
        self.total_noises += 1
        position = Vector2(position)
        self.noises.append(Noise(position, radius, 0, label))
        if position.distance_to(self.player) < 40:
            self.noise_level = max(self.noise_level, min(1., radius / 10))
        if audible:
            self.sound(audible, position)
        budget = radius * self.difficulty.hearing * 1.8
        field = self.layout.sound_field(position, budget)
        for monster in self.monsters:
            if self.elapsed < self.difficulty.grace:
                continue
            multiplier = 1.8 if monster.kind == "Pendengar" else .85
            cost = field.get(self.layout.tile(monster.pos), math.inf)
            if cost > radius * self.difficulty.hearing * multiplier:
                continue
            if monster.state in ("windup", "dash", "recovery"):
                continue
            if monster.state == "chase" and monster.memory > self.difficulty.search_time - .6:
                continue
            monster.target = Vector2(self.layout.nearest_floor(position))
            if label in ("botol pecah","alarm saku") and position.distance_to(self.player)>100 and not self.sees_player(monster):
                if monster.sound_cause!=label or monster.state!="investigate":self.run_stats["lures_worked"]+=1
            monster.state = "investigate"
            monster.memory = self.difficulty.search_time
            monster.repath = 0
            monster.sound_cause = label

    def can_stand(self, position, radius):
        # Circle versus tile AABB, including doors; allows natural wall sliding.
        for y in range(int((position.y - radius) // TILE), int((position.y + radius) // TILE) + 1):
            for x in range(int((position.x - radius) // TILE), int((position.x + radius) // TILE) + 1):
                if self.layout.walkable((x, y)):
                    continue
                nearest_x = max(x * TILE, min(position.x, (x + 1) * TILE))
                nearest_y = max(y * TILE, min(position.y, (y + 1) * TILE))
                if (position.x - nearest_x) ** 2 + (position.y - nearest_y) ** 2 < radius * radius:
                    return False
        return True

    def move(self, position, delta, radius):
        # Substeps prevent sprint/dash tunnelling even at a slower frame rate.
        steps = max(1, math.ceil(delta.length() / 7))
        for _ in range(steps):
            dx = Vector2(delta.x / steps, 0)
            dy = Vector2(0, delta.y / steps)
            if self.can_stand(position + dx, radius):
                position += dx
            if self.can_stand(position + dy, radius):
                position += dy

    def interaction(self):
        choices=[]
        def candidate(action,target,label,pos,limit,door=False):
            distance=self.player.distance_to(pos)
            if distance>=limit:return
            endpoint=Vector2(pos)
            if door and distance>0:endpoint=self.player+(endpoint-self.player)*max(0,(distance-22)/distance)
            if self.layout.line_clear(self.player,endpoint):choices.append((distance,len(choices),action,target,label))
        for i, pos in enumerate(self.fuses):
            candidate("fuse",i,"E  Ambil sekring",pos,65)
        for i, pos in enumerate(self.pickups):
            candidate("bottle",i,"E  Simpan botol",pos,60)
        for i, pos in enumerate(self.medkits):
            candidate("medkit",i,"E  Simpan P3K",pos,60)
        for i,drop in enumerate(self.loot):candidate("loot",i,"E  Ambil "+ITEMS[drop.item].name,drop.pos,58)
        if not getattr(self.layout,"interior",False) and self.player.distance_to(self.layout.panel) < 76:
            if self.power:
                candidate("panel_done",None,"Gerbang terbuka",self.layout.panel,76)
            elif self.collected<2:candidate("missing",None,f"Perlu {2-self.collected} sekring",self.layout.panel,76)
            else:candidate("panel",None,"Tahan E  Panel",self.layout.panel,76)
        if not getattr(self.layout,"interior",False) and self.player.distance_to(self.layout.exit) < 78:
            candidate("exit",None,"E  Keluar" if self.exit_ready else "Gerbang · Daya mati",self.layout.exit,78)
        for cell,door in self.layout.doors.items():
            if not door.passage:candidate("door",cell,"E  Tutup pintu" if door.opened else "E  Buka pintu",self.layout.center(cell),76,True)
        if not choices:return None
        _,_,action,target,label=min(choices)
        return action,target,label

    def interact(self):
        if self.status != "playing" or self.interact_cooldown > 0:
            return
        interaction = self.interaction()
        if not interaction:
            return
        action, target, _ = interaction
        self.interact_cooldown = .18
        if action == "fuse":
            self.fuses.pop(target)
            self.collected += 1
            self.sound("pickup")
            self.notify("Nyalakan panel utama." if self.collected == 2 else "Sekring 1/2")
        elif action == "bottle":
            if self.collect_item("bottle"):self.pickups.pop(target)
        elif action=="loot":
            drop=self.loot[target]
            if self.collect_item(drop.item,drop.natural):
                drop.quantity-=1
                if drop.quantity<=0:self.loot.pop(target)
        elif action == "door":
            door = self.layout.doors[target]
            center = Vector2(self.layout.center(target))
            occupants = [self.player] + [m.pos for m in self.monsters]
            if door.opened and any(abs(p.x - center.x) < TILE / 2 + 14 and abs(p.y - center.y) < TILE / 2 + 14 for p in occupants):
                self.notify("Pintu terhalang", 1.5)
                return
            self.layout.toggle_door(target)
            self.emit_noise(center, 4, "pintu", "door_open" if door.opened else "door_close")
        elif action == "medkit":
            if self.collect_item("medkit"):self.medkits.pop(target)
        elif action == "exit":
            if self.exit_ready:
                self.status = "won"
                self.sound("win")
            else:
                self.notify("Daya mati")
        elif action == "missing":
            self.notify("Perlu 2 sekring")

    def throw(self, aim):
        if self.status != "playing" or self.throw_cooldown > 0:
            return False
        if self.bottles <= 0:
            self.notify("Botol habis", 1.5)
            return False
        direction = Vector2(aim) - self.player
        if direction.length_squared() < 1:
            direction = self.facing.copy()
        direction = direction.normalize()
        destination = self.player.copy()
        for distance in range(12, 281, 8):
            p = self.player + direction * distance
            if not self.layout.walkable(self.layout.tile(p)):
                break
            destination = p
        self.bottles -= 1
        self.throw_cooldown = .6
        self.emit_noise(destination, 11, "botol pecah", "glass")
        used=self.run_stats["items_used"];used["bottle"]=used.get("bottle",0)+1
        self.changed();return True

    def sees_player(self, monster):
        distance = monster.pos.distance_to(self.player)
        limit = 43 if monster.kind == "Pendengar" else (330 if self.flashlight else 235)
        if self.last_mode == "crouch":
            limit *= .82
        if distance > limit or not self.layout.line_clear(monster.pos, self.player):
            return False
        if distance < 65:
            return True
        direction = (self.player - monster.pos).normalize()
        return direction.dot(monster.facing) > .32

    def _follow(self, monster, speed, dt):
        if monster.target is None:
            return
        monster.repath -= dt
        goal = self.layout.tile(monster.target)
        if monster.repath <= 0 and (goal != monster.goal_cell or monster.path_revision != self.layout.revision or not monster.path):
            monster.path = self.layout.path(self.layout.tile(monster.pos), goal)
            monster.goal_cell, monster.path_revision = goal, self.layout.revision
            monster.repath = .3 + self.rng.random() * .1
        if not monster.path:
            delta = monster.target - monster.pos
            if delta.length() > 3 and self.layout.line_clear(monster.pos, monster.target):
                self.move(monster.pos, delta.normalize() * min(delta.length(), speed * dt), 12)
            return
        cell = monster.path[0]
        door = self.layout.doors.get(cell)
        if door and not door.opened and monster.pos.distance_to(self.layout.center(cell)) < 62:
            self.layout.toggle_door(cell)
            monster.wait = .65
            self.sound("door_open", self.layout.center(cell), .65)
            return
        destination = Vector2(self.layout.center(cell))
        delta = destination - monster.pos
        if delta.length() <= 4:
            monster.path.pop(0)
            return
        monster.facing = delta.normalize()
        self.move(monster.pos, monster.facing * min(delta.length(), speed * dt), 12)

    def _update_monster(self, monster, dt):
        monster.cooldown = max(0, monster.cooldown - dt)
        monster.wait = max(0, monster.wait - dt)
        monster.memory = max(0, monster.memory - dt)
        if self.elapsed < self.difficulty.grace:
            return
        monster.vocal_timer -= dt
        if monster.vocal_timer <= 0:
            monster.vocal_timer = self.rng.uniform(10, 19)
            self.sound("monster_" + {"Penjaga": "guard", "Pendengar": "listener", "Penyergap": "ambusher"}[monster.kind], monster.pos, .55)
        visible = self.sees_player(monster)
        if monster.state == "windup":
            monster.timer -= dt
            if monster.timer <= 0:
                monster.state, monster.timer = "dash", .62
            return
        if monster.state == "dash":
            before = monster.pos.copy()
            self.move(monster.pos, monster.dash * 380 * dt, 12)
            monster.timer -= dt
            if monster.timer <= 0 or monster.pos.distance_to(before) < 1:
                monster.state, monster.timer = "recovery", 2.5
                monster.cooldown = 5
            return
        if monster.state == "recovery":
            monster.timer -= dt
            if monster.timer <= 0:
                monster.state, monster.memory = "search", self.difficulty.search_time
            return
        if visible:
            if monster.state != "chase":
                self.chases += 1
                self.sound("monster_" + {"Penjaga": "guard", "Pendengar": "listener", "Penyergap": "ambusher"}[monster.kind], monster.pos, .7)
            monster.state = "chase"
            monster.memory = self.difficulty.search_time
            monster.target = self.player.copy()
            if monster.kind == "Penyergap" and monster.cooldown <= 0 and monster.pos.distance_to(self.player) < 270:
                monster.state, monster.timer = "windup", 1.0
                delta = self.player - monster.pos
                monster.dash = delta.normalize() if delta.length_squared() else monster.facing.copy()
                monster.facing = monster.dash.copy()
        elif monster.state == "chase":
            monster.state = "search"
        if monster.memory <= 0 and monster.state in ("search", "investigate"):
            monster.state, monster.target, monster.path = "patrol", None, []
            monster.sound_cause = ""
        if monster.state == "patrol":
            if monster.target is None or monster.pos.distance_to(monster.target) < 22:
                if monster.target is not None:
                    monster.wait = self.rng.uniform(1.3, 3.8)
                room = self.rng.randrange(ROOM_COUNT)
                monster.target = Vector2(self.layout.center(self.layout.room_center_cell(room)))
                monster.repath = 0
        elif monster.target is not None and monster.pos.distance_to(monster.target) < 18:
            if monster.state == "investigate":
                monster.state = "search"
            if monster.state == "search":
                # Search around evidence, without querying the hidden player's position.
                candidates = list(self.layout.neighbors(self.layout.tile(monster.pos), True))
                if candidates:
                    monster.target = Vector2(self.layout.center(self.rng.choice(candidates)))
                    monster.repath = 0
        if monster.wait > 0:
            return
        speeds = {"Penjaga": 142, "Pendengar": 122, "Penyergap": 118}
        speed = speeds[monster.kind] * self.difficulty.speed
        if monster.state == "patrol":
            speed *= .58
        elif monster.state != "chase":
            speed *= .84
        before = monster.pos.copy()
        self._follow(monster, speed, dt)
        monster.step += monster.pos.distance_to(before)
        if monster.step > (78 if monster.kind != "Penyergap" else 105):
            monster.step = 0
            self.sound("heavy" if monster.kind == "Penjaga" else "whisper", monster.pos, .8)

    def update(self, dt, movement=(0, 0), sprint=False, crouch=False, holding=False, aim=None):
        if self.status != "playing":
            return
        dt = max(0, min(dt, .05))
        self.elapsed += dt
        self.update_equipment(dt)
        self.encounter_timer = max(0, self.encounter_timer - dt)
        self.encounter_cooldown = max(0, self.encounter_cooldown - dt)
        for door in self.layout.doors.values():
            target = float(door.opened)
            door.swing += max(-dt * 4, min(dt * 4, target - door.swing))
        self.invulnerable = max(0, self.invulnerable - dt)
        self.hit_flash = max(0, self.hit_flash - dt)
        self.throw_cooldown = max(0, self.throw_cooldown - dt)
        self.interact_cooldown = max(0, self.interact_cooldown - dt)
        self.message_time = max(0, self.message_time - dt)
        self.noise_level = max(0, self.noise_level - dt * .75)
        if aim is not None:
            delta = Vector2(aim) - self.player
            if delta.length_squared() > 4:
                self.facing = delta.normalize()
        direction = Vector2(movement)
        moving = direction.length_squared() > 0
        if moving:
            direction = direction.normalize()
        if self.exhausted and self.stamina >= 30:
            self.exhausted = False
        running = moving and sprint and not crouch and not self.exhausted and self.stamina > 0
        self.last_mode = "crouch" if crouch else "sprint" if running else "walk"
        speed = 65 if crouch else 225 if running else 125
        if running:
            self.stamina = max(0, self.stamina - (17 if self.effects["energy"]>0 else 23) * dt)
            if self.stamina <= 0:
                self.exhausted = True
                self.sound("breath")
        else:
            self.stamina = min(100, self.stamina + (26 if self.effects["energy"]>0 else 16) * dt)
        before = self.player.copy()
        self.move(self.player, direction * speed * dt, 11)
        traveled = self.player.distance_to(before)
        self.moving = traveled > .05
        if self.moving:
            if running:self.run_stats["sprint_seconds"]+=dt
            if self.effects["quiet"]>0:self.run_stats["quiet_seconds"]+=dt
        self.step_distance += traveled
        if self.step_distance > (72 if running else 52):
            self.step_distance = 0
            radius = 1 if crouch else 7 if running else 3
            if self.effects["quiet"]>0:radius*=.55
            glass = self.layout.tile(self.player) in self.layout.glass
            if glass:
                radius += 4 if not crouch else 1
            label = "pecahan kaca" if glass else "sprint" if running else "langkah"
            self.emit_noise(self.player, radius, label)
            gain = .25 if crouch else .8 if running else .48
            if self.effects["quiet"]>0:gain*=.6
            self.sound("step_" + self.layout.surface_at(self.player), volume=gain)
            if glass:
                self.sound("step_glass", volume=.35)
        self.visited.add(self.layout.room_at(self.player))
        interaction = self.interaction()
        if holding and interaction and interaction[0] == "panel":
            previous = self.panel_progress
            self.panel_progress = min(3., self.panel_progress + dt)
            if int(previous * 2) != int(self.panel_progress * 2):
                self.emit_noise(self.layout.panel, 10, "panel listrik", "panel")
            if self.panel_progress >= 3:
                self.power = True
                self.sound("power")
                self.notify("Keluar lewat gerbang utara.", 5)
        for noise in self.noises:
            noise.age += dt
        self.noises[:] = [n for n in self.noises if n.age < 1.3]
        self.threat = max(0, self.threat - dt * .2)
        self.chase_active = False
        visible_now = set()
        for monster in self.monsters:
            self._update_monster(monster, dt)
            distance = monster.pos.distance_to(self.player)
            if monster.state in ("chase", "windup", "dash"):
                self.chase_active = True
                self.threat = max(self.threat, max(0, 1 - distance / 550))
            if self.elapsed > 2 and self.player_can_see(monster):
                visible_now.add(monster.kind)
                if monster.kind not in self.visible_monsters:
                    self.startle(monster)
            if (self.elapsed > self.difficulty.grace and distance < 24
                    and monster.state not in ("recovery", "windup") and self.layout.line_clear(monster.pos, self.player)):
                self.take_hit(monster)
                if self.status == "lost":
                    break
        self.visible_monsters = visible_now
        if self.exit_ready and self.player.distance_to(self.layout.exit) < 27:
            if self.status == "playing":
                self.status = "won"
                self.sound("win")
