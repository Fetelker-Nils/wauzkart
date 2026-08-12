from ..runtime import *

RESULT_BG = "#070a10"
RESULT_PANEL = "#111824"
RESULT_EDGE = "#344055"
RESULT_GOLD = "#f0c84b"


def _result_button(text, cb, accent=RESULT_GOLD, dark=False):
    btn = QPushButton(text)
    btn.setFont(QFont("Arial", 14, QFont.Bold))
    btn.setMinimumHeight(54)
    btn.setMinimumWidth(190)
    bg = "#171f2c" if dark else accent
    fg = "#ffffff" if dark else "#111111"
    edge = "#53647f" if dark else "#fff0a3"
    hover = "#243147" if dark else "#ffe06a"
    btn.setStyleSheet(f"""
        QPushButton {{
            background:{bg};
            color:{fg};
            border:2px solid {edge};
            border-left:8px solid {accent};
            border-radius:5px;
            padding:10px 24px;
            text-align:left;
        }}
        QPushButton:hover {{
            background:{hover};
            border-right:8px solid {accent};
        }}
        QPushButton:pressed {{
            background:#0d121b;
            color:#ffffff;
        }}
    """)
    btn.clicked.connect(cb)
    return btn


def _race_row(text, color):
    row = QLabel(text)
    row.setFont(QFont("Courier", 17, QFont.Bold))
    row.setAlignment(Qt.AlignCenter)
    row.setMinimumHeight(48)
    row.setStyleSheet(f"""
        QLabel {{
            color:{color};
            background:{RESULT_PANEL};
            border:2px solid {RESULT_EDGE};
            border-left:8px solid {color};
            border-radius:5px;
            padding:8px 18px;
        }}
    """)
    return row


# 
# Ergebnis-Screen
# 
class ResultWidget(QWidget):
    def __init__(self, players, recorder, on_menu, on_replay, on_history=None, xp_gained=0, levelups=None, progress=None, map_name=None, overlay=False):
        super().__init__()
        self.overlay = bool(overlay)
        root_bg = "rgba(7,10,16,170)" if self.overlay else RESULT_BG
        panel_bg = "rgba(7,10,16,0)" if self.overlay else RESULT_BG
        self.setStyleSheet(f"background-color:{root_bg};")
        outer = QVBoxLayout()
        outer.setContentsMargins(34 if self.overlay else 0, 28 if self.overlay else 0, 34 if self.overlay else 0, 28 if self.overlay else 0)
        self.setLayout(outer)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border:none; background:{panel_bg}; }}")
        outer.addWidget(scroll, 1)

        content = QWidget()
        content.setStyleSheet(f"background:{panel_bg};")
        scroll.setWidget(content)

        lay = QVBoxLayout()
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        content.setLayout(lay)

        if map_name == "Raeuber & Bulle":
            self._show_bulle_raeuber_result(players, lay, xp_gained, levelups, progress, on_menu, on_replay, on_history)
        else:
            self._show_normal_result(players, recorder, lay, xp_gained, levelups, progress, on_menu, on_replay, on_history)

    def _show_normal_result(self, players, recorder, lay, xp_gained, levelups, progress, on_menu, on_replay, on_history):
        title = QLabel("RENNEN BEENDET")
        title.setFont(QFont("Arial", 34, QFont.Bold))
        title.setStyleSheet(f"color:{RESULT_GOLD}; background:transparent; border:none;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title); lay.addSpacing(24)

        levelups = levelups or []
        progress = progress or {}
        if levelups:
            lu = QLabel("LEVEL UP")
            lu.setFont(QFont("Arial", 28, QFont.Bold))
            lu.setStyleSheet("color:#4cff72;")
            lu.setAlignment(Qt.AlignCenter)
            lay.addWidget(lu)
            for item in levelups:
                unlocked = item.get("unlocked")
                unlocked_list = unlocked if isinstance(unlocked, list) else ([unlocked] if unlocked else [])
                if not unlocked_list:
                    unlocked_list = ["(alle Items bereits freigeschaltet)"]
                for u in unlocked_list:
                    lbl = QLabel(f"Freigeschaltet: {u}")
                    lbl.setFont(QFont("Arial", 14, QFont.Bold))
                    lbl.setStyleSheet("color:#dddddd;")
                    lbl.setAlignment(Qt.AlignCenter)
                    lay.addWidget(lbl)
            lay.addSpacing(16)

        if progress:
            level = progress.get("level", 1)
            xp = progress.get("xp", 0)
            need = progress.get("need", level * 100)
            xp_lbl = QLabel(f"XP +{int(xp_gained)}   |   Level {level}   ({xp}/{need} XP)")
            xp_lbl.setFont(QFont("Arial", 13, QFont.Bold))
            xp_lbl.setStyleSheet(f"color:#d7dee8; background:{RESULT_PANEL}; border:2px solid {RESULT_EDGE}; border-radius:5px; padding:10px 18px;")
            xp_lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(xp_lbl)
            lay.addSpacing(18)

        places = ["P1", "P2", "P3", "P4"]
        place_colors = ["#ffd700","#c0c0c0","#cd7f32","#888888"]
        sorted_players = sorted(players, key=lambda p: p.finish_place or 99)
        for pl in sorted_players:
            place = pl.finish_place or 4
            place_txt = places[min(place-1, 3)]
            col   = place_colors[min(place-1, 3)]
            t = pl.finish_time; st = pl.start_time
            time_str = f"{t-st:.2f}s" if t and st else "DNF"
            kind = "KI" if pl.is_ai else "DU"
            lay.addWidget(_race_row(f"{place_txt}   {kind:<2}   {pl.name:<16}   {time_str:>8}", col))

        lay.addSpacing(36)

        btn_row = QWidget(); br_lay = QHBoxLayout(); btn_row.setLayout(br_lay)
        br_lay.setAlignment(Qt.AlignCenter); br_lay.setSpacing(20)

        br_lay.addWidget(_result_button("HIGHLIGHTS", on_replay))
        if on_history:
            br_lay.addWidget(_result_button("ALLE RENNEN", on_history, "#ff8a2a"))
        br_lay.addWidget(_result_button("HAUPTMENUE", on_menu, "#52647f", True))
        lay.addWidget(btn_row)

    def _show_bulle_raeuber_result(self, players, lay, xp_gained, levelups, progress, on_menu, on_replay, on_history):
        title = QLabel("RAEUBER & BULLE BEENDET")
        title.setFont(QFont("Arial", 34, QFont.Bold))
        title.setStyleSheet(f"color:{RESULT_GOLD}; background:transparent; border:none;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title); lay.addSpacing(24)

        # Match-Score (falls vorhanden)
        any_pl = players[0] if players else None
        sb = getattr(any_pl, "rb_score_blau", None)
        sr = getattr(any_pl, "rb_score_rot", None)
        rt = getattr(any_pl, "rb_total_rounds", None)
        if sb is not None and sr is not None and rt is not None:
            score_lbl = QLabel(f"Match:  {int(sb)}     {int(sr)}   (Runden: {int(rt)})")
            score_lbl.setFont(QFont("Arial", 16, QFont.Bold))
            score_lbl.setStyleSheet(f"color:#d7dee8; background:{RESULT_PANEL}; border:2px solid {RESULT_EDGE}; border-radius:5px; padding:10px 18px;")
            score_lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(score_lbl)
            lay.addSpacing(12)

        # Bestimme Gewinner
        winner_team = next((getattr(p, "rb_winner_team", None) for p in players if getattr(p, "rb_winner_team", None)), None)
        if winner_team not in ("blau", "rot") and sb is not None and sr is not None:
            winner_team = "blau" if int(sb) > int(sr) else ("rot" if int(sr) > int(sb) else None)
        blau_win = (winner_team == "blau")
        rot_win = (winner_team == "rot")

        # Hauptlayout fuer Teams
        teams_layout = QHBoxLayout()
        teams_layout.setSpacing(50)
        teams_layout.setAlignment(Qt.AlignCenter)

        # Blau-Team links
        blau_widget = QWidget()
        blau_layout = QVBoxLayout()
        blau_layout.setAlignment(Qt.AlignCenter)
        blau_widget.setLayout(blau_layout)

        blau_title = QLabel(" TEAM BLAU (Mauz)")
        blau_title.setFont(QFont("Arial",24,QFont.Bold))
        blau_title.setStyleSheet("color:#ffffff;")
        blau_title.setAlignment(Qt.AlignCenter)
        blau_layout.addWidget(blau_title)

        blau_result = QLabel("GEWONNEN" if blau_win else ("VERLOREN" if rot_win else "UNENTSCHIEDEN"))
        blau_result.setFont(QFont("Arial",20,QFont.Bold))
        blau_result.setStyleSheet("color:#44ff44;" if blau_win else ("color:#ff4444;" if rot_win else "color:#dddddd;"))
        blau_result.setAlignment(Qt.AlignCenter)
        blau_layout.addWidget(blau_result)

        blau_layout.addSpacing(10)
        for pl in players:
            if getattr(pl, "rb_color_team", None) == "blau":
                icon = "" if pl.is_ai else ""
                lbl = QLabel(f"{icon} {pl.name}")
                lbl.setFont(QFont("Arial",16))
                lbl.setStyleSheet("color:#cccccc;")
                lbl.setAlignment(Qt.AlignCenter)
                blau_layout.addWidget(lbl)

        teams_layout.addWidget(blau_widget)

        # Rot-Team rechts
        rot_widget = QWidget()
        rot_layout = QVBoxLayout()
        rot_layout.setAlignment(Qt.AlignCenter)
        rot_widget.setLayout(rot_layout)

        rot_title = QLabel(" TEAM ROT (Wauz)")
        rot_title.setFont(QFont("Arial",24,QFont.Bold))
        rot_title.setStyleSheet("color:#ffffff;")
        rot_title.setAlignment(Qt.AlignCenter)
        rot_layout.addWidget(rot_title)

        rot_result = QLabel("GEWONNEN" if rot_win else ("VERLOREN" if blau_win else "UNENTSCHIEDEN"))
        rot_result.setFont(QFont("Arial",20,QFont.Bold))
        rot_result.setStyleSheet("color:#44ff44;" if rot_win else ("color:#ff4444;" if blau_win else "color:#dddddd;"))
        rot_result.setAlignment(Qt.AlignCenter)
        rot_layout.addWidget(rot_result)

        rot_layout.addSpacing(10)
        for pl in players:
            if getattr(pl, "rb_color_team", None) == "rot":
                icon = "" if pl.is_ai else ""
                lbl = QLabel(f"{icon} {pl.name}")
                lbl.setFont(QFont("Arial",16))
                lbl.setStyleSheet("color:#cccccc;")
                lbl.setAlignment(Qt.AlignCenter)
                rot_layout.addWidget(lbl)

        teams_layout.addWidget(rot_widget)

        lay.addLayout(teams_layout)
        lay.addSpacing(36)

        # Normale Rennen-Ergebnisse auch anzeigen
        races_title = QLabel("RENNVERLAUF")
        races_title.setFont(QFont("Arial", 20, QFont.Bold))
        races_title.setStyleSheet("color:#ffaa44;")
        races_title.setAlignment(Qt.AlignCenter)
        lay.addWidget(races_title)
        lay.addSpacing(12)

        places = ["P1", "P2", "P3", "P4"]
        place_colors = ["#ffd700","#c0c0c0","#cd7f32","#888888"]
        sorted_players = sorted(players, key=lambda p: p.finish_place or 99)
        for pl in sorted_players:
            place = pl.finish_place or 4
            place_txt = places[min(place-1, 3)]
            col   = place_colors[min(place-1, 3)]
            t = pl.finish_time; st = pl.start_time
            time_str = f"{t-st:.2f}s" if t and st else "DNF"
            kind = "KI" if pl.is_ai else "DU"
            lay.addWidget(_race_row(f"{place_txt}   {kind:<2}   {pl.name:<16}   {time_str:>8}", col))

        lay.addSpacing(36)

        # Levelups und Progress wie normal
        levelups = levelups or []
        progress = progress or {}
        if levelups:
            lu = QLabel("LEVEL UP")
            lu.setFont(QFont("Arial", 28, QFont.Bold))
            lu.setStyleSheet("color:#44ff44;")
            lu.setAlignment(Qt.AlignCenter)
            lay.addWidget(lu)
            for item in levelups:
                unlocked = item.get("unlocked")
                unlocked_list = unlocked if isinstance(unlocked, list) else ([unlocked] if unlocked else [])
                if not unlocked_list:
                    unlocked_list = ["(alle Items bereits freigeschaltet)"]
                for u in unlocked_list:
                    lbl = QLabel(f"Freigeschaltet: {u}")
                    lbl.setFont(QFont("Arial", 14, QFont.Bold))
                    lbl.setStyleSheet("color:#dddddd;")
                    lbl.setAlignment(Qt.AlignCenter)
                    lay.addWidget(lbl)
            lay.addSpacing(16)

        if progress:
            level = progress.get("level", 1)
            xp = progress.get("xp", 0)
            need = progress.get("need", level * 100)
            xp_lbl = QLabel(f"XP +{int(xp_gained)}   |   Level {level}   ({xp}/{need} XP)")
            xp_lbl.setFont(QFont("Arial", 13, QFont.Bold))
            xp_lbl.setStyleSheet(f"color:#d7dee8; background:{RESULT_PANEL}; border:2px solid {RESULT_EDGE}; border-radius:5px; padding:10px 18px;")
            xp_lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(xp_lbl)
            lay.addSpacing(18)

        # Buttons
        btn_row = QWidget(); br_lay = QHBoxLayout(); btn_row.setLayout(br_lay)
        br_lay.setAlignment(Qt.AlignCenter); br_lay.setSpacing(20)

        br_lay.addWidget(_result_button("HIGHLIGHTS", on_replay))
        if on_history:
            br_lay.addWidget(_result_button("ALLE RENNEN", on_history, "#ff8a2a"))
        br_lay.addWidget(_result_button("HAUPTMENUE", on_menu, "#52647f", True))
        lay.addWidget(btn_row)
