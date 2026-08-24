import json
import platform
import re
import urllib.request
from urllib.error import HTTPError, URLError

from .. import __version__

REPO = "Fetelker-Nils/wauzkart"
LATEST_API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASE_URL = f"https://github.com/{REPO}/releases/latest"


def _version_tuple(value):
    text = str(value or "").strip().lower()
    if text.startswith("v"):
        text = text[1:]
    parts = []
    for part in text.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits or "0"))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer_version(latest, current=None):
    current = current or __version__
    return _version_tuple(latest) > _version_tuple(current)


def installer_asset_name():
    system = platform.system().lower()
    if system == "windows":
        return "install-wauzkart-windows.exe"
    if system == "darwin":
        return "wauzkart-macos.dmg"
    if system == "linux":
        return "install-wauzkart-linux.sh"
    return ""


def installer_url(asset_name=None, tag=None):
    asset_name = asset_name or installer_asset_name()
    if not asset_name:
        return RELEASE_URL
    if tag:
        return f"https://github.com/{REPO}/releases/download/{tag}/{asset_name}"
    return f"https://github.com/{REPO}/releases/latest/download/{asset_name}"


def _latest_from_api(timeout):
    request = urllib.request.Request(
        LATEST_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "WauzKart-UpdateCheck",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _latest_tag_from_redirect(timeout):
    request = urllib.request.Request(
        RELEASE_URL,
        headers={"User-Agent": "WauzKart-UpdateCheck"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
    match = re.search(r"/releases/tag/([^/?#]+)", final_url or "")
    if not match:
        return None
    return match.group(1)


def check_for_update(timeout=4):
    data = {}
    try:
        data = _latest_from_api(timeout)
    except (HTTPError, URLError, TimeoutError, OSError):
        tag = _latest_tag_from_redirect(timeout)
        data = {
            "tag_name": tag,
            "html_url": f"https://github.com/{REPO}/releases/tag/{tag}" if tag else RELEASE_URL,
            "assets": [],
        }

    tag = str(data.get("tag_name") or "").strip()
    if not tag or not is_newer_version(tag):
        return None

    asset_name = installer_asset_name()
    download_url = installer_url(asset_name, tag)
    for asset in data.get("assets", []) or []:
        if asset.get("name") == asset_name:
            download_url = asset.get("browser_download_url") or download_url
            break

    return {
        "current": __version__,
        "latest": tag.lstrip("v"),
        "tag": tag,
        "url": download_url,
        "release_url": data.get("html_url") or RELEASE_URL,
        "asset": asset_name,
    }
