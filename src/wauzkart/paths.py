import os
import sys
from pathlib import Path

try:
    from _wauz_api import game_data_dir, wauz_api as _wauz_api
except Exception:
    _wauz_api = None

    def game_data_dir(*args, **kwargs):
        return None


if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
LEGACY_DATA_DIR = ASSETS_DIR


def _roaming_data_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Wauzkart"
    return Path(game_data_dir("wauz_cart.py") or (Path.home() / "AppData" / "Roaming" / "Wauzkart"))


DATA_DIR = _roaming_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR = ASSETS_DIR / "sounds"


def data_path(*parts: str) -> str:
    return os.path.join(str(DATA_DIR), *parts)
