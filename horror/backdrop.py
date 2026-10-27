"""Code-rendered campus atmosphere: restrained colours, ink edges and ground mist.

The source photographs remain intact. These are cached display effects, using
pygame only, so architecture and aspect ratio stay tied to the real references.
"""
import math
import pygame

SCENES = ("rektorat", "tower2", "informatika")
NAMES = {"rektorat": "Rektorat", "tower2": "Tower 2", "informatika": "Informatika"}


NIGHT=((8,17,23),(19,34,40),(40,58,62),(70,85,84),(112,123,109),(160,161,133))
DUSK=((16,25,34),(35,49,59),(67,83,88),(105,117,115),(153,157,141),(205,193,161))

# A few lamps in the entrance/window planes, in normalized photograph coordinates.
LAMPS={"rektorat":((.455,.506),(.546,.506),(.503,.589)),
       "tower2":((.526,.337),(.590,.462),(.511,.632)),
       "informatika":((.30,.568),(.478,.472),(.591,.449),(.638,.848),(.946,.614))}


def cover_image(source,size):
    """Fill the whole viewport, preserving proportions and cropping the excess."""
    w,h=map(int,size)
    factor=max(w/source.get_width(),h/source.get_height())
    scaled=pygame.transform.smoothscale(source,(math.ceil(source.get_width()*factor),math.ceil(source.get_height()*factor)))
    canvas=pygame.Surface((w,h)).convert()
    canvas.blit(scaled,scaled.get_rect(center=(w//2,h//2)))
    return canvas


def campus_grade(source,kind,look="night"):
    """Reduce photographic detail to the world's blue/green/ochre palette once."""
    if source.get_width()>1600:
        source=pygame.transform.smoothscale(source,(1600,round(source.get_height()*1600/source.get_width())))
    w,h=source.get_size()
    # Pool small texture detail before mapping broad shapes to discrete paint tones.
    soft=pygame.transform.smoothscale(source,(max(1,round(w*.72)),max(1,round(h*.72))))
    soft=pygame.transform.smoothscale(soft,(w,h))
    gray=pygame.transform.grayscale(soft)
    result=pygame.Surface((w,h)).convert();palette=DUSK if look=="dusk" else NIGHT
    for band in range(16):
        position=band/15*(len(palette)-1);a=min(len(palette)-2,int(position));mix=position-a
        color=tuple(round(palette[a][i]*(1-mix)+palette[a+1][i]*mix) for i in range(3))
        pygame.transform.threshold(result,gray,(band*16+8,)*3,(8,)*3,color,1,inverse_set=True)
    # Continuous sky falloff keeps clouds/rooflines intact, without a hard colour mask.
    falloff=pygame.Surface((w,h))
    for y in range(h):
        p=min(1,y/(h*.68));p=p*p*(3-2*p)
        gain=(.62+.38*p) if look=="dusk" else (.26+.74*p)
        value=round(255*gain)
        pygame.draw.line(falloff,(value,value,value),(0,y),(w,y))
    result.blit(falloff,(0,0),special_flags=pygame.BLEND_RGB_MULT)
    # Thin architectural contours keep rooflines and windows legible in the dark.
    edges=pygame.transform.laplacian(gray)
    ink=pygame.Surface((w,h));ink.fill((255,0,255))
    pygame.transform.threshold(ink,edges,(140,)*3,(116,)*3,(8,19,24),1,inverse_set=True)
    ink.set_colorkey((255,0,255));ink.set_alpha(95);result.blit(ink,(0,0))
    lamps=pygame.Surface((w,h));lamps.fill((0,0,0))
    for x,y in LAMPS[kind]:
        radius=max(10,round(w*.027))
        for r in range(radius,0,-1):
            gain=(1-r/radius)**2*(.65 if look=="dusk" else 1.)
            pygame.draw.circle(lamps,(round(65*gain),round(50*gain),round(26*gain)),(round(x*w),round(y*h)),r)
    result.blit(lamps,(0,0),special_flags=pygame.BLEND_RGB_ADD)
    return result


class CampusAtmosphere:
    """Low-frequency drifting haze; reduced-motion gets the same static composition."""
    def __init__(self):self.cache={}

    def draw(self,surface,time,reduced=False,dusk=False):
        w,h=surface.get_size();key=(w,h,dusk)
        if key not in self.cache:
            mist=pygame.Surface((320,80),pygame.SRCALPHA)
            for y in range(80):
                for x in range(320):
                    envelope=math.sin(math.pi*y/79)**2*math.sin(math.pi*x/319)**.6
                    cloud=.55+.25*math.sin(x*.055+y*.12)+.2*math.cos(x*.026-y*.16)
                    mist.set_at((x,y),(92,116,116,round(envelope*cloud*(17 if dusk else 29))))
            self.cache[key]=pygame.transform.smoothscale(mist,(round(w*1.22),round(h*.33)))
            if len(self.cache)>6:self.cache={key:self.cache[key]}
        layer=self.cache[key];phase=0 if reduced else math.sin(time*.075)
        surface.blit(layer,(-w*.13+phase*w*.035,h*.58))
