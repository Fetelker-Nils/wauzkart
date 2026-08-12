from ..runtime import *
from .replay_widget import ReplayWidget

# 
# Replay-Screen
# 
class ReplayScreen(QWidget):
    def __init__(self, frames, events, on_back, map_name=None, player_names=None):
        super().__init__()
        self.setStyleSheet("background:#000;")
        lay = QVBoxLayout(); lay.setContentsMargins(0,0,0,0); self.setLayout(lay)

        top = QWidget(); top.setStyleSheet("background:#1a1a1a;")
        top_lay = QHBoxLayout(); top.setLayout(top_lay); top.setFixedHeight(50)
        title_txt = "  Highlight-Replay"
        if map_name:
            title_txt += f"      {map_name}"
        title = QLabel(title_txt)
        title.setFont(QFont("Arial",16,QFont.Bold)); title.setStyleSheet("color:#ffcc00;")
        top_lay.addWidget(title)
        top_lay.addStretch()
        btn_back = QPushButton(" Zurueck")
        btn_back.setStyleSheet("background:#333; color:#fff; border-radius:6px; padding:6px 18px;")
        btn_back.setFont(QFont("Arial",13))
        btn_back.clicked.connect(on_back); top_lay.addWidget(btn_back)
        lay.addWidget(top)

        self.replay = ReplayWidget(frames, events, map_name=map_name)
        lay.addWidget(self.replay, stretch=1)

        self._ui_lock = False
        self._fps = max(1, int(getattr(self.replay, "fps", 60) or 60))

        ctrl = QWidget(); ctrl.setStyleSheet("background:#1a1a1a;"); ctrl.setFixedHeight(86)
        cv = QVBoxLayout(); ctrl.setLayout(cv); cv.setContentsMargins(16, 6, 16, 6); cv.setSpacing(6)

        # Row 1: time + focus + play/pause
        cl = QHBoxLayout(); cl.setContentsMargins(0, 0, 0, 0)
        cv.addLayout(cl)

        self.lbl_time = QLabel("Sekunden: 0.0 / 0.0")
        self.lbl_time.setStyleSheet("color:#888;"); self.lbl_time.setFont(QFont("Arial",11))
        cl.addWidget(self.lbl_time)

        names = list(player_names) if player_names else []
        if not names and frames:
            first = frames[0]
            cars = first.get("cars", []) if isinstance(first, dict) else first
            if isinstance(cars, list):
                names = [f"Auto {i+1}" for i in range(len(cars))]

        if names:
            cl.addSpacing(10)
            lbl_focus = QLabel("Fokus:")
            lbl_focus.setStyleSheet("color:#aaa;")
            lbl_focus.setFont(QFont("Arial", 11))
            cl.addWidget(lbl_focus)

            self.cb_focus = QComboBox()
            self.cb_focus.addItems(names)
            self.cb_focus.setStyleSheet("background:#222;color:#fff;border:1px solid #444;padding:4px;")
            self.cb_focus.currentIndexChanged.connect(lambda _: self.replay.set_focus_index(self.cb_focus.currentIndex()))
            cl.addWidget(self.cb_focus)

            btn_prev = QPushButton("")
            btn_prev.setStyleSheet("background:#333; color:#fff; border-radius:6px; padding:6px 12px;")
            btn_prev.setFont(QFont("Arial", 11, QFont.Bold))
            btn_next = QPushButton("")
            btn_next.setStyleSheet("background:#333; color:#fff; border-radius:6px; padding:6px 12px;")
            btn_next.setFont(QFont("Arial", 11, QFont.Bold))

            def step_focus(delta):
                i = (self.cb_focus.currentIndex() + delta) % len(names)
                self.cb_focus.setCurrentIndex(i)

            btn_prev.clicked.connect(lambda: step_focus(-1))
            btn_next.clicked.connect(lambda: step_focus(1))
            cl.addWidget(btn_prev)
            cl.addWidget(btn_next)

            self.chk_follow = QCheckBox("Kamera folgt")
            self.chk_follow.setChecked(True)
            self.chk_follow.setStyleSheet("color:#ddd;")
            self.chk_follow.stateChanged.connect(lambda s: self.replay.set_follow_camera(s == Qt.Checked))
            cl.addWidget(self.chk_follow)
        cl.addStretch()
        self.btn_pp = QPushButton("  Pause")
        self.btn_pp.setStyleSheet("background:#333; color:#fff; border-radius:6px; padding:6px 16px;")
        self.btn_pp.setFont(QFont("Arial",12))

        def toggle():
            if not self.replay.playing and self.replay.frames and self.replay.idx >= (len(self.replay.frames) - 1):
                self.replay.set_frame_index(0)
            self.replay.playing = not self.replay.playing
            self._sync_replay_ui()

        self.btn_pp.clicked.connect(toggle); cl.addWidget(self.btn_pp)
        lay.addWidget(ctrl)

        # Row 2: seek + progress + seconds
        sl = QHBoxLayout(); sl.setContentsMargins(0, 0, 0, 0)
        cv.addLayout(sl)

        lbl_pos = QLabel("Sek:")
        lbl_pos.setStyleSheet("color:#aaa;"); lbl_pos.setFont(QFont("Arial", 10))
        sl.addWidget(lbl_pos)

        self.spin_sec = QSpinBox()
        self.spin_sec.setStyleSheet("background:#222;color:#fff;border:1px solid #444;padding:2px;")
        self.spin_sec.setFixedWidth(70)
        sl.addWidget(self.spin_sec)

        self.seek = QSlider(Qt.Horizontal)
        self.seek.setStyleSheet("QSlider{background:#1a1a1a;}")
        sl.addWidget(self.seek, stretch=1)

        self.prog = QProgressBar()
        self.prog.setTextVisible(False)
        self.prog.setFixedWidth(160)
        self.prog.setStyleSheet("""
            QProgressBar{background:#111;border:1px solid #333;border-radius:6px;}
            QProgressBar::chunk{background:#ffcc00;border-radius:6px;}
        """)
        sl.addWidget(self.prog)

        self.lbl_rest = QLabel("Rest: 0.0s")
        self.lbl_rest.setStyleSheet("color:#aaa;"); self.lbl_rest.setFont(QFont("Arial", 10))
        sl.addWidget(self.lbl_rest)

        self._was_playing_seek = False

        def on_seek_value(v):
            if self._ui_lock:
                return
            self.replay.set_frame_index(v)
            self._sync_replay_ui()

        def on_spin_sec(v):
            if self._ui_lock:
                return
            self.replay.set_frame_index(int(v * self._fps))
            self._sync_replay_ui()

        def seek_pressed():
            self._was_playing_seek = bool(self.replay.playing)
            self.replay.playing = False
            self._sync_replay_ui()

        def seek_released():
            self.replay.playing = bool(self._was_playing_seek)
            self._sync_replay_ui()

        self.seek.valueChanged.connect(on_seek_value)
        self.seek.sliderPressed.connect(seek_pressed)
        self.seek.sliderReleased.connect(seek_released)
        self.spin_sec.valueChanged.connect(on_spin_sec)

        self.tick = QTimer(); self.tick.timeout.connect(self._sync_replay_ui); self.tick.start(100)
        self._sync_replay_ui()

    def _sync_replay_ui(self):
        fps = max(1, int(self._fps or 60))
        total_frames = max(1, len(self.replay.frames))
        idx = max(0, min(total_frames - 1, int(getattr(self.replay, "idx", 0) or 0)))

        total_s = (total_frames - 1) / fps if total_frames > 1 else 0.0
        cur_s = idx / fps
        rest_s = max(0.0, total_s - cur_s)

        self.lbl_time.setText(f"Sekunden: {cur_s:0.1f} / {total_s:0.1f}")
        self.lbl_rest.setText(f"Rest: {rest_s:0.1f}s")

        if hasattr(self, "btn_pp") and self.btn_pp is not None:
            self.btn_pp.setText("  Pause" if self.replay.playing else "  Play")

        self._ui_lock = True
        try:
            self.seek.setRange(0, total_frames - 1)
            self.seek.setValue(idx)

            self.prog.setRange(0, total_frames - 1)
            self.prog.setValue(idx)

            max_sec = int(math.ceil(total_s))
            self.spin_sec.setRange(0, max(0, max_sec))
            self.spin_sec.setValue(int(round(cur_s)))
        finally:
            self._ui_lock = False

    def _end_race_bulle_win(self):
        """Beende das Rennen fuer Raeuber & Bulle."""
        self.race_over = True
        now = time.time()
        for pl in self.players:
            if not pl.finished:
                pl.finished = True
                pl.finish_time = now
                self.finish_counter += 1
                pl.finish_place = self.finish_counter
        if self.on_race_over:
            self.on_race_over(self.players, self.recorder, self.recorder.frames, self.recorder.events)
