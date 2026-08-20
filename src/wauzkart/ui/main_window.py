from ..runtime import *
from ..audio.sound import wauz_audio
from ..data.progression import RaceLogger, badge_store, global_progression, unlock_badge
from ..game.entities import Player
from ..network.lan import LAN_PORT, LanClient, LanServer
from ..paths import ASSETS_DIR, _wauz_api
from .history import HistoryWidget
from .menu import MenuWidget
from .race_screen import RaceScreen
from .replay_screen import ReplayScreen
from .results import ResultWidget

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

        self._show_menu()

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
        except Exception:
            pass
        self._position_badge_popup()

    def _position_badge_popup(self):
        if not hasattr(self, "_badge_popup") or self._badge_popup is None:
            return
        if not self._badge_popup.isVisible():
            return
        try:
            self._badge_popup.adjustSize()
            w = self._badge_popup.width()
            h = self._badge_popup.height()
            x = max(10, self.width() - w - 22)
            y = max(10, self.height() - h - 48)
            self._badge_popup.move(x, y)
            self._badge_popup.raise_()
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

    def _clear_stack(self):
        while self.stack.count():
            w = self.stack.widget(0); self.stack.removeWidget(w); w.deleteLater()
