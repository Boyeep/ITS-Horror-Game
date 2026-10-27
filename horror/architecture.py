"""Readable doorway and stair-flight illustrations at arbitrary pixel sizes."""
import math
import pygame
from .characters import InkDrawing


DOOR_SIZE=96
DOOR_ANCHOR=(48,48)


def door_geometry(vertical,swing):
    """All coordinates are offsets from the actual door tile centre, in world units."""
    hinge=pygame.Vector2(-18,0);tip=hinge+pygame.Vector2(36,0).rotate(-90*swing)
    if vertical:hinge=hinge.rotate(90);tip=tip.rotate(90)
    return hinge,tip


def door_original(vertical,swing):
    d=InkDrawing((DOOR_SIZE,DOOR_SIZE),4);origin=pygame.Vector2(DOOR_ANCHOR)
    d.rect((21,30,32,150),(22,35,52,28),2)
    d.rect((101,113,107),(29,37,38,24),1)
    d.rect((163,151,114),(29,57,38,3),.5)
    for x in (22,68):
        d.rect((61,77,80),(x,34,6,29),1)
        d.rect((161,170,155),(x+1,34,4,26),1)
        d.line((199,204,180),[(x+2,36),(x+2,58)],.8)
    hinge,tip=door_geometry(False,swing);axis=(tip-hinge).normalize();normal=pygame.Vector2(-axis.y,axis.x)
    points=[origin+hinge-normal*5.8,origin+tip-normal*5.8,origin+tip+normal*5.8,origin+hinge+normal*5.8]
    d.path((181,129,77),[("M",*points[0]),*[('L',*point) for point in points[1:]]],(64,47,33),1)
    d.line((232,184,113),[points[0]+normal,points[1]+normal],.8)
    for a,b in ((.08,.44),(.54,.91)):
        left=origin+hinge.lerp(tip,a);right=origin+hinge.lerp(tip,b)
        q=[left-normal*3.8,right-normal*3.8,right+normal*3.8,left+normal*3.8]
        d.path((147,98,58),[("M",*q[0]),*[('L',*point) for point in q[1:]]],(207,151,86),.6)
    handle=origin+hinge.lerp(tip,.84)+normal*2
    d.ellipse((64,48,31),(handle.x-1.7,handle.y-2,3.4,4))
    d.line((245,212,125),[handle-axis*2,handle+axis*2],1.2)
    # Clockwise raster rotation preserves the shared hinge at (0,-18) for vertical walls.
    return pygame.transform.rotate(d.surface,-90) if vertical else d.surface


def stair_original(direction):
    down=direction=="down";d=InkDrawing((88,112),4)
    d.rect((11,21,25,180),(4,8,81,101),3)
    d.rect((63,79,84),(4,3,80,101),2)
    d.rect((21,33,39),(15,9,58,86),1)
    # Broad filled treads, vertical risers, sidewalls and distinct landings.
    d.rect((126,139,135),(14,7,60,19),1)
    d.line((170,179,159),[(16,9),(72,9)],1)
    for i in range(8):
        y=26+i*7.2
        value=(7-i) if down else i
        color=(80+value*6,94+value*6,94+value*5)
        d.rect(color,(16,y,56,7.4))
        d.rect((49+value*3,65+value*3,69+value*3),(16,y+4.8,56,2.4))
        d.line((153+value*4,163+value*3,150+value*3),[(17,y),(71,y)],.9)
    d.rect((143,151,139),(14,85,60,17),1)
    d.line((181,187,167),[(16,86),(72,86)],1)
    for x in (7,75):
        d.rect((87,105,108),(x,7,6,91),1)
        d.line((181,191,175),[(x+2,9),(x+2,94)],1.6)
        for y in (20,76):d.line((55,75,82),[(x+2,y),(x+2,y+13)],1.3)
    # A small wayfinding mark is on the landing, away from the treads.
    arrow=1 if down else -1;y=94
    d.line((70,85,78),[(39,y-arrow*2),(44,y+arrow*2),(49,y-arrow*2)],1.4)
    return d.surface
