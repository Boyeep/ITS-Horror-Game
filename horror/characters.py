"""Original flat ink drawings. Curves are rasterized large, then sampled once."""
import math
import pygame

INK=(27,37,43)
HAIR=(36,35,36)
SKIN=(204,164,126)
SKIN_SHADE=(181,139,106)


class InkDrawing:
    def __init__(self,size,scale=3):
        self.scale=scale;self.surface=pygame.Surface((size[0]*scale,size[1]*scale),pygame.SRCALPHA)
    def points(self,points):return [(round(x*self.scale),round(y*self.scale)) for x,y in points]
    def line(self,color,points,width=1):
        pygame.draw.lines(self.surface,color,False,self.points(points),max(1,round(width*self.scale)))
        radius=round(width*self.scale/2)
        if radius:
            for point in (points[0],points[-1]):pygame.draw.circle(self.surface,color,self.points([point])[0],radius)
    def ellipse(self,color,rect,width=0):
        pygame.draw.ellipse(self.surface,color,[round(n*self.scale) for n in rect],round(width*self.scale))
    def rect(self,color,rect,radius=0):
        pygame.draw.rect(self.surface,color,[round(n*self.scale) for n in rect],border_radius=round(radius*self.scale))
    def path(self,color,commands,stroke=None,width=1):
        points=[];cursor=(0,0)
        for command in commands:
            if command[0]=="M" or command[0]=="L":cursor=command[1:];points.append(cursor)
            elif command[0]=="C":
                start=cursor;a=command[1:3];b=command[3:5];end=command[5:7]
                for i in range(1,19):
                    t=i/18;u=1-t
                    points.append((u**3*start[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*end[0],u**3*start[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*end[1]))
                cursor=end
        pygame.draw.polygon(self.surface,color,self.points(points))
        if stroke:self.line(stroke,[*points,points[0]],width)


def portrait_original(kind):
    """Quiet expressions, a short neck and a single understated mouth stroke."""
    d=InkDrawing((300,360));nara=kind=="nara"
    coat=(143,66,61) if nara else (45,98,129)
    trim=(114,52,51) if nara else (31,74,101)
    if nara:
        d.path(HAIR,[("M",82,219),("C",66,174,70,106,79,79),("C",87,39,115,20,148,23),("C",194,16,224,50,224,98),("L",230,230),("C",197,251,109,246,82,219)],INK,2)
    d.path(coat,[("M",30,360),("L",38,285),("C",41,263,69,250,111,239),("L",185,238),("C",226,245,258,264,264,288),("L",276,360)],INK,2.5)
    d.path(trim,[("M",30,360),("L",38,285),("C",40,267,60,258,76,254),("L",74,360)])
    d.path((32,50,61),[("M",113,244),("L",185,244),("L",198,360),("L",104,360)])
    d.path(SKIN_SHADE,[("M",126,207),("L",174,207),("L",175,247),("L",151,269),("L",126,247)],INK,1.5)
    d.path(SKIN,[("M",130,220),("L",170,218),("L",169,244),("L",151,259),("L",131,244)])
    d.path((220,220,205),[("M",117,242),("L",151,262),("L",184,241),("L",174,279),("L",129,278)])
    d.path(coat,[("M",112,239),("L",146,266),("L",123,291),("L",99,251)],INK,1.4)
    d.path(coat,[("M",188,238),("L",156,266),("L",183,289),("L",205,250)],INK,1.4)
    d.ellipse(SKIN_SHADE,(91,130,22,38));d.ellipse(SKIN,(191,130,21,38))
    d.path(SKIN,[("M",104,100),("C",104,68,128,57,152,58),("C",189,58,202,84,199,116),("L",196,169),("C",193,204,172,226,152,229),("C",126,224,104,202,103,169)],INK,1.7)
    d.path(SKIN_SHADE,[("M",104,122),("L",115,132),("L",116,174),("C",118,197,133,218,152,229),("C",127,223,105,203,103,170)])
    d.line((76,59,48),[(119,130),(128,127),(137,129)],1.8)
    d.line((76,59,48),[(165,129),(174,127),(183,130)],1.8)
    for x,y in ((128,143),(175,142)):
        d.ellipse((55,48,42),(x-2.5,y-3.5,5,8))
        d.line((83,64,51),[(x-7,y-4),(x+5,y-4)],1.2)
    d.line((159,118,89),[(152,146),(149,165),(155,168)],1.2)
    # No lip highlight, outline or pointed cheek planes.
    d.line((118,82,66),[(141,191),(154,191),(160,190)],1.3)
    if nara:
        d.path(HAIR,[("M",95,153),("C",83,105,95,62,127,48),("C",170,29,209,60,211,105),("L",203,162),("L",194,130),("C",178,114,165,98,158,78),("C",145,102,130,115,109,120),("L",108,166),("L",100,192)],INK,1.5)
        d.path(HAIR,[("M",200,107),("L",215,116),("L",218,228),("L",196,241),("C",205,208,204,160,200,107)])
        d.line((224,225,207),[(188,84),(201,99)],4)
    else:
        d.path(HAIR,[("M",102,163),("C",90,145,88,113,92,94),("C",88,72,100,52,121,47),("C",135,26,161,32,174,44),("C",201,40,219,61,210,87),("L",204,133),("L",194,125),("L",190,95),("C",176,99,162,89,154,80),("C",142,94,128,101,110,100),("L",110,150)],INK,2)
        d.line((69,65,58),[(105,80),(123,62),(144,58)],2)
        d.path((208,170,63),[("M",80,250),("L",94,246),("L",127,360),("L",108,360)],(138,111,50),1)
        d.line((133,172,181),[(133,280),(150,319),(173,280)],2)
        d.rect((216,219,202),(140,317,23,29),2);d.rect((54,98,121),(143,321,17,6),1)
        d.line((116,132,124),[(145,333),(158,333)],1)
    d.line(trim,[(235,282),(229,325),(232,360)],2)
    return d.surface


def student_original(kind,frame,direction):
    d=InkDrawing((48,64),6);nara=kind=="nara"
    coat=(145,68,61) if nara else (44,99,131);dark=(101,48,47) if nara else (29,70,95)
    walk=math.sin(frame/12*math.tau)*1.4
    # The face is smaller than the old rig; the silhouette carries recognition.
    for side in (-1,1):
        x=23+side*3.4
        d.rect((43,51,58),(x-2.5,48,5,12+walk*side),1.7)
        d.ellipse((28,36,43),(x-3.5,58+walk*side,7,3.8))
    if nara:d.path(HAIR,[("M",13,21),("C",12,7,34,7,35,21),("L",36,43),("L",12,43)],INK,.65)
    d.path(coat,[("M",15,31),("C",16,28,31,28,33,32),("L",33,49),("C",29,52,18,52,15,49)],INK,.65)
    for side in (-1,1):
        x=23.5+side*10
        if kind=="player" and direction=="north" and side==1:
            d.path(coat,[("M",32,33),("L",36,31),("L",40,40),("L",35,46),("L",32,42)],INK,.6)
            d.ellipse(SKIN,(35,33,5,5))
        else:
            d.path(dark,[("M",x-2,33),("L",x+2,33),("L",x+2.5,46),("L",x-2.5,46)],INK,.6)
            d.ellipse(SKIN,(x-2.4,44+walk*side*.3,5,4.5))
    if direction in ("east","west"):
        side=1 if direction=="east" else -1
        if not nara:
            d.rect((135,108,49),(23-side*9-5,31,10,17),3)
            d.rect((218,178,63),(23-side*9-4,31,8,14),2.7)
            d.line((241,215,143),[(23-side*9-2,37),(23-side*9+2,37)],.65)
        d.path(coat,[("M",23+side*6,34),("L",23+side*10,35),("L",23+side*11,42),("L",23+side*7,43)],INK,.5)
        d.ellipse(SKIN,(23+side*11-2,39,4.5,4))
    elif direction=="north" and not nara:
        d.rect((111,89,46),(14,31,19,18),3)
        d.rect((215,174,62),(15,31,17,16),3)
        d.rect((232,192,76),(16,32,15,4),1.5)
        d.rect((184,143,49),(19,39,9,6),1.5)
        d.line((235,209,137),[(22,40),(25,40),(24,43)],.65)
    elif direction=="south":
        d.path((216,219,202),[("M",18,31),("L",24,36),("L",29,31),("L",25,32),("L",23,32)])
        if not nara:
            d.line((219,181,65),[(17,32),(19,49)],1.5)
            d.line((128,173,182),[(22,36),(24,44),(27,36)],.65)
            d.rect((216,220,202),(23,43,4,5),.6)
    d.ellipse(INK,(13.3,9.7,21,24))
    if direction=="north":
        d.ellipse(HAIR,(14,10,19.8,22))
        d.path((45,43,41),[("M",16,18),("C",18,11,29,11,31,20),("C",26,16,20,16,16,18)])
    else:
        d.ellipse(SKIN,(15,13,18,20))
        if direction=="south":
            d.path(HAIR,[("M",14,23),("C",12,10,21,8,28,11),("C",36,12,36,19,33,24),("L",30,20),("L",25,17),("L",20,20),("L",16,19),("L",16,26)])
            for x in (20.5,28):d.ellipse((47,42,37),(x,24,1.3,2.1))
            d.line((128,87,66),[(23,30),(25.5,30)],.55)
        else:
            side=1 if direction=="east" else -1
            # Profile nose is a small contour, rather than the old round protruding lip.
            eye=24+side*5
            d.ellipse((46,42,37),(eye-.6,23.5,1.25,2))
            mouthx=24+side*5.5
            d.line((131,92,70),[(mouthx-side*.5,29),(mouthx+side*1,29)],.45)
            if side>0:
                d.path(HAIR,[("M",15,28),("C",9,18,15,10,22,10),("C",29,7,34,13,34,20),("L",31,19),("L",29,17),("L",25,19),("L",22,17),("L",19,20),("L",19,28)])
            else:
                d.path(HAIR,[("M",33,28),("C",39,18,33,10,26,10),("C",19,7,14,13,14,20),("L",17,19),("L",19,17),("L",23,19),("L",26,17),("L",29,20),("L",29,28)])
    if nara:
        if direction!="north":
            d.path(HAIR,[("M",14,20),("L",17,20),("L",17,39),("L",13,42)])
            d.path(HAIR,[("M",31,20),("L",34,20),("L",35,41),("L",31,39)])
        d.line((230,230,212),[(29,16),(32,19)],1.2)
    return d.surface
