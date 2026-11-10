"""Gameplay rules. Sensors provide evidence; navigation never reads hidden players."""
import math
import random
from dataclasses import dataclass, field

from pygame import Vector2

from .config import DIFFICULTIES, TILE, ROOM_COUNT, ROOM_W, ROOM_H
from .world import Layout
from .inventory import Backpack, ITEMS, Loot, PlacedItem, seed_supplies, new_stats

# Local search (Hill Climbing + Simulated Annealing) parameters and explicit sensor profiles.
SIGNATURE_THRESHOLD = .42
PLAYER_PEAK_AMP = 1.85
PLAYER_PEAK_SIGMA = 3.6
TEMP_INIT = .35
TEMP_MIN = .08
TEMP_MAX = 1.0
TEMP_REHEAT = .82
COOLING_RATE = .88
REHEAT_RATE = 1.65
PLATEAU_EPS = .012
STALL_LIMIT = 4
LOCAL_SEARCH_BUDGET = 8
TRACE_LIMIT = 40

SENSOR_PROFILES = {
    "Penjaga": {"sight_lit": 330., "sight_dark": 235., "hearing": .85, "amp": 1.85, "sigma": 3.6},
    "Pendengar": {"sight_lit": 43., "sight_dark": 43., "hearing": 1.8, "amp": 2.05, "sigma": 4.2},
    "Penyergap": {"sight_lit": 330., "sight_dark": 235., "hearing": .85, "amp": 1.92, "sigma": 3.8},
}


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
    temp: float = TEMP_INIT
    stall_steps: int = 0
    sa_accepted: int = 0
    restarts: int = 0
    last_score: float = 0.
    last_decision: str = "init"
    explore_target: Vector2 | None = None
    visited_cells: list = field(default_factory=list)
    visit_heat: dict = field(default_factory=dict)
    zone_heat: dict = field(default_factory=dict)
    trace: list = field(default_factory=list)


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
        phase_rng = random.Random(seed ^ 0x711C)
        self.hill_phase = (phase_rng.uniform(0, math.tau), phase_rng.uniform(0, math.tau), phase_rng.uniform(.025, .055))

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
            monster.explore_target = None
            monster.visit_heat.clear()
            monster.zone_heat.clear()
            monster.path = []

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
        profile = SENSOR_PROFILES[monster.kind]
        limit = profile["sight_lit" if self.flashlight else "sight_dark"]
        if self.last_mode == "crouch":
            limit *= .82
        if distance > limit or not self.layout.line_clear(monster.pos, self.player):
            return False
        if distance < 65:
            return True
        direction = (self.player - monster.pos).normalize()
        return direction.dot(monster.facing) > .32

    def base_score(self, cell):
        h = self.layout.hill_height(cell)
        if h < 0:
            return -1.
        p1, p2, amp = self.hill_phase
        x, y = cell
        return h + amp * math.sin(.31 * x + p1) * math.cos(.31 * y + p2)

    def player_signature(self, monster, cell):
        if self.elapsed < self.difficulty.grace or self.status != "playing" or not self.layout.walkable(cell, True):
            return 0.
        profile = SENSOR_PROFILES[monster.kind]
        amp, sigma = profile["amp"], profile["sigma"]
        if self.last_mode == "sprint" and self.moving:
            amp *= 1.25
            sigma *= 1.32
        elif self.last_mode == "crouch":
            amp *= .62
            sigma *= .58
        elif not self.moving:
            amp *= .75
            sigma *= .72
        if self.effects["quiet"] > 0:
            amp *= .72
            sigma *= .75
        if monster.kind == "Pendengar" and (not self.moving or self.last_mode == "crouch"):
            amp *= .62
            sigma *= .65
        elif monster.kind != "Pendengar" and self.flashlight:
            amp *= 1.06
            sigma *= 1.05
        visible = self.sees_player(monster)
        dist_m = monster.pos.distance_to(self.player) / TILE
        if visible:
            amp = max(amp, PLAYER_PEAK_AMP * 1.25)
            sigma = max(sigma, dist_m * .68)
        else:
            if dist_m > sigma * 1.85:
                return 0.
            if not self.layout.line_clear(monster.pos, self.player):
                if dist_m > sigma * 1.05 or not self.moving or self.last_mode == "crouch":
                    return 0.
                amp *= .48
        px, py = self.player.x / TILE - .5, self.player.y / TILE - .5
        d_sq = (cell[0] - px) ** 2 + (cell[1] - py) ** 2
        return amp * math.exp(-d_sq / (2. * sigma * sigma))

    def neighborhood_signature(self, monster):
        cur = self.layout.tile(monster.pos)
        cells = (cur, *self.layout.neighbors(cur, True))
        return max((self.player_signature(monster, c) for c in cells), default=0.)

    def score_cell(self, monster, cell, cur=None):
        if not self.layout.walkable(cell, True):
            return -math.inf
        cur = cur or self.layout.tile(monster.pos)
        x, y = cell
        cx, cy = cur
        dx, dy = x - cx, y - cy
        score = self.base_score(cell)
        sig = self.player_signature(monster, cell)
        score += sig
        if monster.target is not None:
            tx, ty = monster.target.x / TILE - .5, monster.target.y / TILE - .5
            d = math.hypot(x - tx, y - ty)
            slope_w = .16 if monster.explore_target is not None else .22
            score += 1.25 * math.exp(-(d * d) / (2. * 3.2 * 3.2)) - slope_w * d
        if cell in self.layout.doors and not self.layout.doors[cell].opened:
            score -= .05
        heat = monster.visit_heat.get(cell, 0.)
        z_pen = .95 * monster.zone_heat.get(((x + dx) // ROOM_W, (y + dy) // ROOM_H), 0) if cell in self.layout.doors else 0.
        backtrack = .45 if len(monster.visited_cells) >= 2 and cell == monster.visited_cells[-2] else 0.
        recent = .16 * sum(1 for c in monster.visited_cells[-6:] if c == cell)
        heat_scale = .32 if sig >= SIGNATURE_THRESHOLD else 1.
        score -= heat_scale * (.28 * heat + z_pen + backtrack + recent)
        if (dx or dy) and monster.facing.length_squared() > 0:
            score += .004 * Vector2(dx, dy).normalize().dot(monster.facing)
        return score

    def _deposit_footprint(self, monster, cell):
        cx, cy = cell
        if len(monster.visit_heat) > 180:
            for k in list(monster.visit_heat):
                monster.visit_heat[k] *= .88
                if monster.visit_heat[k] < .05:
                    del monster.visit_heat[k]
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                nc = (cx + dx, cy + dy)
                if self.layout.walkable(nc, True):
                    factor = .20 if nc in self.layout.doors else 1.
                    monster.visit_heat[nc] = monster.visit_heat.get(nc, 0.) + factor * math.exp(-(dx * dx + dy * dy) / 3.)
        if cell in self.layout.doors and monster.visited_cells:
            px, py = monster.visited_cells[-1]
            ahead = (cx + (cx - px), cy + (cy - py))
            zone = (ahead[0] // ROOM_W, ahead[1] // ROOM_H)
            monster.zone_heat[zone] = monster.zone_heat.get(zone, 0) + 1
        monster.visited_cells.append(cell)
        if len(monster.visited_cells) > 32:
            monster.visited_cells.pop(0)

    def _random_floor_target(self, monster):
        floors = self.layout.floor_cells
        if not floors:
            return monster.pos.copy()
        cur = self.layout.tile(monster.pos)
        best_cell = cur
        best_val = -math.inf
        for _ in range(LOCAL_SEARCH_BUDGET):
            cand = self.rng.choice(floors)
            dist = math.hypot(cand[0] - cur[0], cand[1] - cur[1])
            val = self.base_score(cand) + (.35 if 5 <= dist <= 28 else -.25 if dist < 3 else 0.) - .3 * monster.visit_heat.get(cand, 0.)
            if val > best_val:
                best_val, best_cell = val, cand
        return Vector2(self.layout.center(best_cell))

    def _local_search_step(self, monster):
        cur = self.layout.tile(monster.pos)
        neighbors = list(self.layout.neighbors(cur, True))[:LOCAL_SEARCH_BUDGET]
        if not neighbors:
            return None
        cur_score = self.score_cell(monster, cur, cur)
        scored = [(self.score_cell(monster, n, cur), n) for n in neighbors]
        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, best_cell = scored[0]
        delta_best = best_score - cur_score
        prev_cell = monster.visited_cells[-2] if len(monster.visited_cells) >= 2 else None
        is_oscillating = (best_cell == prev_cell or best_cell in monster.visited_cells[-6:]) and len(neighbors) > 1
        is_local_optimum = delta_best < -PLATEAU_EPS
        is_plateau = abs(delta_best) <= PLATEAU_EPS
        climbing_player = self.player_signature(monster, best_cell) >= SIGNATURE_THRESHOLD
        if (is_local_optimum or is_plateau or is_oscillating) and not climbing_player:
            monster.stall_steps += 1
            monster.temp = min(TEMP_MAX, max(monster.temp * REHEAT_RATE, TEMP_REHEAT))
            reason = "local_optimum" if is_local_optimum else "plateau" if is_plateau else "oscillation"
        else:
            monster.stall_steps = max(0, monster.stall_steps - 1)
            monster.temp = max(TEMP_MIN, monster.temp * COOLING_RATE)
            reason = "hill_climb"
        if monster.stall_steps >= STALL_LIMIT and not climbing_player:
            monster.restarts += 1
            monster.stall_steps = 0
            monster.temp = TEMP_MAX
            if monster.explore_target is not None or monster.target is None or (
                    monster.state in ("patrol", "search") and monster.pos.distance_to(monster.target) < 110):
                monster.explore_target = self._random_floor_target(monster)
                monster.target = monster.explore_target.copy()
                monster.visit_heat.clear()
                cur_score = self.score_cell(monster, cur, cur)
                scored = [(self.score_cell(monster, n, cur), n) for n in neighbors]
                scored.sort(key=lambda item: item[0], reverse=True)
                best_score, best_cell = scored[0]
                delta_best = best_score - cur_score
            reason = "restart_random_floor"
        if reason == "hill_climb" and (delta_best > PLATEAU_EPS or climbing_player):
            chosen_score, chosen_cell = best_score, best_cell
        else:
            pool = [item for item in scored if item[1] != prev_cell] or scored
            cand_score, cand_cell = self.rng.choice(pool)
            delta = cand_score - cur_score
            accept_prob = 1. if delta >= 0 else math.exp(max(-20., delta / max(TEMP_MIN, monster.temp)))
            if self.rng.random() < accept_prob:
                chosen_score, chosen_cell = cand_score, cand_cell
                if delta < 0:
                    monster.sa_accepted += 1
                    if reason != "restart_random_floor":
                        reason = "sa_downhill"
                elif reason != "restart_random_floor":
                    reason = "sa_uphill"
            else:
                chosen_score, chosen_cell = pool[0]
                if chosen_score < cur_score:
                    monster.sa_accepted += 1
                    if reason != "restart_random_floor":
                        reason = "sa_downhill"
        monster.last_score = round(chosen_score, 4)
        monster.last_decision = reason
        monster.goal_cell = chosen_cell
        monster.path = [chosen_cell]
        monster.path_revision = self.layout.revision
        monster.trace.append({"from": cur, "to": chosen_cell, "score": monster.last_score,
                              "delta": round(chosen_score - cur_score, 4), "temp": round(monster.temp, 3),
                              "decision": reason, "state": monster.state})
        if len(monster.trace) > TRACE_LIMIT:
            monster.trace.pop(0)
        return chosen_cell

    def _follow(self, monster, speed, dt):
        if monster.target is None and monster.state == "patrol" and monster.explore_target is None:
            return
        cur = self.layout.tile(monster.pos)
        if not monster.visited_cells or monster.visited_cells[-1] != cur:
            self._deposit_footprint(monster, cur)
        if (monster.target is not None and cur == self.layout.tile(monster.target)
                and self.layout.line_clear(monster.pos, monster.target)):
            delta = monster.target - monster.pos
            if delta.length() > 3:
                monster.facing = delta.normalize()
                self.move(monster.pos, monster.facing * min(delta.length(), speed * dt), 12)
            monster.path = []
            return
        monster.repath -= dt
        if not monster.path or not self.layout.walkable(monster.path[0], True):
            if self._local_search_step(monster) is None:
                return
            monster.repath = .28 + self.rng.random() * .08
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
            if self._local_search_step(monster) is None:
                return
            monster.repath = .28 + self.rng.random() * .08
            cell = monster.path[0]
            door = self.layout.doors.get(cell)
            if door and not door.opened and monster.pos.distance_to(self.layout.center(cell)) < 62:
                self.layout.toggle_door(cell)
                monster.wait = .65
                self.sound("door_open", self.layout.center(cell), .65)
                return
            destination = Vector2(self.layout.center(cell))
            delta = destination - monster.pos
            if delta.length() <= 1:
                return
        monster.facing = delta.normalize()
        before = monster.pos.copy()
        self.move(monster.pos, monster.facing * min(delta.length(), speed * dt), 12)
        if monster.pos.distance_to(before) < .15 and delta.length() > 6:
            center_delta = Vector2(self.layout.center(cur)) - monster.pos
            if center_delta.length() > 1:
                self.move(monster.pos, center_delta.normalize() * min(center_delta.length(), speed * dt), 12)
            monster.path = []
            monster.repath = 0

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
            monster.explore_target = None
            monster.temp = max(TEMP_MIN, min(monster.temp, .14))
            if monster.kind == "Penyergap" and monster.cooldown <= 0 and monster.pos.distance_to(self.player) < 270:
                monster.state, monster.timer = "windup", 1.0
                delta = self.player - monster.pos
                monster.dash = delta.normalize() if delta.length_squared() else monster.facing.copy()
                monster.facing = monster.dash.copy()
        else:
            if monster.state == "chase":
                monster.state = "search"
            lured = (monster.state == "investigate" and monster.sound_cause in ("botol pecah", "alarm saku")
                     and monster.memory > self.difficulty.search_time - 2.5)
            if not lured and self.neighborhood_signature(monster) >= SIGNATURE_THRESHOLD:
                monster.explore_target = None
                monster.target = self.player.copy()
                monster.temp = max(TEMP_MIN, min(monster.temp, .16))
                if monster.state == "patrol":
                    monster.state = "search"
                monster.memory = max(monster.memory, min(self.difficulty.search_time, 3.5))
        if monster.memory <= 0 and monster.state in ("search", "investigate"):
            monster.state, monster.target, monster.path = "patrol", None, []
            monster.explore_target = None
            monster.sound_cause = ""
        if monster.state == "patrol":
            if monster.target is None or monster.pos.distance_to(monster.target) < 22:
                if monster.target is not None:
                    monster.wait = self.rng.uniform(1.3, 3.8)
                cur = self.layout.tile(monster.pos)
                nbs = list(self.layout.neighbors(cur, True))
                cur_b = self.base_score(cur)
                best_nb = max(nbs, key=lambda n: self.base_score(n) - .2 * monster.visit_heat.get(n, 0.), default=None)
                if best_nb is not None and self.base_score(best_nb) > cur_b + PLATEAU_EPS:
                    monster.explore_target = None
                    monster.target = Vector2(self.layout.center(best_nb))
                else:
                    monster.temp = max(monster.temp, TEMP_REHEAT)
                    monster.explore_target = self._random_floor_target(monster)
                    monster.target = monster.explore_target.copy()
                monster.repath = 0
        elif monster.target is not None and monster.pos.distance_to(monster.target) < 18:
            if monster.state == "investigate":
                monster.state = "search"
            if monster.state == "search":
                # Local optimum at vanished peak -> reheat SA and pick a random floor exploration target.
                monster.temp = max(monster.temp, TEMP_REHEAT)
                monster.restarts += 1
                monster.explore_target = self._random_floor_target(monster)
                monster.target = monster.explore_target.copy()
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
