"""Three-act campus mystery, persistent floors, puzzles and complete save state."""
from pygame import Vector2

from .campus import CampusLayout
from .floors import BuildingLayout
from .ground_floor import InformatikaGround
from .simulation import Session, Monster
from .inventory import seed_supplies
from .narrative import coerce_page, speech, document
from .cinematics import CUTSCENES,STAGE_SCENES,CUES,INTRO_LINES
from .speech import duration as speech_duration,pulses

from .story_data import ACTS, CHAPTERS, NOTES, QUESTS
from .story_state import StoryState


class StorySession(StoryState, Session):
    mode_key="story"

    def __init__(self,difficulty="normal",checkpoint=None):
        super().__init__(1960,difficulty,CampusLayout())
        self.campus=self.layout;self.level_key="campus";self.levels={"campus":self.layout};self.level_states={}
        self.stage=0;self.monsters=[];self.fuses=[];self.dialogue=[];self.dialogue_time=0.;self.journal=[]
        self.journal_open=False;self.journal_page=0;self.keypad=False;self.code="";self.code_error=""
        self.terminals=[];self.sequences={"catalog":[],"generator":[]};self.story_items=set();self.triggered=set()
        self.pending_encounter=None;self.ending_pending=False;self.save_request=False;self.play_seconds=0.
        self.puzzle=None;self.switches=[False,False,False];self.frequency=1084;self.puzzle_error=""
        self.shutdown_progress=0.;self.signal_off=False;self.scene_changed=False;self.transition=0.
        self.followers=[];self.companion=None;self.ambient_timer=8.;self.visited_floors=set()
        self.companion_path=[];self.companion_repath=0.
        self.message="";self.message_time=0
        self.cutscene=None;self.pending_scene=None;self.seen_scenes=set()
        self.switch_level("11:0",self.get_layout("11:0").spawn)
        self.transition=0;self.interact_cooldown=0;self.audio_events=[]
        self.start_cutscene("intro")
        if checkpoint:self.restore(checkpoint)

    @property
    def act(self):return 0 if self.stage<6 else 1 if self.stage<16 else 2
    @property
    def modal(self):return bool(self.cutscene or self.dialogue or self.keypad or self.journal_open or self.puzzle)
    @property
    def objective(self):return CHAPTERS[self.stage][1]
    @property
    def exit_ready(self):return self.level_key=="campus" and self.stage==24 and self.power and self.signal_off
    @property
    def location(self):
        if hasattr(self.layout,"location_name"):return self.layout.location_name(self.player)
        return self.layout.room_names[self.layout.room_at(self.player)].title()
    @property
    def goal_rooms(self):
        if self.stage==3:return [self.campus.room_at(p) for p in (self.fuses if self.level_key=="campus" else self.state_for("campus")["fuses"])]
        if self.stage==4:return [[7,21,2][min(2,len(self.terminals))]]
        return CHAPTERS[self.stage][2]

    def get_layout(self,key):
        if key not in self.levels:
            building,floor=map(int,key.split(":"))
            self.levels[key]=InformatikaGround(self.campus.room_names,self.campus.room_kinds) if (building,floor)==(11,0) else BuildingLayout(building,floor)
        return self.levels[key]

    def state_for(self,key):
        if key not in self.level_states:
            layout=self.get_layout(key)
            self.level_states[key]={"fuses":[],"pickups":[Vector2(p) for p in layout.bottle_spawns],
                                    "medkits":[Vector2(p) for p in layout.medkit_spawns],"monsters":[],
                                    "loot":seed_supplies(layout),"placed":[]}
        return self.level_states[key]

    def stash(self):
        self.level_states[self.level_key]={"fuses":self.fuses,"pickups":self.pickups,"medkits":self.medkits,
                                          "monsters":self.monsters,"loot":self.loot,"placed":self.placed}

    def point(self,room,offset=(40,0),floor=0,index=0):
        if floor:return Vector2(self.get_layout(f"{room}:{floor}").quest_point(index))
        if room==11:return Vector2(self.get_layout("11:0").phone_interaction)+Vector2(offset)-Vector2(40,0)
        return Vector2(self.campus.center(self.campus.centers[room]))+Vector2(offset)

    def on_level(self,room,floor):return self.level_key==(f"{room}:{floor}" if floor or room==11 else "campus")

    def building_options(self):
        names=("main","south","courtyard")
        if self.level_key=="campus":
            return [("building_enter",name,Vector2(self.campus.center(cell)),"E  Masuk Informatika") for name,cell in zip(names,self.campus.informatika_entrances)]
        if self.level_key=="11:0":
            return [("building_exit",name,Vector2(pos),"E  Keluar gedung") for name,pos in self.layout.exit_points.items()]
        return []

    def use_building(self,action,entrance):
        if action=="building_enter":
            target=self.get_layout("11:0");self.switch_level("11:0",target.entry_spawns[entrance])
        else:
            index=("main","south","courtyard").index(entrance)
            offset=((40,0),(0,40),(-40,0))[index]
            self.switch_level("campus",Vector2(self.campus.center(self.campus.informatika_entrances[index]))+Vector2(offset))
        self.sound("door_open",volume=.6)

    def switch_level(self,key,destination):
        old_key=self.level_key
        pursuer=next((m for m in self.monsters if m.state in ("chase","windup","dash") and m.pos.distance_to(self.player)<420
                      and self.layout.line_clear(m.pos,self.player)),None)
        if pursuer:
            self.monsters.remove(pursuer)
            self.followers.append({"kind":pursuer.kind,"level":key,"point":list(destination),"time":2.8})
        self.stash();self.layout=self.get_layout(key);self.level_key=key;self.seed=self.layout.seed
        state=self.state_for(key)
        self.fuses,self.pickups,self.medkits,self.monsters=(state[k] for k in ("fuses","pickups","medkits","monsters"))
        self.loot,self.placed=state["loot"],state["placed"]
        self.player=Vector2(destination);self.noises=[];self.visible_monsters=set()
        self.chase_active=False;self.threat=0;self.encounter_timer=0
        self.invulnerable=max(self.invulnerable,1.2);self.interact_cooldown=.45
        self.scene_changed=True;self.transition=.45;self.save_request=True
        self.visited_floors.add(key);self.sound("stairs",volume=.65)
        self.notify(self.location,3)
        if self.companion and old_key==self.companion["level"]:
            self.companion={"level":key,"pos":list(self.player+Vector2(35,0))}
            self.companion_path=[];self.companion_repath=0

    def stair_options(self):
        if self.level_key=="campus":
            return [("enter",n,Vector2(p),"E  Naik · Lantai 2") for n,p in self.campus.stairs.items() if n!=11]
        if self.layout.building==11:
            return [(direction,(11,key),Vector2(p),"E  Turun" if direction=="down" else "E  Naik") for direction,key,p in self.layout.stair_portals]
        return [(direction,self.layout.building,Vector2(pos),"E  Turun" if direction=="down" else "E  Naik")
                for direction,pos in self.layout.stairs]

    def use_stairs(self,direction,building):
        portal=None
        if isinstance(building,tuple):building,portal=building
        if building==11:
            portal=portal or ("se" if direction=="up" else "sw")
            if direction=="down" and self.layout.floor==1:
                target=self.get_layout("11:0")
                self.switch_level("11:0",Vector2(target.stair_points[portal])+Vector2(40,0))
            else:
                floor=1 if direction=="enter" else self.layout.floor+(1 if direction=="up" else -1)
                target=self.get_layout(f"11:{floor}")
                opposite="down" if direction in ("enter","up") else "up"
                point=next(p for d,key,p in target.stair_portals if d==opposite and key==portal)
                self.switch_level(f"11:{floor}",Vector2(point)+Vector2(40,0))
            return
        if direction=="enter":
            target=self.get_layout(f"{building}:1");self.switch_level(f"{building}:1",target.spawn)
        elif direction=="up":
            floor=self.layout.floor+1;target=self.get_layout(f"{building}:{floor}")
            self.switch_level(f"{building}:{floor}",target.spawn)
        elif self.layout.floor==1:
            self.switch_level("campus",Vector2(self.campus.stairs[building])+Vector2(0,40))
        else:
            floor=self.layout.floor-1;target=self.get_layout(f"{building}:{floor}")
            self.switch_level(f"{building}:{floor}",Vector2(target.up)+Vector2(-40,0))

    def open_dialogue(self,pages):
        self.dialogue=[coerce_page(page) for page in pages];self.dialogue_time=0.

    @property
    def typing(self):
        return bool(self.dialogue and self.dialogue[0]["kind"]=="speech" and self.dialogue_time<speech_duration(self.dialogue[0].get("body","")))

    def reveal_dialogue(self):
        if self.dialogue:self.dialogue_time=speech_duration(self.dialogue[0].get("body",""))+.01

    def update_dialogue(self,dt):
        if not self.dialogue or self.dialogue[0]["kind"]!="speech":return
        page=self.dialogue[0];body=page.get("body","");before=self.dialogue_time
        self.dialogue_time=min(speech_duration(body)+.01,before+min(.05,max(0,dt)))
        if pulses(body,before,self.dialogue_time):self.sound("voice_"+page.get("speaker","arga"),volume=.7)
    def start_cutscene(self,key):
        if key not in CUTSCENES or key in self.seen_scenes:return False
        self.cutscene={"id":key,"time":0.};self.save_request=True
        return True

    def finish_cutscene(self):
        if not self.cutscene:return
        key=self.cutscene["id"];self.seen_scenes.add(key);self.cutscene=None;self.save_request=True
        if key=="intro":
            if self.level_key=="11:0":self.facing=(Vector2(self.layout.phone_display)-self.player).normalize()
            self.notify(self.objective,5)
        if not self.dialogue:self.after_presentation()

    def update_cutscene(self,dt):
        before=self.cutscene["time"];key=self.cutscene["id"]
        after=min(CUTSCENES[key],before+min(.05,max(0,dt)))
        self.cutscene["time"]=after
        for moment,sound,volume in CUES.get(key,()):
            if before<moment<=after:self.sound(sound,volume=volume)
        if key=="intro":
            for start,end,speaker,body in INTRO_LINES:
                if speaker and before<end and after>=start and pulses(body,before-start,min(after,end)-start):
                    self.sound("voice_"+speaker,volume=.7)
        if after>=CUTSCENES[key]:self.finish_cutscene()

    def after_presentation(self):
        if self.pending_scene:
            key=self.pending_scene;self.pending_scene=None
            if self.start_cutscene(key):return
        if self.ending_pending:self.status="won";self.sound("win")
        elif self.pending_encounter:
            kind=self.pending_encounter;self.pending_encounter=None;self.spawn_encounter(kind)

    def note(self,key):
        if key not in self.journal:self.journal.append(key)
    def next_dialogue(self,skip=False):
        if not self.dialogue:return
        self.dialogue=[] if skip else self.dialogue[1:];self.dialogue_time=0.
        if not self.dialogue:self.after_presentation()

    def advance(self,stage,pages=()):
        old_act=self.act;self.stage=stage;self.save_request=True
        scene=STAGE_SCENES.get(stage)
        if scene and scene not in self.seen_scenes:self.pending_scene=scene
        self.notify(self.objective,5)
        pages=list(pages)
        if self.act!=old_act:pages.insert(0,(ACTS[self.act],"Kamu menyimpan semua bukti. Jalan pulang kini bergantung pada apa yang benar-benar terjadi pukul 23.47."))
        if pages:self.open_dialogue(pages)
        if scene in ("reunion","shutdown") and self.pending_scene:
            self.pending_scene=None;self.start_cutscene(scene)
        elif not pages and self.pending_scene:self.after_presentation()

    def quest_objects(self):
        if self.stage==4 and self.level_key=="campus":
            return [(f"terminal:{n}",self.point(n),"E  Aktifkan jalur "+label) for n,label in ((7,"Air"),(21,"Mesin"),(2,"Data"))]
        if self.stage==10 and self.on_level(22,1):
            return [(f"catalog:{n}",self.point(22,floor=1,index=i),"E  Baca "+label) for i,(n,label) in enumerate(((9,"Evakuasi 09"),(4,"Catatan 04"),(17,"Rekaman 17")))]
        if self.stage==18 and self.on_level(21,1):
            return [(f"generator:{i}",self.point(21,floor=1,index=i),"E  Putar katup "+chr(65+i)) for i in range(3)]
        quest=QUESTS.get(self.stage)
        if not quest:return []
        key,room,floor,index,label=quest
        if not self.on_level(room,floor):return []
        offset=(-80,80) if key in ("radio","earth") else (40,0)
        actions={"phone":"Periksa ponsel Nara","note":"Baca catatan","locker":"Buka loker","nara":"Bicara dengan Nara",
                 "server":"Gunakan terminal","film":"Baca mikrofilm","log":"Baca buku jaga","photo":"Periksa foto",
                 "incident":"Baca laporan","gate_key":"Ambil kunci gerbang","key":"Buka kotak properti"}
        return [(key,self.point(room,offset,floor,index),"Tahan E  Matikan pemancar" if key=="shutdown" else "E  "+actions.get(key,"Periksa "+label.lower()))]

    def interaction(self):
        for key,pos,label in self.quest_objects():
            if self.player.distance_to(pos)<68 and self.layout.line_clear(self.player,pos):
                return ("shutdown" if key=="shutdown" else "story"),key,label
        for action,key,pos,label in self.building_options():
            if self.player.distance_to(pos)<65 and self.layout.line_clear(self.player,pos):return action,key,label
        for direction,building,pos,label in self.stair_options():
            if self.player.distance_to(pos)<58 and self.layout.line_clear(self.player,pos):
                nearby=super().interaction()
                if nearby and nearby[0]=="door":
                    door=self.layout.doors[nearby[1]]
                    distance=self.player.distance_to(self.layout.center(nearby[1]))
                    if not door.opened and distance<self.player.distance_to(pos):return nearby
                if nearby and nearby[0] in ("fuse","medkit","bottle","loot"):
                    positions={"fuse":self.fuses,"medkit":self.medkits,"bottle":self.pickups,"loot":[p.pos for p in self.loot]}[nearby[0]]
                    if self.player.distance_to(positions[nearby[1]])<self.player.distance_to(pos):return nearby
                return "stairs",(direction,building),label
        if self.level_key=="campus":
            if 16<=self.stage<23 and self.player.distance_to(self.point(19))<68:
                return "story","nara_hint","E  Nara"
            if self.player.distance_to(self.campus.panel)<76 and self.stage<22 and self.stage!=2:
                return "story_block",None,"Panel · Suara masih berulang"
            if self.player.distance_to(self.campus.exit)<78 and not self.exit_ready:
                return "story_block",None,"Gerbang · Kunci mekanis"
        return super().interaction()

    def interact(self):
        if self.status!="playing":return
        if self.cutscene:return
        if self.dialogue:self.next_dialogue();return
        if self.modal or self.interact_cooldown>0:return
        interaction=self.interaction()
        if not interaction:return
        action,key,_=interaction
        if action in ("building_enter","building_exit"):self.use_building(action,key);return
        if action=="stairs":self.use_stairs(*key);return
        if action=="story_block":self.notify(self.objective,3);return
        if action=="shutdown":return
        if action=="story":
            self.interact_cooldown=.2;self.handle_quest(key);return
        before=self.collected;super().interact()
        if self.stage==3 and self.collected>before:
            self.save_request=True
            if self.collected==2:self.advance(4,[("Diagram Nara","Dua sekring terpasang. Diagram menunjuk tiga jalur: AIR, MESIN, DATA.")])
        self.wrap_ending()

    def handle_quest(self,key):
        if key=="nara_hint":self.open_dialogue([speech("nara","Aku menunggu di sini bersama petugas. "+self.objective)]);return
        if key.startswith("terminal:"):self.press_terminal(int(key.split(":")[1]));return
        if key.startswith("catalog:") or key.startswith("generator:"):
            name,value=key.split(":");self.press_sequence(name,int(value));return
        if key=="locker":self.keypad=True;self.code="";self.code_error="";return
        if key in ("circuit","frequency","isolation"):
            self.puzzle=key;self.puzzle_error="";self.sound("radio",volume=.4);return
        events={
            "phone":("pesan",1,"Ponsel",[document("pesan"),speech("arga","Ponsel Nara… menerima pesan dari nomornya sendiri?")]),
            "note":("rak",2,None,[document("rak"),("Di balik kaca","Sosok itu menoleh lebih lambat daripada bayangannya.")]),
            "radio":("rekaman",6,None,[document("rekaman")]),
            "log":("jaga",7,"Kartu asrama",[document("jaga")]),
            "photo":("foto",8,"Foto Nara",[document("foto")]),
            "server":("server",9,"Akses arsip",[("Terminal server","Kamu memasukkan tahun pada cap foto: 1998. Folder SIMPUL terbuka."),document("server")]),
            "film":("film",10,None,[document("film")]),
            "key":(None,12,"Kunci servis",[("Kotak properti","Sebuah kunci berlabel PEMANCAR. Ada tiga goresan di gagangnya. Kamu ingat urutan panel dari daftar evakuasi.")]),
            "antenna":("antena",15,None,[document("antena"),speech("nara","Tasku bukan kuning. Itu tasmu, Arga. Aku di SCC.","Nara · Radio")]),
            "incident":("insiden",17,None,[document("insiden")]),
            "earth":(None,18,"Jalur bumi",[("Halaman Manarul Ilmi","Batang pembumian tertanam di tanah basah. Setelah kabel terhubung, dengung di ponselmu turun satu nada. Nara menunggu kabar dari generator.")]),
            "gate_key":(None,22,"Kunci gerbang",[("Lemari servis","Kunci kuningan bertanda BARAT. Pemancar sudah mati, tetapi daya gerbang harus dipulihkan dari panel rektorat.")]),
        }
        if key=="nara":
            if self.stage==15:
                self.note("nara");self.story_items.add("Radio Nara")
                self.advance(16,[speech("nara","Jahitan tasmu lepas lagi. Aku yang menjahitnya. Bukan suara di ponsel itu."),document("nara")])
            else:
                self.companion={"level":"campus","pos":list(self.point(19))}
                self.advance(24,[speech("nara","Kali ini kita pulang berdua. Jangan berhenti kalau ponselnya berdering.")])
            return
        note,stage,item,pages=events[key]
        if note:self.note(note)
        if item:self.story_items.add(item)
        self.advance(stage,pages)
        if key in ("note","radio","film","antenna","incident"):
            self.pending_encounter={"note":"Penjaga","radio":"Penyergap","film":"Pendengar","antenna":"Penyergap","incident":"Penjaga"}[key]
            self.triggered.add(key)

    def submit_code(self):
        if self.code!="2413":
            self.code_error="Tidak cocok.";self.code="";self.emit_noise(self.player,7,"loker","panel");return False
        self.keypad=False;self.story_items.add("Kartu akses");self.note("jalur")
        self.fuses=[Vector2(p) for p in self.campus.fuses]
        self.advance(3,[("Loker 04","Sebuah kartu akses dan diagram listrik. Di belakang kartu: 'Jika pesannya terulang, itu bukan aku.'"),document("jalur")])
        self.pending_encounter="Pendengar";self.triggered.add("locker");return True

    def press_terminal(self,room):
        expected=(7,21,2)
        if room in self.terminals:self.notify("Jalur aktif",2);return
        if room!=expected[len(self.terminals)]:
            self.terminals=[];self.emit_noise(self.player,12,"alarm panel","panel");self.notify("Urutan salah. Baca diagram.",3);return
        self.terminals.append(room);self.sound("panel");self.save_request=True
        if len(self.terminals)==3:self.advance(5,[("Pemancar","Arus mengalir. Suara Nara memanggilmu ke Taman Alumni. Suaranya terlalu jernih untuk sebuah pemancar tua.")])
        else:self.notify(f"Jalur {len(self.terminals)}/3",2)

    def press_sequence(self,name,value):
        expected={"catalog":[4,17,9],"generator":[0,2,1]}[name];sequence=self.sequences[name]
        if value!=expected[len(sequence)]:
            self.sequences[name]=[];self.emit_noise(self.player,10,"urutan salah","panel");self.notify("Urutan terputus. Periksa catatan.",3);return
        sequence.append(value);self.sound("book" if name=="catalog" else "valve");self.save_request=True
        if len(sequence)==3:
            if name=="catalog":self.note("katalog");self.advance(11,[document("katalog")])
            else:self.story_items.add("Daya cadangan");self.advance(19,[("Generator","Tiga katup terkunci. Lampu darurat kembali menyala. Dari radio, Nara memintamu mengisolasi jalur umpan balik pemancar.")])
        else:self.notify(f"{len(sequence)}/3",2)

    def puzzle_input(self,action):
        if self.puzzle=="frequency" and action in ("left","right"):
            self.frequency=max(1060,min(1090,self.frequency+(-2 if action=="left" else 2)));self.sound("tune",volume=.4)
        elif self.puzzle in ("circuit","isolation") and action in ("0","1","2"):
            index=int(action);self.switches[index]=not self.switches[index];self.sound("panel",volume=.6)
        elif action=="submit":
            correct=self.frequency==1078 if self.puzzle=="frequency" else self.switches==([False,True,False] if self.puzzle=="isolation" else [True,False,True])
            if not correct:
                self.puzzle_error="Belum sesuai catatan.";self.emit_noise(self.player,8,"sinyal salah","radio");return False
            puzzle=self.puzzle;self.puzzle=None;self.sound("power",volume=.45)
            if puzzle=="circuit":self.advance(13,[("Distribusi","Daya penerima menyala. Server mencatat frekuensi perawatan; penerimanya berada satu lantai di atas.")])
            elif puzzle=="frequency":self.advance(14,[speech("nara","Arga? Jangan jawab ponselnya. Temui aku lewat frekuensi ini.","Nara · 107,8 MHz")])
            else:self.advance(20,[("Isolasi","Loop terpisah dari jaringan kampus. Sekarang konsol atap dapat dimatikan. Kamu mendengar empat ketukan dari tangga.")]);self.pending_encounter="Penyergap"
            return True
        return False

    def spawn_encounter(self,kind):
        existing=next((m for m in self.monsters if m.kind==kind),None);choices=[]
        # Each named creature is unique across the campus, its floors and stair transfers.
        for state in self.level_states.values():
            state["monsters"][:]=[m for m in state["monsters"] if m.kind!=kind or m is existing]
        self.followers[:]=[f for f in self.followers if f["kind"]!=kind]
        exits=[Vector2(p) for _,_,p,_ in self.stair_options()]
        if self.level_key=="campus":
            room=self.campus.room_at(self.player)
            if room in self.campus.buildings:
                cx,cy=self.campus.centers[room];exits=[Vector2(self.campus.center((cx,cy+3)))]
        nearest=min(exits,key=lambda p:p.distance_to(self.player)) if exits else None
        exit_delta=nearest-self.player if nearest is not None else Vector2()
        exit_direction=exit_delta.normalize() if exit_delta.length_squared() else Vector2()
        px,py=self.layout.tile(self.player)
        for y in range(max(1,py-8),min(self.layout.height-1,py+9)):
            for x in range(max(1,px-8),min(self.layout.width-1,px+9)):
                pos=Vector2(self.layout.center((x,y)));delta=pos-self.player
                if 150<delta.length()<300 and self.layout.walkable((x,y)) and self.layout.line_clear(self.player,pos):
                    score=delta.normalize().dot(self.facing)*100-abs(delta.length()-230)
                    if delta.normalize().dot(exit_direction)>.2:score-=300
                    choices.append((score,x,y))
        if choices:
            _,x,y=max(choices);pos=Vector2(self.layout.center((x,y)));self.facing=(pos-self.player).normalize()
        else:
            candidates=[Vector2(p) for p in self.layout.monster_spawns]
            pos=max(candidates,key=lambda p:p.distance_to(self.player))
            if pos.distance_to(self.player)<150:return
        monster=existing or Monster(kind,pos,Vector2(1,0))
        monster.pos=pos;monster.target=None;monster.path=[];monster.state="patrol";monster.wait=2.2
        delta=self.player-pos
        if delta.length_squared():monster.facing=delta.normalize()
        if not existing:self.monsters.append(monster)
        if self.player_can_see(monster):self.startle(monster,force=True)

    def wrap_ending(self):
        if self.status=="won" and not self.ending_pending:
            self.audio_events[:]=[e for e in self.audio_events if e[0]!="win"]
            self.status="playing";self.ending_pending=True
            self.pending_scene="ending" if "ending" not in self.seen_scenes else None
            self.open_dialogue([("Gerbang utama","Nara memegang sisi pagar yang lain. Kalian mendorong bersamaan. Di luar, pagi belum datang, tetapi suara serangga kembali terdengar."),
                                ("23.48","Jam di ponsel akhirnya berganti. Nara mencabut baterainya sebelum berkas suara terakhir diputar."),
                                ("Dua orang pulang","Juru Malam berdiri di sisi dalam gerbang. Untuk pertama kalinya, bayangannya berhenti mengikuti kalian.")])

    def update(self,dt,*args,**kwargs):
        if self.cutscene:self.update_cutscene(dt);return
        if self.dialogue:self.update_dialogue(dt);return
        if self.modal or self.ending_pending:return
        holding=kwargs.get("holding",args[3] if len(args)>3 else False)
        interaction=self.interaction()
        super().update(dt,*args,**kwargs)
        dt=min(.05,max(0,dt));self.play_seconds+=dt;self.transition=max(0,self.transition-dt)
        if self.stage==22 and self.power:self.advance(23)
        if self.stage==20 and holding and interaction and interaction[0]=="shutdown":
            before=self.shutdown_progress;self.shutdown_progress=min(5.,before+dt)
            if int(before)!=int(self.shutdown_progress):self.emit_noise(self.player,12,"pemancar","radio")
            if self.shutdown_progress>=5:
                self.signal_off=True;self.note("sunyi");self.advance(21,[("Sunyi",NOTES["sunyi"][1])]);self.spawn_encounter("Penyergap")
        self.ambient_timer-=dt
        if self.ambient_timer<=0:
            self.ambient_timer=self.rng.uniform(12,23)
            if not self.signal_off:
                name="radio" if self.act>0 else "distant"
                offset=Vector2(1,0).rotate(self.rng.randrange(360))*self.rng.uniform(160,350)
                self.sound(name,self.player+offset,.22)
        for follower in self.followers[:]:
            follower["time"]-=dt
            if follower["time"]<=0:
                state=self.state_for(follower["level"]);pos=Vector2(follower["point"])
                monster=Monster(follower["kind"],pos,Vector2(1,0),state="search",target=pos.copy(),memory=6,wait=.7)
                if follower["level"]==self.level_key:self.monsters.append(monster)
                else:state["monsters"].append(monster)
                self.followers.remove(follower)
        if self.companion and self.companion["level"]==self.level_key:
            pos=Vector2(self.companion["pos"])
            if pos.distance_to(self.player)>85:
                self.companion_repath-=dt
                if self.companion_repath<=0:
                    self.companion_path=self.layout.path(self.layout.tile(pos),self.layout.tile(self.player));self.companion_repath=.5
                if self.companion_path:
                    cell=self.companion_path[0];target=Vector2(self.layout.center(cell));delta=target-pos
                    door=self.layout.doors.get(cell)
                    if door and not door.opened and delta.length()<65:
                        self.layout.toggle_door(cell);self.sound("door_open",target,.45)
                    if delta.length()<4:self.companion_path.pop(0)
                    elif delta.length_squared():self.move(pos,delta.normalize()*min(delta.length(),(185 if pos.distance_to(self.player)>200 else 145)*dt),11)
            self.companion["pos"]=list(pos)
        self.wrap_ending()


