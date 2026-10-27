"""Bounded check on the real display, including fullscreen dimensions and audio."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from horror.app import App
from horror.cinematics import CUTSCENES

with tempfile.TemporaryDirectory() as folder:
    app=App(folder)
    assert app.fullscreen
    app.start_story()
    app.session.cutscene["time"]=6.
    clock=pygame.time.Clock()
    for _ in range(90):
        pygame.event.pump();app.update(1/60,{});app.draw();app.present();clock.tick(60)
    assert app.audio.counters.get("voice_nara",0)>0
    pygame.event.clear()
    app.session.cutscene["time"]=43.5
    app.draw()
    app.present()
    out=Path('docs/screenshots')
    out.mkdir(parents=True,exist_ok=True)
    pygame.image.save(app.window,str(out/'fullscreen-story-native.png'))
    report={"display":app.window.get_size(),"canvas":app.screen.get_size(),"world_view":list(app.renderer.view_size),
            "fullscreen":app.fullscreen,"audio":app.audio.available,"mixer":pygame.mixer.get_init(),"mode":app.session.mode_key,
            "music":[sound.get_length() for sound in app.audio.music]}
    assert abs(report['display'][0]/report['display'][1]-report['canvas'][0]/report['canvas'][1])<.002
    app.run(450)
    assert app.session.cutscene is None and "intro" in app.session.seen_scenes
    report["intro_handoff"]=True;report["frames"]=450;report["intro_from_second"]=43.5
    report["voice_nara"]=app.audio.counters.get("voice_nara",0);report["voice_arga"]=app.audio.counters.get("voice_arga",0)
    assert report["voice_nara"]>0 and report["voice_arga"]>0
    Path('docs/native-window.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(report)
