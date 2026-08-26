from ..runtime import *
from ..paths import LEGACY_DATA_DIR, _wauz_api
from ..core.tuning import STYLE_RATINGS
from ..tracks.maps import CHARACTER_DEFS, MAPS
from ..game.highlights import HighlightRecorder

# 
# DATA & LOGGER
# 
import os, json

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
SCORE_FILE = os.path.join(DATA_DIR, "score.json")
BADGES_FILE = os.path.join(DATA_DIR, "badges.json")


def _copy_legacy_file_once(src, dst):
    try:
        src_path = Path(src)
        dst_path = Path(dst)
        if not src_path.exists() or dst_path.exists():
            return
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_bytes(src_path.read_bytes())
    except Exception:
        pass


def _migrate_legacy_user_data():
    legacy_dir = Path(LEGACY_DATA_DIR)
    if not legacy_dir.exists() or legacy_dir.resolve() == Path(DATA_DIR).resolve():
        return
    _copy_legacy_file_once(legacy_dir / "score.json", SCORE_FILE)
    _copy_legacy_file_once(legacy_dir / "badges.json", BADGES_FILE)
    _copy_legacy_file_once(legacy_dir / "races.json", Path(DATA_DIR) / "races.json")
    try:
        for path in legacy_dir.glob("race_*.json"):
            _copy_legacy_file_once(path, Path(DATA_DIR) / path.name)
    except Exception:
        pass


if os.environ.get("WAUZKART_MIGRATE_ASSET_DATA") == "1":
    _migrate_legacy_user_data()

BADGE_DEFS = [
    {"id": "first_race", "name": "Erstes Rennen", "desc": "Beende ein Rennen oder Match."},
    {"id": "first_highlight", "name": "Highlight-Fan", "desc": "Schau ein Highlight-Video."},
    {"id": "watch_history", "name": "Archiv", "desc": "ffne Alle Rennen."},
    {"id": "first_rb", "name": "Raeuber & Bulle", "desc": "Spiele ein Raeuber & Bulle Match."},
    {"id": "rb_win_blau", "name": "Blau gewinnt", "desc": "Gewinne ein Raeuber & Bulle Match als Team Blau."},
    {"id": "rb_win_rot", "name": "Rot gewinnt", "desc": "Gewinne ein Raeuber & Bulle Match als Team Rot."},
    {"id": "rb_free_someone", "name": "Befreiungsaktion", "desc": "Befreie Raeuber mit dem Knopf."},
    {"id": "rb_catch_robber", "name": "Festnahme", "desc": "Fange einen Raeuber als Bulle."},
    {"id": "insignia_thief", "name": "Insignien-Dieb", "desc": "Gewinne ein Insignien-Diebstahl Match."},
    {"id": "ten_races", "name": "Veteran", "desc": "Beende 10 Rennen/Matches."},
    {"id": "level_5", "name": "Level 5", "desc": "Erreiche Level 5."},

    # Schwieriger (weitere 10)
    {"id": "clean_driver", "name": "Saubere Fahrt", "desc": "Beende ein Rennen ohne einen einzigen Crash."},
    {"id": "overtake_master", "name": "berhol-Meister", "desc": "Schaffe 5 berhol-Manver in einem Rennen."},
    {"id": "close_call_survivor", "name": "Knapp entkommen", "desc": "Habe 3 Close Calls in einem Rennen und beende es trotzdem."},
    {"id": "long_race", "name": "Marathon", "desc": "Beende ein 10-Runden-Rennen."},
    {"id": "highlight_addict", "name": "Highlight-Schtig", "desc": "Schau insgesamt 5 Highlight-Videos."},
    {"id": "historian", "name": "Historiker", "desc": "ffne Alle Rennen insgesamt 5 Mal."},
    {"id": "rb_rescuer", "name": "Retter", "desc": "Befreie insgesamt 3 Mal Raeuber mit dem Knopf."},
    {"id": "rb_hunter", "name": "Kopfgeldjaeger", "desc": "Fange insgesamt 5 Raeuber als Bulle."},
    {"id": "rb_champion", "name": "RB-Champion", "desc": "Gewinne insgesamt 5 Raeuber & Bulle Matches."},
    {"id": "ultimate_level", "name": "Level 10", "desc": "Erreiche Level 10."},
]
BADGE_DEF_BY_ID = {b["id"]: b for b in BADGE_DEFS}


class BadgeStore:
    def __init__(self, unlocked=None, stats=None):
        self.unlocked = dict(unlocked or {})  # badge_id -> {"at": ts}
        self.stats = dict(stats or {})        # free-form counters

    def save(self):
        try:
            data = {
                "unlocked": self.unlocked,
                "stats": self.stats,
            }
            with open(BADGES_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def load():
        if not os.path.exists(BADGES_FILE):
            bs = BadgeStore()
            bs.save()
            return bs
        try:
            with open(BADGES_FILE, "r") as f:
                data = json.load(f)
            return BadgeStore(unlocked=data.get("unlocked", {}), stats=data.get("stats", {}))
        except Exception:
            bs = BadgeStore()
            bs.save()
            return bs

    def is_unlocked(self, badge_id):
        return badge_id in self.unlocked

    def unlock(self, badge_id):
        if badge_id not in BADGE_DEF_BY_ID:
            return False
        if badge_id in self.unlocked:
            return False
        self.unlocked[badge_id] = {"at": time.time()}
        self.save()
        return True

    def inc(self, key, amount=1):
        try:
            self.stats[key] = int(self.stats.get(key, 0)) + int(amount)
        except Exception:
            self.stats[key] = self.stats.get(key, 0) + amount
        self.save()
        return self.stats.get(key, 0)


badge_store = BadgeStore.load()


def _get_main_window_for_badges():
    try:
        app = QApplication.instance()
        if app is None:
            return None
        for w in app.topLevelWidgets():
            if hasattr(w, "show_badge_popup"):
                return w
    except Exception:
        return None
    return None


def unlock_badge(badge_id):
    """Unlock a badge and show popup (bottom-right) if it was newly unlocked."""
    try:
        is_new = badge_store.unlock(badge_id)
    except Exception:
        return False
    if not is_new:
        return False

    # Mirror into global Wauz client badges store (home.py -> Badges tab)
    if _wauz_api is not None:
        try:
            _wauz_api.badges.unlock(badge_id)
        except Exception:
            pass

    b = BADGE_DEF_BY_ID.get(badge_id, {"name": badge_id, "desc": ""})
    mw = _get_main_window_for_badges()
    if mw is not None:
        try:
            mw.show_badge_popup(b.get("name"), b.get("desc"))
        except Exception:
            pass
    return True

UNLOCK_SEQUENCE = [
    ("character", "Fuchs"),
    ("character", "Hase"),
    ("style", "Sport"),
    ("style", "Offroad"),
    ("style", "Retro"),
    ("character", "Baer"),
    ("character", "Bot"),
]

class GlobalProgression:
    def __init__(self, level=1, xp=0, unlocked=None):
        self.level = int(level) if level else 1
        self.xp = int(xp) if xp else 0
        unlocked = unlocked or {}
        self.unlocked_characters = list(unlocked.get("characters", []))
        self.unlocked_styles = list(unlocked.get("styles", []))
        self.unlocked_maps = list(unlocked.get("maps", []))
        self._sanitize()

    def _sanitize(self):
        if self.level < 1:
            self.level = 1
        if self.xp < 0:
            self.xp = 0
        # defaults
        if not self.unlocked_styles:
            self.unlocked_styles = ["Standard"]
        if not self.unlocked_characters:
            self.unlocked_characters = ["Mauz", "Wauz"]
        # ensure valid items still exist
        self.unlocked_styles = [s for s in self.unlocked_styles if s in STYLE_RATINGS] or ["Standard"]
        self.unlocked_characters = [c for c in self.unlocked_characters if c in CHARACTER_DEFS] or ["Mauz", "Wauz"]
        if not self.unlocked_maps:
            self.unlocked_maps = ["Oval"]
        self.unlocked_maps = [m for m in self.unlocked_maps if m in MAPS] or ["Oval"]
        # Ensure maps unlocked by level are always available (migration / consistency)
        self._unlock_maps_by_level()

    def xp_needed_for_next_level(self):
        return int(self.level) * 100

    def save(self):
        data = {
            "level": self.level,
            "xp": self.xp,
            "unlocked": {
                "characters": self.unlocked_characters,
                "styles": self.unlocked_styles,
                "maps": self.unlocked_maps,
            },
        }
        try:
            with open(SCORE_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def load():
        if not os.path.exists(SCORE_FILE):
            gp = GlobalProgression()
            gp.save()
            return gp
        try:
            with open(SCORE_FILE, "r") as f:
                data = json.load(f)
            return GlobalProgression(
                level=data.get("level", 1),
                xp=data.get("xp", 0),
                unlocked=data.get("unlocked", {}),
            )
        except Exception:
            gp = GlobalProgression()
            gp.save()
            return gp

    def get_available_characters(self):
        return [c for c in self.unlocked_characters if c in CHARACTER_DEFS]

    def get_available_styles(self):
        return [s for s in self.unlocked_styles if s in STYLE_RATINGS]

    def get_available_maps(self):
        return [m for m in self.unlocked_maps if m in MAPS]

    def _unlock_maps_by_level(self):
        newly = []
        for map_name, m in MAPS.items():
            need = int(m.get("unlock_level", 1))
            if need <= self.level and map_name not in self.unlocked_maps:
                self.unlocked_maps.append(map_name)
                newly.append(map_name)
        return newly

    def _unlock_next_item(self):
        owned_chars = set(self.unlocked_characters)
        owned_styles = set(self.unlocked_styles)
        for typ, name in UNLOCK_SEQUENCE:
            if typ == "character" and name in CHARACTER_DEFS and name not in owned_chars:
                self.unlocked_characters.append(name)
                return f"Charakter: {name}"
            if typ == "style" and name in STYLE_RATINGS and name not in owned_styles:
                self.unlocked_styles.append(name)
                return f"Auto: {name}"
        return None

    def award_xp_after_race(self, players):
        # XP is global (not per player profile). Award per human participant.
        place_bonus = {1: 100, 2: 70, 3: 50}
        gained = 0
        for pl in players:
            if getattr(pl, "is_ai", False):
                continue
            gained += 20  # participation
            place = getattr(pl, "finish_place", None)
            if place in place_bonus:
                gained += place_bonus[place]

        self.xp += gained
        levelups = []
        while self.xp >= self.xp_needed_for_next_level():
            need = self.xp_needed_for_next_level()
            self.xp -= need
            self.level += 1
            unlocked_list = []
            item = self._unlock_next_item()
            if item:
                unlocked_list.append(item)
            newly_maps = self._unlock_maps_by_level()
            for m in newly_maps:
                unlocked_list.append(f"Map: {m}")
            levelups.append({"level": self.level, "unlocked": unlocked_list})

        self._sanitize()
        self.save()
        return gained, levelups

global_progression = GlobalProgression.load()


def reset_all_progress():
    badge_store.unlocked.clear()
    badge_store.stats.clear()
    badge_store.save()

    fresh_progression = GlobalProgression()
    global_progression.level = fresh_progression.level
    global_progression.xp = fresh_progression.xp
    global_progression.unlocked_characters = list(fresh_progression.unlocked_characters)
    global_progression.unlocked_styles = list(fresh_progression.unlocked_styles)
    global_progression.unlocked_maps = list(fresh_progression.unlocked_maps)
    global_progression.save()

    try:
        RaceLogger._write_races_file([])
    except Exception:
        pass

    try:
        for fn in os.listdir(DATA_DIR):
            if fn.startswith("race_") and fn.endswith(".json"):
                os.remove(os.path.join(DATA_DIR, fn))
    except Exception:
        pass

    return {
        "score": SCORE_FILE,
        "badges": BADGES_FILE,
        "races": RaceLogger.RACES_FILE,
    }

class RaceLogger:
    RACES_FILE = os.path.join(DATA_DIR, "races.json")

    @staticmethod
    def _load_races_file():
        if not os.path.exists(RaceLogger.RACES_FILE):
            return []
        try:
            with open(RaceLogger.RACES_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
        return []

    @staticmethod
    def _write_races_file(races):
        with open(RaceLogger.RACES_FILE, "w") as f:
            json.dump(races, f, indent=2)

    @staticmethod
    def _load_legacy_race_files():
        races = []
        for fn in os.listdir(DATA_DIR):
            if not (fn.startswith("race_") and fn.endswith(".json")):
                continue
            path = os.path.join(DATA_DIR, fn)
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    races.append(data)
            except Exception:
                pass
        return races

    @staticmethod
    def _migrate_legacy_to_races_file_if_needed():
        if os.path.exists(RaceLogger.RACES_FILE):
            return
        legacy = RaceLogger._load_legacy_race_files()
        if not legacy:
            return
        legacy.sort(key=lambda x: x.get("timestamp", 0))
        RaceLogger._write_races_file(legacy)

    @staticmethod
    def save_race(players, recorder, frames, events, map_name=None):
        data = {
            'timestamp': time.time(),
            'map_name': map_name,
            'players': [],
            'frames': frames,
            'frame_numbers': getattr(recorder, 'frame_numbers', []),
            'events': events,
            'crash_frames': getattr(recorder, 'crash_frames', []),
            'overtake_frames': getattr(recorder, 'overtake_frames', []),
            'finish_frames': getattr(recorder, 'finish_frames', []),
            'close_call_frames': getattr(recorder, 'close_call_frames', []),
        }

        if map_name == "Raeuber & Bulle":
            any_pl = players[0] if players else None
            winner_team = next((getattr(p, "rb_winner_team", None) for p in players if getattr(p, "rb_winner_team", None)), None)
            data["rb_winner_team"] = winner_team
            if any_pl is not None:
                try:
                    data["rb_score_blau"] = int(getattr(any_pl, "rb_score_blau", 0))
                    data["rb_score_rot"] = int(getattr(any_pl, "rb_score_rot", 0))
                    data["rb_total_rounds"] = int(getattr(any_pl, "rb_total_rounds", 0) or 0)
                except Exception:
                    pass
        for pl in players:
            pdata = {
                'name': pl.name,
                'is_ai': pl.is_ai,
                'laps': pl.laps,
                'finish_time': pl.finish_time - pl.start_time if pl.finish_time and pl.start_time else None,
                'finish_place': pl.finish_place,
                'color': pl.color,
                'style': getattr(pl, 'style', "Standard"),
                'character': getattr(pl, 'character', None),
            }
            if map_name == "Raeuber & Bulle":
                pdata["rb_color_team"] = getattr(pl, "rb_color_team", None)
                pdata["rb_role"] = getattr(pl, "rb_role", None)
                pdata["rb_winner_team"] = getattr(pl, "rb_winner_team", None)
            if map_name == "Insignien-Diebstahl":
                pdata["insignia_score"] = float(getattr(pl, "insignia_score", 0.0) or 0.0)
                pdata["insignia_winner"] = bool(getattr(pl, "insignia_winner", False))
            data['players'].append(pdata)
        races = RaceLogger._load_races_file()
        races.append(data)
        RaceLogger._write_races_file(races)

    @staticmethod
    def load_all():
        RaceLogger._migrate_legacy_to_races_file_if_needed()
        races = RaceLogger._load_races_file()
        races.sort(key=lambda x: x.get("timestamp", 0) if isinstance(x, dict) else 0)
        return [(f"{RaceLogger.RACES_FILE}#{i}", r) for i, r in enumerate(races) if isinstance(r, dict)]

    @staticmethod
    def get_highscore():
        best = None
        for _,data in RaceLogger.load_all():
            for pl in data.get('players',[]):
                if pl.get('finish_place')==1 and pl.get('finish_time') is not None:
                    if best is None or pl['finish_time'] < best['time']:
                        best = {'name':pl['name'],'time':pl['finish_time']}
        return best

    @staticmethod
    def extract_highlight(data):
        frames = data.get('frames',[])
        total = len(frames)
        if not frames:
            return [], []
        frame_numbers = data.get('frame_numbers') or list(range(total))
        best_index = 0
        last_index = max(0, len(data.get('players', [])) - 1)
        last_place = -1
        for idx, pdata in enumerate(data.get('players', [])):
            place = pdata.get('finish_place')
            if place == 1:
                best_index = idx
            try:
                place_int = int(place)
            except Exception:
                continue
            if place_int >= last_place:
                last_place = place_int
                last_index = idx
        from ..game.highlights import build_cinematic_highlight, build_highlight_indices, remap_events
        cinematic_frames, indices = build_cinematic_highlight(
            frames,
            frame_numbers,
            crash_frames=data.get('crash_frames', []),
            overtake_frames=data.get('overtake_frames', []),
            finish_frames=data.get('finish_frames', []),
            close_call_frames=data.get('close_call_frames', []),
            fps=getattr(HighlightRecorder, "FPS", 30),
            best_index=best_index,
            last_index=last_index,
        )
        if not cinematic_frames:
            indices = build_highlight_indices(
                total,
                frame_numbers,
                crash_frames=data.get('crash_frames', []),
                overtake_frames=data.get('overtake_frames', []),
                finish_frames=data.get('finish_frames', []),
                close_call_frames=data.get('close_call_frames', []),
                fps=getattr(HighlightRecorder, "FPS", 30),
                max_frames=getattr(HighlightRecorder, "MAX_HIGHLIGHT_FRAMES", 3600),
            )
            cinematic_frames = [frames[i] for i in indices]
        return cinematic_frames, remap_events(data.get('events', []), frame_numbers, indices)
