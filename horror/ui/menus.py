"""Main menu, pause, help, settings and results presentation."""
import pygame
from ..config import DIFFICULTIES, HEIGHT, MUTED, PAPER


class MenuViews:
    def draw_menu(self):
        r, s = self.renderer, self.screen
        r.backdrop(s,self.time,self.settings["reduced_motion"])
        sx,sy=r.draw.scale(s)
        r.ui_image(s,r.art.crest((round(94*sx),round(94*sy))),(84,139))
        r.text(s, "ITS", (196, 130), 112, PAPER, True)
        r.text(s, "Setelah jam malam", (84, 262), 27, PAPER)
        y=360
        if self.story_checkpoint:
            self.button((84,y,220,46),"Lanjut cerita","continue_story","primary");y+=56
        self.button((84,y,220,48),"Cerita baru" if self.story_checkpoint else "Story Mode","story","text" if self.story_checkpoint else "primary")
        y+=56
        self.button((84,y,220,42),"Muat permainan","load_menu","text")
        y+=56
        self.button((84,y,220,42),"Escape","start","text")
        self.button((84,328,220,28),DIFFICULTIES[self.settings["difficulty"]].name+"  >","cycle_difficulty","text")
        self.button((84,y+62,220,42),"Cara main","help","text")
        self.button((84,y+112,220,42),"Pengaturan","settings","text")
        self.button((84,y+162,220,42),"Keluar","quit","text")
        self.button((self.width-246,HEIGHT-100,210,42),"Pencapaian","achievements","text")

    def modal_base(self, title, subtitle=""):
        r, s = self.renderer, self.screen
        if self.session and self.previous_mode == "pause":
            r.draw_session(s, self.session, self.settings)
            shade = pygame.Surface(s.get_size(), pygame.SRCALPHA)
            shade.fill((4, 9, 12, 225))
            s.blit(shade, (0, 0))
        else:
            r.backdrop(s)
        width = min(920, self.width - 80)
        left = (self.width - width) / 2
        r.panel(s, (left, 125, width, 550), (11, 19, 23), (35, 45, 49))
        r.text(s, title, (left + 40, 161), 34, PAPER)
        return left, width

    def draw_help(self):
        left, width = self.modal_base("Cara main")
        r, s = self.renderer, self.screen
        r.text(s, "Story: ikuti tujuan dan penanda emas. Escape: 2 sekring / panel / gerbang.", (left + 40, 225), 18, PAPER)
        controls = [("WASD", "Gerak"), ("Shift / Ctrl", "Lari / pelan"), ("E / tahan E", "Interaksi / panel"),
                    ("Mouse / Q", "Arah / lempar botol"), ("F / M", "Senter / denah"), ("Esc / F11", "Jeda / layar penuh")]
        column = (width - 80) / 3
        for i, (key, label) in enumerate(controls):
            x, y = left + 40 + i % 3 * column, 288 + i // 3 * 72
            r.text(s, key, (x, y), 16, PAPER)
            r.text(s, label, (x, y + 24), 15, MUTED)
        self.renderer.draw.line(s, (37, 48, 51), (left + 40, 452), (left + width - 40, 452))
        for i, (name, tip) in enumerate((("Penjaga", "Putus pandangan."), ("Pendengar", "Pelan. Gunakan umpan."), ("Penyergap", "Hindari garis terjangan."))):
            x = left + 40 + i * column
            r.text(s, name, (x, 478), 17, PAPER)
            r.text(s, tip, (x, 505), 15, MUTED)
        r.text(s,"B: tas. 1: P3K / 2: energi / 3: alarm / 4: lampu kimia.",(left+40,548),15,MUTED)
        r.text(s,"Dialog: E tampilkan teks, lalu E lanjut. J: catatan. F5 / F9: simpan / muat.",(left+40,574),14,MUTED)
        self.button((left + 40, 605, 180, 42), "Kembali", "back", "primary")

    def draw_settings(self):
        left, width = self.modal_base("Pengaturan")
        r, s = self.renderer, self.screen
        right = left + width - 40
        for i, (name, label) in enumerate((("volume", "Efek suara"), ("music_volume", "Musik"), ("brightness", "Kecerahan"))):
            y = 225 + i * 62
            r.text(s, label, (left + 40, y + 9), 19, PAPER)
            self.button((right - 220, y, 44, 40), "-", name + ":-0.1")
            r.text(s, f"{int(self.settings[name] * 100)}%", (right - 110, y + 10), 18, PAPER, align="center")
            self.button((right - 44, y, 44, 40), "+", name + ":0.1")
        for y, label, action, value in ((411,"Layar","fullscreen","Penuh" if self.fullscreen else "Jendela"), (463,"Efek kamera","motion","Ringan" if self.settings["reduced_motion"] else "Penuh")):
            r.text(s, label, (left + 40, y + 9), 19, PAPER)
            self.button((right - 220, y, 220, 40), value, action)
        r.text(s, "Seed Escape", (left + 40, 524), 19, PAPER)
        self.button((right - 220, 515, 160, 40), self.seed_text or "Acak", "seed", selected=self.seed_focused)
        self.button((right - 48, 515, 48, 40), "R", "random_seed")
        self.button((left + 40, 605, 180, 42), "Kembali", "back", "primary")
        if self.audio and not self.audio.available:
            r.text(s, "Audio tidak tersedia.", (left + 240, 619), 15, MUTED)

    def draw_pause(self):
        r, s = self.renderer, self.screen
        r.draw_session(s, self.session, self.settings)
        shade = pygame.Surface(s.get_size(), pygame.SRCALPHA)
        shade.fill((3, 8, 12, 218))
        s.blit(shade, (0, 0))
        x = self.width / 2 - 120
        r.text(s, "Jeda", (self.width / 2, 175), 36, PAPER, align="center")
        actions=[("Lanjut","resume")]
        if getattr(self.session,"cutscene",None):actions.append(("Lewati adegan","cutscene_skip"))
        if not getattr(self.session,"modal",False):actions.append(("Backpack","backpack"))
        if self.session.mode_key=="story":actions += [("Simpan permainan","save_menu"),("Muat permainan","load_menu")]
        actions += [("Pencapaian","achievements"),("Cara main","help"),("Pengaturan","settings"),("Menu","menu")]
        for i, (label, action) in enumerate(actions):
            self.button((x, 260 + i * 56, 240, 44), label, action, "primary" if i == 0 else "text")

    def draw_result(self):
        r, s, session = self.renderer, self.screen, self.session
        r.backdrop(s)
        x = 84
        won = session.status == "won"
        r.text(s, "Pulang." if won else "Terhenti.", (x, 192), 62, PAPER)
        if not won:
            r.text(s, session.last_attacker or session.death_reason, (x, 282), 18, MUTED)
        minutes, seconds = divmod(int(getattr(session,"play_seconds",session.elapsed)), 60)
        r.text(s, f"{minutes:02}:{seconds:02}", (x, 332), 22, MUTED, mono=True)
        story=session.mode_key=="story"
        if not story or not won:self.button((x, 416, 240, 46),"Dari checkpoint" if story else "Ulangi","retry","primary")
        self.button((x, 480, 240, 42), "Cerita baru" if story else "Map baru", "new", "text")
        self.button((x, 538, 240, 42), "Menu", "menu", "text")
        self.button((self.width-246,HEIGHT-100,210,42),"Pencapaian","achievements","text")
