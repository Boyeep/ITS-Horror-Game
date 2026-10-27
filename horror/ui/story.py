"""Story dialogue, journal, puzzles and save-slot presentation."""
import math
from datetime import datetime
import pygame
from ..config import AMBER, MUTED, PAPER, RED, TEAL
from ..story_data import ACTS, CHAPTERS, NOTES
from ..reader import StoryReader
from ..narrative import document


class StoryViews:
    def draw_story_modal(self):
        r,s,session=self.renderer,self.screen,self.session
        shade=pygame.Surface(s.get_size(),pygame.SRCALPHA)
        shade.fill((3,9,12,120 if session.dialogue else 222));s.blit(shade,(0,0))
        width=min(1020,self.width-80);left=(self.width-width)/2
        if session.dialogue:
            StoryReader(r).dialogue(s,session.dialogue[0],NOTES,width,session.dialogue_time)
            speaking=session.dialogue[0]["kind"] in ("speech","narration")
            self.button((left+width-190,708,160,36),"Tampilkan" if session.typing else "Lanjut","dialogue_next","text" if speaking else "secondary")
        elif session.keypad:
            x=self.width/2-170
            r.panel(s,(x-28,170,396,468),(13,23,27),(58,71,70))
            r.text(s,"Loker 04",(self.width/2,201),27,PAPER,align="center")
            for i in range(4):
                px=x+18+i*80
                r.panel(s,(px-2,263,60,62),(20,32,36),(88,107,101))
                r.text(s,session.code[i] if i<len(session.code) else "·",(px+28,275),28,PAPER,align="center",mono=True)
            for i,digit in enumerate("123456789"):
                self.button((x+19+i%3*104,349+i//3*49,94,40),digit,"digit:"+digit)
            self.button((x+19,496,94,40),"Hapus","code_back","text")
            self.button((x+123,496,94,40),"0","digit:0")
            self.button((x+227,496,94,40),"Buka","code_submit","primary")
            r.text(s,session.code_error,(self.width/2,552),15,RED,align="center")
            self.button((x+70,590,200,32),"Kembali","close_story","text")
        elif session.puzzle:
            x=self.width/2
            r.panel(s,(x-365,180,730,450),(13,23,27),(67,80,77))
            title={"frequency":"Penerima · Lantai 3","circuit":"Distribusi daya","isolation":"Isolasi pemancar"}[session.puzzle]
            r.text(s,title,(x,211),28,PAPER,align="center")
            if session.puzzle=="frequency":
                r.text(s,f"{session.frequency/10:.1f} MHz".replace(".",","),(x,300),48,AMBER,align="center",mono=True)
                for i in range(60):
                    strength=max(.08,1-abs(session.frequency-1078)/15)
                    height=math.sin(i*.7)*strength*25
                    self.renderer.draw.line(s,(92,143,133),(x-180+i*6,409-height),(x-180+i*6,409+height),2)
                self.button((x-240,358,80,40),"<","puzzle:left","text")
                self.button((x+160,358,80,40),">","puzzle:right","text")
            else:
                for i,name in enumerate(("UTARA","TENGAH","SELATAN")):
                    px=x-230+i*230
                    r.text(s,name,(px,291),16,MUTED,align="center")
                    self.renderer.draw.circle(s,TEAL if session.switches[i] else (56,69,69),(px,354),17,2)
                    self.button((px-80,397,160,44),f"{i+1}  "+("Hidup" if session.switches[i] else "Padam"),"puzzle:"+str(i))
            r.text(s,session.puzzle_error,(x,464),16,RED,align="center")
            self.button((x-115,505,230,44),"Konfirmasi","puzzle:submit","primary")
            self.button((x-290,574,190,32),"J  Catatan","puzzle_notes","text")
            self.button((x+100,574,190,32),"Kembali","close_story","text")
        elif session.journal_open:
            r.text(s,CHAPTERS[session.stage][0],(self.width/2,65),25,PAPER,align="center")
            r.text(s,session.objective,(self.width/2,104),17,AMBER,align="center")
            pages=len(session.journal)+1;session.journal_page%=pages
            if session.journal_page<len(session.journal):
                StoryReader(r).document(s,document(session.journal[session.journal_page]),NOTES,(left,169,width,475))
            else:
                r.panel(s,(left,169,width,475),(13,23,27),(48,65,65))
                r.text(s,"Barang cerita",(left+36,200),24,PAPER)
                for i,item in enumerate(sorted(session.story_items)):
                    r.text(s,item,(left+36+(i%3)*(width-72)/3,260+i//3*34),16,MUTED)
                if not session.story_items:r.text(s,"Belum ada barang cerita.",(left+36,260),18,MUTED)
            r.text(s,f"{session.journal_page+1} / {pages}",(self.width/2,683),14,MUTED,align="center")
            self.button((left,670,100,38),"<","journal_prev","text")
            self.button((left+width-100,670,100,38),">","journal_next","text")
            self.button((self.width/2-100,726,200,36),"Kembali","close_story","text")

    def draw_save_browser(self):
        r,s=self.renderer,self.screen;r.backdrop(s)
        width=min(920,self.width-60);left=(self.width-width)/2
        r.panel(s,(left,88,width,650),(11,21,25),(45,62,64))
        loading=self.mode=="load"
        r.text(s,"Muat permainan" if loading else "Simpan permainan",(self.width/2,122),32,PAPER,align="center")
        r.text(s,self.save_notice or "Autosave terpisah dari tiga slot manual.",(self.width/2,181),15,TEAL if self.save_notice else MUTED,align="center")
        slots=("auto","1","2","3") if loading else ("1","2","3")
        for i,slot in enumerate(slots):
            data=self.save_store.read(slot);y=226+i*102
            r.panel(s,(left+28,y,width-56,90),(17,29,33),(39,55,58),2)
            label="Autosave" if slot=="auto" else "Slot "+slot
            r.text(s,label,(left+46,y+12),18,PAPER)
            if data:
                stage=min(24,data["stage"]);act=0 if stage<6 else 1 if stage<16 else 2
                seconds=int(data.get("seconds",0));stamp=""
                try:stamp=datetime.fromisoformat(data.get("saved_at","")).astimezone().strftime("%d %b · %H:%M")
                except ValueError:pass
                r.text(s,f"{ACTS[act]}   /   {seconds//60:02}:{seconds%60:02}",(left+46,y+39),14,AMBER)
                location=data.get("location",CHAPTERS[stage][0])
                r.text(s,f"{location}   ·   {stamp}",(left+46,y+62),13,MUTED)
            else:r.text(s,"Kosong",(left+46,y+48),15,MUTED)
            if not loading or data:self.button((left+width-166,y+23,112,42),"Muat" if loading else "Simpan",("load_slot:" if loading else "save_slot:")+slot)
        self.button((left+32,675,180,38),"Kembali","back_saves","text")
