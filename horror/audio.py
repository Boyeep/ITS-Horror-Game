"""Bundled foley, material-specific footsteps, spatial mixing and quiet ambience."""
import array
import math
import random

import pygame
from .resources import asset_path
from .tension import CueGate, approach, tension_level


class Audio:
    release_cues = True  # set False if a scripted scene supplies its own quiet after a chase
    RECORDED_CUES = ("radio", "distant", "book", "tape", "valve", "tune", "drink", "deploy")
    ATMOSPHERE_BLOCKERS = {"stinger", "alert", "growl", "caught", "hurt", "power", "win", "radio", "phone_vibrate",
                           "monster_guard", "monster_listener", "monster_ambusher"}

    def __init__(self):
        self.available = pygame.mixer.get_init() is not None
        self.volume = .65
        self.music_volume = .45
        self.chase_mix = 0.
        self.night_mix=self.outdoor_mix=0.
        self.rng=random.Random()
        self.last_index={}
        self.sounds = {}
        self.banks = {}
        self.counters = {}
        self.ambient = None
        self.tension, self.heart_fast, self.breath_wait = 0., False, 4.
        self.hush, self.release, self.chase_time, self.relief_due, self.was_indoor, self.watched = 1., 0., 0., 0., None, None
        self.gate = CueGate()
        self.atmosphere_gain = 0.
        if not self.available:
            return
        pygame.mixer.set_num_channels(32)
        pygame.mixer.set_reserved(8)
        self.voice_channel=pygame.mixer.Channel(5)
        self.heart_channel=pygame.mixer.Channel(6)
        self.atmosphere_channel=pygame.mixer.Channel(7)
        self.ambient = pygame.mixer.Channel(0)
        definitions = {
            "power": (1.1, 120, .45, .1),
            "win": (1.5, 330, .3, .02),
            "click": (.06, 650, .25, .01),
            "alarm": (.22, 880, .16, .01),
            "award": (.6, 660, .12, .0),
            "phone_vibrate": (.55, 76, .25, .08),
        }
        for name, values in definitions.items():
            self.sounds[name] = self.synthesize(name, *values)
        self.sounds["heart_slow"] = self.heartbeat(66)
        self.sounds["heart_fast"] = self.heartbeat(112)
        self.banks["breath_heavy"] = [self.breath(length, seed) for length, seed in ((1.5, 1), (1.75, 2), (1.3, 3))]
        self.heart_channel.set_volume(0)
        self.heart_channel.play(self.sounds["heart_slow"], loops=-1)
        for speaker,frequency in (("arga",177),("nara",263)):
            self.banks["voice_"+speaker]=[self.voice_tone(frequency*factor) for factor in (.96,1.,1.04)]
        folder = asset_path("audio")
        sources = {"door_open": ["doorOpen_1.ogg", "doorOpen_2.ogg"],
                   "door_close": ["doorClose_1.ogg", "doorClose_2.ogg"],
                   "glass": ["impactGlass_medium_000.ogg"], "step_glass": ["impactGlass_light_000.ogg"],
                   "pickup": ["cloth1.ogg"], "heal": ["cloth3.ogg"],
                   "hurt": ["impactPunch_medium_000.ogg"], "panel": ["metalClick.ogg"],
                   "whisper": ["cloth3.ogg"], "breath": ["cloth3.ogg"],
                   "heavy": ["footstep_concrete_000.ogg", "footstep_concrete_003.ogg"]}
        sources.update({"step_" + surface: [f"footstep_{surface}_{i:03}.ogg" for i in range(5)]
                        for surface in ("concrete", "wood", "grass")})
        for key, files in sources.items():
            self.banks[key] = [pygame.mixer.Sound(str(folder / file)) for file in files]
        for key, factor in (("whisper", .65), ("heavy", .82), ("breath", .7)):
            self.banks[key] = [self.pitched(sound, factor) for sound in self.banks[key]]
        story = folder.parent / "story_audio"
        self.music = [pygame.mixer.Sound(str(story / name)) for name in ("exploration.ogg", "chase.wav")]
        self.music_channels = [pygame.mixer.Channel(0), pygame.mixer.Channel(1)]
        for channel, sound in zip(self.music_channels, self.music):
            channel.set_volume(0)
            channel.play(sound, loops=-1)
        for key in ("guard", "listener", "ambusher"):
            files=[story/("monster_"+key+".ogg"),*sorted(story.glob("monster_"+key+"_*.ogg"))]
            self.banks["monster_" + key] = [pygame.mixer.Sound(str(path)) for path in files]
        self.night_music=pygame.mixer.Sound(str(story/"nightshift.mp3"))
        self.night_channel=pygame.mixer.Channel(2);self.night_channel.set_volume(0);self.night_channel.play(self.night_music,loops=-1)
        self.outdoor_channel=pygame.mixer.Channel(3);self.outdoor_channel.set_volume(0)
        self.outdoor_channel.play(pygame.mixer.Sound(str(story/"crickets.mp3")),loops=-1)
        self.room_channel=pygame.mixer.Channel(4);self.room_channel.set_volume(0)
        self.room_channel.play(self.synthesize("ambient",4,46,.06,0),loops=-1)
        self.banks["step_asphalt"]=[self.pitched(s,1.04) for s in self.banks["step_concrete"]]
        self.banks["step_metal"]=[self.pitched(s,.94) for s in self.banks["step_concrete"]]
        self.banks["stairs"]=self.banks["step_concrete"]
        self.banks["book"]=self.banks["pickup"]+self.banks["heal"]
        self.banks["valve"]=self.banks["panel"]+self.banks["door_open"]
        self.banks["radio"]=[self.pitched(s,1.55) for s in self.banks["whisper"]]
        self.banks["tune"]=self.banks["panel"]
        self.banks["distant"]=self.banks["door_close"]
        self.banks["drink"]=self.banks["pickup"]
        self.banks["tape"]=self.banks["heal"]
        self.banks["deploy"]=self.banks["panel"]
        for cue in self.RECORDED_CUES:  # real recordings replace the borrowed foley above once they are bundled
            files=self.variants(story,cue)
            if files:self.banks[cue]=[pygame.mixer.Sound(str(path)) for path in files]
        self.banks["alert"] = self.banks["monster_guard"]
        self.banks["growl"] = self.banks["monster_ambusher"]
        self.banks["caught"] = self.banks["monster_listener"]
        stinger = pygame.mixer.Sound(str(story / "stinger.wav"))
        self.sounds["stinger"] = self.trim(stinger, 1.15)

    @staticmethod
    def heartbeat(bpm):
        """Soft synthesized lub-dub; one beat per loop, silent at the loop point."""
        rate, _, channels = pygame.mixer.get_init()
        total = round(rate * 60 / bpm)
        samples = array.array("h", [0] * (total * channels))
        for start, frequency, level in ((0., 52., 1.), (.19, 44., .7)):
            first = round(rate * start)
            for i in range(min(total - first, round(rate * .22))):
                t = i / rate
                value = math.sin(math.tau * frequency * t) * math.exp(-t * 19) * min(1., t / .006) * level
                for channel in range(channels):
                    index = (first + i) * channels + channel
                    samples[index] = max(-32767, min(32767, samples[index] + int(value * 15000)))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    @staticmethod
    def breath(duration, seed):
        """Soft low-passed noise that swells and fades, like a held breath let go."""
        rate, _, channels = pygame.mixer.get_init()
        rng, low, samples = random.Random(seed), 0., array.array("h")
        total = round(rate * duration)
        for i in range(total):
            progress = i / total
            low += (rng.uniform(-1, 1) - low) * .12
            sample = int(low * math.sin(math.pi * progress) ** 2 * (1 - .35 * progress) * 18000)
            samples.extend([sample] * channels)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    @staticmethod
    def variants(folder, cue):
        """Bundled recordings named <cue>_<n>.ogg/.wav/.mp3 (see tools/add_story_audio.py)."""
        return sorted((p for p in folder.glob(cue + "_*") if p.suffix.lower() in (".ogg", ".wav", ".mp3")), key=lambda p: p.name)

    @staticmethod
    def voice_tone(frequency):
        """An original, gently band-limited chiptune syllable; no sampled game audio."""
        rate,_,channels=pygame.mixer.get_init();samples=array.array("h");length=round(rate*.044)
        for i in range(length):
            t=i/rate;attack=min(1,t/.003);release=min(1,(length-i)/(rate*.011))
            phase=math.tau*frequency*t
            tone=math.sin(phase)+.32*math.sin(phase*3)+.14*math.sin(phase*5)
            sample=round(tone*attack*release*2700)
            samples.extend([sample]*channels)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def stop_voice(self):
        if self.available:self.voice_channel.stop()

    @staticmethod
    def trim(sound, seconds):
        rate, _, channels = pygame.mixer.get_init()
        samples = array.array("h", sound.get_raw())
        count = min(len(samples) // channels, int(seconds * rate))
        result = array.array("h")
        for i in range(count):
            envelope = min(1., i / (rate * .006), (count - i) / (rate * .09))
            for ch in range(channels):
                result.append(int(samples[i * channels + ch] * envelope))
        return pygame.mixer.Sound(buffer=result.tobytes())

    def update_context(self, dt, session=None, mode="menu", music_volume=.45):
        if not self.available:
            return
        self.music_volume = music_volume
        playing = mode == "playing" and session is not None
        target = float(playing and session.chase_active and not getattr(session, "modal", False))
        self.chase_mix += (target - self.chase_mix) * min(1., dt * (3 if target else .65))
        duck = .55 if playing and getattr(session,"cutscene",None) else .32 if not playing or getattr(session, "modal", False) else 1.
        indoor=False;night=False
        if playing:
            layout=session.layout
            outdoor=layout.is_outdoor(session.player) if hasattr(layout,"is_outdoor") else layout.room_at(session.player) in layout.outdoors
            indoor=not outdoor
            night=getattr(session,"act",0)>0 and (indoor or getattr(session,"act",0)==2)
        self.night_mix+=(float(night)-self.night_mix)*min(1.,dt*.9)
        duck *= self.atmosphere(dt, session if playing else None, duck, indoor)
        self.outdoor_mix+=(float(playing and not indoor)-self.outdoor_mix)*min(1.,dt*2)
        self.music_channels[0].set_volume(music_volume * .65 * duck * (1 - self.chase_mix)*(1-self.night_mix))
        self.music_channels[1].set_volume(music_volume * .25 * duck * self.chase_mix)
        self.night_channel.set_volume(music_volume*.2*duck*(1-self.chase_mix)*self.night_mix)
        self.outdoor_channel.set_volume(self.volume*.16*duck*self.outdoor_mix*(.3 if self.chase_mix>.5 else 1))
        self.room_channel.set_volume(self.volume*.2*duck*(1-self.outdoor_mix) if playing else 0)

    def atmosphere(self, dt, session, duck, indoor=False):
        """Heartbeat, breathing and the quiet after a scare; returns a factor (<1) that hushes ambience."""
        if session is not self.watched:
            self.watched = session
            self.chase_time, self.release, self.relief_due, self.was_indoor = 0., 0., 0., None
            self.tension, self.hush, self.breath_wait = 0., 1., 4.
            self.atmosphere_channel.stop()
        self.tension = approach(self.tension, tension_level(session) if session else 0., dt)
        self.gate.tick(dt)
        quiet = (session is None or getattr(session, "modal", False) or getattr(session, "cutscene", None)
                 or getattr(session, "status", "playing") != "playing" or self.volume <= 0)
        if quiet:
            self.atmosphere_channel.stop()
        else:
            self.atmosphere_channel.set_volume(self.volume * self.atmosphere_gain * duck)
        fast = self.tension > (.55 if self.heart_fast else .72)
        if fast != self.heart_fast:
            self.heart_fast = fast
            self.heart_channel.play(self.sounds["heart_fast" if fast else "heart_slow"], loops=-1)
        pulse = min(1., max(0., (self.tension - .28) / .5))
        self.heart_channel.set_volume(0 if quiet else self.volume * pulse * .6 * duck)
        free = not quiet and not self.voice_channel.get_busy() and not self.atmosphere_channel.get_busy()
        if not quiet and self.release_cues:
            self.quiet_moments(dt, session, indoor, free)
        self.release = max(0., self.release - dt)
        self.hush = approach(self.hush, .45 if self.release > 0 else 1., dt, rise=.8, fall=4.)
        if not free or self.tension <= .5:
            self.breath_wait = max(self.breath_wait, 2.5)
            return self.hush
        self.breath_wait -= dt
        if self.breath_wait <= 0:
            if self.gate.allow("breath", 4.):
                self.play_atmosphere("breath_heavy", gain=.3 + .5 * self.tension)
            self.breath_wait = 7 - 3.5 * self.tension + self.rng.random() * 2
        return self.hush

    def quiet_moments(self, dt, session, indoor, ready=True):
        """Cues read from what the player just did: a chase that ended, or stepping indoors."""
        if getattr(session, "chase_active", False):
            self.chase_time += dt
            self.relief_due = 0.
        else:
            if self.chase_time >= 3.:
                self.relief_due = 3.  # wait up to 3s for a free moment instead of stacking on another cue
            self.chase_time = 0.
            if self.relief_due > 0:
                self.relief_due -= dt
                if ready and getattr(session, "encounter_timer", 0.) <= 0 and getattr(session, "health", 1) > 0 and self.gate.allow("relief", 20.):
                    self.relief_due, self.release = 0., 3.2
                    self.breath_wait = max(self.breath_wait, 5.)
                    self.play_atmosphere("breath_heavy", gain=.6)
        if ready and self.was_indoor is False and indoor and self.tension < .3 and self.gate.allow("enter", 45.):
            self.release = max(self.release, 1.6)
            self.play_atmosphere("distant", gain=.3)
        self.was_indoor = indoor

    def play_atmosphere(self, name, gain):
        """A reserved channel keeps optional atmosphere separate from gameplay/voice cues."""
        self.atmosphere_gain = gain
        self.play(name, gain=gain, channel=self.atmosphere_channel)

    @staticmethod
    def pitched(sound, factor):
        source = array.array("h", sound.get_raw())
        channels = pygame.mixer.get_init()[2]
        frames = len(source) // channels
        output = array.array("h")
        for i in range(int(frames / factor)):
            cursor = min(frames - 1.001, i * factor)
            left, fraction = int(cursor), cursor % 1
            for channel in range(channels):
                a = source[left * channels + channel]
                b = source[min(frames - 1, left + 1) * channels + channel]
                output.append(int(a + (b - a) * fraction))
        return pygame.mixer.Sound(buffer=output.tobytes())

    @staticmethod
    def synthesize(name, duration, frequency, amplitude, noise):
        rate = pygame.mixer.get_init()[0] if pygame.mixer.get_init() else 44100
        rng = random.Random(name)
        samples = array.array("h")
        total = int(rate * duration)
        for i in range(total):
            t = i / rate
            progress = i / total
            envelope = 1. if name == "ambient" else min(1, t / .015) * (1 - progress) ** 1.5
            tone = math.sin(math.tau * frequency * t)
            tone += .35 * math.sin(math.tau * frequency * 1.51 * t)
            if name in ("win", "pickup"):
                tone += .4 * math.sin(math.tau * frequency * 1.25 * t)
            value = ((1 - noise) * tone * .65 + noise * rng.uniform(-1, 1)) * envelope * amplitude
            sample = int(max(-1, min(1, value)) * 23000)
            samples.extend((sample, sample))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def set_volume(self, volume):
        self.volume = volume
        if self.available and volume<=0:
            self.stop_voice()
            self.heart_channel.set_volume(0)
            self.atmosphere_channel.stop()

    def play(self, name, position=None, listener=None, facing=None, gain=1, *, channel=None):
        if not self.available or (name not in self.sounds and name not in self.banks):
            return
        channel = channel if channel is not None else self.voice_channel if name.startswith("voice_") else pygame.mixer.find_channel()
        if channel is None:
            return
        volume, pan = self.volume * gain, 0.
        if position is not None and listener is not None:
            delta = pygame.Vector2(position) - listener
            distance = delta.length()
            if distance > 850:
                return
            volume *= max(.02, (1 - distance / 850) ** 1.7)
            pan = max(-.85, min(.85, delta.x / 380))
        if name in self.banks:
            count=len(self.banks[name]);choices=[i for i in range(count) if count==1 or i!=self.last_index.get(name)]
            index=self.rng.choice(choices);self.last_index[name]=index
            sound=self.banks[name][index];self.counters[name]=self.counters.get(name,0)+1
        else:
            sound = self.sounds[name]
        if name in self.ATMOSPHERE_BLOCKERS:
            self.atmosphere_channel.stop()
            self.gate.defer(max(self.gate.gap, sound.get_length()))
        channel.play(sound)
        if name.startswith("voice_"):channel.set_volume(volume)
        else:channel.set_volume(volume * (1 - max(0, pan)), volume * (1 + min(0, pan)))

    def drain(self, session):
        for name, position, gain in session.audio_events:
            if position.distance_to(session.player) > 100 and not session.layout.line_clear(position, session.player):
                gain *= .38
            self.play(name, position, session.player, session.facing, gain)
        session.audio_events.clear()
