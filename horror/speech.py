"""Original RPG-style text cadence shared by dialogue, cinematics and audio."""
from bisect import bisect_right
from functools import lru_cache


@lru_cache(maxsize=256)
def timeline(body):
    times=[];seconds=0.
    for char in body:
        seconds+=1/38
        times.append(seconds)
        if char in ".!?":seconds+=.16
        elif char in ",;:":seconds+=.075
    return tuple(times)


def visible_count(body,seconds):return bisect_right(timeline(body),max(0,seconds))
def revealed(body,seconds):return body[:visible_count(body,seconds)]
def duration(body):return timeline(body)[-1] if body else 0.


def pulses(body,before,after):
    times=timeline(body)
    return [times[i] for i in range(visible_count(body,before),visible_count(body,after))
            if body[i].isalnum() and i%3==0]
