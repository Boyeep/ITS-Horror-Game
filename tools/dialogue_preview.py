"""Audition the original character syllables with the same cadence as live text."""
import os
os.environ["SDL_VIDEODRIVER"]="dummy";os.environ["SDL_AUDIODRIVER"]="dummy"
import array
import json
import sys
import wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from horror.audio import Audio
from horror.speech import duration,pulses
from horror.cinematics import INTRO_LINES

pygame.mixer.pre_init(44100,-16,2);pygame.init();audio=Audio()
rate,_,channels=pygame.mixer.get_init();output=array.array("h");labels=[]
for speaker,body in [(speaker,body) for _,_,speaker,body in INTRO_LINES if speaker][:2]:
    begin=len(output)/(rate*channels);length=duration(body)+.65
    samples=array.array("h",[0])*round(rate*channels*length)
    for i,moment in enumerate(pulses(body,0,length)):
        clip=array.array("h",audio.banks["voice_"+speaker][i%3].get_raw());start=round(moment*rate)*channels
        for j,sample in enumerate(clip):
            if start+j<len(samples):samples[start+j]=round(sample*.65*.7)
    labels.append({"speaker":speaker,"text":body,"start":round(begin,3),"seconds":round(length,3)})
    output.extend(samples)
with wave.open("docs/dialogue-preview.wav","wb") as file:
    file.setnchannels(channels);file.setsampwidth(2);file.setframerate(rate);file.writeframes(output.tobytes())
Path("docs/dialogue-preview.json").write_text(json.dumps({"original_synthesized_audio":True,"characters":labels},indent=2),encoding="utf-8")
pygame.quit();print({"preview":"docs/dialogue-preview.wav","seconds":round(len(output)/(rate*channels),2)})
