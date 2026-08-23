# Wauz Kart v1.0.10

Aktuelle Website-Release fuer Wauz Kart.

## Enthalten

- Express-Backend fuer Vercel
- Startseite mit Download
- Garage-Seite mit Charakteren und Autos
- kleine Wauz-Kart-Wiki
- API-Routen fuer Health-Check und Wiki-Daten
- Auto-Update Installer fuer Windows, Linux und macOS
- direkte Release-Downloads fuer Windows EXE, Linux AppImage, Linux DEB und macOS DMG
- Windows Auto-Installer als `install-wauzkart-windows.cmd` und `install-wauzkart-windows.ps1`
- Linux Auto-Installer als `install-wauzkart-linux.sh`
- macOS Auto-Installer als `install-wauzkart-macos.sh`
- Linux DEB-Installer fuer Systeme ohne AppImage-Support
- Linux-Build fix fuer PyOpenGL Platform-Module wie `OpenGL.platform.egl`
- Linux-Soundfix mit QtMultimedia/GStreamer-Paketen und WAV-Fallback ueber QSoundEffect
- Linux-Starter schuetzt vor `sudo wauzkart`, damit Audio ueber die normale Benutzer-Sitzung laeuft
- zusaetzliche GStreamer-Pakete fuer stabilere Audio-Wiedergabe auf Debian, Ubuntu und Linux Mint

## Download

Die Versionen werden als GitHub-Release-Assets hochgeladen:

- `wauzkart-windows.exe`
- `install-wauzkart-windows.cmd`
- `install-wauzkart-windows.ps1`
- `install-wauzkart-linux.sh`
- `wauzkart-linux.AppImage`
- `wauzkart-linux.deb`
- `install-wauzkart-macos.sh`
- `wauzkart-macos.dmg`
