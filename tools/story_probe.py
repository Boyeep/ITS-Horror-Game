"""Known-answer campaign bot; integration evidence, not human difficulty/duration."""
import json
import os
import sys
from pathlib import Path
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from horror.story import StorySession
from tools.campaign_driver import CampaignDriver


def play(difficulty,enemies=True):
    s=StorySession(difficulty);driver=CampaignDriver(s,enemies)
    try:report=driver.run();report["error"]=""
    except (AssertionError,IndexError,ValueError) as exc:
        report={"status":s.status,"stage":s.stage,"seconds":round(s.play_seconds,2),"health":s.health,
                "hits":s.hits_taken,"stairs":driver.stairs,"error":str(exc),"reason":s.death_reason}
    return {"difficulty":difficulty,"enemies":enemies,**report}


if __name__=="__main__":
    results=[play("easy",False),*[play(d) for d in ("easy","normal","hard")]]
    Path("docs/story-probe.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    for result in results:print(result)
