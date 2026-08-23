#!/usr/bin/env bash
set -euo pipefail

TMP_DIR="$(mktemp -d)"
PAYLOAD_FILE="${TMP_DIR}/wauzkart-linux.gz"
BINARY_FILE="${TMP_DIR}/wauzkart"
INSTALL_DIR="/opt/wauzkart"
INSTALL_BIN="${INSTALL_DIR}/wauzkart"
WAIT_PID=""
RESTART_AFTER=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --wait-pid)
      WAIT_PID="${2:-}"
      shift 2
      ;;
    --restart|--auto-update)
      RESTART_AFTER=1
      shift
      ;;
    *)
      shift
      ;;
  esac
done

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

info() {
  printf '\n[Wauz Kart] %s\n' "$1"
}

progress() {
  printf '[Wauz Kart] %s%% - %s\n' "$1" "$2"
}

fail() {
  printf '\n[Wauz Kart] Fehler: %s\n' "$1" >&2
  exit 1
}

wait_for_pid() {
  if [ -z "${WAIT_PID}" ]; then
    return 0
  fi
  progress 8 "Warte, bis die alte Version geschlossen ist..."
  while kill -0 "${WAIT_PID}" >/dev/null 2>&1; do
    sleep 0.5
  done
}

restart_game() {
  if [ "${RESTART_AFTER}" != "1" ]; then
    return 0
  fi
  progress 100 "Starte Wauz Kart neu..."
  if [ -n "${PKEXEC_UID:-}" ] && command -v sudo >/dev/null 2>&1; then
    nohup sudo -u "#${PKEXEC_UID}" env XDG_RUNTIME_DIR="/run/user/${PKEXEC_UID}" DISPLAY="${DISPLAY:-}" WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" XAUTHORITY="${XAUTHORITY:-}" /usr/bin/wauzkart >/dev/null 2>&1 &
    return 0
  fi
  if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ] && command -v sudo >/dev/null 2>&1; then
    USER_ID="$(id -u "${SUDO_USER}" 2>/dev/null || true)"
    nohup sudo -u "${SUDO_USER}" env XDG_RUNTIME_DIR="/run/user/${USER_ID}" DISPLAY="${DISPLAY:-}" WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" XAUTHORITY="${XAUTHORITY:-}" /usr/bin/wauzkart >/dev/null 2>&1 &
    return 0
  fi
  nohup /usr/bin/wauzkart >/dev/null 2>&1 &
}

if ! command -v sudo >/dev/null 2>&1; then
  fail "sudo wurde nicht gefunden. Bitte installiere sudo oder fuehre den Installer als Administrator aus."
fi

if ! command -v base64 >/dev/null 2>&1; then
  fail "base64 wurde nicht gefunden."
fi

if command -v gzip >/dev/null 2>&1; then
  GZIP_CMD="gzip"
else
  fail "gzip wurde nicht gefunden."
fi

progress 3 "Starte Installer..."
wait_for_pid

progress 15 "Installiere benoetigte Systempakete..."
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y libgl1 libegl1 libasound2t64 libpulse0 libpulse-mainloop-glib0 libgstreamer-plugins-base1.0-0 gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-pulseaudio gstreamer1.0-alsa libqt5multimedia5-plugins libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xfixes0 libxkbcommon-x11-0
elif command -v apt >/dev/null 2>&1; then
  sudo apt update
  sudo apt install -y libgl1 libegl1 libasound2t64 libpulse0 libpulse-mainloop-glib0 libgstreamer-plugins-base1.0-0 gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-pulseaudio gstreamer1.0-alsa libqt5multimedia5-plugins libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xfixes0 libxkbcommon-x11-0
else
  info "Kein apt gefunden. Installiere nur die Spiel-Datei; OpenGL/Audio-Pakete muessen eventuell manuell installiert werden."
fi

progress 45 "Entpacke Wauz Kart..."
PAYLOAD_LINE="$(awk '/^__WAUZKART_PAYLOAD_BELOW__$/ { print NR + 1; exit 0; }' "$0")"
if [ -z "${PAYLOAD_LINE}" ]; then
  fail "Installer-Payload wurde nicht gefunden."
fi
tail -n +"${PAYLOAD_LINE}" "$0" | base64 -d > "${PAYLOAD_FILE}"
"${GZIP_CMD}" -dc "${PAYLOAD_FILE}" > "${BINARY_FILE}"
chmod +x "${BINARY_FILE}"

progress 70 "Installiere neue Spiel-Dateien..."
sudo mkdir -p "${INSTALL_DIR}"
sudo install -m 755 "${BINARY_FILE}" "${INSTALL_BIN}"

progress 85 "Erstelle Starter..."
sudo tee /usr/bin/wauzkart >/dev/null <<'SH'
#!/bin/sh
if [ "$(id -u)" = "0" ]; then
  if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ] && command -v sudo >/dev/null 2>&1; then
    USER_ID="$(id -u "$SUDO_USER" 2>/dev/null || true)"
    if [ -n "$USER_ID" ]; then
      exec sudo -u "$SUDO_USER" env XDG_RUNTIME_DIR="/run/user/$USER_ID" DISPLAY="${DISPLAY:-}" WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" XAUTHORITY="${XAUTHORITY:-/home/$SUDO_USER/.Xauthority}" /opt/wauzkart/wauzkart "$@"
    fi
  fi
  echo "Bitte starte Wauz Kart ohne sudo: wauzkart" >&2
fi
exec /opt/wauzkart/wauzkart "$@"
SH
sudo chmod 755 /usr/bin/wauzkart

sudo tee /usr/share/applications/wauzkart.desktop >/dev/null <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Wauz Kart
Exec=wauzkart
Icon=applications-games
Categories=Game;
Terminal=false
DESKTOP

if command -v update-desktop-database >/dev/null 2>&1; then
  sudo update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

restart_game
progress 100 "Fertig."
info "Fertig. Starte Wauz Kart ueber dein App-Menue oder mit: wauzkart"
info "Wichtig: Zum Spielen kein sudo benutzen. sudo ist nur fuer die Installation noetig."
exit 0

__WAUZKART_PAYLOAD_BELOW__
