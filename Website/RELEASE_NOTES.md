# Wauz Kart v1.0.19

Aktuelle Website-Release fuer Wauz Kart.

## Enthalten

- Express-Backend fuer Vercel
- Startseite mit Download
- Garage-Seite mit Charakteren und Autos
- kleine Wauz-Kart-Wiki
- API-Routen fuer Health-Check und Wiki-Daten
- Windows EXE-Installer als `install-wauzkart-windows.exe`
- Linux SH-Installer als `install-wauzkart-linux.sh`
- macOS DMG als `wauzkart-macos.dmg`
- Update-Check beim Spielstart mit passendem Installer-Link fuer das aktuelle System
- bessere Rennstart- und LAN-Fehlermeldungen ohne leere Null/None-Texte
- WSL/Ubuntu-Fix: OpenGL-Projektion ohne GLU
- WSL/Ubuntu-Fix: alle GLU-Kameraaufrufe entfernt und Linux-Updates werden direkt heruntergeladen
- Audio ist auch unter WSL wieder standardmaessig aktiv
- LAN-Rennen zeigen Statistiken erst, wenn alle Online-Spieler im Ziel sind
- Linux DEB-Installer fuer Systeme ohne AppImage-Support
- Linux-Build fix fuer PyOpenGL Platform-Module wie `OpenGL.platform.egl`
- Linux-Soundfix mit QtMultimedia/GStreamer-Paketen und WAV-Fallback ueber QSoundEffect
- Linux-Starter schuetzt vor `sudo wauzkart`, damit Audio ueber die normale Benutzer-Sitzung laeuft
- zusaetzliche GStreamer-Pakete fuer stabilere Audio-Wiedergabe auf Debian, Ubuntu und Linux Mint

## Download

Die Versionen werden als GitHub-Release-Assets hochgeladen:

- `install-wauzkart-windows.exe`
- `install-wauzkart-linux.sh`
- `wauzkart-macos.dmg`
