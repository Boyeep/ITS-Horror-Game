"""Native-resolution portraits and material-specific evidence readers."""
import math
from .config import PAPER, MUTED, AMBER
from .narrative import coerce_page, DOCUMENT_TEXT
from .speech import visible_count


class StoryReader:
    def __init__(self,renderer):self.r=renderer

    def portrait(self,s,kind,rect):
        r=self.r;x,y,w,h=rect;sx,sy=r.draw.scale(s)
        r.ui_image(s,r.art.portrait(kind,(round(w*sx),round(h*sy))),(x,y))

    def fitted(self,s,body,rect,size=21,family=None,color=(47,49,43),spacing=1.55,seconds=None):
        r=self.r;x,y,w,h=rect
        while size>14 and len(r.wrap_lines(body,w,size,family))*round(size*spacing)>h:size-=1
        return r.wrapped(s,body,(x,y),w,size,color,spacing,family,visible_count(body,seconds) if seconds is not None else None)

    def dialogue(self,s,page,notes,width,seconds=None):
        r=self.r;page=coerce_page(page);kind=page["kind"]
        if kind not in ("speech","narration"):
            self.document(s,page,notes,((r.width-width)/2,138,width,520));return
        left=(r.width-width)/2;r.panel(s,(left,520,width,238),(12,22,26),(79,97,94),2)
        offset=210 if kind=="speech" else 32
        if kind=="speech":
            r.draw.rect(s,(22,40,46),(left+14,533,172,211),border_radius=3)
            self.portrait(s,page.get("speaker","arga"),(left+7,478,191,270))
        r.text(s,page.get("title") or "…",(left+offset,548),20,AMBER)
        self.fitted(s,page.get("body",""),(left+offset,591,width-offset-32,107),21,None,PAPER,1.4,seconds if kind=="speech" else None)

    def document(self,s,page,notes,rect):
        r=self.r;page=coerce_page(page);kind=page["kind"];key=page.get("document")
        title,summary=notes[key] if key in notes else (page.get("title","Catatan"),page.get("body",""))
        body=DOCUMENT_TEXT.get(key,summary);x,y,w,h=rect
        ink=(50,50,43);paper=(222,215,186)
        if kind=="message":
            w=min(w,500);x=(r.width-w)/2
            r.panel(s,(x-8,y-14,w+16,h+28),(24,32,36),(85,104,106),22)
            r.panel(s,(x,y,w,h),(13,23,29),(42,58,63),16)
            r.draw.rect(s,(6,12,16),(x+w/2-40,y+9,80,7),border_radius=4)
            sx,sy=r.draw.scale(s)
            r.ui_image(s,r.art.face_icon("nara",(round(58*sx),round(80*sy))),(x+24,y+32))
            r.text(s,"Nara",(x+94,y+49),23,PAPER)
            r.text(s,"23.47",(x+94,y+83),14,MUTED)
            r.draw.line(s,(46,64,66),(x+24,y+125),(x+w-24,y+125))
            r.panel(s,(x+24,y+157,w-48,214),(36,57,63),(55,78,79),10)
            self.fitted(s,"Arga, aku masih di perpustakaan. Catatanku di arsip lantai 2. Kalau lampu mati, jangan lewat bundaran.",(x+44,y+181,w-88,172),22,None,PAPER,1.5)
            r.wrapped(s,"Pesan masuk ke ponsel Nara sendiri.",(x+30,y+h-80),w-60,16,AMBER)
            return
        if kind=="screen":
            r.panel(s,(x-8,y-8,w+16,h+16),(25,36,39),(83,103,101),8)
            r.panel(s,(x,y,w,h),(9,21,24),(42,70,66),4)
            r.text(s,"SIMPUL   /   ARSIP LOKAL",(x+32,y+26),14,(104,155,143),mono=True)
            r.draw.line(s,(45,77,70),(x+32,y+64),(x+w-32,y+64))
            r.text(s,title,(x+32,y+88),25,(193,216,194))
            self.fitted(s,body,(x+32,y+145,w-64,h-195),21,"consolas",(151,187,166),1.6)
            r.text(s,"23:47  ·  LOKAL",(x+32,y+h-39),13,(91,134,122),mono=True)
            return
        r.draw.rect(s,(5,11,14),(x+8,y+11,w,h),border_radius=3)
        if kind=="book":
            r.draw.rect(s,(68,56,43),(x-10,y-10,w+20,h+22),border_radius=4)
            r.draw.rect(s,(196,187,157),(x-3,y+5,w+6,h))
            r.draw.rect(s,paper,(x,y,w/2,h));r.draw.rect(s,(230,223,196),(x+w/2,y,w/2,h))
            for offset,color in ((-9,(201,191,160)),(-4,(184,175,147)),(0,(140,131,108)),(3,(202,193,165))):
                r.draw.line(s,color,(x+w/2+offset,y+3),(x+w/2+offset,y+h-3),3)
            r.text(s,title,(x+28,y+27),24,ink,family="georgia")
            size=21;column=w/2-64
            while size>14:
                lines=r.wrap_lines(body,column,size,"georgia")
                if math.ceil(len(lines)/2)*round(size*1.6)<h-140:break
                size-=1
            half=math.ceil(len(lines)/2)
            for i,line in enumerate(lines):
                side=i//half;row=i%half
                r.text(s,line,(x+30+side*w/2,y+100+row*round(size*1.6)),size,ink,family="georgia")
            for side in range(2):r.text(s,str(4+side),(x+w*(.25+.5*side),y+h-36),14,(122,113,92),align="center",family="georgia")
            return
        if kind=="photo":
            # A physical print and handwriting on its reverse, kept together in the journal.
            photo_w=min(250,w*.32)
            r.draw.rect(s,(226,221,202),(x,y,photo_w,h))
            r.draw.rect(s,(61,90,98),(x+12,y+12,photo_w-24,h-78))
            for i in range(4):r.draw.rect(s,(126,144,139),(x+24+i*(photo_w-48)/4,y+35,15,90))
            self.portrait(s,"arga",(x+5,y+h-300,photo_w*.6,215))
            self.portrait(s,"nara",(x+photo_w*.4,y+h-294,photo_w*.6,211))
            r.text(s,"17 / 08 / 1998",(x+photo_w/2,y+h-47),14,ink,align="center",mono=True)
            x+=photo_w+20;w-=photo_w+20
        r.draw.rect(s,paper,(x,y,w,h),border_radius=2)
        r.draw.polygon(s,(194,184,151),[(x+w-27,y),(x+w,y+27),(x+w-27,y+27)])
        r.draw.line(s,(178,141,123),(x+38,y+22),(x+38,y+h-22))
        r.text(s,title,(x+58,y+30),23,ink,family="georgia")
        family="segoeprint,segoe print,georgia" if key in ("rak","nara","foto") else "georgia"
        self.fitted(s,body,(x+58,y+98,w-89,h-130),21,family,ink,1.55)
