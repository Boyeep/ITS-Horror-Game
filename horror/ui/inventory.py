"""Backpack and achievement presentation."""
import math
import pygame
from ..config import AMBER, MUTED, PAPER, TEAL
from ..inventory import ITEMS
from ..achievements import ACHIEVEMENTS, BY_KEY


class InventoryViews:
    def draw_backpack(self):
        r,s,game=self.renderer,self.screen,self.session
        r.draw_session(s,game,self.settings)
        shade=pygame.Surface(s.get_size(),pygame.SRCALPHA);shade.fill((3,10,14,228));s.blit(shade,(0,0))
        width=min(1100,self.width-64);left=(self.width-width)/2
        r.panel(s,(left,72,width,668),(12,23,28),(59,76,77),3)
        r.ui_item(s,"backpack",58,(left+25,87))
        r.text(s,"Backpack",(left+96,99),32,PAPER)
        used=game.backpack.used;color=AMBER if used>=10 else TEAL
        r.text(s,f"{used} / {game.backpack.capacity} ruang",(left+width-32,108),17,color,align="right",mono=True)
        self.renderer.draw.rect(s,(41,57,60),(left+width-190,140,158,3))
        self.renderer.draw.rect(s,color,(left+width-190,140,158*min(1,used/game.backpack.capacity),3))
        self.button((left+32,164,192,38),"Perlengkapan","bag_tab:supplies","text",self.bag_tab=="supplies")
        self.button((left+232,164,192,38),"Barang penting","bag_tab:keys","text",self.bag_tab=="keys")
        self.renderer.draw.line(s,(42,60,64),(left+32,216),(left+width-32,216))
        if self.bag_tab=="supplies":
            columns=4 if width>=900 else 3
            gridwidth=width*.58;cell=(gridwidth-42)/columns
            for i,(key,item) in enumerate(ITEMS.items()):
                x=left+30+i%columns*cell;y=240+i//columns*148
                selected=key==self.bag_selected;quantity=game.backpack.count(key)
                self.button((x,y,cell-12,136),"","bag_select:"+key,selected=selected)
                size=min(88,int(cell-26))
                r.ui_item(s,key,size,(x+(cell-12)/2,y+7),"midtop",255 if quantity else 65)
                r.text(s,item.name,(x+(cell-12)/2,y+100),13,PAPER if quantity else MUTED,align="center")
                r.text(s,str(quantity),(x+cell-23,y+12),16,color if quantity else (82,103,108),align="right",mono=True)
            x=left+gridwidth+14;detail=width-gridwidth-48
            self.renderer.draw.line(s,(42,60,64),(x-18,238),(x-18,661))
            key=self.bag_selected;item=ITEMS[key];quantity=game.backpack.count(key)
            r.ui_item(s,key,116,(x+detail/2,239),"midtop")
            r.text(s,item.name,(x,366),23,PAPER)
            bottom=r.wrapped(s,item.description,(x,406),detail,17,MUTED,1.5)
            r.text(s,f"Ruang {item.space}/buah · Maks. {item.stack}",(x,max(510,bottom+12)),13,MUTED)
            if item.shortcut:r.text(s,"Cepat: "+item.shortcut,(x,554),14,AMBER)
            if quantity:
                self.button((x,594,detail,42),"Gunakan","bag_use","primary")
                self.button((x,644,detail,34),"X  Letakkan","bag_drop","text")
            else:r.text(s,"Belum dibawa",(x,609),17,MUTED)
        else:
            keys=[(label,1) for label in sorted(getattr(game,"story_items",set())) if label not in ("Jalur bumi","Daya cadangan")]
            if game.collected:keys.insert(0,("Sekring",game.collected))
            cardwidth=(width-80)/2
            for i,(label,count) in enumerate(keys):
                x=left+32+i%2*(cardwidth+16);y=236+i//2*64
                r.panel(s,(x,y,cardwidth,58),(17,31,37),(40,57,62),2)
                r.ui_key_item(s,label,50,(x+5,y+3))
                r.text(s,label+(f" ×{count}" if count>1 else ""),(x+66,y+19),17,PAPER)
            if not keys:r.text(s,"Belum ada barang penting.",(left+36,267),19,MUTED)
            r.text(s,"Tidak memakai ruang tas. Digunakan saat berinteraksi.",(left+32,692),14,MUTED)
        if self.bag_notice:r.text(s,self.bag_notice,(left+32,220),13,AMBER)
        self.button((left+width-192,690,160,34),"Kembali","bag_close","text")

    def draw_achievements(self):
        r,s=self.renderer,self.screen;r.backdrop(s)
        width=min(1120,self.width-64);left=(self.width-width)/2
        r.panel(s,(left,76,width,666),(11,22,28),(44,65,71),3)
        r.text(s,"Pencapaian",(left+32,110),34,PAPER)
        r.text(s,f"{len(self.achievements.unlocked)} / {len(ACHIEVEMENTS)}",(left+width-32,122),20,AMBER,align="right",mono=True)
        self.renderer.draw.line(s,(39,58,65),(left+32,177),(left+width-32,177))
        columns=2 if width>=850 else 1;count=columns*3
        page=self.achievement_page%math.ceil(len(ACHIEVEMENTS)/count);cardwidth=(width-64-16*(columns-1))/columns
        for i,a in enumerate(ACHIEVEMENTS[page*count:page*count+count]):
            x=left+32+i%columns*(cardwidth+16);y=202+i//columns*146
            unlocked=a.key in self.achievements.unlocked
            r.panel(s,(x,y,cardwidth,132),(19,35,42) if unlocked else (14,27,34),(83,93,74) if unlocked else (35,53,60),2)
            r.ui_badge(s,a.badge,72,(x+10,y+20),unlocked)
            r.text(s,a.title,(x+94,y+16),19,PAPER if unlocked else MUTED)
            r.wrapped(s,a.description,(x+94,y+48),cardwidth-111,14,MUTED,1.35)
            value=a.goal if unlocked else self.achievements.progress.get(a.key,0)
            barwidth=cardwidth-150
            self.renderer.draw.rect(s,(38,54,61),(x+94,y+108,barwidth,3))
            self.renderer.draw.rect(s,AMBER if unlocked else TEAL,(x+94,y+108,barwidth*min(1,value/a.goal),3))
            r.text(s,"OK" if unlocked else f"{int(value)}/{int(a.goal)}",(x+cardwidth-12,y+101),12,AMBER if unlocked else MUTED,align="right",mono=True)
        pages=math.ceil(len(ACHIEVEMENTS)/count)
        self.button((left+32,682,150,38),"Kembali","achievements_back","text")
        self.button((left+width-250,682,54,38),"<","achievement_page:-1","text")
        r.text(s,f"{page+1} / {pages}",(left+width-139,692),16,MUTED,align="center",mono=True)
        self.button((left+width-82,682,54,38),">","achievement_page:1","text")

    def draw_achievement_toast(self):
        if not self.achievement_toast or self.mode not in ("playing","pause","result"):return
        a=BY_KEY[self.achievement_toast];r,s=self.renderer,self.screen
        width=min(354,self.width-40);x=self.width-width-24;y=88
        r.panel(s,(x,y,width,82),(17,34,41),(123,125,87),3)
        r.ui_badge(s,a.badge,62,(x+9,y+10))
        r.text(s,"Pencapaian terbuka",(x+84,y+15),12,AMBER)
        r.text(s,a.title,(x+84,y+38),17,PAPER)
