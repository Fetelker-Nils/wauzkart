from ..runtime import *
from ..data.progression import RaceLogger

HISTORY_BG = "#070a10"
HISTORY_PANEL = "#111824"
HISTORY_EDGE = "#344055"
HISTORY_GOLD = "#f0c84b"


def _history_button_style(accent=HISTORY_GOLD):
    return f"""
        QPushButton {{
            text-align:left;
            color:#ffffff;
            background:{HISTORY_PANEL};
            border:2px solid {HISTORY_EDGE};
            border-left:8px solid {accent};
            border-radius:5px;
            padding:12px 16px;
        }}
        QPushButton:hover {{
            background:#1a2433;
            border-color:{accent};
            border-right:8px solid {accent};
        }}
        QPushButton:pressed {{
            background:#0b1018;
        }}
    """


# 
# History / Archive screen
# 
class HistoryWidget(QWidget):
    def __init__(self, on_back, on_show_race):
        super().__init__()
        self.on_back = on_back
        self.on_show_race = on_show_race
        self.setStyleSheet(f"background:{HISTORY_BG};")
        lay = QVBoxLayout()
        lay.setAlignment(Qt.AlignTop)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)
        self.setLayout(lay)

        title = QLabel("RENNHISTORIE")
        title.setFont(QFont("Arial", 32, QFont.Bold))
        title.setStyleSheet(f"color:{HISTORY_GOLD}; background:transparent; border:none;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title); lay.addSpacing(12)

        hs = RaceLogger.get_highscore()
        if hs:
            lbl = QLabel(f"BESTZEIT   {hs['time']:.2f}s   {hs['name']}")
            lbl.setFont(QFont("Courier", 14, QFont.Bold))
            lbl.setStyleSheet(f"color:#88ff88; background:{HISTORY_PANEL}; border:2px solid {HISTORY_EDGE}; border-radius:5px; padding:10px 16px;")
            lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(lbl)
            lay.addSpacing(10)

        # Scrollable area for race list
        self.list_widget = QWidget(); lw_lay = QVBoxLayout(); lw_lay.setAlignment(Qt.AlignTop); self.list_widget.setLayout(lw_lay)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.list_widget)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{HISTORY_BG}; }}
            QScrollArea QWidget {{ background:{HISTORY_BG}; }}
            QScrollBar:vertical {{ background:#10141c; width:10px; border-radius:5px; }}
            QScrollBar::handle:vertical {{ background:#52647f; border-radius:5px; }}
        """)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lay.addWidget(scroll)
        self.refresh_list()

        btn_back = QPushButton("ZURUECK")
        btn_back.setFont(QFont("Arial", 13, QFont.Bold))
        btn_back.setMinimumHeight(52)
        btn_back.setStyleSheet(_history_button_style("#52647f"))
        btn_back.clicked.connect(self.on_back)
        lay.addWidget(btn_back)

    def refresh_list(self):
        # clear existing entries
        layout = self.list_widget.layout()
        for i in reversed(range(layout.count())):
            w = layout.itemAt(i).widget()
            if w: w.setParent(None)
        races = RaceLogger.load_all()
        # show most recent first
        for path,data in reversed(races):
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('timestamp',0)))
            map_name = data.get("map_name") or "Rennen"
            wtxt = f"{ts}   {map_name}"
            if data.get("map_name") == "Raeuber & Bulle":
                wt = data.get("rb_winner_team")
                if wt not in ("blau", "rot"):
                    wt = next((p.get("rb_winner_team") for p in data.get("players", []) if p.get("rb_winner_team") in ("blau", "rot")), None)
                if wt == "blau":
                    wtxt += "  Gewinner: Blau"
                elif wt == "rot":
                    wtxt += "  Gewinner: Rot"
                else:
                    wtxt += "  Gewinner: Down"
            elif data.get("map_name") == "Insignien-Diebstahl":
                winner = next((p for p in data.get("players", []) if p.get("insignia_winner")), None)
                if winner is None:
                    players = data.get("players", [])
                    winner = max(players, key=lambda p: p.get("insignia_score", 0), default=None)
                if winner:
                    wtxt += f"  Sieger {winner.get('name', '?')} ({int(winner.get('insignia_score', 0))} Punkte)"
            else:
                winner = next((p for p in data.get('players',[]) if p.get('finish_place')==1), None)
                if winner and winner.get('finish_time') is not None:
                    wtxt += f"  Sieger {winner['name']} ({winner['finish_time']:.2f}s)"
            btn = QPushButton(wtxt)
            btn.setFont(QFont("Arial", 12, QFont.Bold))
            btn.setMinimumHeight(54)
            btn.setStyleSheet(_history_button_style("#ff8a2a" if data.get("map_name") in ("Raeuber & Bulle", "Insignien-Diebstahl") else HISTORY_GOLD))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            def make_cb(p=path,d=data):
                self.on_show_race(p,d)
            btn.clicked.connect(make_cb)
            layout.addWidget(btn)
        # add stretch to push items to top
        layout.addStretch(1)
