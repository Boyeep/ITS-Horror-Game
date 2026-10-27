from dataclasses import dataclass

WIDTH, HEIGHT = 1280, 800
VIEW_WIDTH, VIEW_HEIGHT = 640, 400
from .version import VERSION
TILE = 40
COLS, ROWS = 6, 5
ROOM_COUNT = COLS * ROWS
SPAWN_ROOM, PANEL_ROOM, EXIT_ROOM = 26, 4, 5
ROOM_W, ROOM_H = 11, 9
INK = (9, 15, 19)
PAPER = (228, 232, 219)
MUTED = (142, 160, 158)
AMBER = (238, 184, 101)
TEAL = (109, 200, 179)
RED = (230, 103, 94)


@dataclass(frozen=True)
class Difficulty:
    name: str
    hearing: float
    search_time: float
    speed: float
    bottles: int
    grace: float
    damage: float


DIFFICULTIES = {
    "easy": Difficulty("Easy", .65, 4.0, .89, 5, 12, .8),
    "normal": Difficulty("Normal", 1.0, 7.0, 1.0, 4, 9, 1.),
    "hard": Difficulty("Hard", 1.35, 10.0, 1.07, 3, 7, 1.2),
}

ROOM_NAMES = [
    "REKTORAT", "RUANG SENAT", "LAB KOMPUTER", "TEKNIK ELEKTRO", "PANEL UTAMA", "GERBANG UTARA",
    "PERPUSTAKAAN", "RUANG BACA", "DPTSI", "INFORMATIKA", "LAB ROBOTIKA", "BENGKEL",
    "PLASA DR. ANGKA", "TAMAN ALUMNI", "TAMAN KAMPUS", "KORIDOR PUSAT", "RUANG KULIAH", "STUDIO DESAIN",
    "KANTIN", "GRAHA SEPULUH NOPEMBER", "SELASAR", "RUANG KELAS", "LAB ELEKTRONIKA", "ARSIP",
    "POS SATPAM", "PARKIR", "GERBANG SELATAN", "RUANG DOSEN", "SEKRETARIAT HIMPUNAN", "GUDANG",
]
ROOM_KINDS = [
    "admin", "meeting", "computer", "lab", "power", "gate",
    "library", "library", "computer", "computer", "lab", "workbench",
    "plaza", "garden", "garden", "walkway", "classroom", "studio",
    "canteen", "meeting", "walkway", "classroom", "lab", "archive",
    "lobby", "parking", "gate", "admin", "meeting", "storage",
]
OUTDOOR_KINDS = {"plaza", "garden", "walkway", "parking", "gate"}
