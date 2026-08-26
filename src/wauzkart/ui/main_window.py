from ..runtime import *
import platform
import shutil
import subprocess
import tempfile
import urllib.request
from .. import __version__
from ..audio.sound import wauz_audio
from ..core.updates import check_for_update
from ..data.legal import accept_terms, has_accepted_terms
from ..data.progression import RaceLogger, badge_store, global_progression, unlock_badge
from ..game.entities import Player
from ..network.lan import LAN_PORT, LanClient, LanServer
from ..paths import ASSETS_DIR, _wauz_api
from .history import HistoryWidget
from .legal import TermsDialog, UpdateHelpDialog
from .menu import MenuWidget
from .race_screen import RaceScreen
from .replay_screen import ReplayScreen
from .results import ResultWidget


class _UpdateSignal(QObject):
    found = pyqtSignal(dict)
    progress = pyqtSignal(int, str)
    failed = pyqtSignal(str)
    install = pyqtSignal(str)


class UpdateProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wauz Kart Update")
        self.setModal(True)
        self.setFixedSize(520, 220)
        self.setStyleSheet("""
            QDialog {
                background: #070b13;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QProgressBar {
                background: #101927;
                color: #ffffff;
                border: 2px solid #f4c945;
                border-radius: 8px;
                height: 28px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: #f4c945;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)
        self.setLayout(layout)

        self.title = QLabel("Update wird installiert")
        self.title.setFont(QFont("Arial", 20, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        self.detail = QLabel("Bereite Update vor...")
        self.detail.setWordWrap(True)
        self.detail.setFont(QFont("Arial", 11, QFont.Bold))
        self.detail.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.detail)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        layout.addWidget(self.progress)

    def set_progress(self, percent, text):
        self.progress.setValue(max(0, min(100, int(percent))))
        self.detail.setText(str(text or ""))


# 
# MainWindow
# 
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wauz Kart")
        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setGeometry(100,100,1400,800)
        self.stack = QStackedWidget(); self.setCentralWidget(self.stack)

        self._version_label = QLabel(f"v{__version__}", self)
        self._version_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._version_label.setStyleSheet("""
            QLabel {
                background: rgba(8, 12, 18, 180);
                color: #ffffff;
                border: 1px solid rgba(255, 204, 0, 170);
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        self._version_label.setFont(QFont("Arial", 9, QFont.Bold))
        self._version_label.show()

        # Badge popup (bottom-right)
        self._badge_popup = QLabel("", self)
        self._badge_popup.setWordWrap(True)
        self._badge_popup.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._badge_popup.setStyleSheet("""
            QLabel{
                background: rgba(20,20,20,220);
                color: #ffffff;
                border: 2px solid #ffcc00;
                border-radius: 10px;
                padding: 10px 12px;
            }
        """)
        self._badge_popup.setFont(QFont("Arial", 11, QFont.Bold))
        self._badge_popup.hide()
        self._badge_popup_timer = QTimer(self)
        self._badge_popup_timer.setSingleShot(True)
        self._badge_popup_timer.timeout.connect(self._badge_popup.hide)
        self._lan_session = None
        self._update_dialog = None
        self._update_signal = _UpdateSignal(self)
        self._update_signal.found.connect(self._show_update_dialog)
        self._update_signal.progress.connect(self._set_update_progress)
        self._update_signal.failed.connect(self._show_update_failed)
        self._update_signal.install.connect(self._start_update_installer)

        self._show_menu()
        self._position_version_label()
        QTimer.singleShot(350, self._first_start_flow)

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        self._position_version_label()
        self._position_badge_popup()

    def _position_version_label(self):
        if not hasattr(self, "_version_label") or self._version_label is None:
            return
        try:
            self._version_label.adjustSize()
            w = self._version_label.width()
            h = self._version_label.height()
            self._version_label.move(max(8, self.width() - w - 12), max(8, self.height() - h - 10))
            self._version_label.raise_()
        except Exception:
            pass

    def _position_badge_popup(self):
        if not hasattr(self, "_badge_popup") or self._badge_popup is None:
            return
        if not self._badge_popup.isVisible():
            return
        try:
            self._badge_popup.adjustSize()
            w = self._badge_popup.width()
            h = self._badge_popup.height()
            version_h = self._version_label.height() if hasattr(self, "_version_label") else 0
            x = max(10, self.width() - w - 22)
            y = max(10, self.height() - h - version_h - 58)
            self._badge_popup.move(x, y)
            self._badge_popup.raise_()
            self._version_label.raise_()
        except Exception:
            pass

    def show_badge_popup(self, badge_name, badge_desc=None):
        badge_desc = badge_desc or ""
        txt = f" Abzeichen freigeschaltet!\n{badge_name}"
        if badge_desc:
            txt += f"\n{badge_desc}"
        self._badge_popup.setText(txt)
        self._badge_popup.show()
        self._position_badge_popup()
        self._badge_popup_timer.start(3500)

    def _show_menu(self):
        self._stop_lan_session()
        wauz_audio.play_menu_music()
        self._clear_stack()
        menu = MenuWidget(self._start_race, on_history=self._show_history)
        self.stack.addWidget(menu); self.stack.setCurrentWidget(menu)
        self._position_version_label()

    def _check_for_updates(self):
        def run_check():
            try:
                update = check_for_update()
            except Exception:
                update = None
            if update:
                self._update_signal.found.emit(update)

        threading.Thread(target=run_check, daemon=True).start()

    def _first_start_flow(self):
        if not has_accepted_terms():
            dlg = TermsDialog(self)
            if dlg.exec_() != QDialog.Accepted:
                QApplication.quit()
                return
            accept_terms()
        QTimer.singleShot(850, self._check_for_updates)

    def _show_update_dialog(self, update):
        if not update:
            return
        latest = update.get("latest", "")
        current = update.get("current", "")
        asset = update.get("asset", "") or "GitHub Release"
        url = update.get("url") or update.get("release_url")

        if not url or not asset:
            return

        self._update_dialog = UpdateProgressDialog(self)
        self._update_dialog.set_progress(
            0,
            f"Neue Version {latest} gefunden. Installiert ist {current}. Lade {asset} herunter...",
        )
        self._update_dialog.show()

        def run_update():
            try:
                target = self._download_update_file(update)
            except Exception as exc:
                self._update_signal.failed.emit(str(exc) or "Unbekannter Download-Fehler.")
                return
            self._update_signal.install.emit(str(target))

        threading.Thread(target=run_update, daemon=True).start()

    def _download_update_file(self, update):
        url = update.get("url") or update.get("release_url")
        asset = update.get("asset") or "wauzkart-update"
        target_dir = Path(tempfile.gettempdir()) / "WauzKartUpdate"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / asset
        if target.exists():
            try:
                target.unlink()
            except Exception:
                pass

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "WauzKart-AutoUpdater"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            with open(target, "wb") as out:
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    if total > 0:
                        percent = int((done / total) * 95)
                    else:
                        percent = min(95, int(done / (1024 * 1024)))
                    self._update_signal.progress.emit(percent, f"Lade Update herunter... {percent}%")
        if str(target).endswith(".sh"):
            try:
                target.chmod(0o755)
            except Exception:
                pass
        self._update_signal.progress.emit(100, "Download fertig. Starte Installation...")
        return target

    def _set_update_progress(self, percent, text):
        if self._update_dialog is not None:
            self._update_dialog.set_progress(percent, text)

    def _show_update_failed(self, text):
        if self._update_dialog is not None:
            self._update_dialog.close()
            self._update_dialog = None
        UpdateHelpDialog(str(text or "Unbekannter Fehler."), self).exec_()

    def _start_update_installer(self, target_text):
        target = Path(target_text)
        try:
            self._set_update_progress(100, "Installation startet. Wauz Kart wird danach neu gestartet...")
            should_quit = self._run_update_installer(target)
            if should_quit:
                QTimer.singleShot(500, QApplication.quit)
            elif self._update_dialog is not None:
                self._update_dialog.set_progress(100, "Update-Datei wurde geoeffnet. Folge dem Installer-Fenster.")
        except Exception as exc:
            self._show_update_failed(str(exc))

    def _run_update_installer(self, target):
        system = platform.system().lower()
        pid = str(os.getpid())
        if system == "windows":
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.Popen(
                [str(target), "--auto-update", "--restart", "--wait-pid", pid],
                cwd=str(target.parent),
                creationflags=flags,
            )
            return True
        if system == "linux":
            args = [str(target), "--auto-update", "--restart", "--wait-pid", pid]
            if shutil.which("pkexec"):
                subprocess.Popen(["pkexec", "env", "DISPLAY=" + os.environ.get("DISPLAY", ""), "XAUTHORITY=" + os.environ.get("XAUTHORITY", ""), *args], cwd=str(target.parent))
                return True
            terminal = shutil.which("x-terminal-emulator") or shutil.which("gnome-terminal") or shutil.which("konsole") or shutil.which("xterm")
            if terminal:
                subprocess.Popen([terminal, "-e", *args], cwd=str(target.parent))
                return True
            subprocess.Popen(args, cwd=str(target.parent))
            return True
        if system == "darwin":
            subprocess.Popen(["open", str(target)], cwd=str(target.parent))
            return False
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
        return False

    def _stop_lan_session(self):
        if self._lan_session is not None:
            try:
                self._lan_session.stop()
            except AttributeError:
                try:
                    self._lan_session.close()
                except Exception:
                    pass
            except Exception:
                pass
            self._lan_session = None

    def _start_race(self, num_humans, diff_name, laps, map_name="Oval", car_colors=None, car_styles=None, characters=None, show_ai_views=False, teams=None, rb_rounds=None, rb_round_time=None, track_size="klein", network_config=None):
        network_config = dict(network_config or {})
        network_server = None
        network_client = None
        local_player_index = int(network_config.get("local_player_index", 0) or 0)

        if network_config.get("mode") == "host":
            lan_settings = {
                "player_count": num_humans,
                "diff_name": diff_name,
                "laps": laps,
                "map_name": map_name,
                "car_colors": car_colors or [],
                "car_styles": car_styles or [],
                "characters": characters or [],
                "track_size": track_size,
            }
            network_server = LanServer(num_humans, lan_settings, port=int(network_config.get("port", LAN_PORT)))
            network_server.start()
            self._lan_session = network_server
        elif network_config.get("mode") == "client":
            network_client = LanClient(network_config.get("host", ""), port=int(network_config.get("port", LAN_PORT)), name=network_config.get("name", "Spieler"))
            network_client.connect()
            self._lan_session = network_client
            settings = network_client.settings
            num_humans = int(settings.get("player_count") or network_client.player_count or num_humans)
            diff_name = settings.get("diff_name", diff_name)
            laps = int(settings.get("laps", laps) or laps)
            map_name = settings.get("map_name", map_name)
            car_colors = settings.get("car_colors", car_colors or [])
            car_styles = settings.get("car_styles", car_styles or [])
            characters = settings.get("characters", characters or [])
            track_size = settings.get("track_size", track_size)
            local_player_index = int(network_client.slot)

        wauz_audio.play_race_music()
        self._clear_stack()

        def finished(players, rec, frames, events):
            # Speichere das Rennen im Hintergrund, um Verzgerung zu vermeiden
            def save_in_background():
                RaceLogger.save_race(players, rec, rec.frames, rec.events, map_name=map_name)
            threading.Thread(target=save_in_background, daemon=True).start()

            # Badges / Stats
            unlock_badge("first_race")
            finished_count = badge_store.inc("races_finished", 1)

            # Coins reward (small, per finished race/match)
            if _wauz_api is not None:
                try:
                    _wauz_api.coins.add(2)
                except Exception:
                    pass
            if finished_count >= 10:
                unlock_badge("ten_races")
            if map_name == "Raeuber & Bulle":
                unlock_badge("first_rb")
                wt = next((getattr(p, "rb_winner_team", None) for p in (players or []) if getattr(p, "rb_winner_team", None)), None)
                if wt == "blau":
                    unlock_badge("rb_win_blau")
                elif wt == "rot":
                    unlock_badge("rb_win_rot")
                if wt in ("blau", "rot"):
                    wins = badge_store.inc("rb_matches_won", 1)
                    if int(wins or 0) >= 5:
                        unlock_badge("rb_champion")
            if global_progression and int(getattr(global_progression, "level", 1)) >= 5:
                unlock_badge("level_5")
            if global_progression and int(getattr(global_progression, "level", 1)) >= 10:
                unlock_badge("ultimate_level")

            # Harder badges for normal races
            if map_name != "Raeuber & Bulle":
                try:
                    if int(laps or 0) >= 10:
                        unlock_badge("long_race")
                except Exception:
                    pass
                try:
                    crash_count = len(getattr(rec, "crash_frames", []) or [])
                    if crash_count == 0:
                        unlock_badge("clean_driver")
                except Exception:
                    pass
                try:
                    overtake_count = len(getattr(rec, "overtake_frames", []) or [])
                    if overtake_count >= 5:
                        unlock_badge("overtake_master")
                except Exception:
                    pass
                try:
                    close_calls = len(getattr(rec, "close_call_frames", []) or [])
                    if close_calls >= 3:
                        unlock_badge("close_call_survivor")
                except Exception:
                    pass
            
            xp_gained, levelups = global_progression.award_xp_after_race(players) if global_progression else (0, [])
            progress = None
            if global_progression:
                progress = {
                    "level": global_progression.level,
                    "xp": global_progression.xp,
                    "need": global_progression.xp_needed_for_next_level(),
                }
            self._show_result(players, rec, frames, events, xp_gained=xp_gained, levelups=levelups, progress=progress, map_name=map_name)
        screen = RaceScreen(num_humans, diff_name, laps, map_name, self._show_menu, finished, car_colors, car_styles, characters, show_ai_views=show_ai_views, teams=teams, rb_rounds=rb_rounds, rb_round_time=rb_round_time, track_size=track_size, network_server=network_server, network_client=network_client, local_player_index=local_player_index)
        self.stack.addWidget(screen); self.stack.setCurrentWidget(screen)
        self._position_version_label()
        screen.setFocus()

    def _show_result(self, players, recorder, frames, events, xp_gained=0, levelups=None, progress=None, map_name=None):
        wauz_audio.stop()
        wauz_audio.play_end_music()
        current = self.stack.currentWidget()
        if hasattr(current, "show_result_overlay"):
            current.show_result_overlay(
                players,
                recorder,
                frames,
                events,
                xp_gained=xp_gained,
                levelups=levelups,
                progress=progress,
                map_name=map_name,
                on_menu=self._show_menu,
                on_replay=lambda: self._show_replay(frames, events, players, recorder, xp_gained, levelups, progress, map_name),
                on_history=self._show_history,
            )
            return
        self._clear_stack()
        result = ResultWidget(players, recorder,
            on_menu=self._show_menu,
            on_replay=lambda: self._show_replay(frames, events, players, recorder, xp_gained, levelups, progress, map_name),
            on_history=self._show_history,
            xp_gained=xp_gained,
            levelups=levelups,
            progress=progress,
            map_name=map_name)
        self.stack.addWidget(result); self.stack.setCurrentWidget(result)
        self._position_version_label()

    def _show_replay(self, frames, events, players, recorder, xp_gained=0, levelups=None, progress=None, map_name=None):
        wauz_audio.stop()
        wauz_audio.play_highlight_music()
        unlock_badge("first_highlight")
        try:
            watched = badge_store.inc("highlights_watched", 1)
            if int(watched or 0) >= 5:
                unlock_badge("highlight_addict")
        except Exception:
            pass
        try:
            best_index = 0
            last_index = max(0, len(players or []) - 1)
            last_place = -1
            for i, pl in enumerate(players or []):
                if getattr(pl, "finish_place", None) == 1:
                    best_index = i
                place = getattr(pl, "finish_place", None)
                if place is not None and int(place) >= last_place:
                    last_place = int(place)
                    last_index = i
            highlight_frames, highlight_events = recorder.get_highlight(best_index=best_index, last_index=last_index) if recorder is not None else (frames, events)
        except Exception:
            highlight_frames, highlight_events = frames, events
        if not highlight_frames:
            highlight_frames, highlight_events = frames, events
        self._clear_stack()
        replay = ReplayScreen(
            highlight_frames,
            highlight_events,
            on_back=lambda: self._show_result(players, recorder, frames, events, xp_gained=xp_gained, levelups=levelups, progress=progress, map_name=map_name),
            map_name=map_name,
            player_names=[p.name for p in (players or [])],
        )
        self.stack.addWidget(replay); self.stack.setCurrentWidget(replay)
        self._position_version_label()

    def _show_history(self):
        wauz_audio.stop()
        unlock_badge("watch_history")
        try:
            opened = badge_store.inc("history_opened", 1)
            if int(opened or 0) >= 5:
                unlock_badge("historian")
        except Exception:
            pass
        self._clear_stack()
        hist = HistoryWidget(on_back=self._show_menu,
                              on_show_race=self._open_history_race)
        self.stack.addWidget(hist); self.stack.setCurrentWidget(hist)
        self._position_version_label()

    def _open_history_race(self, path, data):
        wauz_audio.stop()
        frames, events = RaceLogger.extract_highlight(data)
        map_name = data.get("map_name")
        players = []
        for pd in data.get('players',[]):
            pl = Player(0,0,0,(0,0,0),pd.get('name'), is_ai=pd.get('is_ai',False))
            pl.laps = pd.get('laps',0)
            pl.finish_time = (data['timestamp'] + pd.get('finish_time',0)) if pd.get('finish_time') else None
            pl.start_time = data['timestamp']
            pl.finish_place = pd.get('finish_place')
            pl.color = tuple(pd.get('color', (255,255,255)))
            pl.style = pd.get('style', 'Standard')
            pl.character = pd.get('character')
            players.append(pl)
        self._clear_stack()
        
        # Erstelle einen Result Screen fuer die History
        if map_name == "Raeuber & Bulle":
            class RBHistoryResultScreen(QWidget):
                def __init__(self, data, frames, events, on_replay, on_back):
                    super().__init__()
                    self.setStyleSheet("background:#111111;")
                    lay = QVBoxLayout(); lay.setAlignment(Qt.AlignTop); self.setLayout(lay)

                    title = QLabel(" Raeuber & Bulle  Match")
                    title.setFont(QFont("Arial", 28, QFont.Bold))
                    title.setStyleSheet("color:#ffcc00;")
                    title.setAlignment(Qt.AlignCenter)
                    lay.addWidget(title); lay.addSpacing(12)

                    wt = data.get("rb_winner_team")
                    if wt not in ("blau", "rot"):
                        wt = next((p.get("rb_winner_team") for p in data.get("players", []) if p.get("rb_winner_team") in ("blau", "rot")), None)

                    winner_txt = "Gewinner: Down"
                    winner_col = "#dddddd"
                    if wt == "blau":
                        winner_txt = "Gewinner: Blau"
                        winner_col = "#66aaff"
                    elif wt == "rot":
                        winner_txt = "Gewinner: Rot"
                        winner_col = "#ff6666"

                    wlbl = QLabel(winner_txt)
                    wlbl.setFont(QFont("Arial", 20, QFont.Bold))
                    wlbl.setStyleSheet(f"color:{winner_col};")
                    wlbl.setAlignment(Qt.AlignCenter)
                    lay.addWidget(wlbl); lay.addSpacing(8)

                    sb = data.get("rb_score_blau")
                    sr = data.get("rb_score_rot")
                    rt = data.get("rb_total_rounds")
                    if sb is not None and sr is not None and rt is not None:
                        score = QLabel(f"Match:  {int(sb)}     {int(sr)}   (Runden: {int(rt)})")
                        score.setFont(QFont("Arial", 14, QFont.Bold))
                        score.setStyleSheet("color:#dddddd;")
                        score.setAlignment(Qt.AlignCenter)
                        lay.addWidget(score); lay.addSpacing(12)

                    lay.addSpacing(16)
                    br_lay = QHBoxLayout()
                    replay_btn = QPushButton("  Highlights anschauen")
                    replay_btn.setFont(QFont("Arial", 12))
                    replay_btn.setStyleSheet("background:#ff6600;color:#fff;border-radius:6px;padding:8px;")
                    replay_btn.clicked.connect(on_replay)
                    br_lay.addWidget(replay_btn)

                    back_btn = QPushButton(" Zurueck")
                    back_btn.setFont(QFont("Arial", 12))
                    back_btn.setStyleSheet("background:#444;color:#fff;border-radius:6px;padding:8px;")
                    back_btn.clicked.connect(on_back)
                    br_lay.addWidget(back_btn)

                    lay.addLayout(br_lay)

            result_screen = RBHistoryResultScreen(
                data, frames, events,
                on_replay=lambda: self._show_history_replay(frames, events, map_name=map_name, player_names=[p.name for p in (players or [])]),
                on_back=self._show_history
            )
            self.stack.addWidget(result_screen); self.stack.setCurrentWidget(result_screen)
            self._position_version_label()
            return

        class HistoryResultScreen(QWidget):
            def __init__(self, players, frames, events, on_replay, on_back):
                super().__init__()
                self.setStyleSheet("background:#111111;")
                lay = QVBoxLayout(); lay.setAlignment(Qt.AlignTop); self.setLayout(lay)
                
                # Titel
                title = QLabel(" Renndetails")
                title.setFont(QFont("Arial", 28, QFont.Bold))
                title.setStyleSheet("color:#ffcc00;")
                title.setAlignment(Qt.AlignCenter)
                lay.addWidget(title); lay.addSpacing(12)
                
                # Sortiere Spieler nach Platzierung
                sorted_players = sorted(players, key=lambda p: p.finish_place if p.finish_place else 999)
                medals = ["", "", ""]
                for i, pl in enumerate(sorted_players):
                    medal = medals[i] if i < 3 else f"{i+1}."
                    time_str = f"{pl.finish_time:.2f}s" if pl.finish_time else "DNF"
                    result_txt = f"{medal} {pl.name}: {time_str}"
                    lbl = QLabel(result_txt)
                    lbl.setFont(QFont("Courier", 16))
                    lbl.setStyleSheet("color:#ffffff;")
                    lbl.setAlignment(Qt.AlignCenter)
                    lay.addWidget(lbl); lay.addSpacing(6)
                
                lay.addSpacing(16)
                
                # Buttons
                br_lay = QHBoxLayout()
                replay_btn = QPushButton("  Highlights anschauen")
                replay_btn.setFont(QFont("Arial", 12))
                replay_btn.setStyleSheet("background:#ff6600;color:#fff;border-radius:6px;padding:8px;")
                replay_btn.clicked.connect(on_replay)
                br_lay.addWidget(replay_btn)
                
                back_btn = QPushButton(" Zurueck")
                back_btn.setFont(QFont("Arial", 12))
                back_btn.setStyleSheet("background:#444;color:#fff;border-radius:6px;padding:8px;")
                back_btn.clicked.connect(on_back)
                br_lay.addWidget(back_btn)
                
                lay.addLayout(br_lay)
        
        result_screen = HistoryResultScreen(
            players, frames, events,
            on_replay=lambda: self._show_history_replay(frames, events, map_name=map_name, player_names=[p.name for p in (players or [])]),
            on_back=self._show_history
        )
        self.stack.addWidget(result_screen); self.stack.setCurrentWidget(result_screen)
        self._position_version_label()
    
    def _show_history_replay(self, frames, events, map_name=None, player_names=None):
        wauz_audio.stop()
        wauz_audio.play_highlight_music()
        unlock_badge("first_highlight")
        try:
            watched = badge_store.inc("highlights_watched", 1)
            if int(watched or 0) >= 5:
                unlock_badge("highlight_addict")
        except Exception:
            pass
        self._clear_stack()
        replay = ReplayScreen(frames, events, on_back=lambda: self._show_history(), map_name=map_name, player_names=player_names)
        self.stack.addWidget(replay); self.stack.setCurrentWidget(replay)
        self._position_version_label()

    def _clear_stack(self):
        while self.stack.count():
            w = self.stack.widget(0); self.stack.removeWidget(w); w.deleteLater()
