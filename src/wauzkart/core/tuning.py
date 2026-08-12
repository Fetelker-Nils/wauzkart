from ..runtime import *

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

STYLE_RATINGS = {
    "Standard": (7, 7),
    "Sport":    (9, 7),
    "Offroad":  (6, 9),
    "Retro":    (7, 6),
}

CHARACTER_RATING_MODS = {
    "Mauz":  (0, 1),
    "Wauz":  (1, 0),
    "Fuchs": (2, -1),
    "Hase":  (-1, 2),
    "Baer":   (-2, 1),
    "Bot":   (1, 1),
}

def compute_drive_ratings(style, character):
    base_speed, base_acc = STYLE_RATINGS.get(style, STYLE_RATINGS["Standard"])
    mod_speed, mod_acc = CHARACTER_RATING_MODS.get(character, (0, 0))
    speed = _clamp(base_speed + mod_speed, 1, 10)
    acc = _clamp(base_acc + mod_acc, 1, 10)
    return int(speed), int(acc)

def apply_drive_tuning(pl):
    speed, acc = compute_drive_ratings(getattr(pl, "style", "Standard"), getattr(pl, "character", None))

    # Map ratings (1..10) to actual physics numbers.
    # Defaults were acc=12, max_speed=14; keep similar range but allow clear differences.
    pl.max_speed = 10.0 + speed * 0.8   # 10.8 .. 18.0
    pl.acc = 7.0 + acc * 0.9            # 7.9 .. 16.0

    # Keep boost logic consistent (used by _update_boost_status)
    pl.base_max_speed = pl.max_speed

