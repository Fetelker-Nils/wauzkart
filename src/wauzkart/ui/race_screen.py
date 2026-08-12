from ..runtime import *
from ..core.rendering import _hud_text_color_for_rgb
from ..tracks.maps import *
from ..game.race_widget import RaceWidget
from .rb_intermission import RBIntermissionDialog
from .results import ResultWidget

# 
# Renn-Screen  (HUD fuer 14 Spieler)
# 
class RaceScreen(QWidget):
    def __init__(self, num_humans, ai_diff_name, laps, map_name="Oval", on_quit=None, on_finish=None, car_colors=None, car_styles=None, characters=None, show_ai_views=False, teams=None, rb_rounds=None, rb_round_time=None, track_size="klein"):
        super().__init__()
        self.on_quit   = on_quit
        self.on_finish = on_finish
        self.num_humans = num_humans
        self.win_laps   = laps
        self.map_name   = map_name
        self.car_colors = car_colors or []
        self.car_styles = car_styles or []
        self.characters = characters or []
        self.show_ai_views = bool(show_ai_views)
        self.teams = teams or []
        self.rb_rounds = rb_rounds
        self.rb_round_time = rb_round_time
        self.track_size = track_size if map_name != "Raeuber & Bulle" else "klein"
        self.result_overlay = None
        self.setStyleSheet("background:#1a1a1a;")
        lay = QHBoxLayout(); lay.setContentsMargins(0,0,0,0); self.setLayout(lay)

        # HUD (Sidebar) - Scrollbar hinzufgen
        hud_scroll = QScrollArea()
        hud_scroll.setWidgetResizable(True)
        hud_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        hud_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        hud_scroll.setFixedWidth(320 if map_name == "Raeuber & Bulle" else 200)
        hud_scroll.setStyleSheet("QScrollArea { background:#1e1e1e; border: none; }")
        
        hud = QWidget(); hud.setStyleSheet("background:#1e1e1e;")
        hl  = QVBoxLayout(); hl.setContentsMargins(10,10,10,10); hud.setLayout(hl)
        
        hud_scroll.setWidget(hud)

        title = QLabel("WAUZ KART 3D")
        title.setFont(QFont("Arial",11,QFont.Bold)); title.setStyleSheet("color:#ffcc00;")
        hl.addWidget(title); hl.addSpacing(4)

        diff_lbl = QLabel(f"KI: {ai_diff_name}")
        diff_lbl.setFont(QFont("Arial",9)); diff_lbl.setStyleSheet("color:#555;")
        hl.addWidget(diff_lbl); hl.addSpacing(8)

        # Raeuber & Bulle: klare Rollenanzeige fuer menschliche Spieler
        self.lbl_rb_roles = QLabel("")
        self.lbl_rb_roles.setWordWrap(True)
        self.lbl_rb_roles.setFont(QFont("Arial", 11, QFont.Bold))
        self.lbl_rb_roles.setStyleSheet("color:#dddddd;")
        self.lbl_rb_roles.setVisible(False)
        hl.addWidget(self.lbl_rb_roles)
        hl.addSpacing(8)

        # Steuerungslegende
        ctrl_map = ["W A S D", "   ", "T G F H", "I K J L"]
        # Fuer Raeuber & Bulle: 12 Spieler
        num_players = 12 if map_name == "Raeuber & Bulle" else 4
        self.hud_labels = []
        for i in range(num_players):
            is_human = i < num_humans
            if is_human:
                cfg = PLAYER_CONFIGS[i]
                # determine HUD color: either provided car color or default hud
                if i < len(self.car_colors):
                    rgb = self.car_colors[i]
                    raw = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
                    color = _hud_text_color_for_rgb(rgb, raw)
                else:
                    color = cfg["hud_color"]
            else:
                if i < len(self.car_colors):
                    rgb = self.car_colors[i]
                    raw = f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
                    color = _hud_text_color_for_rgb(rgb, raw)
                else:
                    ai_idx = i - num_humans
                    ai_hud_colors = ["#44dd44", "#ffbb00", "#cc44ff", "#44ffff", "#ff4444", "#4444ff", "#44ff44", "#ffff44", "#ff44ff", "#44ffff", "#ffffff", "#888888"]
                    color = ai_hud_colors[ai_idx % len(ai_hud_colors)]

            lbl = QLabel()
            lbl.setWordWrap(True)
            lbl.setFont(QFont("Courier",10 if map_name == "Raeuber & Bulle" else 9))
            lbl.setStyleSheet(f"color:{color};"); hl.addWidget(lbl)
            self.hud_labels.append(lbl)
            if i < num_players - 1: hl.addSpacing(2)

        hl.addStretch()

        self.lbl_cd = QLabel("")
        self.lbl_cd.setFont(QFont("Arial",44,QFont.Bold))
        self.lbl_cd.setAlignment(Qt.AlignCenter); self.lbl_cd.setStyleSheet("color:#ffcc00;")
        hl.addWidget(self.lbl_cd); hl.addStretch()

        self.lbl_timer = QLabel("")
        self.lbl_timer.setFont(QFont("Arial",12))  # Kleinerer Text fuer die Zeit
        self.lbl_timer.setAlignment(Qt.AlignCenter); self.lbl_timer.setStyleSheet("color:#ffcc00;")
        self.lbl_timer.setVisible(False)  # Standardmig versteckt
        hl.addWidget(self.lbl_timer); hl.addStretch()

        ctrl = QLabel("Runden: " + str(self.win_laps))
        ctrl.setFont(QFont("Arial",9)); ctrl.setStyleSheet("color:#444;")
        hl.addWidget(ctrl); hl.addSpacing(8)

        btn_quit = QPushButton("  Aufhren")
        btn_quit.setFont(QFont("Arial",10))
        btn_quit.setStyleSheet("""
            QPushButton{background:#441111;color:#ff6666;border-radius:6px;padding:6px;}
            QPushButton:hover{background:#661111;}
        """)
        btn_quit.clicked.connect(self._quit); hl.addWidget(btn_quit)

        # GL
        self.race = RaceWidget(
            num_humans,
            ai_diff_name,
            self.win_laps,
            map_name,
            car_colors=self.car_colors,
            car_styles=self.car_styles,
            characters=self.characters,
            show_ai_views=self.show_ai_views,
            teams=teams,
            rb_rounds=self.rb_rounds,
            rb_round_time=self.rb_round_time,
            track_size=self.track_size,
        )
        self.race.on_race_over = self._race_over
        self.race.on_rb_round_over = self._rb_round_over

        lay.addWidget(hud_scroll)
        lay.addWidget(self.race, stretch=1)

        self.hud_t = QTimer(); self.hud_t.timeout.connect(self._update_hud); self.hud_t.start(30)

    def keyPressEvent(self, e):
        key_map = {
            Qt.Key_W:'w', Qt.Key_S:'s', Qt.Key_A:'a', Qt.Key_D:'d',
            Qt.Key_Up:'UP', Qt.Key_Down:'DOWN', Qt.Key_Left:'LEFT', Qt.Key_Right:'RIGHT',
            Qt.Key_T:'t', Qt.Key_G:'g', Qt.Key_F:'f', Qt.Key_H:'h',
            Qt.Key_I:'i', Qt.Key_K:'k', Qt.Key_J:'j', Qt.Key_L:'l',
            Qt.Key_Escape: 'ESC',
            Qt.Key_F3: 'F3',
        }
        if e.key() in key_map:
            k = key_map[e.key()]
            if k == 'ESC': self._quit(); return
            if k == 'F3':
                self.race.cycle_camera_mode()
                return
            self.race.keys[k] = True
            self.race.register_rocket(k)

    def keyReleaseEvent(self, e):
        key_map = {
            Qt.Key_W:'w', Qt.Key_S:'s', Qt.Key_A:'a', Qt.Key_D:'d',
            Qt.Key_Up:'UP', Qt.Key_Down:'DOWN', Qt.Key_Left:'LEFT', Qt.Key_Right:'RIGHT',
            Qt.Key_T:'t', Qt.Key_G:'g', Qt.Key_F:'f', Qt.Key_H:'h',
            Qt.Key_I:'i', Qt.Key_K:'k', Qt.Key_J:'j', Qt.Key_L:'l',
        }
        if e.key() in key_map:
            self.race.keys[key_map[e.key()]] = False

    def _quit(self):
        self.hud_t.stop(); self.race.timer.stop()
        self.on_quit()

    def _race_over(self, players=None, recorder=None, frames=None, events=None):
        if players is None:
            players = self.race.players
        if recorder is None:
            recorder = self.race.recorder
        if frames is None or events is None:
            frames, events = recorder.get_highlight()
        self.on_finish(players, recorder, frames, events)

    def show_result_overlay(self, players, recorder, frames, events, xp_gained=0, levelups=None, progress=None, map_name=None, on_menu=None, on_replay=None, on_history=None):
        if self.result_overlay is not None:
            self.result_overlay.setParent(None)
            self.result_overlay.deleteLater()
        self.race.result_live_preview = True
        self.result_overlay = ResultWidget(
            players,
            recorder,
            on_menu=on_menu or self.on_quit,
            on_replay=on_replay or (lambda: None),
            on_history=on_history,
            xp_gained=xp_gained,
            levelups=levelups,
            progress=progress,
            map_name=map_name or self.map_name,
            overlay=True,
        )
        self.result_overlay.setParent(self)
        self.result_overlay.setGeometry(self.rect())
        self.result_overlay.show()
        self.result_overlay.raise_()

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        if self.result_overlay is not None:
            self.result_overlay.setGeometry(self.rect())

    def _rb_round_over(self, info):
        # Small between-round menu (RB mode)
        try:
            dlg = RBIntermissionDialog(info, parent=self)
            res = dlg.exec_()
        except Exception:
            res = QDialog.Accepted

        if res == QDialog.Accepted:
            self.race.rb_start_next_round()
            self.setFocus()
            return

        self._quit()

    def _update_hud(self):
        gl = self.race; now = time.time()
        cd = gl.get_countdown_text(); self.lbl_cd.setText(cd)
        if gl.countdown_phase == 'two':   self.lbl_cd.setStyleSheet("color:#ff8800;")
        elif gl.countdown_phase == 'go':  self.lbl_cd.setStyleSheet("color:#44ff44;")
        else:                             self.lbl_cd.setStyleSheet("color:#ffcc00;")
        standings = gl.get_current_standings()

        # Raeuber & Bulle: Rollenanzeige (fuer jeden menschlichen Spieler)
        if gl.map_name == "Raeuber & Bulle":
            ctrl_names = ["WASD", "", "TFGH", "IJKL"]
            lines = []
            for i in range(min(self.num_humans, len(gl.players))):
                pl = gl.players[i]
                color_team = getattr(pl, "rb_color_team", None) or "Down"
                team_icon = "" if color_team == "blau" else ("" if color_team == "rot" else "")
                role_icon = "" if pl.team == "bulle" else ""
                lines.append(f"Spieler {i+1} ({ctrl_names[i]}): {team_icon} {role_icon}")
            self.lbl_rb_roles.setText("\n".join(lines))
            self.lbl_rb_roles.setVisible(True)
        else:
            self.lbl_rb_roles.setVisible(False)
        
        # Timer fuer Raeuber & Bulle
        if gl.map_name == "Raeuber & Bulle" and gl.game_timer is not None:
            timer_text = f"Zeit: {max(0, gl.game_timer):.1f}s"
            if now < getattr(gl, "rb_button_cooldown_until", 0.0):
                timer_text += f" | Knopf CD: {gl.rb_button_cooldown_until - now:.1f}s"
            r_idx = getattr(gl, "rb_round_index", 1)
            r_total = getattr(gl, "rb_total_rounds", 4)
            sb = int(getattr(gl, "rb_score_blau", 0))
            sr = int(getattr(gl, "rb_score_rot", 0))
            timer_text += f" | Runde: {r_idx}/{r_total} | Punkte: {sb} {sr}"
            self.lbl_timer.setText(timer_text)
            self.lbl_timer.setVisible(True)
        else:
            self.lbl_timer.setVisible(False)
        
        em = {1:"",2:"",3:"",4:"4"}
        ctrl_names = ["WASD", "", "TFGH", "IJKL"]
        for i, pl in enumerate(gl.players):
            icon = "" if pl.is_ai else f"{ctrl_names[i]}"
            lines = [f"{icon} {pl.name}"]
            if gl.map_name == "Raeuber & Bulle":
                role_icon = "" if pl.team == "bulle" else ""
                color_team = getattr(pl, "rb_color_team", None) or "Down"
                team_icon = "" if color_team == "blau" else ("" if color_team == "rot" else "")
                lines[0] += f" {team_icon} {role_icon}"
                if getattr(pl, "rb_caught", False):
                    lines.append("Im Gefaengnis")
                else:
                    lines.append("Auf der Flucht" if pl.team == "raeuber" else "Jagt Raeuber")
            else:
                lines.append(f"Runde: {pl.laps}/{self.win_laps}")
                place = standings.get(pl, 4)
                lines.append(f"{em.get(place,'')} Platz {place}")
            if pl.start_time: lines.append(f"{now-pl.start_time:.1f}s")
            if pl.crash_timer > now: lines.append(" CRASH!")
            if gl.map_name != "Raeuber & Bulle" and pl.finished and pl.finish_place: lines.append(f"{em.get(pl.finish_place,'')} Endplatz {pl.finish_place}")
            elif pl.rocket_boost and not gl.is_racing(): lines.append(f" +{pl.boost_amount*100:.0f}%")
            self.hud_labels[i].setText("\n".join(lines))
