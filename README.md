# Wauz Kart

Eigenes Projekt fuer Wauz Kart.

## Struktur

```text
WauzKart/
  assets/                 Spieldaten, Sounds, Icon, Web-Dateien
  src/wauzkart/           Python-Package
    app.py                Startpunkt
    runtime.py            Gemeinsame Imports fuer Qt, OpenGL und Standardbibliothek
    paths.py              Projekt-, Asset- und Datenpfade
    audio/                Musik und Sound
    core/                 Rendering-Helfer und Fahrwerte
    data/                 Scores, Badges, Progression, Rennhistorie
    game/                 Spieler, Items, Partikel, Rennen, Highlights
    tracks/               Maps, Streckenformen und Startpositionen
    ui/                   Menues, Screens, Widgets und Dialoge
    __main__.py           Start via python -m wauzkart
  wauz_kart.py            Kompatibler Starter
  start_wauzkart.bat      Windows-Starter
  requirements.txt        Abhaengigkeiten
  pyproject.toml          Projekt-Metadaten
```

## Starten

```bat
start_wauzkart.bat
```

Oder direkt:

```bat
python wauz_kart.py
```

Falls Abhaengigkeiten fehlen:

```bat
pip install -r requirements.txt
```
