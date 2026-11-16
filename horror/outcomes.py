"""Terminal presentations consume a frozen frame, never a mutable gameplay session."""
import pygame
from .config import HEIGHT, PAPER, MUTED


def ease(value):
    value=max(0.,min(1.,value));return value*value*(3-2*value)


class OutcomePresentation:
    def __init__(self, frame, won, story=False):
        self.frame=frame.copy();self.won=won;self.story=story;self.time=0.
        self.duration=6.5 if won else 5.5

    def update(self,dt):
        self.time=min(self.duration,self.time+min(.05,max(0.,dt)))
        return self.time>=self.duration

    @staticmethod
    def shade(screen, color, alpha):
        layer=pygame.Surface(screen.get_size(),pygame.SRCALPHA)
        layer.fill((*color,round(max(0,min(255,alpha)))));screen.blit(layer,(0,0))

    def draw(self,screen,r,reduced=False):
        t=self.time
        image=pygame.transform.scale(self.frame,screen.get_size())
        if not self.won and not reduced:
            zoom=1+.025*ease(t/3.)
            image=pygame.transform.smoothscale(image,(round(screen.get_width()*zoom),round(screen.get_height()*zoom)))
        screen.blit(image,((screen.get_width()-image.get_width())//2,(screen.get_height()-image.get_height())//2))
        if self.won:
            self.shade(screen,(12,19,24),180)
            opening=float(t>=2.) if reduced else ease((t-1)/3.)
            center=r.width/2
            r.draw.polygon(screen,(74,82,75),[(center-180,HEIGHT),(center-70,220),(center+70,220),(center+180,HEIGHT)])
            r.draw.rect(screen,(6,13,18),(center-220-opening*220,150,220,470))
            r.draw.rect(screen,(6,13,18),(center+opening*220,150,220,470))
            for x in range(0,220,28):
                r.draw.line(screen,(73,88,86),(center-220-opening*220+x,150),(center-220-opening*220+x,620),5)
                r.draw.line(screen,(73,88,86),(center+opening*220+x,150),(center+opening*220+x,620),5)
            r.draw.line(screen,(137,148,126),(center-260,144),(center+260,144),8)
            self.shade(screen,(169,174,146),35*ease((t-3)/3.))
            caption="Gerbang terbuka." if t<3.5 else "Tidak ada langkah yang mengikutimu."
        else:
            self.shade(screen,(3,7,12),245*ease(t/3.5))
            caption="Arga tidak sempat pulang." if self.story else "Langkahmu berhenti di sini."
        r.draw.rect(screen,(3,8,12),(0,0,r.width,66))
        r.draw.rect(screen,(3,8,12),(0,HEIGHT-66,r.width,66))
        if t>1.4:r.text(screen,caption,(r.width/2,HEIGHT-120),24,PAPER,align="center")
        if t>3.7 and not self.won:r.text(screen,"Sunyi.",(r.width/2,HEIGHT/2-25),38,MUTED,align="center")
        if t>self.duration-.5:self.shade(screen,(3,8,12),255*ease((t-self.duration+.5)/.5))
