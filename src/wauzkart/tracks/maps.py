from ..runtime import *

TRACK_SCALE = 2.5
TRACK_SIZE_FACTORS = {
    "klein": 1.0,
    "gross": 2.0,
}

BASE_OUTER_R = 40
BASE_INNER_R = 18
BASE_TRACK_WIDTH = BASE_OUTER_R - BASE_INNER_R
BASE_MID_R = (BASE_OUTER_R + BASE_INNER_R) / 2
MID_R = BASE_MID_R * TRACK_SCALE
OUTER_R = MID_R + BASE_TRACK_WIDTH / 2
INNER_R = MID_R - BASE_TRACK_WIDTH / 2
WIN_LAPS = 3

# Startpositionen fuer bis zu 4 Spieler/KI
START_POSITIONS = [
    (MID_R - 5.4, -3.0, 180),
    (MID_R - 1.8, -3.0, 180),
    (MID_R + 1.8, -3.0, 180),
    (MID_R + 5.4, -3.0, 180),
]

# Spieler-Konfigurationen
PLAYER_CONFIGS = [
    {"name": "P1", "color": (1.0, 0.2, 0.2), "keys": ("w","s","a","d"),        "hud_color": "#ff5555"},
    {"name": "P2", "color": (0.2, 0.5, 1.0), "keys": ("UP","DOWN","LEFT","RIGHT"), "hud_color": "#5599ff"},
    {"name": "P3", "color": (0.2, 0.9, 0.2), "keys": ("t","g","f","h"),        "hud_color": "#44dd44"},
    {"name": "P4", "color": (1.0, 0.7, 0.0), "keys": ("i","k","j","l"),        "hud_color": "#ffbb00"},
]

# KI-Farueben
AI_COLORS = [
    (0.2, 0.9, 0.2),
    (1.0, 0.7, 0.0),
    (0.8, 0.2, 0.8),
    (0.2, 0.9, 0.9),
]
AI_NAMES = ["KI 1", "KI 2", "KI 3", "KI 4"]

CHARACTER_DEFS = {
    "Mauz":  {"main": (0.95, 0.82, 0.18), "accent": (0.18, 0.18, 0.18), "hat": "ears"},
    "Wauz":  {"main": (0.75, 0.55, 0.25), "accent": (0.12, 0.12, 0.12), "hat": "ears"},
    "Fuchs": {"main": (1.00, 0.45, 0.15), "accent": (0.15, 0.15, 0.15), "hat": "ears"},
    "Hase":  {"main": (0.92, 0.92, 0.92), "accent": (0.15, 0.15, 0.15), "hat": "ears"},
    "Baer":   {"main": (0.55, 0.36, 0.20), "accent": (0.12, 0.10, 0.08), "hat": "none"},
    "Bot":   {"main": (0.55, 0.75, 0.95), "accent": (0.05, 0.10, 0.14), "hat": "antenna"},
}
CHARACTER_NAMES = list(CHARACTER_DEFS.keys())

# Gesamte Farbpalette (menschliche Auswahl + KI-Farueben) fuer eindeutige Zuweisung
ALL_CAR_COLORS = [
    (1.0, 0.2, 0.2),   # rot
    (0.2, 0.9, 0.2),   # grn
    (0.2, 0.5, 1.0),   # blau
    (1.0, 0.7, 0.0),   # gelb
    (1.0, 1.0, 1.0),   # wei
    (0.1, 0.1, 0.1),   # schwarz
    (0.8, 0.2, 0.8),   # violett
    (0.2, 0.9, 0.9),   # cyan
]

# Parkpltze fuer fertige Autos
PARKING_SPOTS = [
    [55 * TRACK_SCALE, -10 * TRACK_SCALE],
    [55 * TRACK_SCALE, 10 * TRACK_SCALE],
    [-55 * TRACK_SCALE, -10 * TRACK_SCALE],
    [-55 * TRACK_SCALE, 10 * TRACK_SCALE],
]

# KI-Schwierigkeitsstufen mit erweiterten intelligenten Parametern
AI_DIFFICULTIES = {
    "Leicht":   dict(
        # Minimal intelligent und langsam
        look_ahead=10, speed=0.55, sharp=0.3, wobble=10.0,
        prediction_depth=1,      # Nur 1 Punkt voraus
        opponent_awareness=0.1,  # Kaum Gegner-Reaktion
        racing_line_quality=0.4, # Schlechte Rennlinie
        overtake_aggression=0.1, # Sehr defensiv
        brake_predictiveness=0.3, # Schlechtes Bremsen
        adaptive_difficulty=0.05, # Kaum Anpassung
        # Notfall-Manver kaum
        emergency_ram_chance=0.0,
        emergency_crash_dodge=0.0,
        risky_maneuver_threshold=0.0,
        emergency_spin_chance=0.0
    ),
    "Mittel":   dict(
        look_ahead=28, speed=0.75, sharp=0.6, wobble=4.5,
        # Neue intelligente Parameter
        prediction_depth=2,      # 2 Punkte voraus
        opponent_awareness=0.45,  # Leichte Gegner-Reaktion
        racing_line_quality=0.65, # Durchschnittliche Rennlinie
        overtake_aggression=0.35, # Zurueckhaltend
        brake_predictiveness=0.5, # Mittelmiges Bremsen
        adaptive_difficulty=0.2,
        # Notfall-Manver
        emergency_ram_chance=0.05,     # Sehr selten rammen
        emergency_crash_dodge=0.05,    # Sehr selten aggressive Ausweichmanver
        risky_maneuver_threshold=0.05, # Kleine Chancen
        emergency_spin_chance=0.0  # Keine Spins
    ),
    "Schwer":   dict(
        look_ahead=36, speed=0.85, sharp=0.8, wobble=1.2,
        prediction_depth=3,      # 3 Punkte voraus
        opponent_awareness=0.7, # Gute Gegner-Reaktion
        racing_line_quality=0.85, # Sehr gute Rennlinie, aber deutlich unter Profi
        overtake_aggression=0.55, # Moderat aggressiv
        brake_predictiveness=0.7, # Gute Bremsvorhersage
        adaptive_difficulty=0.45,
        # Notfall-Manver hufig
        emergency_ram_chance=0.25,
        emergency_crash_dodge=0.35,
        risky_maneuver_threshold=0.35,
        emergency_spin_chance=0.02  # Selten Spins
    ),
    "Profi":    dict(
        look_ahead=42, speed=1.04, sharp=1.0, wobble=0.8,
        # Neue intelligente Parameter
        prediction_depth=5,      # 5 Punkte voraus
        opponent_awareness=1.0,  # Maximale Gegner-Reaktion
        racing_line_quality=1.0, # Perfekte Rennlinie
        overtake_aggression=1.0, # Maximale Aggression
        brake_predictiveness=1.0, # Perfekte Bremsvorhersage
        adaptive_difficulty=1.0,
        # Notfall-Manver - EXTREM AGGRESSIV
        emergency_ram_chance=0.05,    # Nur ca. 5% Chance
        emergency_crash_dodge=0.8,    # Sehr aggressive Ausweichmanver
        risky_maneuver_threshold=1.0, # Maximales Risiko
        # Notfall-Drehung (
        emergency_spin_chance=0.2     # 20% Chance bei extremem Stress
    ),
}

# Map-Hilfsfunktionen fuer unterschiedliche Streckenformen

def oval_outer(a):
    """Klassisches Oval - sanfte Kurven"""
    r = math.radians(a)
    return 1.0 + 0.25 * math.sin(r * 2)

def oval_inner(a):
    """Innenverlauf Oval"""
    r = math.radians(a)
    return 0.65 + 0.15 * math.sin(r * 2)

def quad_outer(a):
    """Rechteck mit vier scharfen Ecken"""
    # Sehr starke Cosinus-Funktion fuer quadratische Form
    r = math.radians(a)
    return 1.1 + 0.45 * (math.cos(r * 2) ** 2)

def quad_inner(a):
    """Innenverlauf Quad"""
    r = math.radians(a)
    return 0.65 + 0.35 * (math.cos(r * 2) ** 2)

def eight_outer(a):
    """Acht-frmige Strecke mit zwei Schleifen (Lemniskate-hnlich)"""
    r = math.radians(a)
    # Zwei berlagerte Schleifen
    return 1.0 + 0.4 * math.sin(r) * math.cos(r * 0.5)

def eight_inner(a):
    """Innenverlauf Acht"""
    r = math.radians(a)
    return 0.55 + 0.3 * math.sin(r) * math.cos(r * 0.5)

def triangle_outer(a):
    """Dreieck mit drei scharfen Ecken und geraden Seiten"""
    # Bei 60, 180, 300 sind die Spitzen
    r = math.radians(a)
    # Drei Spitzen mit starken Amplituden-Schwankungen
    return 1.15 + 0.5 * (math.cos(r * 3) ** 2) + 0.2 * math.cos(r * 1.5)

def triangle_inner(a):
    """Innenverlauf Dreieck"""
    r = math.radians(a)
    return 0.55 + 0.4 * (math.cos(r * 3) ** 2) + 0.15 * math.cos(r * 1.5)

# Zustzliche Streckenformen (fuer Map-Unlocks)
def chicane_outer(a):
    """Unruhige Strecke mit Chicanes (mehrere Kurvenwechsel)"""
    r = math.radians(a)
    return 1.02 + 0.22 * math.sin(r * 2) + 0.12 * math.sin(r * 5 + 0.7) + 0.06 * math.cos(r * 9)

def chicane_inner(a):
    """Innenverlauf Chicane"""
    r = math.radians(a)
    return 0.62 + 0.10 * math.sin(r * 2) + 0.08 * math.sin(r * 5 + 0.7) + 0.04 * math.cos(r * 9)

def wave_outer(a):
    """Wellenfrmige Strecke (flssig aber wechselnd)"""
    r = math.radians(a)
    return 1.05 + 0.28 * math.sin(r * 1.5) + 0.10 * math.cos(r * 4.0)

def wave_inner(a):
    """Innenverlauf Welle"""
    r = math.radians(a)
    return 0.63 + 0.16 * math.sin(r * 1.5) + 0.06 * math.cos(r * 4.0)

# Maps/Strecken-Konfigurationen
MAPS = {
    "Oval": {
        "name": "Oval",
        "description": "Klassische ovale Strecke  sanfte Kurven, perfekt zum Lernen",
        "unlock_level": 1,
        "config": {
            "type": "oval",
            "outer_mod": oval_outer,
            "inner_mod": oval_inner,
            "outer_base": 40,
            "inner_base": 18,
            "width_factor": 1.0,
            "obstacles": [],
            # Startpositionen
            "start_positions": [
                (25.5, -3.0, 180),
                (32.5, -3.0, 180),
                (25.5, -7.5, 180),
                (32.5, -7.5, 180),
            ],
            # Parkpltze fuer fertige Autos
            "parking_spots": [
                [55, -10],
                [55, 10],
                [-55, -10],
                [-55, 10],
            ],
        }
    },
    "Quad": {
        "name": "Quad",
        "description": "Rechteckiges Layout mit scharfen Ecken  anspruchsvoll!",
        "unlock_level": 2,
        "config": {
            "type": "quad",
            "outer_mod": quad_outer,
            "inner_mod": quad_inner,
            "outer_base": 42,
            "inner_base": 16,
            "width_factor": 0.95,
            "obstacles": [
                {"x": 0, "z": -26, "w": 6, "l": 3.2, "h": 1.0, "color": (0.75, 0.20, 0.20)},
                {"x": 0, "z": 26,  "w": 6, "l": 3.2, "h": 1.0, "color": (0.75, 0.20, 0.20)},
                {"x": -26, "z": 0, "w": 3.2, "l": 6, "h": 1.0, "color": (0.75, 0.20, 0.20)},
                {"x": 26,  "z": 0, "w": 3.2, "l": 6, "h": 1.0, "color": (0.75, 0.20, 0.20)},
            ],
            "start_positions": [
                (25.5, -3.0, 180),
                (32.5, -3.0, 180),
                (25.5, -7.5, 180),
                (32.5, -7.5, 180),
            ],
            "parking_spots": [
                [57, -10],
                [57, 10],
                [-57, -10],
                [-57, 10],
            ],
        }
    },
    "Acht": {
        "name": "Acht",
        "description": "Acht-frmige Lemniskate  zwei elegante Schleifen",
        "unlock_level": 4,
        "config": {
            "type": "eight",
            "outer_mod": eight_outer,
            "inner_mod": eight_inner,
            "outer_base": 38,
            "inner_base": 16,
            "width_factor": 1.1,
            "obstacles": [
                {"x": 0, "z": 0, "w": 5.5, "l": 5.5, "h": 1.2, "color": (0.20, 0.55, 0.85)},
            ],
            "start_positions": [
                (24.0, -3.0, 180),
                (30.0, -3.0, 180),
                (24.0, -7.5, 180),
                (30.0, -7.5, 180),
            ],
            "parking_spots": [
                [53, -10],
                [53, 10],
                [-53, -10],
                [-53, 10],
            ],
        }
    },
    "Dreieck": {
        "name": "Dreieck",
        "description": "Dreieckige Strecke mit drei extremen Kurven  Profi-Challenge!",
        "unlock_level": 3,
        "config": {
            "type": "triangle",
            "outer_mod": triangle_outer,
            "inner_mod": triangle_inner,
            "outer_base": 43,
            "inner_base": 15,
            "width_factor": 0.9,
            "obstacles": [
                {"x": 10, "z": 12, "w": 4.5, "l": 3.0, "h": 1.1, "color": (0.85, 0.60, 0.10)},
                {"x": -10, "z": -12, "w": 4.5, "l": 3.0, "h": 1.1, "color": (0.85, 0.60, 0.10)},
            ],
            "start_positions": [
                (24.5, -3.0, 180),
                (31.5, -3.0, 180),
                (24.5, -7.5, 180),
                (31.5, -7.5, 180),
            ],
            "parking_spots": [
                [58, -10],
                [58, 10],
                [-58, -10],
                [-58, 10],
            ],
        }
    },
    "Chicane": {
        "name": "Chicane",
        "description": "Viele Richtungswechsel + enge Kurven  wer zu frh lenkt, fliegt!",
        "unlock_level": 5,
        "config": {
            "type": "chicane",
            "outer_mod": chicane_outer,
            "inner_mod": chicane_inner,
            "outer_base": 46,
            "inner_base": 14,
            "width_factor": 0.88,
            "obstacles": [
                {"x": -8, "z": -18, "w": 4.0, "l": 3.2, "h": 1.0, "color": (0.60, 0.25, 0.85)},
                {"x":  8, "z": -10, "w": 4.0, "l": 3.2, "h": 1.0, "color": (0.60, 0.25, 0.85)},
                {"x": -8, "z":  -2, "w": 4.0, "l": 3.2, "h": 1.0, "color": (0.60, 0.25, 0.85)},
                {"x":  8, "z":   6, "w": 4.0, "l": 3.2, "h": 1.0, "color": (0.60, 0.25, 0.85)},
                {"x": -8, "z":  14, "w": 4.0, "l": 3.2, "h": 1.0, "color": (0.60, 0.25, 0.85)},
            ],
            "start_positions": [
                (26.5, -3.0, 180),
                (33.5, -3.0, 180),
                (26.5, -7.5, 180),
                (33.5, -7.5, 180),
            ],
            "parking_spots": [
                [60, -10],
                [60, 10],
                [-60, -10],
                [-60, 10],
            ],
        }
    },
    "Slalom": {
        "name": "Slalom",
        "description": "Hindernis-Parcours: Slalom-Tore auf der Runde  sauber fahren!",
        "unlock_level": 6,
        "config": {
            "type": "slalom",
            "outer_mod": wave_outer,
            "inner_mod": wave_inner,
            "outer_base": 45,
            "inner_base": 15,
            "width_factor": 0.9,
            "obstacles": [
                {"x": -12, "z": -22, "w": 3.2, "l": 3.2, "h": 1.0, "color": (0.95, 0.35, 0.10)},
                {"x":  12, "z": -16, "w": 3.2, "l": 3.2, "h": 1.0, "color": (0.95, 0.35, 0.10)},
                {"x": -12, "z": -10, "w": 3.2, "l": 3.2, "h": 1.0, "color": (0.95, 0.35, 0.10)},
                {"x":  12, "z":  -4, "w": 3.2, "l": 3.2, "h": 1.0, "color": (0.95, 0.35, 0.10)},
                {"x": -12, "z":   2, "w": 3.2, "l": 3.2, "h": 1.0, "color": (0.95, 0.35, 0.10)},
                {"x":  12, "z":   8, "w": 3.2, "l": 3.2, "h": 1.0, "color": (0.95, 0.35, 0.10)},
                {"x": -12, "z":  14, "w": 3.2, "l": 3.2, "h": 1.0, "color": (0.95, 0.35, 0.10)},
                {"x":  12, "z":  20, "w": 3.2, "l": 3.2, "h": 1.0, "color": (0.95, 0.35, 0.10)},
            ],
            "start_positions": [
                (26.5, -3.0, 180),
                (33.5, -3.0, 180),
                (26.5, -7.5, 180),
                (33.5, -7.5, 180),
            ],
            "parking_spots": [
                [62, -10],
                [62, 10],
                [-62, -10],
                [-62, 10],
            ],
        }
    },
    "Raeuber & Bulle": {
        "name": "Raeuber & Bulle",
        "description": "Offene quadratische Flche fuer Teamspiel  Gefaengnis in der Mitte, freie Fahrt!",
        "unlock_level": 1,
        "config": {
            "type": "open_square",
            "outer_mod": lambda a: 1.0,  # Keine Modifikation, flache Flche
            "inner_mod": lambda a: 0.0,
            "outer_base": 110,  # Grere Spielflche (Radius)
            "inner_base": 0,
            "width_factor": 1.0,
            "obstacles": [
                {"x": 0, "z": 10, "w": 10, "l": 5, "h": 2, "color": (0.5, 0.5, 0.5)},  # Gefaengnis
                {"x": 0, "z": 5, "w": 2, "l": 2, "h": 1, "color": (0, 1, 0)},  # Freilass-Knopf
                # Mauern fuer Bereiche (am Rand der sichtbaren Map)
                {"x": -110, "z": 0, "w": 2, "l": 220, "h": 3, "color": (0.6, 0.6, 0.6)},  # Vertikale Mauer links
                {"x": 110, "z": 0, "w": 2, "l": 220, "h": 3, "color": (0.6, 0.6, 0.6)},   # Vertikale Mauer rechts
                {"x": 0, "z": -110, "w": 220, "l": 2, "h": 3, "color": (0.6, 0.6, 0.6)},  # Horizontale Mauer unten
                {"x": 0, "z": 110, "w": 220, "l": 2, "h": 3, "color": (0.6, 0.6, 0.6)},   # Horizontale Mauer oueben
                # Zustzliche Hindernisse
                {"x": -55, "z": 55, "w": 6, "l": 6, "h": 2, "color": (0.8, 0.4, 0.4)},  # Rote Box
                {"x": 55, "z": -55, "w": 6, "l": 6, "h": 2, "color": (0.4, 0.8, 0.4)},  # Grne Box
            ],
            "start_positions": [
                (10, 10, 225), (15, 10, 225), (20, 10, 225), (25, 10, 225), (30, 10, 225), (35, 10, 225),  # Raeuber
                (-10, -10, 45), (-15, -10, 45), (-20, -10, 45), (-25, -10, 45), (-30, -10, 45), (-35, -10, 45),  # Bullen
            ],
            "parking_spots": [],
            "item_boxes": [
                {"x": 80, "z": 80},
                {"x": -80, "z": -80},
                {"x": 0, "z": 80},
                {"x": 80, "z": 0},
            ],
        }
    },
    "Insignien-Diebstahl": {
        "name": "Insignien-Diebstahl",
        "description": "Arena-Battle: halte die goldene Insigne, klaue sie zurueck und sammle Punkte.",
        "unlock_level": 1,
        "config": {
            "type": "open_square",
            "outer_mod": lambda a: 1.0,
            "inner_mod": lambda a: 0.0,
            "outer_base": 92,
            "inner_base": 0,
            "width_factor": 1.0,
            "obstacles": [
                {"x": -24, "z": 0, "w": 6, "l": 18, "h": 2.4, "color": (0.48, 0.48, 0.50)},
                {"x": 24, "z": 0, "w": 6, "l": 18, "h": 2.4, "color": (0.48, 0.48, 0.50)},
                {"x": 0, "z": -24, "w": 18, "l": 6, "h": 2.4, "color": (0.56, 0.44, 0.30)},
                {"x": 0, "z": 24, "w": 18, "l": 6, "h": 2.4, "color": (0.56, 0.44, 0.30)},
                {"x": -92, "z": 0, "w": 2, "l": 184, "h": 3.2, "color": (0.62, 0.62, 0.62)},
                {"x": 92, "z": 0, "w": 2, "l": 184, "h": 3.2, "color": (0.62, 0.62, 0.62)},
                {"x": 0, "z": -92, "w": 184, "l": 2, "h": 3.2, "color": (0.62, 0.62, 0.62)},
                {"x": 0, "z": 92, "w": 184, "l": 2, "h": 3.2, "color": (0.62, 0.62, 0.62)},
            ],
            "start_positions": [
                (-12, -54, 0), (-4, -54, 0), (4, -54, 0), (12, -54, 0),
            ],
            "parking_spots": [],
            "item_boxes": [
                {"x": -52, "z": -52},
                {"x": 52, "z": -52},
                {"x": -52, "z": 52},
                {"x": 52, "z": 52},
            ],
        }
    }
}


def _scale_point3(point, scale):
    x, z, rot = point
    return (x * scale, z * scale, rot)


def _scale_point2(point, scale):
    x, z = point
    return [x * scale, z * scale]


def _scale_obstacle(ob, scale):
    out = dict(ob)
    for key in ("x", "z"):
        if key in out:
            out[key] = out[key] * scale
    return out


def _single_row_start_positions(center_radius):
    spacing = 3.6
    z = -3.0
    return [
        (center_radius - spacing * 1.5, z, 180),
        (center_radius - spacing * 0.5, z, 180),
        (center_radius + spacing * 0.5, z, 180),
        (center_radius + spacing * 1.5, z, 180),
    ]


def _scaled_track_mods(old_outer, old_inner, old_outer_mod, old_inner_mod, scale, new_outer_base, new_inner_base):
    def desired(a):
        old_o = old_outer * old_outer_mod(a)
        old_i = old_inner * old_inner_mod(a)
        center = (old_o + old_i) * 0.5 * scale
        width = max(6.0, old_o - old_i)
        return center + width * 0.5, max(1.0, center - width * 0.5)

    def outer_mod(a):
        outer, _ = desired(a)
        return outer / new_outer_base

    def inner_mod(a):
        _, inner = desired(a)
        return inner / new_inner_base

    return outer_mod, inner_mod


def _scale_item_box(box, scale):
    out = dict(box)
    if "x" in out:
        out["x"] = out["x"] * scale
    if "z" in out:
        out["z"] = out["z"] * scale
    return out


def _scale_race_maps(scale=TRACK_SCALE):
    for name, entry in MAPS.items():
        cfg = entry.get("config", {})
        if cfg.get("type") == "open_square":
            continue
        old_outer = float(cfg.get("outer_base", OUTER_R / scale))
        old_inner = float(cfg.get("inner_base", INNER_R / scale))
        old_outer_mod = cfg.get("outer_mod", lambda a: 1.0)
        old_inner_mod = cfg.get("inner_mod", lambda a: 0.65)
        new_outer_base = old_outer * scale
        new_inner_base = old_inner * scale
        cfg["outer_mod"], cfg["inner_mod"] = _scaled_track_mods(
            old_outer, old_inner, old_outer_mod, old_inner_mod, scale, new_outer_base, new_inner_base
        )
        cfg["outer_base"] = new_outer_base
        cfg["inner_base"] = new_inner_base
        start_outer = cfg["outer_base"] * cfg["outer_mod"](0)
        start_inner = cfg["inner_base"] * cfg["inner_mod"](0)
        cfg["start_positions"] = _single_row_start_positions((start_outer + start_inner) * 0.5)
        cfg["parking_spots"] = [_scale_point2(p, scale) for p in cfg.get("parking_spots", [])]
        cfg["obstacles"] = [_scale_obstacle(ob, scale) for ob in cfg.get("obstacles", [])]
        if "item_boxes" in cfg:
            cfg["item_boxes"] = [_scale_item_box(box, scale) for box in cfg.get("item_boxes", [])]


_scale_race_maps()


def make_track_config_for_size(map_name, size_name="klein"):
    entry = MAPS.get(map_name, MAPS["Oval"])
    cfg = dict(entry.get("config", {}))
    factor = TRACK_SIZE_FACTORS.get(str(size_name or "klein").lower(), 1.0)

    cfg["start_positions"] = list(cfg.get("start_positions", START_POSITIONS))
    cfg["parking_spots"] = [list(p) for p in cfg.get("parking_spots", PARKING_SPOTS)]
    cfg["obstacles"] = [dict(ob) for ob in cfg.get("obstacles", [])]
    if "item_boxes" in cfg:
        cfg["item_boxes"] = [dict(box) for box in cfg.get("item_boxes", [])]

    if factor == 1.0:
        return cfg

    if cfg.get("type") == "open_square":
        cfg["outer_base"] = float(cfg.get("outer_base", OUTER_R)) * factor
        cfg["start_positions"] = [_scale_point3(p, factor) for p in cfg.get("start_positions", [])]
        cfg["parking_spots"] = [_scale_point2(p, factor) for p in cfg.get("parking_spots", [])]
        cfg["obstacles"] = [_scale_obstacle(ob, factor) for ob in cfg.get("obstacles", [])]
        if "item_boxes" in cfg:
            cfg["item_boxes"] = [_scale_item_box(box, factor) for box in cfg.get("item_boxes", [])]
        return cfg

    old_outer = float(cfg.get("outer_base", OUTER_R))
    old_inner = float(cfg.get("inner_base", INNER_R))
    old_outer_mod = cfg.get("outer_mod", lambda a: 1.0)
    old_inner_mod = cfg.get("inner_mod", lambda a: 0.65)
    new_outer_base = old_outer * factor
    new_inner_base = old_inner * factor
    cfg["outer_mod"], cfg["inner_mod"] = _scaled_track_mods(
        old_outer, old_inner, old_outer_mod, old_inner_mod, factor, new_outer_base, new_inner_base
    )
    cfg["outer_base"] = new_outer_base
    cfg["inner_base"] = new_inner_base
    start_outer = cfg["outer_base"] * cfg["outer_mod"](0)
    start_inner = cfg["inner_base"] * cfg["inner_mod"](0)
    cfg["start_positions"] = _single_row_start_positions((start_outer + start_inner) * 0.5)
    cfg["parking_spots"] = [_scale_point2(p, factor) for p in cfg.get("parking_spots", [])]
    cfg["obstacles"] = [_scale_obstacle(ob, factor) for ob in cfg.get("obstacles", [])]
    if "item_boxes" in cfg:
        cfg["item_boxes"] = [_scale_item_box(box, factor) for box in cfg.get("item_boxes", [])]
    return cfg
