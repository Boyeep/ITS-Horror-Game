"""Export a short audition of the actual game sound banks, without narration."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import json
import sys
import wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from horror.audio import Audio

pygame.mixer.pre_init(44100,-16,2)
pygame.init()
audio=Audio()
rate=pygame.mixer.get_init()[0]
data=bytearray();labels=[]
for name,count in (('door_open',1),('door_close',1),('step_concrete',5),('step_wood',5),('step_grass',5)):
    labels.append({'bank':name,'seconds':round(len(data)/(rate*4),3)})
    for index in range(count):
        sound=audio.banks[name][index%len(audio.banks[name])]
        data.extend(sound.get_raw())
        data.extend(b'\0'*int(rate*4*.16))
    data.extend(b'\0'*int(rate*4*.45))
with wave.open('docs/audio-preview.wav','wb') as output:
    output.setnchannels(2);output.setsampwidth(2);output.setframerate(rate);output.writeframes(data)
Path('docs/audio-preview.json').write_text(json.dumps(labels,indent=2),encoding='utf-8')
pygame.quit()
print('Audio preview exported:',len(data)//(rate*4),'seconds')
