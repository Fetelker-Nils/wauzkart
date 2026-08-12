from ..runtime import *

# 
# Raeuber & Bulle: Zwischenrunden-Men
# 
class RBIntermissionDialog(QDialog):
    def __init__(self, info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Runde beendet")
        self.setStyleSheet("background:#111;")
        self.setFixedSize(520, 300)

        info = info or {}
        winner_role = info.get("winner_role")
        winner_team = info.get("winner_team")
        round_finished = int(info.get("round_finished") or 1)
        round_next = int(info.get("round_next") or (round_finished + 1))
        total_rounds = int(info.get("total_rounds") or 4)
        sb = int(info.get("score_blau") or 0)
        sr = int(info.get("score_rot") or 0)

        lay = QVBoxLayout()
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(10)
        self.setLayout(lay)

        title = QLabel(f"Runde {round_finished} beendet")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color:#ffcc00;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        win_txt = "Runde beendet"
        win_col = "#dddddd"
        if winner_team in ("blau", "rot") and winner_role in ("bulle", "raeuber"):
            team_icon = "" if winner_team == "blau" else ""
            role_icon = "" if winner_role == "bulle" else ""
            win_txt = f"{team_icon} Team gewinnt diese Runde (+1)   {role_icon}"
            win_col = "#66aaff" if winner_team == "blau" else "#ff6666"

        wlbl = QLabel(win_txt)
        wlbl.setFont(QFont("Arial", 14, QFont.Bold))
        wlbl.setStyleSheet(f"color:{win_col};")
        wlbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(wlbl)

        score = QLabel(f"Stand:  {sb}     {sr}")
        score.setFont(QFont("Arial", 16, QFont.Bold))
        score.setStyleSheet("color:#ffffff;")
        score.setAlignment(Qt.AlignCenter)
        lay.addWidget(score)

        next_lbl = QLabel(f"Nchste Runde: {round_next}/{total_rounds}  (Rollen wechseln)")
        next_lbl.setFont(QFont("Arial", 12))
        next_lbl.setStyleSheet("color:#aaaaaa;")
        next_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(next_lbl)

        lay.addStretch(1)

        btn_row = QWidget()
        bl = QHBoxLayout()
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)
        btn_row.setLayout(bl)

        btn_quit = QPushButton(" Aufhren")
        btn_quit.setFont(QFont("Arial", 12, QFont.Bold))
        btn_quit.setStyleSheet("background:#441111;color:#ff6666;border-radius:8px;padding:10px 18px;")
        btn_quit.clicked.connect(self.reject)
        bl.addWidget(btn_quit)

        bl.addStretch(1)

        btn_next = QPushButton(" Nchste Runde")
        btn_next.setFont(QFont("Arial", 12, QFont.Bold))
        btn_next.setStyleSheet("background:#4CAF50;color:#fff;border-radius:8px;padding:10px 18px;")
        btn_next.clicked.connect(self.accept)
        btn_next.setDefault(True)
        btn_next.setAutoDefault(True)
        bl.addWidget(btn_next)

        lay.addWidget(btn_row)

