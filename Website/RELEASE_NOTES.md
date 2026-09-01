# Wauz Kart v1.0.46

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
- Windows-Installer hat jetzt einen eigenen Wauz-Kart-Look mit Wizard-Banner, Header-Logo und eigenen Setup-Texten
- Raeuber & Bulle spielt jetzt battle-maessiger mit Items, Front-Fangen, Gefaengnis-Slots, Befreiungszaehlern und besserer Battle-KI
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
- Insignien-Diebstahl hat weniger Power-ups, weniger Item-Boxen und eine ruhigere Arena-KI
- Insignien-Arena grafisch verbessert mit Asphaltplatten, Randlichtern, goldenen Battle-Markierungen und besserer Insigne
- Update-Check robuster gemacht, wenn GitHub-API oder Latest-Redirect gecacht/limitiert sind
- Linux-Build fix fuer PyOpenGL Platform-Module wie `OpenGL.platform.egl`
- Linux-Soundfix mit QtMultimedia/GStreamer-Paketen und WAV-Fallback ueber QSoundEffect
- Linux-Starter schuetzt vor `sudo wauzkart`, damit Audio ueber die normale Benutzer-Sitzung laeuft
- zusaetzliche GStreamer-Pakete fuer stabilere Audio-Wiedergabe auf Debian, Ubuntu und Linux Mint
- LAN-Rennen bleiben nach Zieleinlauf aktiv, bis alle Online-Spieler fertig sind
- LAN-Snapshots serialisieren den Sieger stabil als Spieler-Index
- Insignien-Diebstahl zeigt grosse Punkte oben im Rennen
- Item-Auswahl, Angriffswarnung und Zielmeldung wurden als groessere Racing-HUD-Overlays verbessert
- Start-Countdown `3, 2, 1, LOS!` erscheint jetzt gross in der Bildschirmmitte
- Item-Auswahl-HUD wurde nochmal groesser und auffaelliger gemacht
- Linux-Auto-Updates starten den Installer jetzt in einem Terminal statt per direktem `pkexec`
- Linux-Update-Terminal bleibt bei Fehlern offen, damit Passwortabfrage und Fehlermeldungen sichtbar bleiben
- Release-Build sammelt jetzt alle `wauzkart`-Submodule explizit ein, damit `wauzkart.ui.main_window` in Installer-Builds sicher enthalten ist
- Entry-Point enthaelt jetzt einen direkten Import-Smoke-Test fuer `wauzkart.ui.main_window`
- GitHub Actions startet jede gebaute Windows/Linux/macOS-App mit `--smoke-import`, bevor Installer veroeffentlicht werden
- `wauzkart.ui.main_window` ist jetzt zusaetzlich als expliziter Hidden-Import in allen Release-Builds eingetragen
- Der Smoke-Test prueft die Modul-Paketierung ohne GUI/OpenGL-Initialisierung, damit Linux/macOS-Builds nicht am Headless-Runner scheitern
- Windows-Release-Build prueft den gepackten Import mit `--smoke-import`; Linux/macOS bauen mit explizitem Hidden-Import ohne Headless-Starttest
- Windows-Installer wird jetzt mit Inno Setup gebaut statt als zweite PyInstaller-EXE
- Windows-Spiel wird als PyInstaller-Onedir-App verpackt, damit der Installer weniger wie ein selbstentpackendes Malware-Paket wirkt
- Windows-Auto-Update nutzt jetzt normale Inno-Setup-Parameter fuer stille Installation
- Windows-Installer installiert zusaetzlich den `src\wauzkart`-Fallback, falls PyInstaller ein Modul im internen Archiv nicht findet
- Windows-Entry-Point nutzt bei installierten Builds den Ordner der EXE fuer den `src`-Suchpfad
- Windows-Smoke-Test importiert jetzt `wauzkart.app` wirklich, statt nur nach dem Modulnamen zu suchen
- Python-3.11-Syntaxfehler im Linux-Update-Launcher-F-String behoben
- LAN/Online-Host kann jetzt auch `Raeuber & Bulle` und `Insignien-Diebstahl` starten
- LAN-Clients uebernehmen Battle-Settings wie Teams, Runden und Rundentimer vom Host
- Raeuber-&-Bulle-Scores, Rollen, Rundenstatus und Gefangenenstatus werden im LAN-Snapshot gespiegelt
- Insignien-Diebstahl-KI plant jetzt seitliche Umwege, wenn die direkte Linie zum Ziel durch Hindernisse fuehrt
- Windows-Auto-Update startet Wauz Kart nach der Installation wieder sichtbar statt im Hintergrund

## Download

Die Versionen werden als GitHub-Release-Assets hochgeladen:

- `install-wauzkart-windows.exe`
- `install-wauzkart-linux.sh`
- `wauzkart-macos.dmg`
