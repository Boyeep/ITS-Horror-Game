"""Native-pixel UI drawing over a stable logical 800-unit layout."""
import os
import pygame


def enable_native_dpi():
    os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS","permonitorv2")
    if os.name!="nt" or os.environ.get("SDL_VIDEODRIVER")=="dummy":return
    try:
        import ctypes
        call=ctypes.windll.user32.SetProcessDpiAwarenessContext
        call.argtypes=[ctypes.c_void_p];call.restype=ctypes.c_bool
        call(ctypes.c_void_p(-4))
    except (AttributeError,OSError):
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError,OSError):pass


class ScaledDraw:
    def __init__(self,renderer):self.renderer=renderer
    def scale(self,surface):
        if surface in self.renderer.ui_layers:return self.renderer.ui_scale
        return (1.,1.)
    def point(self,surface,p):
        sx,sy=self.scale(surface);return (round(p[0]*sx),round(p[1]*sy))
    def box(self,surface,r):
        sx,sy=self.scale(surface)
        return pygame.Rect(round(r[0]*sx),round(r[1]*sy),round(r[2]*sx),round(r[3]*sy))
    def width(self,surface,w):return max(1,round(w*min(self.scale(surface)))) if w else 0
    def rect(self,surface,color,rect,width=0,border_radius=0,**kwargs):
        return pygame.draw.rect(surface,color,self.box(surface,rect),self.width(surface,width),border_radius=round(border_radius*min(self.scale(surface))),**kwargs)
    def line(self,surface,color,start,end,width=1):
        return pygame.draw.line(surface,color,self.point(surface,start),self.point(surface,end),self.width(surface,width))
    def lines(self,surface,color,closed,points,width=1):
        return pygame.draw.lines(surface,color,closed,[self.point(surface,p) for p in points],self.width(surface,width))
    def circle(self,surface,color,center,radius,width=0):
        return pygame.draw.circle(surface,color,self.point(surface,center),round(radius*min(self.scale(surface))),self.width(surface,width))
    def ellipse(self,surface,color,rect,width=0):
        return pygame.draw.ellipse(surface,color,self.box(surface,rect),self.width(surface,width))
    def polygon(self,surface,color,points,width=0):
        return pygame.draw.polygon(surface,color,[self.point(surface,p) for p in points],self.width(surface,width))
    def arc(self,surface,color,rect,start,stop,width=1):
        return pygame.draw.arc(surface,color,self.box(surface,rect),start,stop,self.width(surface,width))
