"""Read-only tension model shared by sound and picture.

Nothing here changes a session. It only reads values the simulation already
keeps (threat, encounter_timer, health), so monster behaviour stays in the
simulation code and these atmosphere effects follow whatever it decides.
"""
import math


def light_dip(time, level):
    """0..1 soft dip shared by torch and lamps so they flicker together; at most ~3 dips a second."""
    wave = math.sin(time * 7) * math.sin(time * 11 + 1.3) + .6 * math.sin(time * 4.3 + .4)
    return max(0., min(1., (wave - (1.55 - .95 * level)) / .4))


def tension_level(session):
    """How strained the moment is: 0 is calm, 1 is about to be caught."""
    level = max(getattr(session, "threat", 0.), getattr(session, "encounter_timer", 0.) / .65)
    top = max(1, getattr(session, "max_health", 100))
    hurt = 1 - getattr(session, "health", top) / top
    if hurt > .5:
        level = max(level, (hurt - .5) * 1.4)
    return max(0., min(1., level))


def approach(value, target, dt, rise=2.5, fall=.5):
    """Move value toward target: tension builds quickly and drains slowly."""
    rate = rise if target > value else fall
    return value + (target - value) * min(1., dt * rate)


class CueGate:
    """Cooldowns so atmosphere cues neither stack nor repeat back to back."""

    def __init__(self, gap=2.5):
        self.gap = gap
        self.clock = 0.
        self.after = {}
        self.quiet_until = 0.

    def tick(self, dt):
        self.clock += dt

    def defer(self, duration):
        """Leave space for a gameplay/scene cue without consuming its own cooldown."""
        self.quiet_until = max(self.quiet_until, self.clock + duration)

    def allow(self, name, cooldown):
        """True when the cue may play now; records it so the next one waits."""
        if self.clock < self.quiet_until or self.clock < self.after.get(name, 0.):
            return False
        self.after[name] = self.clock + cooldown
        self.quiet_until = self.clock + self.gap
        return True
