# Wauz Kart v1.0.29

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
- Versionsanzeige unten rechts im Spiel-Fenster
- Auto-Updater mit Download-Fortschritt, Installationsstart und Neustart
- Windows-Installer mit detailliertem Fortschrittsfenster
- Linux-Installer mit Prozent-Ausgaben und Restart-Modus
- LAN-Discovery findet Windows/Linux-Hosts robuster ueber mehrere Broadcast-Adressen
- Online-Rennen wechseln nicht mehr durch kurze Verbindungswackler in Einzelspieler
- Items koennen im Rennen mit Linksklick manuell ausgeloest werden
- Menschliche Spieler-Items feuern nicht mehr automatisch
- Update-Check funktioniert auch, wenn die GitHub-API gerade limitiert ist
- Updates laden jetzt immer den Installer der exakt gefundenen Release-Version
- Erster Spielstart zeigt Nutzungsbedingungen und AGB mit Zustimmung
- Update-Fehler oeffnen einen Hilfe-Dialog mit Hilfe-Seite
- Website hat neue Hilfe- und AGB-Seiten
- Root-Vercel-Build liefert Hilfe, AGB, Robots und Sitemap aus
- Linux DEB-Installer fuer Systeme ohne AppImage-Support
- Neuer Modus `Insignien-Diebstahl` mit Arena-Map, goldener Insigne, Stehlen durch Treffer/Kontakt und Score-Ende
- Linux-Build fix fuer PyOpenGL Platform-Module wie `OpenGL.platform.egl`
- Linux-Soundfix mit QtMultimedia/GStreamer-Paketen und WAV-Fallback ueber QSoundEffect
- Linux-Starter schuetzt vor `sudo wauzkart`, damit Audio ueber die normale Benutzer-Sitzung laeuft
- zusaetzliche GStreamer-Pakete fuer stabilere Audio-Wiedergabe auf Debian, Ubuntu und Linux Mint

## Download

Die Versionen werden als GitHub-Release-Assets hochgeladen:

- `install-wauzkart-windows.exe`
- `install-wauzkart-linux.sh`
- `wauzkart-macos.dmg`
