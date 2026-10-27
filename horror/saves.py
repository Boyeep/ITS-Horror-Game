"""Atomic autosave + three independent manual slots, with last-good backups."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from .config import DIFFICULTIES


class SaveStore:
    slots=("auto","1","2","3")

    def __init__(self,directory):
        self.root=Path(directory)/"saves"
        self.recovered=False

    def path(self,slot):
        if str(slot) not in self.slots:raise ValueError("Unknown save slot")
        return self.root/("autosave.json" if str(slot)=="auto" else f"slot-{slot}.json")

    @staticmethod
    def valid(data):
        if not isinstance(data,dict):return False
        version=data.get("version")
        basic=(version in (1,2,3,4,5,6,7) and type(data.get("stage")) is int and 0<=data["stage"]<(8 if version==1 else 25)
               and data.get("difficulty") in DIFFICULTIES)
        if not basic:return False
        def vector(value):
            return isinstance(value,list) and len(value)==2 and all(type(n) in (int,float) and math.isfinite(n) for n in value)
        if "player" in data and not vector(data["player"]):return False
        if "seconds" in data and (type(data["seconds"]) not in (int,float) or not math.isfinite(data["seconds"]) or data["seconds"]<0):return False
        if version in (2,3,4,5,6,7):
            if not isinstance(data.get("layers"),dict) or not isinstance(data.get("level"),str) or not vector(data.get("player")):return False
            for layer in data["layers"].values():
                if not isinstance(layer,dict):return False
                for key in ("fuses","medkits","pickups"):
                    if not isinstance(layer.get(key,[]),list) or not all(vector(p) for p in layer.get(key,[])):return False
        return True

    def read(self,slot):
        path=self.path(slot)
        self.recovered=False
        for candidate in (path,path.with_suffix(".bak")):
            try:
                data=json.loads(candidate.read_text(encoding="utf-8"))
                if self.valid(data):
                    self.recovered=candidate!=path
                    return data
            except (OSError,ValueError,TypeError):pass
        return None

    def write(self,slot,data):
        if not self.valid(data):raise ValueError("Invalid save payload")
        payload=dict(data)
        payload["saved_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
        content=json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)
        path=self.path(slot);self.root.mkdir(parents=True,exist_ok=True)
        # Copy only a decodable current save into backup; a broken file never replaces it.
        try:
            previous=json.loads(path.read_text(encoding="utf-8"))
            if self.valid(previous):
                path.with_suffix(".bak").write_text(json.dumps(previous,ensure_ascii=False,allow_nan=False),encoding="utf-8")
        except (OSError,ValueError,TypeError):pass
        temporary=path.with_suffix(".tmp")
        temporary.write_text(content,encoding="utf-8");temporary.replace(path)
        return json.loads(content)

    def migrate(self,directory):
        if self.read("auto") is not None:return
        try:
            legacy=json.loads((Path(directory)/"story.json").read_text(encoding="utf-8"))
            if self.valid(legacy):self.write("auto",legacy)
        except (OSError,ValueError,TypeError):pass
