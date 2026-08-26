import json
import time
from pathlib import Path

from ..paths import DATA_DIR


TERMS_VERSION = "2026-08-26"
LEGAL_FILE = Path(DATA_DIR) / "legal.json"


def _load_legal_data():
    try:
        if LEGAL_FILE.exists():
            return json.loads(LEGAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_legal_data(data):
    LEGAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEGAL_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def has_accepted_terms():
    data = _load_legal_data()
    return str(data.get("accepted_terms_version") or "") == TERMS_VERSION


def accept_terms():
    data = _load_legal_data()
    data["accepted_terms_version"] = TERMS_VERSION
    data["accepted_at"] = time.time()
    _save_legal_data(data)
