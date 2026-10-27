"""Local achievements survive retries, new campaigns and loading older saves."""
import json
import math
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path


@dataclass(frozen=True)
class Achievement:
    key: str
    title: str
    description: str
    goal: float
    badge: str


ACHIEVEMENTS=(
    Achievement("supplies","Bekal pertama","Ambil satu perlengkapan dari dunia.",1,"bag"),
    Achievement("collector","Siap berangkat","Temukan lima jenis perlengkapan dalam satu perjalanan.",5,"bag"),
    Achievement("first_aid","Pertolongan pertama","Gunakan P3K atau perban saat terluka.",1,"heal"),
    Achievement("second_wind","Napas kedua","Minum energi saat stamina 25 atau kurang.",1,"energy"),
    Achievement("quiet_steps","Langkah ringan","Bergerak 10 detik dengan lakban peredam aktif.",10,"step"),
    Achievement("decoy","Salah arah","Alihkan monster ke botol atau alarm yang jauh darimu.",1,"alarm"),
    Achievement("trail","Jejak cahaya","Letakkan lampu kimia di tiga area berbeda.",3,"glow"),
    Achievement("explorer","Kenal kampus","Kunjungi 20 area dalam satu perjalanan.",20,"map"),
    Achievement("floors","Naik kelas","Kunjungi kesembilan lantai atas Story Mode.",9,"stairs"),
    Achievement("evidence","Tidak ada yang hilang","Kumpulkan seluruh 13 bukti cerita.",13,"book"),
    Achievement("story","Dua orang pulang","Tuntaskan ketiga bab Story Mode.",1,"exit"),
    Achievement("escape","Lewat gerbang","Menangkan satu run Escape.",1,"exit"),
    Achievement("hard","Malam tersulit","Menangkan Escape pada Hard.",1,"moon"),
    Achievement("unhurt","Tanpa luka","Menangkan Escape tanpa terkena serangan.",1,"shield"),
    Achievement("walker","Tidak perlu berlari","Menangkan Escape tanpa sprint.",1,"step"),
)
BY_KEY={a.key:a for a in ACHIEVEMENTS}


class AchievementProfile:
    def __init__(self,directory):
        self.path=Path(directory)/"achievements.json"
        self.unlocked={};self.progress={};self.dirty=False;self.recovered=False
        for candidate in (self.path,self.path.with_suffix(".bak")):
            try:
                data=json.loads(candidate.read_text(encoding="utf-8"))
                if not isinstance(data,dict) or data.get("version")!=1:continue
                self.unlocked={k:v for k,v in data.get("unlocked",{}).items() if k in BY_KEY and isinstance(v,str)}
                for key,value in data.get("progress",{}).items():
                    if key in BY_KEY and type(value) in (int,float) and math.isfinite(value):self.progress[key]=max(0,min(BY_KEY[key].goal,value))
                self.recovered=candidate!=self.path;break
            except (OSError,ValueError,TypeError,AttributeError):pass

    @staticmethod
    def measure(session):
        stats=session.run_stats;story=session.mode_key=="story";won=session.status=="won"
        return {"supplies":stats["items_found"],"collector":len(set(stats["found_types"])),
                "first_aid":stats["heals_used"],"second_wind":stats["low_stamina_drinks"],
                "quiet_steps":stats["quiet_seconds"],"decoy":stats["lures_worked"],"trail":len(set(stats["glow_areas"])),
                "explorer":len(session.visited),"floors":sum(":" in key and key.rsplit(":",1)[1]!="0" for key in set(getattr(session,"visited_floors",set()))),
                "evidence":len(set(getattr(session,"journal",[]))),"story":int(won and story),
                "escape":int(won and not story),"hard":int(won and not story and session.difficulty_key=="hard"),
                "unhurt":int(won and not story and session.hits_taken==0),
                "walker":int(won and not story and stats["sprint_seconds"]==0)}

    def observe(self,session):
        values=self.measure(session);new=[]
        for achievement in ACHIEVEMENTS:
            key=achievement.key;value=min(achievement.goal,max(0,values[key]))
            if value>self.progress.get(key,0):self.progress[key]=value;self.dirty=True
            if value>=achievement.goal and key not in self.unlocked:
                self.unlocked[key]=datetime.now(timezone.utc).isoformat(timespec="seconds");self.dirty=True;new.append(key)
        return new

    def save(self):
        if not self.dirty:return True
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            if self.path.exists():
                try:
                    raw=self.path.read_text(encoding="utf-8");old=json.loads(raw)
                    if isinstance(old,dict) and old.get("version")==1:self.path.with_suffix(".bak").write_text(raw,encoding="utf-8")
                except (OSError,ValueError):pass
            temporary=self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"version":1,"unlocked":self.unlocked,"progress":self.progress},indent=2,allow_nan=False),encoding="utf-8")
            temporary.replace(self.path);self.dirty=False;return True
        except (OSError,ValueError):return False
