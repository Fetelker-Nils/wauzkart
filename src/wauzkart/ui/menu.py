from ..runtime import *
from ..core.rendering import _draw_kart_model, _gl_box_lit, _set_look_at, _set_perspective
from ..core.tuning import STYLE_RATINGS, compute_drive_ratings
from ..data.progression import GlobalProgression, global_progression, reset_all_progress
from ..network.lan import LAN_PORT, discover_hosts
from ..paths import ASSETS_DIR
from ..tracks.maps import *
from .dialogs import ScoreBadgesDialog, TeamSelectionDialog

PANEL_STYLE = """
    QWidget {
        background:#10141b;
        border:2px solid #323b49;
        border-radius:6px;
    }
"""

LABEL_STYLE = """
    QLabel {
        color:#111111;
        background:#f0c84b;
        border:2px solid #fff0a3;
        border-radius:4px;
        padding:8px 16px;
    }
"""

INFO_STYLE = """
    QLabel {
        color:#d7dee8;
        background:transparent;
        border-left:5px solid #f0c84b;
        border-top:none;
        border-right:none;
        border-bottom:none;
        border-radius:4px;
        padding:9px 14px;
    }
"""

COMBO_STYLE = """
    QComboBox {
        background:#161c26;
        color:#ffffff;
        border:2px solid #3d485a;
        border-left:6px solid #f0c84b;
        border-radius:4px;
        padding:7px 18px;
        min-width:200px;
    }
    QComboBox:hover { border-color:#f0c84b; }
    QComboBox QAbstractItemView {
        background:#202633;
        color:#ffffff;
        selection-background-color:#f0c84b;
        selection-color:#111111;
    }
"""

def make_section_label(text):
    label = QLabel(text)
    label.setFont(QFont("Arial", 15, QFont.Bold))
    label.setStyleSheet(LABEL_STYLE)
    label.setAlignment(Qt.AlignCenter)
    label.setFixedWidth(300)
    wrap = QWidget()
    layout = QHBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setAlignment(Qt.AlignCenter)
    wrap.setLayout(layout)
    layout.addWidget(label)
    return wrap, label

def style_action_button(button, bg, hover, pressed, color="#ffffff", border="#00000000"):
    button.setStyleSheet(f"""
        QPushButton {{
            background:{bg};
            color:{color};
            border:2px solid {border};
            border-left:8px solid #f0c84b;
            border-radius:5px;
            padding:16px 24px;
            font-size:16px;
            font-weight:bold;
        }}
        QPushButton:hover {{
            background:{hover};
            border-right:8px solid #f0c84b;
        }}
        QPushButton:pressed {{
            background:{pressed};
            padding-top:18px;
            padding-bottom:14px;
        }}
    """)

def style_race_choice(button, active=False, accent="#f0c84b"):
    if active:
        bg, hover, pressed, fg, edge = accent, "#ffe06a", "#c79522", "#111111", "#fff0a3"
    else:
        bg, hover, pressed, fg, edge = "#151b24", "#222b3a", "#0e131b", "#e8eef7", "#3f4b5e"
    button.setStyleSheet(f"""
        QPushButton {{
            background:{bg};
            color:{fg};
            border:2px solid {edge};
            border-left:8px solid {accent};
            border-radius:3px;
            padding:8px 10px;
            text-align:left;
        }}
        QPushButton:hover {{
            background:{hover};
            border-right:8px solid {accent};
        }}
        QPushButton:pressed {{
            background:{pressed};
        }}
    """)

# 
# Startmen  (mit Spieleranzahl-Auswahl)
# 
class CarPreviewWidget(QOpenGLWidget):
    def __init__(self, parent=None, min_size=340):
        super().__init__(parent)
        self._car_color = (1.0, 1.0, 1.0)
        self._car_style = "Standard"
        self._character = CHARACTER_NAMES[0] if CHARACTER_NAMES else None
        self._rot = 0.0
        self._t = QTimer(self)
        self._t.timeout.connect(self._tick)
        self._t.start(33)  # ~30 FPS
        self.setMinimumSize(min_size, min_size)

    def set_car(self, color, style, character=None):
        if color is not None:
            self._car_color = color
        if style is not None:
            self._car_style = style
        if character is not None:
            self._character = character
        self.update()

    def _tick(self):
        self._rot = (self._rot + 0.6) % 360.0
        self.update()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glShadeModel(GL_SMOOTH)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # Quads in this file are often drawn as single-sided surfaces; culling would hide them
        # depending on winding / camera angle.
        glDisable(GL_CULL_FACE)
        glClearColor(0.09, 0.12, 0.17, 1.0)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        w = max(self.width(), 1)
        h = max(self.height(), 1)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        _set_perspective(45, w / h, 0.1, 100)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        _set_look_at(0, 2.4, 6.2, 0, 0.65, 0, 0, 1, 0)

        _gl_box_lit(-3.2, -0.08, -3.2, 3.2, 0.02, 3.2, (0.08, 0.11, 0.15))
        for z in [-2.4, -1.2, 0.0, 1.2, 2.4]:
            glColor3f(0.22, 0.27, 0.34)
            glBegin(GL_LINES)
            glVertex3f(-3.0, 0.04, z); glVertex3f(3.0, 0.04, z)
            glEnd()
        _gl_box_lit(-2.9, 0.02, 2.7, 2.9, 0.20, 3.0, (0.36, 0.28, 0.08))
        _gl_box_lit(-2.9, 0.02, -3.0, 2.9, 0.20, -2.7, (0.36, 0.28, 0.08))

        glPushMatrix()
        glTranslatef(0, 0.1, 0)
        glRotatef(self._rot, 0, 1, 0)
        _draw_kart_model(self._car_color, self._car_style, self._character, False)
        glPopMatrix()

    def _draw_car(self):
        _draw_kart_model(self._car_color, self._car_style, self._character, False)


class CarOptionsDialog(QDialog):
    def __init__(self, num_humans, parent=None, map_name=None, teams=None):
        super().__init__(parent)
        self.setWindowTitle("Fahrzeug-Auswahl")
        self.setStyleSheet("background:#0b0e14;")
        outer = QVBoxLayout(); outer.setAlignment(Qt.AlignTop); self.setLayout(outer)
        
        self._map_name = map_name
        self._teams = list(teams) if teams else []

        self._slot_names = []
        self._slot_is_ai = []
        num_ai = 4 - num_humans
        for i in range(4):
            if i < num_humans:
                self._slot_names.append(f"Spieler {i+1}")
                self._slot_is_ai.append(False)
            else:
                ai_idx = i - num_humans
                self._slot_names.append(AI_NAMES[ai_idx] if ai_idx < len(AI_NAMES) else f"KI {ai_idx+1}")
                self._slot_is_ai.append(True)

        self._color_values = {
            "rot": (1.0, 0.2, 0.2),
            "grn": (0.2, 0.9, 0.2),
            "blau": (0.2, 0.5, 1.0),
            "gelb": (1.0, 0.7, 0.0),
            "wei": (1.0, 1.0, 1.0),
            "schwarz": (0.1, 0.1, 0.1),
            "violett": (0.8, 0.2, 0.8),
            "cyan": (0.2, 0.9, 0.9),
        }
        self._color_names = list(self._color_values.keys())
        self._available_characters = global_progression.get_available_characters() if global_progression else (CHARACTER_NAMES or [])
        self._styles = global_progression.get_available_styles() if global_progression else ["Standard", "Sport", "Offroad", "Retro"]
        self._enforcing = False

        desc = QLabel("GARAGE: FAHRER, KART UND FARBE")
        desc.setStyleSheet(LABEL_STYLE)
        desc.setAlignment(Qt.AlignCenter)
        desc.setFont(QFont("Arial", 14, QFont.Bold))
        outer.addWidget(desc); outer.addSpacing(10)

        grid_wrap = QWidget()
        grid = QGridLayout(); grid.setSpacing(10); grid_wrap.setLayout(grid)
        outer.addWidget(grid_wrap, stretch=1)

        self.character_combos = []
        self.style_combos = []
        self.color_combos = []
        self.previews = []
        self.info_labels = []

        def mk_combo(items):
            cb = QComboBox()
            cb.addItems(items)
            cb.setStyleSheet(COMBO_STYLE)
            return cb

        for slot in range(4):
            card = QWidget()
            card.setStyleSheet(PANEL_STYLE)
            cl = QVBoxLayout(); cl.setContentsMargins(10,10,10,10); cl.setSpacing(8); card.setLayout(cl)

            title = QLabel(self._slot_names[slot])
            title.setStyleSheet("color:#ffdd55; background:transparent; border:none;")
            title.setFont(QFont("Arial", 13, QFont.Bold))
            cl.addWidget(title)

            row = QWidget()
            rl = QHBoxLayout(); rl.setContentsMargins(0,0,0,0); rl.setSpacing(10); row.setLayout(rl)
            cl.addWidget(row)

            def add_labeled_combo(label, combo):
                box = QWidget()
                bl = QVBoxLayout(); bl.setContentsMargins(0,0,0,0); bl.setSpacing(4); box.setLayout(bl)
                lbl = QLabel(label)
                lbl.setStyleSheet("color:#8fa6c5; background:transparent; border:none;")
                lbl.setFont(QFont("Arial", 9, QFont.Bold))
                bl.addWidget(lbl)
                bl.addWidget(combo)
                return box

            char_combo = mk_combo(self._available_characters if self._available_characters else ["Down"])
            style_combo = mk_combo(self._styles)
            color_combo = mk_combo(self._color_names)

            rl.addWidget(add_labeled_combo("Charakter", char_combo), 0)
            rl.addWidget(add_labeled_combo("Auto", style_combo), 0)
            rl.addWidget(add_labeled_combo("Farbe", color_combo), 0)

            preview = CarPreviewWidget(min_size=210)
            preview.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            rl.addWidget(preview, 1, Qt.AlignRight)

            info = QLabel("")
            info.setStyleSheet(INFO_STYLE)
            info.setFont(QFont("Arial", 9))
            cl.addWidget(info)

            self.character_combos.append(char_combo)
            self.style_combos.append(style_combo)
            self.color_combos.append(color_combo)
            self.previews.append(preview)
            self.info_labels.append(info)

            if self._slot_is_ai[slot]:
                char_combo.setEnabled(False)
                style_combo.setEnabled(False)
                color_combo.setEnabled(False)
            
            # Bei Raeuber & Bulle: Farueben nicht aenderbar
            if self._map_name == "Raeuber & Bulle" and not self._slot_is_ai[slot]:
                color_combo.setEnabled(False)

            char_combo.currentIndexChanged.connect(lambda _=None, s=slot: self._on_changed(s, "character"))
            style_combo.currentIndexChanged.connect(lambda _=None, s=slot: self._on_changed(s, "style"))
            color_combo.currentIndexChanged.connect(lambda _=None, s=slot: self._on_changed(s, "color"))

            grid.addWidget(card, slot // 2, slot % 2)

        btn_row = QWidget()
        bl = QHBoxLayout(); bl.setContentsMargins(0,0,0,0); btn_row.setLayout(bl)
        bl.addStretch(1)
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        style_action_button(btn_ok, "#f0c84b", "#ffe06a", "#c79522", "#111111", "#fff0a3")
        bl.addWidget(btn_ok)
        outer.addWidget(btn_row)

        self.resize(1120, 720)
        self._seed_defaults(num_humans)
        self._recompute_ai_choices()
        self._refresh_previews()

    def _seed_defaults(self, num_humans):
        for slot in range(4):
            if slot < num_humans:
                self.style_combos[slot].setCurrentText(self._styles[0])
                
                # Bei Raeuber & Bulle: Farueben basierend auf Teams setzen
                if self._map_name == "Raeuber & Bulle" and slot < len(self._teams):
                    team = self._teams[slot]
                    if team == "rot":
                        self.color_combos[slot].setCurrentText("rot")
                    elif team == "blau":
                        self.color_combos[slot].setCurrentText("blau")
                else:
                    self.color_combos[slot].setCurrentText(self._color_names[slot % len(self._color_names)])
                if self._available_characters:
                    self.character_combos[slot].setCurrentText(self._available_characters[slot % len(self._available_characters)])

    def _on_changed(self, slot, field):
        if self._enforcing:
            return
        self._enforcing = True
        try:
            if field == "color":
                self._enforce_unique_combo(self.color_combos, slot, self._color_names)
            if field == "character":
                self._enforce_unique_combo(self.character_combos, slot, self._available_characters if self._available_characters else [])
            self._recompute_ai_choices()
            self._refresh_previews()
        finally:
            self._enforcing = False

    def _enforce_unique_combo(self, combos, keep_idx, allowed):
        if not combos or not allowed:
            return
        if keep_idx < 0 or keep_idx >= len(combos):
            keep_idx = 0
        used = set()
        keep_val = combos[keep_idx].currentText()
        used.add(keep_val)
        for idx, cb in enumerate(combos):
            if idx == keep_idx:
                continue
            v = cb.currentText()
            if v in used:
                for cand in allowed:
                    if cand not in used:
                        cb.setCurrentText(cand)
                        v = cand
                        break
            used.add(v)

    def _compute_best_ai_choices(self):
        """Return desired (character, style, color) for each AI slot (best ratings)."""
        used_colors = set()
        used_chars = set()
        for i, is_ai in enumerate(self._slot_is_ai):
            if not is_ai:
                used_colors.add(self.color_combos[i].currentText())
                used_chars.add(self.character_combos[i].currentText())

        free_colors = [c for c in self._color_names if c not in used_colors]
        free_chars = [c for c in (self._available_characters if self._available_characters else []) if c not in used_chars]
        if not free_chars and self._available_characters:
            free_chars = list(self._available_characters)

        def score(style, character):
            sp, ac = compute_drive_ratings(style, character)
            return sp * 1.35 + ac

        choices = {}
        for i, is_ai in enumerate(self._slot_is_ai):
            if not is_ai:
                continue

            candidates_chars = free_chars[:] if free_chars else (list(self._available_characters) if self._available_characters else ["Mauz"])
            candidates_styles = self._styles[:] if self._styles else ["Standard"]

            best = None
            for ch in candidates_chars:
                for st in candidates_styles:
                    sc = score(st, ch)
                    if best is None or sc > best[0]:
                        best = (sc, ch, st)

            if best is None:
                ch = (self._available_characters[0] if self._available_characters else "Mauz")
                st = (self._styles[0] if self._styles else "Standard")
            else:
                _, ch, st = best

            if ch in free_chars:
                free_chars.remove(ch)

            col = free_colors.pop(0) if free_colors else self._color_names[i % len(self._color_names)]
            choices[i] = {"character": ch, "style": st, "color": col}

        return choices

    def _recompute_ai_choices(self):
        choices = self._compute_best_ai_choices()
        for i, is_ai in enumerate(self._slot_is_ai):
            if not is_ai:
                continue
            ch = choices.get(i, {})
            if ch:
                self.character_combos[i].setCurrentText(ch["character"])
                self.style_combos[i].setCurrentText(ch["style"])
                self.color_combos[i].setCurrentText(ch["color"])

        self._enforce_unique_combo(self.color_combos, 0, self._color_names)
        if self._available_characters:
            self._enforce_unique_combo(self.character_combos, 0, self._available_characters)

    def _refresh_previews(self):
        for i in range(4):
            color_name = self.color_combos[i].currentText()
            style_name = self.style_combos[i].currentText()
            char_name = self.character_combos[i].currentText()
            color = self._color_values.get(color_name, (1.0, 1.0, 1.0))
            self.previews[i].set_car(color, style_name, char_name)
            speed, acc = compute_drive_ratings(style_name, char_name)
            self.info_labels[i].setText(f"Geschwindigkeit: {speed}   Beschleunigung: {acc}")

    def get_colors(self):
        return [self._color_values.get(cb.currentText(), (1, 1, 1)) for cb in self.color_combos]

    def get_styles(self):
        return [combo.currentText() for combo in self.style_combos]

    def get_characters(self):
        return [combo.currentText() for combo in self.character_combos]
class TutorialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anleitung")
        self.setStyleSheet("background:#111; color:#fff;")
        self.resize(720, 520)

        outer = QVBoxLayout()
        outer.setContentsMargins(14, 14, 14, 14)
        self.setLayout(outer)

        title = QLabel("ANLEITUNG")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color:#ffcc00;")
        title.setAlignment(Qt.AlignLeft)
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #333; border-radius: 10px; }")
        outer.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout()
        lay.setContentsMargins(14, 14, 14, 14)
        content.setLayout(lay)

        self.lbl = QLabel()
        self.lbl.setWordWrap(True)
        self.lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl.setTextFormat(Qt.RichText)
        self.lbl.setFont(QFont("Arial", 11))
        self.lbl.setStyleSheet("color:#e6e6e6;")
        lay.addWidget(self.lbl)

        btn_close = QPushButton("Schlieen")
        btn_close.setFont(QFont("Arial", 12, QFont.Bold))
        btn_close.setStyleSheet("background:#333;color:#fff;border-radius:8px;padding:10px 20px;")
        btn_close.clicked.connect(self.accept)
        outer.addWidget(btn_close, 0, alignment=Qt.AlignRight)

        self.lbl.setText(self._load_text())

    def _load_text(self):
        p = ASSETS_DIR / "tutorial.json"
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            safe_p = html.escape(str(p))
            return (
                "<div style='font-family:Arial;'>"
                "<h2 style='color:#ffcc00; margin:0 0 8px 0;'>Keine Anleitung gefunden</h2>"
                "<p style='margin:0 0 6px 0; color:#e6e6e6;'>Datei fehlt oder ist kaputt:</p>"
                f"<pre style='background:#0b0b0b; padding:10px; border-radius:8px; color:#ddd;'>{safe_p}</pre>"
                "</div>"
            )

        title = html.escape(str(data.get("title", "Anleitung")))
        parts = [
            "<div style='font-family:Arial;'>",
            f"<h1 style='color:#ffcc00; margin:0 0 10px 0; font-size:22px;'>{title}</h1>",
        ]

        for sec in data.get("sections", []) or []:
            st = sec.get("title")
            if st:
                parts.append(
                    f"<h2 style='color:#ffffff; margin:14px 0 6px 0; font-size:16px;'>"
                    f"{html.escape(str(st))}"
                    "</h2>"
                )

            lines = sec.get("text", []) or []
            if not lines:
                continue

            parts.append("<ul style='margin:0 0 6px 18px; padding:0;'>")
            for t in lines:
                s = "" if t is None else str(t)
                # If the JSON contains literal backslash-n sequences, render them as real line breaks.
                s = s.replace("\\n", "\n")
                s = html.escape(s).replace("\n", "<br>")
                parts.append(f"<li style='margin:4px 0; color:#e6e6e6;'>{s}</li>")
            parts.append("</ul>")

        parts.append("</div>")
        return "".join(parts)

class MenuWidget(QWidget):
    def __init__(self, on_start, on_history=None):
        super().__init__()
        self.on_start = on_start
        self.on_history = on_history
        self.setStyleSheet("background-color:#0b0e14;")
        
        # Haupt-ScrollArea fuer das gesamte Menu
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { background-color:#0b0e14; border: none; }")
        
        # Container-Widget fuer den Inhalt
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color:#0b0e14;")
        lay = QVBoxLayout(); lay.setAlignment(Qt.AlignCenter); content_widget.setLayout(lay)
        
        scroll_area.setWidget(content_widget)
        
        # Hauptlayout fuer dieses Widget
        main_lay = QVBoxLayout(); main_lay.setContentsMargins(0,0,0,0); self.setLayout(main_lay)
        main_lay.addWidget(scroll_area)

        title = QLabel("WAUZ KART")
        title.setFont(QFont("Arial",42,QFont.Bold))
        title.setStyleSheet("""
            QLabel {
                color:#ffdd55;
                background:#151922;
                border:3px solid #f0c84b;
                border-radius:14px;
                padding:18px 70px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        subtitle = QLabel("GARAGE  STRECKE  RENNEN")
        subtitle.setFont(QFont("Arial", 11, QFont.Bold))
        subtitle.setStyleSheet("color:#8fa6c5; letter-spacing:0px;")
        subtitle.setAlignment(Qt.AlignCenter)
        lay.addWidget(subtitle)
        lay.addSpacing(20)

        #  Spieleranzahl 
        players_wrap, players_lbl = make_section_label("FAHRER")
        lay.addWidget(players_wrap)
        lay.addSpacing(8)

        btn_row = QWidget(); br_lay = QHBoxLayout()
        br_lay.setAlignment(Qt.AlignCenter); br_lay.setSpacing(12); btn_row.setLayout(br_lay)
        self.num_buttons = []
        self.selected_players = 2  # Standard

        player_descs = {
            0: ("0 Spieler", "4 KI"),
            1: ("1 Spieler", "3 KI"),
            2: ("2 Spieler", "2 KI"),
            3: ("3 Spieler", "1 KI"),
            4: ("4 Spieler", "Kein KI"),
        }

        for n in [0, 1, 2, 3, 4]:
            btn_text = "NUR KI" if n == 0 else f"{n}  Spieler"
            btn = QPushButton(btn_text)
            btn.setFont(QFont("Arial",13,QFont.Bold))
            btn.setFixedSize(110, 54)
            btn.setCheckable(True)
            btn.setProperty("n", n)
            self.num_buttons.append(btn)
            br_lay.addWidget(btn)

        lay.addWidget(btn_row)
        lay.addSpacing(6)

        # Info-Label was "n Spieler" bedeutet
        self.players_info_lbl = QLabel()
        self.players_info_lbl.setFont(QFont("Arial",12))
        self.players_info_lbl.setStyleSheet(INFO_STYLE)
        self.players_info_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.players_info_lbl)
        lay.addSpacing(10)

        # Steuerungsbersicht
        self.ctrl_lbl = QLabel()
        self.ctrl_lbl.setFont(QFont("Arial",11))
        self.ctrl_lbl.setStyleSheet(INFO_STYLE)
        self.ctrl_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.ctrl_lbl)
        lay.addSpacing(20)

        # Verbinde Buttons
        for btn in self.num_buttons:
            btn.clicked.connect(lambda checked, b=btn: self._select_players(b.property("n")))

        #  KI-Schwierigkeit 
        diff_wrap, diff_lbl = make_section_label("GEGNER-KI")
        lay.addWidget(diff_wrap)
        lay.addSpacing(8)

        #  Rundenanzahl (Rennen) 
        laps_wrap_label, self.laps_lbl = make_section_label("RUNDEN")
        lay.addWidget(laps_wrap_label)
        lay.addSpacing(8)

        self.laps_combo = QComboBox()
        self.laps_combo.addItems([str(i) for i in range(1,11)])
        self.laps_combo.setCurrentText("3")
        self.laps_combo.setFont(QFont("Arial",15))
        self.laps_combo.setStyleSheet(COMBO_STYLE)
        self.laps_combo.setFixedWidth(250)
        self.laps_wrap = QWidget(); lw_lay = QHBoxLayout()
        lw_lay.setAlignment(Qt.AlignCenter); self.laps_wrap.setLayout(lw_lay)
        lw_lay.addWidget(self.laps_combo); lay.addWidget(self.laps_wrap)

        #  Raeuber & Bulle Match-Settings 
        rb_label_wrap, self.rb_settings_lbl = make_section_label("RAEUBER & BULLE")
        lay.addWidget(rb_label_wrap)
        lay.addSpacing(8)

        rb_grid = QWidget()
        rb_gl = QGridLayout()
        rb_gl.setContentsMargins(0, 0, 0, 0)
        rb_gl.setHorizontalSpacing(12)
        rb_gl.setVerticalSpacing(8)
        rb_grid.setLayout(rb_gl)

        def mk_rb_lbl(text):
            l = QLabel(text)
            l.setFont(QFont("Arial", 12))
            l.setStyleSheet("color:#d7dee8;")
            l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return l

        self.rb_rounds_spin = QSpinBox()
        self.rb_rounds_spin.setMinimum(4)
        self.rb_rounds_spin.setMaximum(20)
        self.rb_rounds_spin.setValue(4)
        self.rb_rounds_spin.setFont(QFont("Arial", 13))
        self.rb_rounds_spin.setStyleSheet("background:#202633;color:#fff;border:2px solid #455168;border-radius:8px;padding:6px 10px;")
        self.rb_rounds_spin.setFixedWidth(140)

        self.rb_time_combo = QComboBox()
        # Sekunden pro Runde
        self.rb_time_combo.addItems(["60", "90", "120", "180", "240"])
        self.rb_time_combo.setCurrentText("180")
        self.rb_time_combo.setFont(QFont("Arial", 13))
        self.rb_time_combo.setStyleSheet(COMBO_STYLE)
        self.rb_time_combo.setFixedWidth(140)

        rb_gl.addWidget(mk_rb_lbl("Runden (min 4):"), 0, 0)
        rb_gl.addWidget(self.rb_rounds_spin, 0, 1)
        rb_gl.addWidget(mk_rb_lbl("Zeit pro Runde (s):"), 1, 0)
        rb_gl.addWidget(self.rb_time_combo, 1, 1)

        self.rb_settings_wrap = QWidget()
        rbw_lay = QHBoxLayout()
        rbw_lay.setAlignment(Qt.AlignCenter)
        self.rb_settings_wrap.setLayout(rbw_lay)
        rbw_lay.addWidget(rb_grid)
        lay.addWidget(self.rb_settings_wrap)

        lay.addSpacing(26)

        self.diff_combo = QComboBox()
        self.diff_combo.addItems(list(AI_DIFFICULTIES.keys()))
        self.diff_combo.setCurrentText("Mittel")
        self.diff_combo.setFont(QFont("Arial",15))
        self.diff_combo.setStyleSheet(COMBO_STYLE)
        self.diff_combo.setFixedWidth(250)
        combo_wrap = QWidget(); cw_lay = QHBoxLayout()
        cw_lay.setAlignment(Qt.AlignCenter); combo_wrap.setLayout(cw_lay)
        cw_lay.addWidget(self.diff_combo); lay.addWidget(combo_wrap)
        lay.addSpacing(6)

        self.desc_lbl = QLabel()
        self.desc_lbl.setFont(QFont("Arial",12)); self.desc_lbl.setStyleSheet(INFO_STYLE)
        self.desc_lbl.setAlignment(Qt.AlignCenter); lay.addWidget(self.desc_lbl)
        self.diff_combo.currentTextChanged.connect(self._update_desc)
        self._update_desc(self.diff_combo.currentText())
        lay.addSpacing(12)

        # Option: KI-Sicht im Splitscreen anzeigen (immer 4 Teile)
        self.cb_ai_view = QCheckBox("Computer-Sicht anzeigen (immer 4 Splitscreen-Teile)")
        self.cb_ai_view.setFont(QFont("Arial", 12, QFont.Bold))
        self.cb_ai_view.setStyleSheet("""
            QCheckBox { color:#d7dee8; spacing:10px; }
            QCheckBox::indicator { width:20px; height:20px; }
        """)
        self.cb_ai_view.setChecked(False)
        cb_wrap = QWidget(); cb_lay = QHBoxLayout()
        cb_lay.setAlignment(Qt.AlignCenter); cb_wrap.setLayout(cb_lay)
        cb_lay.addWidget(self.cb_ai_view)
        lay.addWidget(cb_wrap)

        lay.addSpacing(26)

        self._select_players(2)  # Standard

        #  Spielmodus 
        mode_wrap_label, mode_lbl = make_section_label("MODUS")
        lay.addWidget(mode_wrap_label)
        lay.addSpacing(8)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Rennen", "Raeuber & Bulle", "Insignien-Diebstahl"])
        self.mode_combo.setCurrentText("Rennen")
        self.mode_combo.setFont(QFont("Arial",15))
        self.mode_combo.setStyleSheet(COMBO_STYLE)
        self.mode_combo.setFixedWidth(250)
        mode_wrap = QWidget(); mw_lay = QHBoxLayout()
        mw_lay.setAlignment(Qt.AlignCenter); mode_wrap.setLayout(mw_lay)
        mw_lay.addWidget(self.mode_combo); lay.addWidget(mode_wrap)
        lay.addSpacing(6)

        self.mode_desc_lbl = QLabel()
        self.mode_desc_lbl.setFont(QFont("Arial",12)); self.mode_desc_lbl.setStyleSheet(INFO_STYLE)
        self.mode_desc_lbl.setAlignment(Qt.AlignCenter); lay.addWidget(self.mode_desc_lbl)
        self.mode_combo.currentTextChanged.connect(self._update_mode_desc)
        self._update_mode_desc(self.mode_combo.currentText())
        lay.addSpacing(12)

        #  Map-Auswahl 
        map_wrap_label, map_lbl = make_section_label("STRECKE")
        lay.addWidget(map_wrap_label)
        lay.addSpacing(8)

        map_btn_row = QWidget(); mbr_lay = QHBoxLayout()
        mbr_lay.setAlignment(Qt.AlignCenter); mbr_lay.setSpacing(8); map_btn_row.setLayout(mbr_lay)
        self.map_buttons = []
        battle_maps = {"Raeuber & Bulle", "Insignien-Diebstahl"}
        self.available_maps = [m for m in (global_progression.get_available_maps() if global_progression else ["Oval"]) if m not in battle_maps]
        default_map = "Oval" if "Oval" in self.available_maps else (self.available_maps[0] if self.available_maps else "Oval")
        self.selected_map = default_map

        for map_name in MAPS.keys():
            unlocked = map_name in self.available_maps
            btn = QPushButton(map_name if unlocked else f" {map_name}")
            btn.setFont(QFont("Arial",12,QFont.Bold))
            btn.setFixedSize(100, 45)
            btn.setCheckable(True)
            btn.setProperty("map", map_name)
            btn.setEnabled(unlocked)
            self.map_buttons.append(btn)
            mbr_lay.addWidget(btn)
            btn.clicked.connect(lambda checked, b=btn: self._select_map(b.property("map")))

        lay.addWidget(map_btn_row)
        lay.addSpacing(6)

        self.map_desc_lbl = QLabel()
        self.map_desc_lbl.setFont(QFont("Arial",11)); self.map_desc_lbl.setStyleSheet(INFO_STYLE)
        self.map_desc_lbl.setAlignment(Qt.AlignCenter); lay.addWidget(self.map_desc_lbl)
        self._select_map(default_map)  # Standard
        lay.addSpacing(26)

        guide_btn = QPushButton("  ANLEITUNG")
        guide_btn.setFont(QFont("Arial",14,QFont.Bold))
        style_action_button(guide_btn, "#253044", "#31405c", "#1a2230", "#ffffff", "#465879")
        guide_btn.setFixedWidth(260)
        guide_wrap = QWidget(); gw_lay = QHBoxLayout()
        gw_lay.setAlignment(Qt.AlignCenter); guide_wrap.setLayout(gw_lay)
        gw_lay.addWidget(guide_btn); lay.addWidget(guide_wrap)
        guide_btn.clicked.connect(self._show_tutorial)

        lay.addSpacing(12)

        btn = QPushButton("  RENNEN STARTEN")
        btn.setFont(QFont("Arial",20,QFont.Bold))
        style_action_button(btn, "#f0c84b", "#ffe06a", "#c79522", "#111111", "#fff0a3")
        btn.setFixedWidth(320)
        btn_wrap = QWidget(); bw_lay = QHBoxLayout()
        bw_lay.setAlignment(Qt.AlignCenter); btn_wrap.setLayout(bw_lay)
        bw_lay.addWidget(btn); lay.addWidget(btn_wrap)
        btn.clicked.connect(self._start)

        lay.addSpacing(12)

        if on_history:
            hist_btn = QPushButton("  ALLE RENNEN")
            hist_btn.setFont(QFont("Arial",14,QFont.Bold))
            style_action_button(hist_btn, "#b65f22", "#d6782d", "#8f4519", "#ffffff", "#f0a56e")
            hist_btn.setFixedWidth(260)
            hist_wrap = QWidget(); hw_lay = QHBoxLayout()
            hw_lay.setAlignment(Qt.AlignCenter); hist_wrap.setLayout(hw_lay)
            hw_lay.addWidget(hist_btn); lay.addWidget(hist_wrap)
            hist_btn.clicked.connect(on_history)

        lay.addSpacing(10)

        sb_btn = QPushButton("  SCORE & ABZEICHEN")
        sb_btn.setFont(QFont("Arial", 14, QFont.Bold))
        style_action_button(sb_btn, "#28324a", "#344263", "#1f273a", "#ffffff", "#566789")
        sb_btn.setFixedWidth(260)
        sb_wrap = QWidget(); sbw_lay = QHBoxLayout()
        sbw_lay.setAlignment(Qt.AlignCenter); sb_wrap.setLayout(sbw_lay)
        sbw_lay.addWidget(sb_btn); lay.addWidget(sb_wrap)
        sb_btn.clicked.connect(self._show_score_badges)

    def _show_tutorial(self):
        dlg = TutorialDialog(self)
        dlg.exec_()

    def _show_score_badges(self):
        dlg = ScoreBadgesDialog(self)
        dlg.exec_()

    def _select_players(self, n):
        self.selected_players = n
        active_style = """
            QPushButton { background:#f0c84b; color:#111; border-radius:10px;
                          border:2px solid #fff0a3; }
        """
        inactive_style = """
            QPushButton { background:#202633; color:#c9d2df; border-radius:10px;
                          border:2px solid #455168; }
            QPushButton:hover { background:#2c3546; color:#fff; border-color:#71809a; }
        """
        for btn in self.num_buttons:
            btn.setStyleSheet(active_style if btn.property("n") == n else inactive_style)
            btn.setChecked(btn.property("n") == n)

        # Mode-dependent total players (Rennen: 4, Raeuber & Bulle: 12)
        total_players = 4
        try:
            if getattr(self, "mode_combo", None) and self.mode_combo.currentText() == "Raeuber & Bulle":
                total_players = 12
        except Exception:
            total_players = 4
        num_ai = max(0, total_players - n)
        ai_txt = f"{num_ai} KI-Gegner" if num_ai > 0 else "Kein KI  reine Spieler-Runde!"
        self.players_info_lbl.setText(ai_txt)

        # Automatisch Computer-Sicht aktivieren bei NUR KI und nicht aenderbar machen
        if n == 0:
            self.cb_ai_view.setChecked(True)
            self.cb_ai_view.setEnabled(False)
        else:
            self.cb_ai_view.setEnabled(True)

        # Steuerungsbersicht
        ctrl_lines = []
        labels = ["W A S D", "   ", "T G F H", "I K J L"]
        for i in range(n):
            ctrl_lines.append(f" P{i+1}: {labels[i]}")
        if num_ai > 0:
            ctrl_lines.append(f" {num_ai} KI")
        ctrl_lines.append("Schnellstart: Bei '2!' Vorwaerts druecken!")
        self.ctrl_lbl.setText("   |   ".join(ctrl_lines[:4]) + ("\n" + ctrl_lines[-1] if len(ctrl_lines) > 4 else ""))

    def _update_desc(self, name):
        texts = {
            "Leicht": " Langsam, schlenkernd  perfekt zum ueben",
            "Mittel": " Ausgeglichener Gegner",
            "Schwer": " Schnell und praezise  eine echte Herausforderung",
            "Profi":  " Maximale Geschwindigkeit, kaum Fehler  viel Glueck!",
        }
        self.desc_lbl.setText(texts.get(name, ""))

    def _update_mode_desc(self, mode):
        texts = {
            "Rennen": " Klassisches Autorennen mit Runden und Platzierungen",
            "Raeuber & Bulle": " 6 vs 6  Blau/Rot Teams, Rollen wechseln pro Runde, Punkt pro Rundensieg",
            "Insignien-Diebstahl": " Arena-Battle: Insigne halten, Punkte sammeln, durch Treffer klauen",
        }
        self.mode_desc_lbl.setText(texts.get(mode, ""))
        # Update KI/Steuerungs-Info abhngig vom Modus.
        self._select_players(getattr(self, "selected_players", 2))

        is_rb = (mode == "Raeuber & Bulle")
        is_insignia = (mode == "Insignien-Diebstahl")
        # Rennen: Rundenanzahl sichtbar, RB-Settings verstecken
        self.laps_lbl.setVisible(not (is_rb or is_insignia))
        self.laps_wrap.setVisible(not (is_rb or is_insignia))
        # Raeuber & Bulle: Match-Settings sichtbar
        self.rb_settings_lbl.setVisible(is_rb)
        self.rb_settings_wrap.setVisible(is_rb)

    def _select_map(self, map_name):
        if map_name not in self.available_maps:
            map_data = MAPS.get(map_name, {})
            need = int(map_data.get("unlock_level", 1))
            desc = map_data.get("description", "")
            self.map_desc_lbl.setText(f" Gesperrt (ab Level {need})  {desc}")
            return
        self.selected_map = map_name
        active_style = """
            QPushButton { background:#f0c84b; color:#111; border-radius:10px;
                          border:2px solid #fff0a3; }
        """
        inactive_style = """
            QPushButton { background:#202633; color:#c9d2df; border-radius:10px;
                          border:2px solid #455168; }
            QPushButton:hover { background:#2c3546; color:#fff; border-color:#71809a; }
        """
        locked_style = """
            QPushButton { background:#121722; color:#5d6675; border-radius:10px;
                          border:2px solid #222a36; }
        """
        for btn in self.map_buttons:
            if not btn.isEnabled():
                btn.setStyleSheet(locked_style)
                btn.setChecked(False)
            else:
                btn.setStyleSheet(active_style if btn.property("map") == map_name else inactive_style)
                btn.setChecked(btn.property("map") == map_name)
        
        map_data = MAPS.get(map_name, {})
        need = int(map_data.get("unlock_level", 1))
        self.map_desc_lbl.setText(f"Level {need}+  {map_data.get('description','')}")

    def _start(self):
        mode = self.mode_combo.currentText()
        if mode == "Raeuber & Bulle":
            map_name = "Raeuber & Bulle"
            num_humans = self.selected_players  # Spieler drfen in diesem Modus mitfahren
            laps = 0
            diff_name = self.diff_combo.currentText()
            rb_rounds = int(self.rb_rounds_spin.value())
            rb_round_time = int(self.rb_time_combo.currentText())
            
            # Team-Auswahl fuer menschliche Spieler
            teams = None
            if num_humans > 0:
                dlg = TeamSelectionDialog(num_humans, parent=self)
                if dlg.exec_() != QDialog.Accepted:
                    return  # Abbruch
                teams = dlg.get_teams()
        elif mode == "Insignien-Diebstahl":
            map_name = "Insignien-Diebstahl"
            num_humans = self.selected_players
            laps = 0
            diff_name = self.diff_combo.currentText()
            teams = None
            rb_rounds = None
            rb_round_time = int(self.rb_time_combo.currentText())
        else:
            map_name = self.selected_map
            num_humans = self.selected_players
            laps = int(self.laps_combo.currentText())
            diff_name = self.diff_combo.currentText()
            teams = None
            rb_rounds = None
            rb_round_time = None
        
        # zeigen Auswahl-Dialog fuer Fahrzeugfarbe falls menschliche Spieler
        car_colors = None
        characters = None
        if num_humans > 0:
            dlg = CarOptionsDialog(num_humans, parent=self, map_name=map_name, teams=teams)
            if dlg.exec_() == QDialog.Accepted:
                car_colors = dlg.get_colors()
                car_styles = dlg.get_styles()
                characters = dlg.get_characters()
            else:
                return  # abbruch
        else:
            car_styles = []
        self.on_start(num_humans, diff_name, laps, map_name, car_colors, car_styles, characters, self.cb_ai_view.isChecked(), teams, rb_rounds, rb_round_time)


class HoverPlayerButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.hovered = None

    def enterEvent(self, event):
        if self.hovered:
            self.hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.hovered:
            self.hovered(False)
        super().leaveEvent(event)


class HoverCountPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered = None

    def enterEvent(self, event):
        if self.hovered:
            self.hovered(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.hovered:
            self.hovered(False)
        super().leaveEvent(event)


class MenuWidget(QWidget):
    """Three-step game menu: players, mode, garage."""

    def __init__(self, on_start, on_history=None):
        super().__init__()
        self.on_start = on_start
        self.on_history = on_history
        self.selected_players = 1
        self.selected_mode = "Rennen"
        self.selected_map = "Oval"
        self.network_mode = None
        self.active_slot = 0
        self.cb_ai_view = QCheckBox()
        self.cb_ai_view.setChecked(False)
        self.rb_rounds_spin = QSpinBox()
        self.rb_rounds_spin.setValue(4)
        self.rb_time_combo = QComboBox()
        self.rb_time_combo.addItems(["60", "90", "120", "180", "240"])
        self.rb_time_combo.setCurrentText("180")
        self.insignia_time_combo = QComboBox()
        self.insignia_time_combo.addItems(["60", "90", "120", "180", "240"])
        self.insignia_time_combo.setCurrentText("120")
        self.laps_combo = QComboBox()
        self.laps_combo.addItems([str(i) for i in range(1, 11)])
        self.laps_combo.setCurrentText("3")
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(list(AI_DIFFICULTIES.keys()))
        self.diff_combo.setCurrentText("Mittel")

        self._color_values = {
            "rot": (1.0, 0.2, 0.2),
            "gruen": (0.2, 0.9, 0.2),
            "blau": (0.2, 0.5, 1.0),
            "gelb": (1.0, 0.7, 0.0),
            "weiss": (1.0, 1.0, 1.0),
            "schwarz": (0.1, 0.1, 0.1),
            "violett": (0.8, 0.2, 0.8),
            "cyan": (0.2, 0.9, 0.9),
        }
        self._all_characters = list(CHARACTER_NAMES or ["Mauz"])
        self._all_styles = list(STYLE_RATINGS.keys()) or ["Standard"]
        self._battle_maps = {"Raeuber & Bulle", "Insignien-Diebstahl"}
        self._all_maps = [m for m in MAPS.keys() if m not in self._battle_maps] or ["Oval"]
        self._reload_garage_unlocks()

        self.slot_characters = []
        self.slot_styles = []
        self.slot_colors = []
        for i in range(4):
            self.slot_characters.append(self._available_characters[i % len(self._available_characters)])
            self.slot_styles.append(self._styles[i % len(self._styles)])
            self.slot_colors.append(list(self._color_values.values())[i % len(self._color_values)])

        self.setStyleSheet("background:#05070c;")
        self.setAttribute(Qt.WA_StyledBackground, True)
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        self.setLayout(root)
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        self.player_screen = self._build_player_screen()
        self.mode_screen = self._build_mode_screen()
        self.garage_screen = self._build_garage_screen()
        self.team_screen = self._build_team_screen()
        self.stack.addWidget(self.player_screen)
        self.stack.addWidget(self.mode_screen)
        self.stack.addWidget(self.garage_screen)
        self.stack.addWidget(self.team_screen)
        self.stack.setCurrentWidget(self.player_screen)

    def _reload_garage_unlocks(self, reset_slots=False):
        self._available_characters = global_progression.get_available_characters() if global_progression else list(self._all_characters)
        self._styles = global_progression.get_available_styles() if global_progression else list(self._all_styles)
        self.available_maps = [m for m in (global_progression.get_available_maps() if global_progression else list(self._all_maps)) if m not in self._battle_maps]

        self._available_characters = [c for c in self._available_characters if c in self._all_characters] or ["Mauz"]
        self._styles = [s for s in self._styles if s in self._all_styles] or ["Standard"]
        self.available_maps = [m for m in self.available_maps if m in self._all_maps] or ["Oval"]

        if self.selected_map in self._battle_maps:
            pass
        elif self.selected_map not in self.available_maps:
            self.selected_map = "Oval" if "Oval" in self.available_maps else self.available_maps[0]

        if hasattr(self, "slot_characters"):
            for i in range(len(self.slot_characters)):
                if reset_slots or self.slot_characters[i] not in self._available_characters:
                    self.slot_characters[i] = self._available_characters[i % len(self._available_characters)]
        if hasattr(self, "slot_styles"):
            for i in range(len(self.slot_styles)):
                if reset_slots or self.slot_styles[i] not in self._styles:
                    self.slot_styles[i] = self._styles[i % len(self._styles)]

    def _screen(self, stage_name):
        screen = QWidget()
        screen.setObjectName(stage_name)
        screen.setAttribute(Qt.WA_StyledBackground, True)
        screen.setStyleSheet(self._background_style(stage_name))
        layout = QHBoxLayout()
        layout.setContentsMargins(38, 30, 38, 30)
        layout.setSpacing(24)
        screen.setLayout(layout)
        return screen, layout

    def _background_style(self, stage_name):
        names = {
            "players": "background_start.png",
            "mode": "background_mode.png",
            "garage": "background_garage.png",
            "team": "background_team.png",
        }
        image_path = ASSETS_DIR / names.get(stage_name, "")
        if image_path.is_file():
            path = str(image_path).replace("\\", "/")
            return f"""
                QWidget#{stage_name} {{
                    border-image:url("{path}") 0 0 0 0 stretch stretch;
                    background-color:#05070c;
                    color:#ffffff;
                }}
            """
        return f"""
            QWidget#{stage_name} {{
                background-color:#05070c;
                color:#ffffff;
            }}
        """

    def _big_title(self, text):
        label = QLabel(text)
        label.setFont(QFont("Arial", 34, QFont.Bold))
        label.setAlignment(Qt.AlignLeft)
        label.setStyleSheet("color:#ffdd55; background:transparent; border:none;")
        return label

    def _menu_button(self, text, width=260, height=64):
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 15, QFont.Bold))
        btn.setFixedSize(width, height)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        style_action_button(btn, "#202633", "#2f3a50", "#151b26", "#ffffff", "#52647f")
        return btn

    def _choice_button(self, text, width=140, height=56):
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 12, QFont.Bold))
        btn.setFixedSize(width, height)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        style_race_choice(btn, False)
        return btn

    def _quick_icon(self, kind):
        pix = QPixmap(56, 56)
        pix.fill(Qt.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(QColor("#10141c"), 3))
        painter.setBrush(QBrush(QColor("#f0c84b")))

        if kind == "trophy":
            painter.drawRoundedRect(18, 14, 20, 24, 4, 4)
            painter.drawRect(23, 38, 10, 8)
            painter.drawRoundedRect(15, 45, 26, 6, 2, 2)
            painter.drawArc(7, 17, 16, 18, 70 * 16, 200 * 16)
            painter.drawArc(33, 17, 16, 18, -90 * 16, 200 * 16)
        elif kind == "history":
            painter.drawRoundedRect(12, 12, 32, 36, 4, 4)
            painter.setPen(QPen(QColor("#10141c"), 4))
            for y in (21, 30, 39):
                painter.drawLine(19, y, 37, y)
            painter.setBrush(QBrush(QColor("#ff4a4a")))
            painter.drawRect(39, 12, 6, 18)
        else:
            painter.drawEllipse(12, 12, 32, 32)
            painter.setPen(QPen(QColor("#10141c"), 5))
            painter.drawLine(28, 22, 28, 33)
            painter.drawPoint(28, 40)

        painter.end()
        return QIcon(pix)

    def _quick_button(self, text, kind):
        btn = QToolButton()
        btn.setText(text)
        btn.setIcon(self._quick_icon(kind))
        btn.setIconSize(QSize(46, 46))
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setFixedSize(128, 92)
        btn.setFont(QFont("Arial", 8, QFont.Bold))
        btn.setStyleSheet("""
            QToolButton {
                background:rgba(13, 17, 24, 185);
                color:#ffffff;
                border:2px solid #52647f;
                border-top:4px solid #f0c84b;
                border-radius:5px;
                padding:5px;
            }
            QToolButton:hover {
                background:rgba(35, 44, 60, 220);
                border-color:#f0c84b;
            }
            QToolButton:pressed {
                background:rgba(8, 10, 15, 230);
                padding-top:7px;
            }
        """)
        return btn

    def _scroll_panel(self, width):
        scroll = QScrollArea()
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(width)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { background:transparent; border:none; }
            QScrollArea QWidget { background:transparent; }
            QScrollArea > QWidget > QWidget { background:transparent; }
            QScrollBar:vertical { background:#10141c; width:10px; border-radius:5px; }
            QScrollBar::handle:vertical { background:#455168; border-radius:5px; }
        """)
        scroll.viewport().setStyleSheet("background:transparent;")
        body = QWidget()
        body.setStyleSheet("background:transparent;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(10)
        body.setLayout(layout)
        scroll.setWidget(body)
        return scroll, layout

    def _build_player_screen(self):
        screen, layout = self._screen("players")
        left = QWidget()
        left.setStyleSheet("background:transparent; border:none;")
        left.setFixedWidth(680)
        left_lay = QVBoxLayout()
        left_lay.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        left_lay.setSpacing(16)
        left.setLayout(left_lay)
        layout.addWidget(left)
        layout.addStretch(1)

        left_lay.addWidget(self._big_title("WAUZ KART"))
        hint = QLabel("Waehle, wer faehrt.")
        hint.setFont(QFont("Arial", 12, QFont.Bold))
        hint.setStyleSheet(INFO_STYLE)
        left_lay.addWidget(hint)

        ai_btn = self._menu_button("NUR KI", 310, 82)
        solo_btn = self._menu_button("EINZELSPIELER", 310, 82)
        multi_row = QWidget()
        multi_row.setStyleSheet("background:transparent; border:none;")
        multi_lay = QHBoxLayout()
        multi_lay.setContentsMargins(0, 0, 0, 0)
        multi_lay.setSpacing(10)
        multi_lay.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        multi_row.setLayout(multi_lay)
        multi_btn = HoverPlayerButton("MEHRSPIELER")
        multi_btn.setFont(QFont("Arial", 15, QFont.Bold))
        multi_btn.setFixedSize(310, 82)
        style_action_button(multi_btn, "#202633", "#2f3a50", "#151b26", "#ffffff", "#52647f")
        multi_lay.addWidget(multi_btn)
        count_panel = HoverCountPanel()
        count_panel.setStyleSheet("background:transparent; border:none;")
        count_panel.setFixedSize(230, 82)
        count_lay = QHBoxLayout()
        count_lay.setContentsMargins(0, 0, 0, 0)
        count_lay.setSpacing(8)
        count_lay.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        count_panel.setLayout(count_lay)
        count_panel.setVisible(False)
        multi_lay.addWidget(count_panel)

        self._hide_count_timer = QTimer(self)
        self._hide_count_timer.setSingleShot(True)
        self._hide_count_timer.timeout.connect(lambda: count_panel.setVisible(False))

        def set_count_panel(show):
            if show:
                self._hide_count_timer.stop()
                count_panel.setVisible(True)
            else:
                self._hide_count_timer.start(180)

        multi_btn.hovered = set_count_panel
        count_panel.hovered = set_count_panel

        for n in (2, 3, 4):
            count = self._choice_button(str(n), 68, 82)
            count.clicked.connect(lambda checked=False, value=n: self._choose_players(value))
            count_lay.addWidget(count)

        ai_btn.clicked.connect(lambda: self._choose_players(0))
        solo_btn.clicked.connect(lambda: self._choose_players(1))
        multi_btn.clicked.connect(lambda: self._choose_players(2))
        left_lay.addWidget(ai_btn)
        left_lay.addWidget(solo_btn)
        left_lay.addWidget(multi_row)

        lan_row = QWidget()
        lan_row.setStyleSheet("background:transparent; border:none;")
        lan_lay = QHBoxLayout()
        lan_lay.setContentsMargins(0, 0, 0, 0)
        lan_lay.setSpacing(10)
        lan_lay.setAlignment(Qt.AlignLeft)
        lan_row.setLayout(lan_lay)
        host_btn = self._menu_button("LAN HOSTEN", 190, 62)
        join_btn = self._menu_button("LAN BEITRETEN", 210, 62)
        host_btn.clicked.connect(self._choose_lan_host)
        join_btn.clicked.connect(self._join_lan_race)
        lan_lay.addWidget(host_btn)
        lan_lay.addWidget(join_btn)
        left_lay.addWidget(lan_row)

        quick_row = QWidget()
        quick_row.setStyleSheet("background:transparent; border:none;")
        quick_lay = QHBoxLayout()
        quick_lay.setContentsMargins(0, 2, 0, 0)
        quick_lay.setSpacing(10)
        quick_lay.setAlignment(Qt.AlignLeft)
        quick_row.setLayout(quick_lay)
        badge_btn = self._quick_button("ERFOLGE", "trophy")
        badge_btn.clicked.connect(self._show_score_badges)
        quick_lay.addWidget(badge_btn)
        if self.on_history:
            history_btn = self._quick_button("ALLE RENNEN", "history")
            history_btn.clicked.connect(self.on_history)
            quick_lay.addWidget(history_btn)
        help_btn = self._quick_button("HILFE", "help")
        help_btn.clicked.connect(self._show_tutorial)
        quick_lay.addWidget(help_btn)
        reset_btn = self._quick_button("RESET", "reset")
        reset_btn.clicked.connect(self._reset_progress)
        quick_lay.addWidget(reset_btn)
        left_lay.addWidget(quick_row)
        return screen

    def _show_tutorial(self):
        dlg = TutorialDialog(self)
        dlg.exec_()

    def _show_score_badges(self):
        dlg = ScoreBadgesDialog(self)
        dlg.exec_()

    def _style_reset_message_box(self, msg):
        self._style_dialog(msg)

    def _style_dialog(self, dlg):
        dlg.setStyleSheet("""
            QDialog, QMessageBox, QInputDialog {
                background:#10141c;
                color:#ffffff;
            }
            QLabel {
                color:#ffffff;
                background:transparent;
                border:none;
            }
            QLineEdit, QSpinBox {
                background:#f7fbff;
                color:#111111;
                border:2px solid #f0c84b;
                border-radius:5px;
                padding:8px 10px;
                selection-background-color:#f0c84b;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background:#f0c84b;
                border:1px solid #9b6f18;
                width:22px;
            }
            QPushButton {
                background:#f0c84b;
                color:#111111;
                border:2px solid #fff0a3;
                border-bottom:4px solid #9b6f18;
                border-radius:5px;
                padding:9px 20px;
                min-width:96px;
                font-weight:bold;
            }
            QPushButton:hover {
                background:#ffe06a;
            }
            QPushButton:pressed {
                background:#c79522;
                padding-top:11px;
                padding-bottom:7px;
            }
        """)

    def _style_reset_message_box_old(self, msg):
        msg.setStyleSheet("""
            QMessageBox {
                background:#10141c;
                color:#ffffff;
            }
            QMessageBox QLabel {
                color:#ffffff;
                background:transparent;
                border:none;
            }
            QMessageBox QPushButton {
                background:#f0c84b;
                color:#111111;
                border:2px solid #fff0a3;
                border-bottom:4px solid #9b6f18;
                border-radius:5px;
                padding:8px 18px;
                min-width:80px;
            }
            QMessageBox QPushButton:hover {
                background:#ffe06a;
            }
        """)

    def _reset_progress(self):
        msg = QMessageBox(self)
        self._style_reset_message_box(msg)
        msg.setWindowTitle("Alles zuruecksetzen?")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Willst du wirklich alles loeschen?")
        msg.setInformativeText("Erfolge, Score, freigeschaltete Inhalte und alle gespeicherten Rennen werden zurueckgesetzt.")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        if msg.exec_() != QMessageBox.Yes:
            return

        msg2 = QMessageBox(self)
        self._style_reset_message_box(msg2)
        msg2.setWindowTitle("Sicher?")
        msg2.setIcon(QMessageBox.Warning)
        msg2.setText("Das kann nicht rueckgaengig gemacht werden.")
        msg2.setInformativeText("Nochmal bestaetigen, um alles wirklich zu loeschen.")
        msg2.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg2.setDefaultButton(QMessageBox.No)
        if msg2.exec_() != QMessageBox.Yes:
            return

        global global_progression
        reset_all_progress()
        global_progression = GlobalProgression.load()
        self.selected_mode = "Rennen"
        self.active_slot = 0
        self._reload_garage_unlocks(reset_slots=True)
        self._refresh_garage()
        done = QMessageBox(self)
        self._style_reset_message_box(done)
        done.setWindowTitle("Zurueckgesetzt")
        done.setIcon(QMessageBox.Information)
        done.setText("Erfolge, Score und Rennen wurden geloescht.")
        done.setStandardButtons(QMessageBox.Ok)
        done.exec_()

    def _build_mode_screen(self):
        screen, layout = self._screen("mode")
        left = QWidget()
        left.setStyleSheet("background:transparent; border:none;")
        left.setFixedWidth(360)
        left_lay = QVBoxLayout()
        left_lay.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        left_lay.setSpacing(16)
        left.setLayout(left_lay)
        layout.addWidget(left)
        layout.addStretch(1)

        left_lay.addWidget(self._big_title("MODUS"))
        hint = QLabel("Jetzt waehle das Spiel.")
        hint.setFont(QFont("Arial", 12, QFont.Bold))
        hint.setStyleSheet(INFO_STYLE)
        left_lay.addWidget(hint)
        race_btn = self._menu_button("RENNEN", 310, 82)
        rb_btn = self._menu_button("RAEUBER & BULLE", 310, 82)
        insignia_btn = self._menu_button("INSIGNIEN-DIEBSTAHL", 310, 82)
        back_btn = self._menu_button("ZURUECK", 230, 64)
        race_btn.clicked.connect(lambda: self._choose_mode("Rennen"))
        rb_btn.clicked.connect(lambda: self._choose_mode("Raeuber & Bulle"))
        insignia_btn.clicked.connect(lambda: self._choose_mode("Insignien-Diebstahl"))
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.player_screen))
        left_lay.addWidget(race_btn)
        left_lay.addWidget(rb_btn)
        left_lay.addWidget(insignia_btn)
        left_lay.addSpacing(20)
        left_lay.addWidget(back_btn)
        return screen

    def _build_garage_screen(self):
        screen, layout = self._screen("garage")
        left, left_lay = self._scroll_panel(340)
        left_lay.setAlignment(Qt.AlignTop)

        center = QWidget()
        center.setStyleSheet("background:transparent; border:none;")
        center_lay = QGridLayout()
        center_lay.setSpacing(14)
        center.setLayout(center_lay)

        right, right_lay = self._scroll_panel(370)
        right_lay.setAlignment(Qt.AlignTop)

        layout.addWidget(left)
        layout.addWidget(center, 1)
        layout.addWidget(right)

        left_lay.addWidget(self._big_title("CHARAKTER"))
        char_hint = QLabel("PIT CREW")
        char_hint.setFont(QFont("Arial", 10, QFont.Bold))
        char_hint.setStyleSheet(INFO_STYLE)
        left_lay.addWidget(char_hint)
        char_grid = QWidget()
        char_grid.setStyleSheet("background:transparent; border:none;")
        char_lay = QGridLayout()
        char_lay.setContentsMargins(0, 0, 0, 0)
        char_lay.setHorizontalSpacing(8)
        char_lay.setVerticalSpacing(8)
        char_grid.setLayout(char_lay)
        self.character_buttons = []
        for idx, ch in enumerate(self._all_characters):
            btn = self._choice_button(ch, 150, 62)
            btn.clicked.connect(lambda checked=False, value=ch: self._set_character(value))
            self.character_buttons.append(btn)
            char_lay.addWidget(btn, idx // 2, idx % 2)
        left_lay.addWidget(char_grid)
        left_lay.addStretch(1)

        self.previews = []
        for slot, pos in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
            card = QWidget()
            card.setStyleSheet("""
                QWidget {
                    background:#0e131b;
                    border:2px solid #303a49;
                    border-top:4px solid #f0c84b;
                    border-radius:5px;
                }
            """)
            card_lay = QVBoxLayout()
            card_lay.setContentsMargins(8, 8, 8, 8)
            card_lay.setSpacing(6)
            card.setLayout(card_lay)
            title = QPushButton(f"SPIELER {slot + 1}")
            title.setCheckable(True)
            title.clicked.connect(lambda checked=False, value=slot: self._select_slot(value))
            style_race_choice(title, False)
            preview = CarPreviewWidget(min_size=205)
            preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            card_lay.addWidget(title)
            card_lay.addWidget(preview, 1)
            center_lay.addWidget(card, *pos)
            self.previews.append((preview, title))

        right_lay.addWidget(self._big_title("AUTO"))
        car_hint = QLabel("SETUP")
        car_hint.setFont(QFont("Arial", 10, QFont.Bold))
        car_hint.setStyleSheet(INFO_STYLE)
        right_lay.addWidget(car_hint)
        style_grid = QWidget()
        style_grid.setStyleSheet("background:transparent; border:none;")
        style_lay = QGridLayout()
        style_lay.setContentsMargins(0, 0, 0, 0)
        style_lay.setHorizontalSpacing(8)
        style_lay.setVerticalSpacing(8)
        style_grid.setLayout(style_lay)
        self.style_buttons = []
        for idx, style in enumerate(self._all_styles):
            btn = self._choice_button(style, 160, 60)
            btn.clicked.connect(lambda checked=False, value=style: self._set_style(value))
            self.style_buttons.append(btn)
            style_lay.addWidget(btn, idx // 2, idx % 2)
        right_lay.addWidget(style_grid)

        color_label = QLabel("FARBE")
        color_label.setFont(QFont("Arial", 14, QFont.Bold))
        color_label.setStyleSheet(LABEL_STYLE)
        right_lay.addWidget(color_label)
        color_grid = QWidget()
        color_grid.setStyleSheet("background:transparent; border:none;")
        color_lay = QGridLayout()
        color_lay.setContentsMargins(0, 0, 0, 0)
        color_lay.setHorizontalSpacing(8)
        color_lay.setVerticalSpacing(8)
        color_grid.setLayout(color_lay)
        self.color_buttons = []
        for idx, (name, rgb) in enumerate(self._color_values.items()):
            btn = self._choice_button(name.upper(), 160, 48)
            btn.clicked.connect(lambda checked=False, value=rgb: self._set_color(value))
            self.color_buttons.append((btn, rgb))
            color_lay.addWidget(btn, idx // 2, idx % 2)
        right_lay.addWidget(color_grid)

        self.map_panel = QWidget()
        self.map_panel.setStyleSheet("background:transparent; border:none;")
        map_lay = QVBoxLayout()
        map_lay.setContentsMargins(0, 8, 0, 0)
        map_lay.setSpacing(8)
        self.map_panel.setLayout(map_lay)
        map_label = QLabel("STRECKE")
        map_label.setFont(QFont("Arial", 14, QFont.Bold))
        map_label.setStyleSheet(LABEL_STYLE)
        map_lay.addWidget(map_label)
        map_grid = QWidget()
        map_grid.setStyleSheet("background:transparent; border:none;")
        map_grid_lay = QGridLayout()
        map_grid_lay.setContentsMargins(0, 0, 0, 0)
        map_grid_lay.setHorizontalSpacing(8)
        map_grid_lay.setVerticalSpacing(8)
        map_grid.setLayout(map_grid_lay)
        self.map_buttons = []
        for idx, map_name in enumerate(self._all_maps):
            btn = self._choice_button(map_name, 160, 52)
            btn.clicked.connect(lambda checked=False, value=map_name: self._select_map(value))
            self.map_buttons.append(btn)
            map_grid_lay.addWidget(btn, idx // 2, idx % 2)
        map_lay.addWidget(map_grid)
        right_lay.addWidget(self.map_panel)

        settings_label = QLabel("RENN-SETUP")
        settings_label.setFont(QFont("Arial", 14, QFont.Bold))
        settings_label.setStyleSheet(LABEL_STYLE)
        right_lay.addWidget(settings_label)

        setup_grid = QWidget()
        setup_grid.setStyleSheet("background:transparent; border:none;")
        setup_lay = QGridLayout()
        setup_lay.setContentsMargins(0, 0, 0, 0)
        setup_lay.setHorizontalSpacing(8)
        setup_lay.setVerticalSpacing(8)
        setup_grid.setLayout(setup_lay)

        def setup_lbl(text):
            label = QLabel(text)
            label.setFont(QFont("Arial", 10, QFont.Bold))
            label.setStyleSheet("color:#d7dee8; background:transparent; border:none;")
            return label

        self.laps_combo.setFont(QFont("Arial", 12, QFont.Bold))
        self.laps_combo.setStyleSheet(COMBO_STYLE)
        self.laps_combo.setFixedWidth(160)
        self.diff_combo.setFont(QFont("Arial", 12, QFont.Bold))
        self.diff_combo.setStyleSheet(COMBO_STYLE)
        self.diff_combo.setFixedWidth(160)
        setup_lay.addWidget(setup_lbl("RUNDEN"), 0, 0)
        setup_lay.addWidget(self.laps_combo, 0, 1)
        setup_lay.addWidget(setup_lbl("KI"), 1, 0)
        setup_lay.addWidget(self.diff_combo, 1, 1)
        right_lay.addWidget(setup_grid)

        self.rb_setup_panel = QWidget()
        self.rb_setup_panel.setStyleSheet("background:transparent; border:none;")
        rb_setup_lay = QGridLayout()
        rb_setup_lay.setContentsMargins(0, 0, 0, 0)
        rb_setup_lay.setHorizontalSpacing(8)
        rb_setup_lay.setVerticalSpacing(8)
        self.rb_setup_panel.setLayout(rb_setup_lay)
        self.rb_rounds_spin.setMinimum(4)
        self.rb_rounds_spin.setMaximum(20)
        self.rb_rounds_spin.setFont(QFont("Arial", 12, QFont.Bold))
        self.rb_rounds_spin.setStyleSheet("background:#161c26;color:#fff;border:2px solid #3d485a;border-left:6px solid #f0c84b;border-radius:4px;padding:7px 10px;")
        self.rb_rounds_spin.setFixedWidth(160)
        self.rb_time_combo.setFont(QFont("Arial", 12, QFont.Bold))
        self.rb_time_combo.setStyleSheet(COMBO_STYLE)
        self.rb_time_combo.setFixedWidth(160)
        rb_setup_lay.addWidget(setup_lbl("RB-RUNDEN"), 0, 0)
        rb_setup_lay.addWidget(self.rb_rounds_spin, 0, 1)
        rb_setup_lay.addWidget(setup_lbl("ZEIT"), 1, 0)
        rb_setup_lay.addWidget(self.rb_time_combo, 1, 1)
        right_lay.addWidget(self.rb_setup_panel)

        self.insignia_setup_panel = QWidget()
        self.insignia_setup_panel.setStyleSheet("background:transparent; border:none;")
        insignia_setup_lay = QGridLayout()
        insignia_setup_lay.setContentsMargins(0, 0, 0, 0)
        insignia_setup_lay.setHorizontalSpacing(8)
        insignia_setup_lay.setVerticalSpacing(8)
        self.insignia_setup_panel.setLayout(insignia_setup_lay)
        self.insignia_time_combo.setFont(QFont("Arial", 12, QFont.Bold))
        self.insignia_time_combo.setStyleSheet(COMBO_STYLE)
        self.insignia_time_combo.setFixedWidth(160)
        insignia_setup_lay.addWidget(setup_lbl("BATTLE-ZEIT"), 0, 0)
        insignia_setup_lay.addWidget(self.insignia_time_combo, 0, 1)
        right_lay.addWidget(self.insignia_setup_panel)

        right_lay.addStretch(1)

        start = self._menu_button("START", 300, 82)
        style_action_button(start, "#f0c84b", "#ffe06a", "#c79522", "#111111", "#fff0a3")
        start.clicked.connect(self._start)
        back = self._menu_button("ZURUECK", 230, 64)
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.mode_screen))
        right_lay.addWidget(start)
        right_lay.addWidget(back)
        self._refresh_garage()
        return screen

    def _build_team_screen(self):
        screen, layout = self._screen("team")
        left = QWidget()
        left.setStyleSheet("background:transparent; border:none;")
        left.setFixedWidth(360)
        left_lay = QVBoxLayout()
        left_lay.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        left_lay.setSpacing(14)
        left.setLayout(left_lay)
        layout.addWidget(left)

        left_lay.addWidget(self._big_title("TEAM"))
        hint = QLabel("Waehle fuer jeden Spieler ein Team.")
        hint.setFont(QFont("Arial", 12, QFont.Bold))
        hint.setStyleSheet(INFO_STYLE)
        left_lay.addWidget(hint)

        self.team_grid = QWidget()
        self.team_grid.setStyleSheet("background:transparent; border:none;")
        self.team_grid_lay = QGridLayout()
        self.team_grid_lay.setContentsMargins(0, 0, 0, 0)
        self.team_grid_lay.setHorizontalSpacing(10)
        self.team_grid_lay.setVerticalSpacing(10)
        self.team_grid.setLayout(self.team_grid_lay)
        left_lay.addWidget(self.team_grid)

        start = self._menu_button("START", 300, 82)
        style_action_button(start, "#f0c84b", "#ffe06a", "#c79522", "#111111", "#fff0a3")
        start.clicked.connect(lambda: self._finish_start(self._team_choices))
        back = self._menu_button("ZURUECK", 230, 64)
        back.clicked.connect(lambda: self.stack.setCurrentWidget(self.garage_screen))
        left_lay.addSpacing(14)
        left_lay.addWidget(start)
        left_lay.addWidget(back)
        layout.addStretch(1)
        self._team_buttons = []
        self._team_choices = []
        return screen

    def _choose_players(self, n):
        self.network_mode = None
        self.selected_players = int(n)
        self.cb_ai_view.setChecked(n == 0)
        self.active_slot = 0
        self.stack.setCurrentWidget(self.mode_screen)

    def _choose_lan_host(self):
        dlg = QInputDialog(self)
        self._style_dialog(dlg)
        dlg.setWindowTitle("LAN hosten")
        dlg.setLabelText("Spieler im LAN-Rennen:")
        dlg.setInputMode(QInputDialog.IntInput)
        dlg.setIntRange(2, 4)
        dlg.setIntStep(1)
        dlg.setIntValue(2)
        if dlg.exec_() != QDialog.Accepted:
            return
        players = dlg.intValue()
        self.network_mode = "host"
        self.selected_players = int(players)
        self.cb_ai_view.setChecked(False)
        self.active_slot = 0
        self.stack.setCurrentWidget(self.mode_screen)

    def _join_lan_race(self):
        found = discover_hosts(timeout=1.6)
        default_host = found[0].get("ip", "") if found else ""
        if found:
            label = found[0]
            info = QMessageBox(self)
            self._style_dialog(info)
            info.setWindowTitle("LAN Host gefunden")
            info.setText(f"Host gefunden: {label.get('ip')}:{label.get('port', LAN_PORT)}")
            info.setInformativeText("Du kannst diese IP direkt benutzen oder eine andere IP eingeben.")
            info.setStandardButtons(QMessageBox.Ok)
            info.exec_()
        ip_dlg = QInputDialog(self)
        self._style_dialog(ip_dlg)
        ip_dlg.setWindowTitle("LAN beitreten")
        ip_dlg.setLabelText("Host-IP:")
        ip_dlg.setInputMode(QInputDialog.TextInput)
        ip_dlg.setTextValue(default_host)
        if ip_dlg.exec_() != QDialog.Accepted:
            return
        host = ip_dlg.textValue()
        if not str(host).strip():
            return
        try:
            self.on_start(
                1,
                self.diff_combo.currentText(),
                int(self.laps_combo.currentText()),
                self.selected_map,
                self.slot_colors[:1],
                self.slot_styles[:1],
                self.slot_characters[:1],
                False,
                None,
                None,
                None,
                network_config={"mode": "client", "host": str(host).strip(), "port": LAN_PORT},
            )
        except Exception as exc:
            self._show_start_error("LAN Verbindung", "Verbindung konnte nicht hergestellt werden.", exc)

    def _error_text(self, exc):
        text = str(exc or "").strip()
        if text and text.lower() not in ("none", "null"):
            return text
        name = exc.__class__.__name__ if exc is not None else ""
        if name and name not in ("Exception", "RuntimeError"):
            return name
        return "Bitte pruefe, ob ein LAN-Host laeuft und ob Firewall oder Netzwerk den Start blockieren."

    def _show_start_error(self, title, text, exc):
        msg = QMessageBox(self)
        self._style_dialog(msg)
        msg.setWindowTitle(title)
        msg.setText(text)
        detail = self._error_text(exc)
        if detail:
            msg.setInformativeText(detail)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def _choose_mode(self, mode):
        if self.network_mode == "host" and mode in ("Raeuber & Bulle", "Insignien-Diebstahl"):
            msg = QMessageBox(self)
            self._style_dialog(msg)
            msg.setWindowTitle("LAN")
            msg.setText("LAN geht aktuell nur fuer Rennen.")
            msg.setInformativeText("Battle-Modi kommen spaeter im LAN dazu.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            mode = "Rennen"
        self._reload_garage_unlocks()
        self.selected_mode = mode
        if mode == "Raeuber & Bulle":
            self.selected_map = "Raeuber & Bulle"
        elif mode == "Insignien-Diebstahl":
            self.selected_map = "Insignien-Diebstahl"
        elif self.selected_map in self._battle_maps:
            self.selected_map = self.available_maps[0]
        self.map_panel.setVisible(mode == "Rennen")
        self.laps_combo.setVisible(mode == "Rennen")
        self.rb_setup_panel.setVisible(mode == "Raeuber & Bulle")
        if hasattr(self, "insignia_setup_panel"):
            self.insignia_setup_panel.setVisible(mode == "Insignien-Diebstahl")
        self._refresh_garage()
        self.stack.setCurrentWidget(self.garage_screen)

    def _select_slot(self, slot):
        self.active_slot = int(slot)
        self._refresh_garage()

    def _set_character(self, character):
        if character not in self._available_characters:
            return
        self.slot_characters[self.active_slot] = character
        self._refresh_garage()

    def _set_style(self, style):
        if style not in self._styles:
            return
        self.slot_styles[self.active_slot] = style
        self._refresh_garage()

    def _set_color(self, color):
        self.slot_colors[self.active_slot] = color
        self._refresh_garage()

    def _select_map(self, map_name):
        if map_name not in self.available_maps and map_name != "Raeuber & Bulle":
            return
        if map_name != "Raeuber & Bulle":
            self.selected_map = map_name
        self._refresh_garage()

    def _refresh_garage(self):
        self._reload_garage_unlocks()
        self.map_panel.setVisible(self.selected_mode == "Rennen")
        self.laps_combo.setVisible(self.selected_mode == "Rennen")
        if hasattr(self, "rb_setup_panel"):
            self.rb_setup_panel.setVisible(self.selected_mode == "Raeuber & Bulle")
        if hasattr(self, "insignia_setup_panel"):
            self.insignia_setup_panel.setVisible(self.selected_mode == "Insignien-Diebstahl")
        for slot, (preview, title) in enumerate(self.previews):
            preview.set_car(self.slot_colors[slot], self.slot_styles[slot], self.slot_characters[slot])
            visible = slot < max(1, self.selected_players)
            preview.setVisible(visible or self.selected_players == 0)
            title.setVisible(visible or self.selected_players == 0)
            title.setText("KI" if self.selected_players == 0 and slot == 0 else f"SPIELER {slot + 1}")
            title.setChecked(slot == self.active_slot)
            style_race_choice(title, slot == self.active_slot)
        self.active_slot = min(self.active_slot, max(0, self.selected_players - 1))
        for btn in self.character_buttons:
            allowed = btn.text() in self._available_characters
            btn.setEnabled(allowed)
            active = allowed and btn.text() == self.slot_characters[self.active_slot]
            style_race_choice(btn, active)
        for btn in self.style_buttons:
            allowed = btn.text() in self._styles
            btn.setEnabled(allowed)
            active = allowed and btn.text() == self.slot_styles[self.active_slot]
            style_race_choice(btn, active)
        for btn, rgb in self.color_buttons:
            active = rgb == self.slot_colors[self.active_slot]
            style_race_choice(btn, active)
        for btn in self.map_buttons:
            allowed = btn.text() in self.available_maps
            btn.setEnabled(allowed)
            active = allowed and btn.text() == self.selected_map
            style_race_choice(btn, active)

    def _start(self):
        num_humans = self.selected_players
        mode = self.selected_mode
        if mode == "Raeuber & Bulle":
            if num_humans > 0:
                self._prepare_team_screen()
                self.stack.setCurrentWidget(self.team_screen)
                return
            self._finish_start(None)
        elif mode == "Insignien-Diebstahl":
            self._finish_start(None)
        else:
            self._finish_start(None)

    def _prepare_team_screen(self):
        for i in reversed(range(self.team_grid_lay.count())):
            item = self.team_grid_lay.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
        self._team_buttons = []
        self._team_choices = []
        for i in range(max(0, self.selected_players)):
            self._team_choices.append("blau" if i % 2 == 0 else "rot")
            label = QLabel(f"SPIELER {i + 1}")
            label.setFont(QFont("Arial", 12, QFont.Bold))
            label.setStyleSheet(INFO_STYLE)
            blau = self._choice_button("BLAU", 120, 54)
            rot = self._choice_button("ROT", 120, 54)
            blau.clicked.connect(lambda checked=False, idx=i: self._set_team_choice(idx, "blau"))
            rot.clicked.connect(lambda checked=False, idx=i: self._set_team_choice(idx, "rot"))
            self.team_grid_lay.addWidget(label, i, 0)
            self.team_grid_lay.addWidget(blau, i, 1)
            self.team_grid_lay.addWidget(rot, i, 2)
            self._team_buttons.append((blau, rot))
        self._refresh_team_buttons()

    def _set_team_choice(self, idx, team):
        if 0 <= idx < len(self._team_choices):
            self._team_choices[idx] = team
        self._refresh_team_buttons()

    def _refresh_team_buttons(self):
        for idx, pair in enumerate(self._team_buttons):
            blau, rot = pair
            choice = self._team_choices[idx] if idx < len(self._team_choices) else "blau"
            style_race_choice(blau, choice == "blau", "#4aa3ff")
            style_race_choice(rot, choice == "rot", "#ff4a4a")

    def _finish_start(self, teams):
        num_humans = self.selected_players
        mode = self.selected_mode
        if mode == "Raeuber & Bulle":
            map_name = "Raeuber & Bulle"
            laps = 0
            rb_rounds = int(self.rb_rounds_spin.value())
            rb_round_time = int(self.rb_time_combo.currentText())
        elif mode == "Insignien-Diebstahl":
            map_name = "Insignien-Diebstahl"
            laps = 0
            rb_rounds = None
            rb_round_time = int(self.insignia_time_combo.currentText())
        else:
            map_name = self.selected_map
            laps = int(self.laps_combo.currentText())
            rb_rounds = None
            rb_round_time = None
        count = 0 if num_humans == 0 else num_humans
        car_colors = self.slot_colors[:count]
        car_styles = self.slot_styles[:count]
        characters = self.slot_characters[:count]
        try:
            self.on_start(
                num_humans,
                self.diff_combo.currentText(),
                laps,
                map_name,
                car_colors,
                car_styles,
                characters,
                self.cb_ai_view.isChecked(),
                teams,
                rb_rounds,
                rb_round_time,
                network_config={"mode": "host", "port": LAN_PORT} if self.network_mode == "host" else None,
            )
        except Exception as exc:
            title = "LAN Verbindung" if self.network_mode == "host" else "Rennstart"
            self._show_start_error(title, "Rennen konnte nicht gestartet werden.", exc)
