import json
import math
import os
import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from .ui.menus import MenuViews
from .ui.story import StoryViews
from .ui.inventory import InventoryViews
from .audio import Audio
from .config import AMBER, DIFFICULTIES, HEIGHT, INK, MUTED, PAPER, RED, TEAL, WIDTH
from .render import Renderer
from .simulation import Session
from .story import StorySession
from .saves import SaveStore
from .inventory import ITEMS
from .achievements import AchievementProfile, ACHIEVEMENTS
from .pixels import enable_native_dpi
from .cinematics import CinematicRenderer


DEFAULT_SETTINGS = {"volume": .65, "brightness": .6, "reduced_motion": False,
                    "music_volume": .45, "difficulty": "normal", "wins": 0, "best_seconds": None}


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: str
    style: str = "secondary"
    selected: bool = False


class App(MenuViews, StoryViews, InventoryViews):
    width = WIDTH

    def __init__(self, data_dir=None, audio=True):
        enable_native_dpi()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.fullscreen = os.environ.get("SDL_VIDEODRIVER") != "dummy"
        self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if self.fullscreen else pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Setelah Jam Malam | ITS Horror Game")
        icon = pygame.Surface((64, 64), pygame.SRCALPHA)
        icon.fill(INK)
        pygame.draw.rect(icon, AMBER, (23, 14, 18, 36), 3, border_radius=3)
        pygame.draw.rect(icon, AMBER, (19, 12, 26, 7))
        pygame.draw.rect(icon, AMBER, (19, 45, 26, 7))
        pygame.draw.lines(icon, TEAL, False, [(32, 23), (27, 32), (36, 32), (31, 41)], 3)
        pygame.display.set_icon(icon)
        self.screen = pygame.Surface(self.window.get_size()).convert()
        self.renderer = Renderer()
        self.audio = Audio() if audio else None
        self.data_dir = Path(data_dir or Path(os.getenv("APPDATA", str(Path.home()))) / "ITS-Horror-Game")
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()
        self.save_store=SaveStore(self.data_dir)
        self.save_store.migrate(self.data_dir)
        self.story_checkpoint = self.load_story()
        self.achievements=AchievementProfile(self.data_dir)
        self.achievement_page=0;self.achievement_return="menu"
        self.achievement_queue=[];self.achievement_toast=None;self.toast_time=0.;self.profile_timer=0.
        self.bag_selected="bandage";self.bag_tab="supplies";self.bag_return="playing";self.bag_notice=""
        if self.audio:
            self.audio.set_volume(self.settings["volume"])
        self.mode, self.previous_mode = "menu", "menu"
        self.session = None
        self.buttons = []
        self.focus, self.seed_focused, self.seed_text = 0, False, ""
        self.running = True
        self.debug, self.map_open = False, False
        self.time = 0.
        self.mouse = pygame.Vector2(-100, -100)
        self.mouse_active = False
        self.fps = 60.
        self.ui_notice = ""
        self.save_notice="";self.save_return="menu"
        self.canvas_window_size = None
        self.resize_canvas()
        self.draw()
        self.present()

    def load_settings(self):
        try:
            saved = json.loads((self.data_dir / "settings.json").read_text(encoding="utf-8"))
            if not isinstance(saved, dict):
                return
            for key in ("volume", "brightness", "music_volume"):
                value = saved.get(key)
                if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                    self.settings[key] = max(0, min(1, value))
            if saved.get("difficulty") in DIFFICULTIES:
                self.settings["difficulty"] = saved["difficulty"]
            if isinstance(saved.get("reduced_motion"), bool):
                self.settings["reduced_motion"] = saved["reduced_motion"]
            if isinstance(saved.get("wins"), int) and saved["wins"] >= 0:
                self.settings["wins"] = saved["wins"]
            if isinstance(saved.get("best_seconds"), (int, float)) and not isinstance(saved["best_seconds"], bool) and math.isfinite(saved["best_seconds"]) and saved["best_seconds"] > 0:
                self.settings["best_seconds"] = saved["best_seconds"]
        except (OSError, ValueError, TypeError):
            pass

    def save_settings(self):
        if hasattr(self,"achievements"):self.achievements.save()
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            temporary = self.data_dir / "settings.tmp"
            temporary.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
            temporary.replace(self.data_dir / "settings.json")
        except OSError:
            self.ui_notice = "Pengaturan tidak dapat disimpan; sesi tetap bisa dimainkan."

    def load_story(self):
        data=self.save_store.read("auto")
        return data if data and not data.get("completed") else None

    def save_story(self,slot="auto"):
        if not self.session or self.session.mode_key!="story" or self.session.status=="lost":return False
        try:
            data=self.session.snapshot()
            saved=self.save_store.write(slot,data)
            if slot=="auto":self.story_checkpoint=None if data["completed"] else saved
            self.session.save_request=False
            return True
        except (OSError,ValueError,TypeError):
            self.ui_notice="Penyimpanan gagal. Progres sesi masih aktif."
            return False

    def start_story(self, resume=False,data=None,recover=False):
        self.set_mode("loading");self.draw();self.present()
        data=data if data is not None else self.story_checkpoint if resume else None
        difficulty=data["difficulty"] if data else self.settings["difficulty"]
        try:self.session=StorySession(difficulty,data)
        except (ValueError,TypeError,KeyError,IndexError,OverflowError):
            self.session=StorySession(self.settings["difficulty"])
            self.ui_notice="Checkpoint rusak. Cerita dimulai kembali."
        if recover:
            self.session.health=self.session.stamina=100
            self.session.backpack.add("bottle",max(0,2-self.session.bottles))
            self.session.invulnerable=2
            for monster in self.session.monsters:monster.wait=max(2.2,monster.wait)
        self.renderer.seed=None
        self.renderer.update_camera(self.session,snap=True)
        self.debug=self.map_open=False
        self.set_mode("playing")
        self.save_story()

    def sync_scene(self):
        if self.session and getattr(self.session,"scene_changed",False):
            self.renderer.seed=None;self.renderer.update_camera(self.session,snap=True)
            self.mouse_active=False;self.map_open=False;self.session.scene_changed=False

    def to_canvas(self, pos):
        w, h = self.window.get_size()
        return pygame.Vector2(pos[0] * self.width / w, pos[1] * HEIGHT / h)

    def resize_canvas(self):
        w, h = self.window.get_size()
        self.width = max(640, 2 * round(HEIGHT * w / max(1, h) / 2))
        self.screen = pygame.Surface((w,h)).convert()
        self.renderer.resize(self.width)
        self.renderer.bind_ui(self.screen)
        self.canvas_window_size = (w, h)
        if hasattr(self, "mouse"):
            self.mouse = self.to_canvas(pygame.mouse.get_pos())
        if self.session:
            self.renderer.update_camera(self.session, snap=True)

    def set_mode(self, mode):
        if self.audio and mode!="playing":self.audio.stop_voice()
        self.mode, self.focus = mode, 0
        self.seed_focused = False
        self.mouse_active = False

    def start(self, seed=None):
        self.set_mode("loading")
        self.draw()
        self.present()
        if seed is None:
            seed = int(self.seed_text) if self.seed_text else random.SystemRandom().randrange(1, 1_000_000_000)
        self.session = Session(seed, self.settings["difficulty"])
        self.renderer.seed = None
        self.renderer.camera.update(0, 0)
        self.renderer.update_camera(self.session, snap=True)
        self.debug, self.map_open = False, False
        self.set_mode("playing")
        self.save_settings()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if self.fullscreen else pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.resize_canvas()

    def action(self, action):
        if self.audio:
            self.audio.play("click")
        if action == "start":
            self.start()
        elif action=="backpack":
            if self.session and not getattr(self.session,"modal",False):
                self.bag_return=self.mode;self.bag_notice="";self.bag_tab="supplies"
                owned=[k for k in ITEMS if self.session.backpack.count(k)]
                self.bag_selected=owned[0] if owned else "bottle"
                self.map_open=False;self.set_mode("backpack");self.focus=999
        elif action=="bag_close":self.set_mode(self.bag_return)
        elif action.startswith("bag_select:"):
            self.bag_selected=action.split(":")[1];self.bag_notice=""
        elif action.startswith("bag_tab:"):
            self.bag_tab=action.split(":")[1];self.bag_notice="";self.focus=999
        elif action in ("bag_use","bag_drop"):
            result=self.session.use_item(self.bag_selected) if action=="bag_use" else self.session.drop_item(self.bag_selected)
            self.bag_notice=self.session.message
            self.observe_achievements()
            if result and action=="bag_use":self.set_mode(self.bag_return)
        elif action=="achievements":
            self.achievement_return=self.mode;self.achievement_page=0
            self.achievements.save();self.set_mode("achievements")
        elif action=="achievements_back":self.set_mode(self.achievement_return)
        elif action.startswith("achievement_page:"):
            count=6 if min(1120,self.width-64)>=850 else 3
            self.achievement_page=(self.achievement_page+int(action.split(":")[1]))%math.ceil(len(ACHIEVEMENTS)/count)
        elif action in ("story", "continue_story"):
            self.start_story(action=="continue_story")
        elif action.startswith("digit:"):
            if len(self.session.code)<4:self.session.code+=action.split(":")[1]
        elif action=="code_back":self.session.code=self.session.code[:-1]
        elif action=="code_submit":self.session.submit_code()
        elif action=="close_story":
            self.session.keypad=self.session.journal_open=False
            self.session.puzzle=None
        elif action.startswith("puzzle:"):self.session.puzzle_input(action.split(":")[1])
        elif action=="puzzle_notes":self.session.puzzle=None;self.session.journal_open=True
        elif action in ("save_menu","load_menu"):
            self.save_return="pause" if self.mode=="playing" else self.mode
            self.save_notice="";self.set_mode("save" if action=="save_menu" else "load")
        elif action=="back_saves":self.set_mode(self.save_return)
        elif action.startswith("save_slot:"):
            slot=action.split(":")[1]
            if self.save_story(slot):
                self.save_story();self.save_notice=f"Slot {slot} tersimpan."
        elif action.startswith("load_slot:"):
            data=self.save_store.read(action.split(":")[1])
            if data:
                self.save_story();self.start_story(data=data)
            else:self.save_notice="Save tidak dapat dibaca."
        elif action=="dialogue_next":self.advance_dialogue()
        elif action=="cutscene_skip":
            if self.audio:self.audio.stop_voice()
            self.session.finish_cutscene()
            if self.mode=="pause":self.set_mode("playing")
        elif action=="journal_next":self.session.journal_page+=1
        elif action=="journal_prev":self.session.journal_page-=1
        elif action.startswith("difficulty:"):
            self.settings["difficulty"] = action.split(":")[1]
        elif action == "cycle_difficulty":
            choices = list(DIFFICULTIES)
            self.settings["difficulty"] = choices[(choices.index(self.settings["difficulty"]) + 1) % len(choices)]
        elif action == "seed":
            self.seed_focused = True
        elif action == "random_seed":
            self.seed_text = ""
            self.seed_focused = False
        elif action == "quit":
            self.save_story()
            self.achievements.save()
            self.running = False
        elif action == "help":
            self.previous_mode = self.mode
            self.set_mode("help")
        elif action == "settings":
            self.previous_mode = self.mode
            self.set_mode("settings")
        elif action == "back":
            self.save_settings()
            self.set_mode(self.previous_mode)
        elif action == "resume":
            self.set_mode("playing")
        elif action == "menu":
            self.save_story()
            self.achievements.save()
            self.set_mode("menu")
        elif action == "retry":
            if self.session.mode_key=="story":self.start_story(resume=True,recover=True)
            else:self.start(self.session.seed)
        elif action == "new":
            if self.session.mode_key=="story":self.start_story()
            else:self.start(random.SystemRandom().randrange(1, 1_000_000_000))
        elif action.startswith(("volume:", "brightness:", "music_volume:")):
            name, delta = action.split(":")
            self.settings[name] = round(max(0, min(1, self.settings[name] + float(delta))), 2)
            if self.audio:
                self.audio.set_volume(self.settings["volume"])
            self.save_settings()
        elif action == "motion":
            self.settings["reduced_motion"] = not self.settings["reduced_motion"]
            self.save_settings()
        elif action == "fullscreen":
            self.toggle_fullscreen()

    def events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.save_story()
                self.achievements.save()
                self.running = False
            elif event.type in (pygame.WINDOWSIZECHANGED, pygame.VIDEORESIZE):
                self.resize_canvas()
            elif event.type == pygame.WINDOWFOCUSLOST and self.mode == "playing":
                self.set_mode("pause")
            elif event.type == pygame.MOUSEMOTION:
                self.mouse = self.to_canvas(event.pos)
                self.mouse_active = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.mouse = self.to_canvas(event.pos)
                if self.mode != "playing" or getattr(self.session,"modal",False):
                    for i, button in enumerate(self.buttons):
                        if button.rect.collidepoint(self.mouse):
                            self.focus = i
                            self.action(button.action)
                            break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue
                if event.key==pygame.K_F5 and self.session and self.session.mode_key=="story" and self.mode in ("playing","pause"):
                    self.action("save_menu");continue
                if event.key==pygame.K_F9 and self.mode in ("playing","pause","menu"):
                    self.action("load_menu");continue
                if self.mode=="backpack":
                    self.bag_key(event);continue
                if self.mode=="achievements":
                    if event.key==pygame.K_ESCAPE:self.action("achievements_back");continue
                    if event.key in (pygame.K_LEFT,pygame.K_RIGHT):
                        self.action("achievement_page:"+("-1" if event.key==pygame.K_LEFT else "1"));continue
                if self.mode == "playing":
                    if self.session.mode_key=="story" and self.story_key(event):continue
                    if event.key == pygame.K_ESCAPE:
                        self.set_mode("pause")
                    elif event.key == pygame.K_e:
                        self.session.interact()
                    elif event.key == pygame.K_q:
                        aim = self.renderer.screen_to_world(self.mouse) if self.mouse_active else self.session.player + self.session.facing * 280
                        self.session.throw(aim)
                    elif event.key == pygame.K_f:
                        self.session.flashlight = not self.session.flashlight
                    elif event.key == pygame.K_m:
                        self.map_open = not self.map_open
                    elif event.key == pygame.K_F3:
                        self.debug = not self.debug
                    elif event.key in (pygame.K_b,pygame.K_TAB):self.action("backpack")
                    elif event.key in (pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4):
                        self.session.use_item({pygame.K_1:"medkit",pygame.K_2:"energy",pygame.K_3:"alarm",pygame.K_4:"glow"}[event.key])
                    continue
                if event.key == pygame.K_ESCAPE:
                    if self.mode in ("save","load"):
                        self.action("back_saves")
                    elif self.mode == "pause":
                        self.set_mode("playing")
                    elif self.mode in ("help", "settings"):
                        self.action("back")
                    elif self.seed_focused:
                        self.seed_focused = False
                    continue
                if self.seed_focused and self.mode in ("menu", "settings"):
                    if event.key == pygame.K_BACKSPACE:
                        self.seed_text = self.seed_text[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                        self.seed_focused = False
                    elif getattr(event, "unicode", "").isascii() and getattr(event, "unicode", "").isdigit() and len(self.seed_text) < 9:
                        self.seed_text += event.unicode
                    continue
                if event.key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_UP, pygame.K_LEFT, pygame.K_RIGHT):
                    delta = -1 if event.key in (pygame.K_UP, pygame.K_LEFT) or (event.key == pygame.K_TAB and getattr(event, "mod", 0) & pygame.KMOD_SHIFT) else 1
                    self.focus = (self.focus + delta) % max(1, len(self.buttons))
                    self.mouse_active = False
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.buttons:
                    self.action(self.buttons[self.focus % len(self.buttons)].action)

    def update(self, dt, keys=None):
        self.time += dt
        self.toast_time=max(0,self.toast_time-dt)
        if self.toast_time<=0:
            self.achievement_toast=None
            if self.achievement_queue:
                self.achievement_toast=self.achievement_queue.pop(0);self.toast_time=4.
                if self.audio:self.audio.play("award",gain=.3)
        self.profile_timer+=dt
        if self.profile_timer>10:self.achievements.save();self.profile_timer=0
        if self.audio:self.audio.update_context(dt,self.session,self.mode,self.settings["music_volume"])
        if self.mode=="backpack":
            self.session.item_cooldown=max(0,self.session.item_cooldown-dt)
            self.session.throw_cooldown=max(0,self.session.throw_cooldown-dt)
        if self.mode != "playing":
            return
        self.sync_scene()
        keys = keys if keys is not None else pygame.key.get_pressed()
        def pressed(key):
            return bool(keys[key]) if not isinstance(keys, dict) else bool(keys.get(key, False))
        movement = (int(pressed(pygame.K_d) or pressed(pygame.K_RIGHT)) - int(pressed(pygame.K_a) or pressed(pygame.K_LEFT)),
                    int(pressed(pygame.K_s) or pressed(pygame.K_DOWN)) - int(pressed(pygame.K_w) or pressed(pygame.K_UP)))
        direction = pygame.Vector2(movement)
        keyboard_facing = direction.normalize() if direction.length_squared() else self.session.facing
        aim = self.renderer.screen_to_world(self.mouse) if self.mouse_active else self.session.player + keyboard_facing * 200
        self.session.update(dt, movement, pressed(pygame.K_LSHIFT) or pressed(pygame.K_RSHIFT),
                            pressed(pygame.K_LCTRL) or pressed(pygame.K_RCTRL), pressed(pygame.K_e), aim)
        self.sync_scene()
        self.renderer.update_camera(self.session, dt)
        self.observe_achievements()
        if getattr(self.session,"save_request",False):self.save_story()
        if self.audio:
            self.audio.drain(self.session)
        else:
            self.session.audio_events.clear()
        if self.session.status != "playing":
            if self.session.status == "won":
                if self.session.mode_key=="story":self.save_story()
                else:
                    self.settings["wins"] += 1
                    best = self.settings["best_seconds"]
                    if best is None or self.session.elapsed < best:
                        self.settings["best_seconds"] = self.session.elapsed
                self.save_settings()
            self.set_mode("result")

    def observe_achievements(self):
        if not self.session:return
        keys=self.achievements.observe(self.session)
        if keys:
            self.achievement_queue.extend(keys)
            if not self.achievements.save():self.ui_notice="Pencapaian belum dapat disimpan."

    def bag_key(self,event):
        key=event.key
        if key in (pygame.K_b,pygame.K_ESCAPE):self.action("bag_close");return
        if key==pygame.K_TAB:
            self.action("bag_tab:"+("keys" if self.bag_tab=="supplies" else "supplies"));return
        if self.bag_tab!="supplies":return
        catalog=list(ITEMS);index=catalog.index(self.bag_selected)
        columns=4 if min(1100,self.width-64)>=900 else 3
        if key in (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_DOWN):
            delta={pygame.K_LEFT:-1,pygame.K_RIGHT:1,pygame.K_UP:-columns,pygame.K_DOWN:columns}[key]
            self.bag_selected=catalog[(index+delta)%len(catalog)];self.bag_notice="";self.mouse_active=False;self.focus=999
        elif key in (pygame.K_RETURN,pygame.K_e):self.action("bag_use")
        elif key==pygame.K_x:self.action("bag_drop")

    def story_key(self,event):
        session=self.session
        key=event.key
        if session.cutscene:
            if key in (pygame.K_RETURN,pygame.K_KP_ENTER):
                if self.audio:self.audio.stop_voice()
                session.finish_cutscene()
            elif key==pygame.K_ESCAPE:self.set_mode("pause")
            return True
        if session.dialogue:
            if key in (pygame.K_e,pygame.K_RETURN,pygame.K_SPACE):self.advance_dialogue()
            elif key==pygame.K_ESCAPE:self.set_mode("pause")
            return True
        if session.keypad:
            digit=getattr(event,"unicode","")
            if digit.isascii() and digit.isdigit() and len(session.code)<4:session.code+=digit
            elif key==pygame.K_BACKSPACE:session.code=session.code[:-1]
            elif key in (pygame.K_RETURN,pygame.K_KP_ENTER):session.submit_code()
            elif key==pygame.K_ESCAPE:session.keypad=False
            return True
        if session.puzzle:
            if key==pygame.K_ESCAPE:session.puzzle=None
            elif key==pygame.K_j:session.puzzle=None;session.journal_open=True
            elif key==pygame.K_LEFT:session.puzzle_input("left")
            elif key==pygame.K_RIGHT:session.puzzle_input("right")
            elif key in (pygame.K_RETURN,pygame.K_KP_ENTER):session.puzzle_input("submit")
            elif getattr(event,"unicode","") in ("1","2","3"):session.puzzle_input(str(int(event.unicode)-1))
            return True
        if session.journal_open:
            if key in (pygame.K_j,pygame.K_ESCAPE):session.journal_open=False
            elif key==pygame.K_RIGHT:session.journal_page+=1
            elif key==pygame.K_LEFT:session.journal_page-=1
            return True
        if key==pygame.K_j:
            session.journal_open=True;self.map_open=False
            return True
        return False

    def advance_dialogue(self):
        if self.audio:self.audio.stop_voice()
        if self.session.typing:self.session.reveal_dialogue()
        else:self.session.next_dialogue()

    def button(self, rect, label, action, style="secondary", selected=False):
        r = self.renderer
        index = len(self.buttons)
        rect = pygame.Rect(rect)
        self.buttons.append(Button(rect, label, action, style, selected))
        hovered = rect.collidepoint(self.mouse) if self.mouse_active else index == self.focus
        accent = PAPER if style != "danger" else RED
        primary = style == "primary"
        fill = accent if primary else (25, 34, 38) if hovered or selected else (13, 22, 26)
        border = (117, 133, 138) if hovered or selected else (35, 45, 49)
        if style != "text" or hovered:
            r.panel(self.screen, rect, fill, border, radius=2)
        if action == "random_seed":
            icon=pygame.Rect(rect.centerx-7,rect.centery-7,14,14)
            self.renderer.draw.arc(self.screen,PAPER,icon,.2,5.4,1)
            self.renderer.draw.polygon(self.screen,PAPER,[(rect.centerx+6,rect.centery-5),(rect.centerx+10,rect.centery-3),(rect.centerx+5,rect.centery)])
        else:
            r.centered_text(self.screen,label,rect,18,INK if primary else PAPER,primary)
        if hovered:
            self.renderer.draw.rect(self.screen, PAPER if primary else accent, rect.inflate(6, 6), 1, border_radius=5)


    def draw(self):
        self.sync_scene()
        self.renderer.bind_ui(self.screen)
        self.buttons = []
        if self.mode == "menu":
            self.draw_menu()
        elif self.mode == "loading":
            self.renderer.backdrop(self.screen)
            self.renderer.text(self.screen, "Memuat", (self.width / 2, 380), 20, MUTED, align="center")
        elif self.mode == "playing":
            if getattr(self.session,"cutscene",None):
                CinematicRenderer(self.renderer).draw(self.screen,self.session,self.settings)
            else:self.renderer.draw_session(self.screen, self.session, self.settings, self.debug, self.map_open, self.fps)
            if getattr(self.session,"modal",False) and not getattr(self.session,"cutscene",None):self.draw_story_modal()
            elif self.mouse_active and not getattr(self.session,"cutscene",None):
                x, y = self.mouse
                self.renderer.draw.circle(self.screen, (160, 184, 171), (int(x), int(y)), 5, 1)
                self.renderer.draw.line(self.screen, (160, 184, 171), (x - 9, y), (x - 5, y))
                self.renderer.draw.line(self.screen, (160, 184, 171), (x + 5, y), (x + 9, y))
        elif self.mode == "pause":
            self.draw_pause()
        elif self.mode == "help":
            self.draw_help()
        elif self.mode == "settings":
            self.draw_settings()
        elif self.mode == "result":
            self.draw_result()
        elif self.mode in ("save","load"):
            self.draw_save_browser()
        elif self.mode=="backpack":self.draw_backpack()
        elif self.mode=="achievements":self.draw_achievements()
        self.draw_achievement_toast()
        if self.ui_notice:
            self.renderer.text(self.screen, self.ui_notice, (self.width / 2, 75), 15, AMBER, align="center")
        pygame.mouse.set_visible(self.mode != "playing" or getattr(self.session,"modal",False))

    def present(self):
        w, h = self.window.get_size()
        if self.canvas_window_size != (w, h):
            self.resize_canvas()
            self.draw()
        frame = self.screen if (w, h) == self.screen.get_size() else pygame.transform.scale(self.screen, (w, h))
        self.window.blit(frame, (0, 0))
        pygame.display.flip()

    def run(self, max_frames=None):
        clock, frames = pygame.time.Clock(), 0
        while self.running and (max_frames is None or frames < max_frames):
            dt = min(clock.tick(60) / 1000, .05)
            self.fps = clock.get_fps()
            self.events(pygame.event.get())
            self.update(dt)
            self.draw()
            self.present()
            frames += 1
        self.save_settings()
        self.save_story()
        self.achievements.save()
        pygame.quit()
