@echo off
setlocal

set "REPO=Fetelker-Nils/wauzkart"
set "PS1_URL=https://github.com/%REPO%/releases/latest/download/install-wauzkart-windows.ps1"
set "PS1_FILE=%TEMP%\install-wauzkart-windows.ps1"

echo.
echo [Wauz Kart] Lade den neuesten Windows-Installer...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%PS1_URL%' -OutFile '%PS1_FILE%' -UseBasicParsing"
if errorlevel 1 (
  echo.
  echo [Wauz Kart] Fehler: Download fehlgeschlagen.
  pause
  exit /b 1
)

echo.
echo [Wauz Kart] Starte Installation oder Update...
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1_FILE%"
if errorlevel 1 (
  echo.
  echo [Wauz Kart] Fehler: Installation fehlgeschlagen.
  pause
  exit /b 1
)

echo.
echo [Wauz Kart] Fertig.
pause
