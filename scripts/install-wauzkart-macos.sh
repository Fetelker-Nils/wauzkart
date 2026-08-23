#!/usr/bin/env bash
set -euo pipefail

REPO="Fetelker-Nils/wauzkart"
DMG_URL="${WAUZKART_MACOS_DMG_URL:-https://github.com/${REPO}/releases/latest/download/wauzkart-macos.dmg}"
TMP_DIR="$(mktemp -d)"
DMG_FILE="${TMP_DIR}/wauzkart-macos.dmg"
MOUNT_DIR="${TMP_DIR}/mount"

cleanup() {
  if mount | grep -q "${MOUNT_DIR}"; then
    hdiutil detach "${MOUNT_DIR}" -quiet || true
  fi
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

if ! command -v hdiutil >/dev/null 2>&1; then
  fail "hdiutil wurde nicht gefunden. Dieses Skript laeuft nur auf macOS."
fi

if [ -w "/Applications" ]; then
  TARGET_DIR="/Applications"
else
  TARGET_DIR="${HOME}/Applications"
  mkdir -p "${TARGET_DIR}"
fi

info "Lade die neueste macOS-Version herunter..."
if command -v curl >/dev/null 2>&1; then
  curl -L --fail --progress-bar "${DMG_URL}" -o "${DMG_FILE}"
elif command -v wget >/dev/null 2>&1; then
  wget -O "${DMG_FILE}" "${DMG_URL}"
else
  fail "curl oder wget wird benoetigt."
fi

info "Oeffne DMG..."
mkdir -p "${MOUNT_DIR}"
hdiutil attach "${DMG_FILE}" -mountpoint "${MOUNT_DIR}" -nobrowse -quiet

APP_PATH="$(find "${MOUNT_DIR}" -maxdepth 1 -name '*.app' -type d | head -n 1)"
if [ -z "${APP_PATH}" ]; then
  fail "Im DMG wurde keine App gefunden."
fi

APP_NAME="$(basename "${APP_PATH}")"
TARGET_APP="${TARGET_DIR}/${APP_NAME}"

info "Installiere oder aktualisiere ${APP_NAME}..."
rm -rf "${TARGET_APP}"
cp -R "${APP_PATH}" "${TARGET_APP}"
xattr -dr com.apple.quarantine "${TARGET_APP}" >/dev/null 2>&1 || true

info "Fertig. Beim naechsten Ausfuehren dieses Installers wird automatisch auf die neueste Version aktualisiert."
info "Start: ${TARGET_APP}"
