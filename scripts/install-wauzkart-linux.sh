#!/usr/bin/env bash
set -euo pipefail

REPO="Fetelker-Nils/wauzkart"
DEB_URL="${WAUZKART_DEB_URL:-https://github.com/${REPO}/releases/latest/download/wauzkart-linux.deb}"
TMP_DIR="$(mktemp -d)"
DEB_FILE="${TMP_DIR}/wauzkart-linux.deb"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

info() {
  printf '\n[Wauz Kart] %s\n' "$1"
}

fail() {
  printf '\n[Wauz Kart] Fehler: %s\n' "$1" >&2
  exit 1
}

if ! command -v sudo >/dev/null 2>&1; then
  fail "sudo wurde nicht gefunden. Bitte installiere sudo oder fuehre die DEB-Datei manuell als Administrator aus."
fi

info "Lade aktuellen Linux-DEB-Installer herunter..."
if command -v curl >/dev/null 2>&1; then
  curl -L --fail --progress-bar "${DEB_URL}" -o "${DEB_FILE}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${DEB_FILE}" "${DEB_URL}"
else
  fail "curl oder wget wird benoetigt."
fi

info "Installiere Wauz Kart und benoetigte Systempakete..."
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y "${DEB_FILE}"
elif command -v apt >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y "${DEB_FILE}"
elif command -v dpkg >/dev/null 2>&1; then
  sudo dpkg -i "${DEB_FILE}" || {
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get install -f -y
    else
      fail "dpkg konnte Abhaengigkeiten nicht automatisch installieren."
    fi
  }
else
  fail "Kein unterstuetzter Paketmanager gefunden. Bitte nutze Debian, Ubuntu, Linux Mint oder installiere die DEB-Datei manuell."
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  sudo update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

info "Fertig. Starte Wauz Kart ueber dein App-Menue oder mit: wauzkart"
