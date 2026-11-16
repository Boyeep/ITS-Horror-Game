"""Repeatable pursuit probes; scripted tactics are not human difficulty ratings."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pygame import Vector2
from horror.simulation import Session, Monster
from horror.floors import BuildingLayout


def run(difficulty, kind, mode, tactic):
    layout = BuildingLayout(22, 1) if mode == "story" else None
    s = Session(42, difficulty)
    if layout is not None:s.layout=layout
    # Controlled sight/noise arena, using the same collision and runtime planner.
    w, h = s.layout.width, s.layout.height
    s.layout.grid = [[int(x in (0, w-1) or y in (0, h-1)) for x in range(w)] for y in range(h)]
    s.layout.doors = {}; s.layout.glass = set()
    s.layout.ensure_hill_map(force=True)
    s.player = Vector2(s.layout.center((8, h//2)))
    m = Monster(kind, s.player-Vector2(180, 0), Vector2(1, 0), state="chase", memory=7.)
    s.monsters = [m]; s.fuses = []; s.loot = []; s.placed = []
    s.elapsed = 20.; s.audio_events.clear()
    chase_seconds = 0.; lost_at = None; previous = m.state; hits = 0
    for frame in range(600):
        elapsed = frame * .05
        if tactic == "still":
            direction = (0, 0); sprint = crouch = False
        elif tactic == "straight":
            direction = (1, 0); sprint = s.stamina > 12
            crouch = False
        else:
            # A corner loop, followed by a diversion and quiet departure.
            direction = ((1,0),(0,1),(-1,0),(0,-1))[int(elapsed/2.) % 4]
            sprint = elapsed < 6.; crouch = elapsed >= 6.
            if frame == 120:
                s.throw(s.player + Vector2(-240, 0))
                s.flashlight = False
        s.update(.05, direction, sprint, crouch, aim=s.player+Vector2(100,0))
        s.audio_events.clear()
        chase_seconds += .05 * (m.state in ("chase", "windup", "dash", "attack"))
        if previous in ("chase", "windup", "dash", "attack") and m.state in ("search", "patrol"):
            lost_at = round(elapsed, 2)
        previous = m.state
        if s.status != "playing":
            break
    return {"difficulty":difficulty,"monster":kind,"mode":mode,"tactic":tactic,
            "status":s.status,"seconds":round((frame+1)*.05,2),"chase_seconds":round(chase_seconds,2),
            "hits":s.hits_taken,"health":s.health,"lost_visual_at":lost_at,
            "end_state":m.state,"final_distance":round(m.pos.distance_to(s.player),1),
            "loss_rule":"vision/signature absent, then memory expiration" if m.state in ("search","patrol") else ""}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("build/balance-probe.json"))
    args=parser.parse_args()
    results=[run(d,k,m,t) for d in ("easy","normal","hard")
             for k in ("Penjaga","Pendengar","Penyergap")
             for m in ("escape","story") for t in ("still","straight","divert")]
    report={"commit":subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
            "scope":"54 scripted 30-second arena probes; no human playtest or progression inference", "results":results}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    for d in ("easy","normal","hard"):
        subset=[r for r in results if r["difficulty"]==d]
        print(d,{"lost":sum(r["status"]=="lost" for r in subset),"survived":sum(r["status"]=="playing" for r in subset),
                 "mean_chase_seconds":round(sum(r["chase_seconds"] for r in subset)/len(subset),2)})


if __name__=="__main__":main()
