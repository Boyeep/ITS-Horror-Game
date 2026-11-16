"""Monster tuning, separate from HC/SA decisions. Speeds are world pixels/second."""
from dataclasses import dataclass


@dataclass(frozen=True)
class MonsterBalance:
    speed: float
    damage: int
    melee_windup: float
    attack_interval: float
    memory: float
    cue: str
    melee_follow: float = .9
    dash_speed: float = 380.
    dash_windup: float = 1.
    dash_duration: float = .62
    recovery: float = 2.5
    dash_cooldown: float = 5.


MONSTER_BALANCE = {
    "Penjaga": MonsterBalance(142., 28, .50, 1.8, 1.15, "heavy"),
    "Pendengar": MonsterBalance(122., 22, .65, 2.0, 1.30, "whisper"),
    "Penyergap": MonsterBalance(118., 24, .55, 1.8, 1.0, "growl"),
}


@dataclass(frozen=True)
class Pressure:
    pursuit: float
    vision: float
    reaction: float


# Multiply the existing Difficulty.speed; Easy keeps its v0.1 chase speeds.
PRESSURE = {"easy": Pressure(1., 1., 1.25),
            "normal": Pressure(1.25, 1.25, 1.),
            "hard": Pressure(1.30, 1.35, .9)}

SENSOR_PROFILES = {
    "Penjaga": {"sight_lit": 330., "sight_dark": 235., "hearing": .85, "amp": 1.85, "sigma": 3.6},
    "Pendengar": {"sight_lit": 43., "sight_dark": 43., "hearing": 1.8, "amp": 2.05, "sigma": 4.2},
    "Penyergap": {"sight_lit": 330., "sight_dark": 235., "hearing": .85, "amp": 1.92, "sigma": 3.8},
}
