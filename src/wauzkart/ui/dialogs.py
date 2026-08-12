from ..runtime import *
from ..data.progression import BADGE_DEFS, RaceLogger, badge_store, global_progression

# 
# Score & Abzeichen
# 
class ScoreBadgesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Score & Abzeichen")
        self.setStyleSheet("background:#111;")
        self.setFixedSize(720, 620)

        outer = QVBoxLayout()
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(10)
        self.setLayout(outer)

        title = QLabel("  Score & Abzeichen")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setStyleSheet("color:#ffcc00;")
        title.setAlignment(Qt.AlignCenter)
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:#111; }")
        outer.addWidget(scroll, 1)

        content = QWidget()
        content.setStyleSheet("background:#111;")
        scroll.setWidget(content)
        lay = QVBoxLayout()
        lay.setAlignment(Qt.AlignTop)
        lay.setSpacing(14)
        content.setLayout(lay)

        def section_header(text):
            h = QLabel(text)
            h.setFont(QFont("Arial", 14, QFont.Bold))
            h.setStyleSheet("color:#ffffff;")
            h.setAlignment(Qt.AlignLeft)
            return h

        # Score / Progress
        lay.addWidget(section_header("  Score"))
        gp = GlobalProgression.load() if "GlobalProgression" in globals() else None
        if gp is None:
            gp = global_progression

        level = int(getattr(gp, "level", 1) or 1) if gp else 1
        xp = int(getattr(gp, "xp", 0) or 0) if gp else 0
        need = int(gp.xp_needed_for_next_level() if gp else (level * 100))
        races_finished = int(badge_store.stats.get("races_finished", 0)) if "badge_store" in globals() else 0

        hs = RaceLogger.get_highscore() if "RaceLogger" in globals() else None
        hs_txt = ""
        if hs and isinstance(hs, dict):
            try:
                hs_txt = f"{hs.get('time', 0):.2f}s von {hs.get('name', 'Down')}"
            except Exception:
                hs_txt = ""

        score_lbl = QLabel(
            f"Level: {level}\n"
            f"XP: {xp} / {need}\n"
            f"Beendete Rennen/Matches: {races_finished}\n"
            f"Bestzeit (Rennen): {hs_txt}"
        )
        score_lbl.setFont(QFont("Courier", 12))
        score_lbl.setStyleSheet("color:#dddddd; background:#161616; border:1px solid #333; border-radius:10px; padding:10px;")
        score_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lay.addWidget(score_lbl)

        # Badges
        lay.addWidget(section_header(f"  Abzeichen ({len(BADGE_DEFS)})"))
        for b in BADGE_DEFS:
            bid = b.get("id")
            name = b.get("name", bid)
            desc = b.get("desc", "")
            unlocked = bid in badge_store.unlocked
            icon = "" if unlocked else ""
            col = "#88ff88" if unlocked else "#aaaaaa"

            when_txt = ""
            if unlocked:
                try:
                    ts = float(badge_store.unlocked.get(bid, {}).get("at", 0.0) or 0.0)
                    if ts > 0:
                        when_txt = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))
                except Exception:
                    when_txt = ""

            row = QWidget()
            row_l = QVBoxLayout()
            row_l.setContentsMargins(12, 10, 12, 10)
            row_l.setSpacing(4)
            row.setLayout(row_l)
            row.setStyleSheet("background:#161616; border:1px solid #333; border-radius:10px;")

            line1 = QLabel(f"{icon}  {name}")
            line1.setFont(QFont("Arial", 12, QFont.Bold))
            line1.setStyleSheet(f"color:{col};")
            row_l.addWidget(line1)

            line2_txt = desc
            if when_txt:
                line2_txt += f"   (freigeschaltet: {when_txt})"
            line2 = QLabel(line2_txt)
            line2.setWordWrap(True)
            line2.setFont(QFont("Arial", 10))
            line2.setStyleSheet("color:#dddddd;")
            row_l.addWidget(line2)

            lay.addWidget(row)

        lay.addStretch(1)

        btn_row = QWidget()
        br = QHBoxLayout()
        br.setContentsMargins(0, 0, 0, 0)
        br.setSpacing(10)
        btn_row.setLayout(br)

        btn_close = QPushButton(" Schlieen")
        btn_close.setFont(QFont("Arial", 12, QFont.Bold))
        btn_close.setStyleSheet("background:#333;color:#fff;border-radius:8px;padding:10px 18px;")
        btn_close.clicked.connect(self.accept)
        br.addStretch(1)
        br.addWidget(btn_close)
        outer.addWidget(btn_row)

# 
# Tutorial-Dialog
# 
class TutorialDialogLegacy(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tutorial - Wauz Kart")
        self.setStyleSheet("background:#111;")
        self.setFixedSize(600, 500)
        lay = QVBoxLayout(); self.setLayout(lay)

        title = QLabel("  Tutorial")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color:#ffcc00;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        lay.addSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:#111; border:none;")
        content = QWidget()
        content_lay = QVBoxLayout()
        content.setLayout(content_lay)

        tutorial_text = """
        <h2 style="color:#ffcc00;">Willkommen bei Wauz Kart!</h2>
        <p style="color:#ddd; font-size:14px;">
        Wauz Kart ist ein lustiges Rennspiel fuer 1-4 Spieler. Hier sind die Grundlagen:
        </p>

        <h3 style="color:#ffaa00;">Steuerung:</h3>
        <ul style="color:#ddd; font-size:14px;">
        <li><b>Spieler 1:</b> W A S D (Beschleunigen, Links, Bremsen, Rechts)</li>
        <li><b>Spieler 2:</b> Pfeiltasten (   )</li>
        <li><b>Spieler 3:</b> T G F H</li>
        <li><b>Spieler 4:</b> I K J L</li>
        </ul>

        <h3 style="color:#ffaa00;">Spielmodi:</h3>
        <ul style="color:#ddd; font-size:14px;">
        <li><b>Normales Rennen:</b> Sammle alle Checkpoints und fahre die meisten Runden.</li>
        <li><b> Raeuber & Bulle:</b> Waehle dein Team! Bullen fangen Raeuber, Raeuber entkommen.</li>
        <li><b>Verschiedene Maps:</b> Oval, Achter, Stadt, etc. - jede mit eigenen Herausforderungen.</li>
        </ul>

        <h3 style="color:#ffaa00;">Tipps:</h3>
        <ul style="color:#ddd; font-size:14px;">
        <li>Drifte um Kurven fuer Extra-Speed!</li>
        <li>Sammle Power-Ups fuer Vorteile.</li>
        <li>Schliee Runden ab, um zu gewinnen.</li>
        <li>In Raeuber & Bulle: Arbeite mit deinem Team zusammen!</li>
        </ul>

        <h3 style="color:#ffaa00;">Level-System:</h3>
        <p style="color:#ddd; font-size:14px;">
        Gewinne Rennen, um XP zu sammeln und aufzusteigen. Hhere Levels schalten neue Maps und Items frei!
        </p>

        <p style="color:#aaa; font-size:12px; text-align:center;">
        Viel Spa beim Spielen! 
        </p>
        """

        text_label = QLabel(tutorial_text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("background:#111; border:none;")
        content_lay.addWidget(text_label)

        scroll.setWidget(content)
        lay.addWidget(scroll)

        btn_close = QPushButton("Schlieen")
        btn_close.setStyleSheet("""
            QPushButton { background:#4CAF50; color:#fff; border-radius:5px; padding:10px 20px; font-size:16px; }
            QPushButton:hover { background:#45a049; }
        """)
        btn_close.clicked.connect(self.accept)
        lay.addWidget(btn_close, alignment=Qt.AlignCenter)

# 
# Team-Auswahl-Dialog fuer Raeuber & Bulle
# 
class TeamSelectionDialog(QDialog):
    def __init__(self, num_humans, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Team-Auswahl - Raeuber & Bulle")
        self.setStyleSheet("background:#111;")
        self.setFixedSize(620, 480)
        self.num_humans = num_humans
        self.team_choices = [None] * num_humans  # None, "bulle", "raeuber"
        
        lay = QVBoxLayout()
        self.setLayout(lay)
        
        title = QLabel(" Raeuber & Bulle  Team-Auswahl")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color:#ffcc00;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)
        
        desc = QLabel("Waehle dein Team:  Mauz (Blau) oder  Wauz (Rot).\nDie Rollen (/) wechseln pro Runde automatisch  Teams bleiueben gleich.")
        desc.setStyleSheet("color:#ddd; font-size:14px;")
        desc.setAlignment(Qt.AlignCenter)
        lay.addWidget(desc)
        lay.addSpacing(12)

        quick_row = QWidget()
        quick_lay = QHBoxLayout()
        quick_lay.setContentsMargins(0, 0, 0, 0)
        quick_lay.setSpacing(10)
        quick_row.setLayout(quick_lay)

        btn_swap = QPushButton("Teams tauschen")
        btn_swap.setStyleSheet("""
            QPushButton { background:#333; color:#fff; border-radius:6px; padding:8px 14px; }
            QPushButton:hover { background:#444; }
        """)
        btn_swap.clicked.connect(self._swap_teams)

        btn_reset = QPushButton("Reset")
        btn_reset.setStyleSheet("""
            QPushButton { background:#333; color:#fff; border-radius:6px; padding:8px 14px; }
            QPushButton:hover { background:#444; }
        """)
        btn_reset.clicked.connect(self._reset_teams)

        quick_lay.addStretch(1)
        quick_lay.addWidget(btn_swap)
        quick_lay.addWidget(btn_reset)
        quick_lay.addStretch(1)
        lay.addWidget(quick_row)
        lay.addSpacing(12)

        # Scrollbarer Bereich fuer (Spielerwahl + Live-Tabelle + Status)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border:none; background:#111; }")
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(scroll, 1)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background:#111;")
        scroll.setWidget(scroll_content)
        slay = QVBoxLayout()
        slay.setContentsMargins(0, 0, 0, 0)
        slay.setSpacing(10)
        scroll_content.setLayout(slay)
        
        # Spieler-Auswahl
        self.player_widgets = []
        self.player_rows = []
        for i in range(num_humans):
            pw = QWidget()
            pw_lay = QHBoxLayout()
            pw.setLayout(pw_lay)
            pw.setStyleSheet("background:#161616; border:1px solid #222; border-radius:8px;")
            
            lbl = QLabel(f"Spieler {i+1}:")
            lbl.setStyleSheet("color:#fff; font-size:16px;")
            pw_lay.addWidget(lbl)
            
            btn_bulle = QPushButton(" Mauz (Blau)")
            btn_bulle.setStyleSheet("""
                QPushButton { background:#333; color:#fff; border-radius:5px; padding:5px 15px; }
                QPushButton:hover { background:#555; }
                QPushButton:checked { background:#0088ff; }
            """)
            btn_bulle.setCheckable(True)
            btn_bulle.clicked.connect(lambda checked, idx=i: self._select_team(idx, "blau", checked))
            
            btn_raeuber = QPushButton(" Wauz (Rot)")
            btn_raeuber.setStyleSheet("""
                QPushButton { background:#333; color:#fff; border-radius:5px; padding:5px 15px; }
                QPushButton:hover { background:#555; }
                QPushButton:checked { background:#ff4444; }
            """)
            btn_raeuber.setCheckable(True)
            btn_raeuber.clicked.connect(lambda checked, idx=i: self._select_team(idx, "rot", checked))
            
            pw_lay.addWidget(btn_bulle)
            pw_lay.addWidget(btn_raeuber)
            pw_lay.addStretch(1)
            
            self.player_widgets.append((btn_bulle, btn_raeuber))
            self.player_rows.append(pw)
            slay.addWidget(pw)
        
        slay.addSpacing(6)

        # Live-Team-Tabelle (je 6 Slots inkl. KI-Auffllung)
        teams_row = QWidget()
        teams_lay = QHBoxLayout()
        teams_lay.setContentsMargins(0, 0, 0, 0)
        teams_lay.setSpacing(16)
        teams_row.setLayout(teams_lay)

        def mk_team_box(title_text, border_color):
            box = QWidget()
            box.setStyleSheet(f"background:#0f0f0f; border:1px solid {border_color}; border-radius:10px;")
            bl = QVBoxLayout()
            bl.setContentsMargins(10, 10, 10, 10)
            bl.setSpacing(6)
            box.setLayout(bl)

            t = QLabel(title_text)
            t.setFont(QFont('Arial', 14, QFont.Bold))
            t.setStyleSheet("color:#fff;")
            t.setAlignment(Qt.AlignCenter)
            bl.addWidget(t)

            slots = []
            for _ in range(6):
                lbl = QLabel("")
                lbl.setFont(QFont("Courier", 11))
                lbl.setStyleSheet("color:#cfcfcf;")
                lbl.setAlignment(Qt.AlignLeft)
                bl.addWidget(lbl)
                slots.append(lbl)

            return box, slots

        bulle_box, self.bulle_slots = mk_team_box(" TEAM BLAU (6)", "#1d4a6b")
        raeuber_box, self.raeuber_slots = mk_team_box(" TEAM ROT (6)", "#6b1d1d")
        teams_lay.addWidget(bulle_box, 1)
        teams_lay.addWidget(raeuber_box, 1)
        slay.addWidget(teams_row)

        slay.addSpacing(4)

        # Status-Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color:#ffaa00; font-size:14px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        slay.addWidget(self.status_label)
        slay.addStretch(1)
        
        # Buttons
        btn_row = QWidget()
        btn_lay = QHBoxLayout()
        btn_row.setLayout(btn_lay)
        
        btn_ok = QPushButton("OK")
        btn_ok.setStyleSheet("""
            QPushButton { background:#4CAF50; color:#fff; border-radius:5px; padding:10px 20px; }
            QPushButton:hover { background:#45a049; }
        """)
        btn_ok.clicked.connect(self._check_and_accept)
        btn_ok.setDefault(True)
        btn_ok.setAutoDefault(True)
        
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.setStyleSheet("""
            QPushButton { background:#f44336; color:#fff; border-radius:5px; padding:10px 20px; }
            QPushButton:hover { background:#da190b; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        btn_lay.addWidget(btn_cancel)
        btn_lay.addWidget(btn_ok)
        
        lay.addWidget(btn_row)
        
        self._update_status()
    
    def _select_team(self, player_idx, team, checked):
        btn_bulle, btn_raeuber = self.player_widgets[player_idx]

        # clicked() wird nach dem internen Toggle ausgelst. Darum ist "checked"
        # die Quelle der Wahrheit: checked=True => auswhlen, checked=False => abwhlen.
        if checked:
            if team == "blau":
                btn_raeuber.setChecked(False)
                self.team_choices[player_idx] = "blau"
            else:
                btn_bulle.setChecked(False)
                self.team_choices[player_idx] = "rot"
        else:
            # abwhlen: entweder bleibt das andere Team aktiv, oder None
            if btn_bulle.isChecked() and not btn_raeuber.isChecked():
                self.team_choices[player_idx] = "blau"
            elif btn_raeuber.isChecked() and not btn_bulle.isChecked():
                self.team_choices[player_idx] = "rot"
            else:
                btn_bulle.setChecked(False)
                btn_raeuber.setChecked(False)
                self.team_choices[player_idx] = None

        self._update_status()

    def _swap_teams(self):
        teams_now = self.get_teams()
        for i in range(self.num_humans):
            t = teams_now[i] if i < len(teams_now) else None
            if t == "blau":
                t = "rot"
            elif t == "rot":
                t = "blau"
            self.team_choices[i] = t
            btn_bulle, btn_raeuber = self.player_widgets[i]
            btn_bulle.setChecked(t == "blau")
            btn_raeuber.setChecked(t == "rot")
        self._update_status()

    def _reset_teams(self):
        for i in range(self.num_humans):
            self.team_choices[i] = None
            btn_bulle, btn_raeuber = self.player_widgets[i]
            btn_bulle.setChecked(False)
            btn_raeuber.setChecked(False)
        self._update_status()
    
    def _update_status(self):
        teams_now = self.get_teams()
        blau = teams_now.count("blau")
        rot = teams_now.count("rot")
        unassigned = teams_now.count(None)

        for i in range(self.num_humans):
            row = self.player_rows[i]
            t = teams_now[i] if i < len(teams_now) else None
            if t == "blau":
                row.setStyleSheet("background:#0e2233; border:1px solid #1d4a6b; border-radius:8px;")
            elif t == "rot":
                row.setStyleSheet("background:#331010; border:1px solid #6b1d1d; border-radius:8px;")
            else:
                row.setStyleSheet("background:#161616; border:1px solid #222; border-radius:8px;")
        
        if unassigned > 0:
            self.status_label.setText(f"Noch {unassigned} Spieler ohne Team!")
            self.status_label.setStyleSheet("color:#ffaa00; font-size:14px;")
        else:
            ai_blau = max(0, 6 - blau)
            ai_rot = max(0, 6 - rot)
            self.status_label.setText(
                f"Menschen:  {blau},  {rot}   |   Mit KI:  {blau+ai_blau} vs  {rot+ai_rot}"
            )
            self.status_label.setStyleSheet("color:#44ff44; font-size:14px;")

        # Live-Tabelle aktualisieren: je 6 Slots pro Team (Menschen zuerst, dann KI-Auffllung)
        bulle_entries = []
        raeuber_entries = []
        for i, t in enumerate(teams_now):
            if t == "blau":
                bulle_entries.append(f"Spieler {i+1}")
            elif t == "rot":
                raeuber_entries.append(f"Spieler {i+1}")

        for k in range(max(0, 6 - len(bulle_entries))):
            bulle_entries.append(f"KI Blau {k+1}")
        for k in range(max(0, 6 - len(raeuber_entries))):
            raeuber_entries.append(f"KI Rot {k+1}")

        bulle_entries = (bulle_entries + [""] * 6)[:6]
        raeuber_entries = (raeuber_entries + [""] * 6)[:6]

        for i in range(6):
            self.bulle_slots[i].setText(f"{i+1}. {bulle_entries[i]}")
            self.raeuber_slots[i].setText(f"{i+1}. {raeuber_entries[i]}")
    
    def _check_and_accept(self):
        # Sync from UI (robust gegen evtl. UI-State/Model-State Drift)
        self.team_choices = self.get_teams()
        if None in self.team_choices:
            QMessageBox.warning(self, "Unvollstndig", "Alle Spieler mssen ein Team whlen!")
            return
        self.accept()
    
    def is_balanced(self):
        blau = sum(1 for t in self.team_choices if t == "blau")
        rot = sum(1 for t in self.team_choices if t == "rot")
        return abs(blau - rot) <= 1
    
    def get_teams(self):
        teams = []
        for btn_bulle, btn_raeuber in self.player_widgets:
            is_bulle = btn_bulle.isChecked()
            is_raeuber = btn_raeuber.isChecked()
            if is_bulle and not is_raeuber:
                teams.append("blau")
            elif is_raeuber and not is_bulle:
                teams.append("rot")
            else:
                teams.append(None)
        return teams

