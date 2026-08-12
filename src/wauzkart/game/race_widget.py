from ..runtime import *
from ..audio.sound import WauzCartAudio
from ..core.rendering import (
    _draw_ground,
    _draw_kart_model,
    _draw_track_decoration,
    _draw_track_ribbon,
    _gl_box,
    _gl_box_lit,
    _hud_text_color_for_rgb,
)
from ..core.tuning import _clamp, apply_drive_tuning
from ..data.progression import unlock_badge
from ..game.entities import Player, Particle, SpeedBoostItem, ItemBox, spawn_explosion
from ..game.highlights import HighlightRecorder
from ..tracks.maps import *

# 
# GL-Rennwidget  (untersttzt 1-4 Spieler)
# 
class RaceWidget(QOpenGLWidget):
    def __init__(self, num_humans, ai_diff_name, win_laps, map_name="Oval", car_colors=None, car_styles=None, characters=None, parent=None, show_ai_views=False, teams=None, rb_rounds=None, rb_round_time=None, track_size="klein"):
        super().__init__(parent)
        self.car_colors = car_colors or []
        self.car_styles = car_styles or []
        self.characters = characters or []
        self.setFocusPolicy(Qt.StrongFocus)
        self.last_time    = time.time()
        self.frame_idx    = 0
        self.timer        = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)
        self.num_humans   = num_humans
        self.teams = teams or []
        self.show_ai_views = bool(show_ai_views)
        self.camera_mode = 0
        self.win_laps     = win_laps
        self.map_name     = map_name
        self.track_size   = track_size if map_name != "Raeuber & Bulle" else "klein"
        self.map_config   = make_track_config_for_size(map_name, self.track_size)
        self.obstacles    = self.map_config.get("obstacles", [])

        # Raeuber & Bulle: Rollen-Mapping muss existieren, bevor Spieler gebaut werden
        # (da _rb_apply_roles_to_players() im Player-Setup aufgerufen wird).
        if map_name == "Raeuber & Bulle":
            self.rb_role_blau = "bulle"
            self.rb_role_rot = "raeuber"
        
        # Hole Map-spezifische Gren und Positionen
        self.outer_r = self.map_config.get('outer_base', OUTER_R)
        self.inner_r = self.map_config.get('inner_base', INNER_R)
        self.mid_r = (self.outer_r + self.inner_r) / 2
        self.start_positions = self.map_config.get('start_positions', START_POSITIONS)
        self.parking_spots = self.map_config.get('parking_spots', PARKING_SPOTS)
        self.obstacles = self._prepare_obstacles(self.obstacles)

        diff = AI_DIFFICULTIES[ai_diff_name]
        def make_ai_diff():
            d = dict(diff)
            d['speed'] = d['speed'] * random.uniform(0.96, 1.04)
            d['wobble']= d['wobble']* random.uniform(0.8, 1.2)
            return d

        # Erstelle alle Fahrzeuge
        # Fuer Raeuber & Bulle: Menschliche Spieler koennen mitspielen, Teams zuweisen
        if map_name == "Raeuber & Bulle":
            # Es sollen insgesamt 12 Spieler in diesem Modus sein
            num_ai = max(0, 12 - num_humans)
        else:
            num_ai = max(0, 4 - num_humans)

        self.players = []

        used_colors = set()
        used_chars = set()

        def pick_unique_color(preferred=None):
            if preferred is not None and preferred not in used_colors:
                used_colors.add(preferred)
                return preferred
            for c in ALL_CAR_COLORS:
                if c not in used_colors:
                    used_colors.add(c)
                    return c
            # Fallback (sollte bei max 4 Autos nie passieren)
            while True:
                c = (random.random(), random.random(), random.random())
                if c not in used_colors:
                    used_colors.add(c)
                    return c

        def pick_unique_character(preferred=None):
            if not CHARACTER_NAMES:
                return None
            if preferred is not None and preferred in CHARACTER_NAMES and preferred not in used_chars:
                used_chars.add(preferred)
                return preferred
            for ch in CHARACTER_NAMES:
                if ch not in used_chars:
                    used_chars.add(ch)
                    return ch
            ch = random.choice(CHARACTER_NAMES)
            used_chars.add(ch)
            return ch

        if map_name == "Raeuber & Bulle":
            rb_color_team_colors = {
                "rot": (1.0, 0.2, 0.2),
                "blau": (0.2, 0.5, 1.0),
            }

            def normalize_rb_color_team(value, fallback):
                if value is None:
                    return fallback
                try:
                    t = str(value).strip().lower()
                except Exception:
                    return fallback
                if t in ("blau", "blue", "mauz", "mauz team", "mauzteam"):
                    return "blau"
                if t in ("rot", "red", "wauz", "wauz team", "wauzteam"):
                    return "rot"
                return fallback

            # Startpositionen sind (in der Map-Config) nach Teams sortiert:
            # erste 6 = Rot-Team, zweite 6 = Blau-Team.
            sp = list(self.start_positions) if self.start_positions else []
            rot_spawns = sp[:6]
            blau_spawns = sp[6:12]

            def next_spawn(color_team):
                if color_team == "rot" and rot_spawns:
                    return rot_spawns.pop(0)
                if color_team == "blau" and blau_spawns:
                    return blau_spawns.pop(0)
                # Fallback: nimm was noch da ist
                if rot_spawns:
                    return rot_spawns.pop(0)
                if blau_spawns:
                    return blau_spawns.pop(0)
                return (0, 0, 0)

            # Farb-Teams der menschlichen Spieler (falls nicht geliefert -> Auto)
            human_color_teams = []
            for i in range(num_humans):
                raw = self.teams[i] if i < len(self.teams) else None
                human_color_teams.append(normalize_rb_color_team(raw, "blau" if i % 2 == 0 else "rot"))

            # Menschliche Spieler erstellen (Farbe = Teamfarbe; Rolle wird pro Runde gesetzt)
            for i in range(num_humans):
                cfg = PLAYER_CONFIGS[i]
                color_team = human_color_teams[i]
                sx, sz, srot = next_spawn(color_team)

                style = self.car_styles[i] if i < len(self.car_styles) else "Standard"
                character = self.characters[i] if i < len(self.characters) else None
                character = pick_unique_character(character)

                col = rb_color_team_colors.get(color_team, (1.0, 1.0, 1.0))
                pl = Player(sx, sz, srot, col, cfg["name"], is_ai=False, style=style, character=character, team=None)
                pl.rb_color_team = color_team
                apply_drive_tuning(pl)
                self.players.append(pl)

            # KI auffllen: exakt 6 vs 6 (Farb-Teams)
            human_blau = human_color_teams.count("blau")
            human_rot = human_color_teams.count("rot")
            need_blau = max(0, 6 - human_blau)
            need_rot = max(0, 6 - human_rot)

            for i in range(need_blau):
                sx, sz, srot = next_spawn("blau")
                character = pick_unique_character()
                pl = Player(
                    sx, sz, srot,
                    rb_color_team_colors["blau"],
                    f"KI Blau {i+1}",
                    is_ai=True,
                    ai_diff=make_ai_diff(),
                    style="Standard",
                    character=character,
                    team=None,
                )
                pl.rb_color_team = "blau"
                apply_drive_tuning(pl)
                self.players.append(pl)

            for i in range(need_rot):
                sx, sz, srot = next_spawn("rot")
                character = pick_unique_character()
                pl = Player(
                    sx, sz, srot,
                    rb_color_team_colors["rot"],
                    f"KI Rot {i+1}",
                    is_ai=True,
                    ai_diff=make_ai_diff(),
                    style="Standard",
                    character=character,
                    team=None,
                )
                pl.rb_color_team = "rot"
                apply_drive_tuning(pl)
                self.players.append(pl)

            # Rollen initial anwenden (Runde 1)
            self._rb_apply_roles_to_players()
        else:
            # Normale Rennen: menschliche und KI-Spieler
            for i in range(num_humans):
                cfg = PLAYER_CONFIGS[i]
                sx, sz, srot = self.start_positions[i]
                color = cfg["color"]
                style = "Standard"
                character = None
                # override with selected color/style if provided
                if i < len(self.car_colors):
                    color = self.car_colors[i]
                if i < len(self.car_styles):
                    style = self.car_styles[i]
                if i < len(self.characters):
                    character = self.characters[i]
                color = pick_unique_color(color)
                character = pick_unique_character(character)
                pl = Player(sx, sz, srot, color, cfg["name"], is_ai=False, style=style, character=character)
                apply_drive_tuning(pl)
                self.players.append(pl)

            for i in range(num_ai):
                slot = num_humans + i
                sx, sz, srot = self.start_positions[slot]
                preferred = None
                if slot < len(self.car_colors):
                    preferred = self.car_colors[slot]
                else:
                    preferred = AI_COLORS[i % len(AI_COLORS)] if AI_COLORS else None
                col = pick_unique_color(preferred)
                style = "Standard"
                character = None
                if slot < len(self.car_styles):
                    style = self.car_styles[slot]
                if slot < len(self.characters):
                    character = self.characters[slot]
                character = pick_unique_character(character)
                pl = Player(sx, sz, srot, col, AI_NAMES[i], is_ai=True, ai_diff=make_ai_diff(), style=style, character=character)
                apply_drive_tuning(pl)
                self.players.append(pl)

        self.winner         = None
        self.finish_counter = 0
        self.keys           = {}
        self.countdown_phase= 'idle'
        self.phase_timer    = time.time()
        self.race_over      = False
        self.result_live_preview = False
        self.human_finish_overtime_started_at = None
        self.human_finish_overtime_duration = 10.0
        self.parking_occupied = [False] * len(self.parking_spots)
        self.last_positions = []
        self.pending_attacks = []  # flying item attacks

        self.recorder = HighlightRecorder()
        self.recorder.start()

        # Raeuber & Bulle Timer
        self.rb_total_rounds = max(4, int(rb_rounds or 4)) if map_name == "Raeuber & Bulle" else None
        self.rb_round_time_limit = float(rb_round_time or 180) if map_name == "Raeuber & Bulle" else None
        self.rb_round_index = 1 if map_name == "Raeuber & Bulle" else None
        self.rb_score_blau = 0
        self.rb_score_rot = 0
        self.rb_match_tiebreaker = None
        # Rollen pro Runde (Team bleibt fix: blau/rot)
        self.rb_role_blau = "bulle" if map_name == "Raeuber & Bulle" else None
        self.rb_role_rot = "raeuber" if map_name == "Raeuber & Bulle" else None
        self.game_timer = (self.rb_round_time_limit if map_name == "Raeuber & Bulle" else None)
        self.rb_winner_team = None
        self.rb_button_pos = (0.0, 5.0)
        self.rb_button_radius = 3.5
        self.rb_button_hold_required = 1.0
        self.rb_button_hold = 0.0
        self.rb_button_cooldown_until = 0.0
        self.rb_catch_radius = 4.2
        self.rb_jail_pos = (0.0, 10.0)
        self.rb_guard_radius = 4.0

        # Power-ups / Items (fuer Raeuber & Bulle deaktiviert)
        self.powerups_enabled = (map_name != "Raeuber & Bulle")

        self.items = []
        self.powerup_spawn_interval = 2.5
        self.max_powerups = 16 if self.powerups_enabled else 0
        self.next_powerup_spawn_time = (time.time() + 1.0) if self.powerups_enabled else float("inf")

        # Item-Boxen (feste Pltze) + initiale Power-ups
        self.item_boxes = []
        self.oil_slicks = []
        self.item_box_item_pool = []
        if self.powerups_enabled:
            self._init_item_boxes()
            self.item_box_item_pool = ["abknaller", "turbo", "wirbler", "schild", "frost", "oelspur"]
            for _ in range(10):
                self._spawn_random_powerup()

        self.on_race_over = None  # callback  MainWindow
        self.on_rb_round_over = None  # callback  RaceScreen (between rounds)
        self.rb_between_rounds = False
        self.rb_last_round_winner = None
        self.rb_last_round_index = None

    def _prepare_obstacles(self, obstacles):
        """Move obstacles onto the track and away from the start line / grid."""
        if not obstacles:
            return []

        # Open-square maps use absolute obstacle coordinates from the config.
        # Do not "snap" them onto the circular track ring.
        if self.map_config.get("type") == "open_square":
            prepared = []
            for ob in obstacles:
                try:
                    prepared.append({
                        "x": float(ob.get("x", 0.0)),
                        "z": float(ob.get("z", 0.0)),
                        "w": float(ob.get("w", 3.0)),
                        "l": float(ob.get("l", 3.0)),
                        "h": float(ob.get("h", 1.0)),
                        "color": ob.get("color", (0.8, 0.2, 0.2)),
                    })
                except Exception:
                    continue
            return prepared

        outer_mod = self.map_config.get('outer_mod')
        inner_mod = self.map_config.get('inner_mod')
        outer_base = self.map_config.get('outer_base', self.outer_r)
        inner_base = self.map_config.get('inner_base', self.inner_r)

        prepared = []
        for ob in obstacles:
            try:
                ox = float(ob.get("x", 0))
                oz = float(ob.get("z", 0))
                w = float(ob.get("w", 3.0))
                l = float(ob.get("l", 3.0))
                h = float(ob.get("h", 1.0))
                col = ob.get("color", (0.8, 0.2, 0.2))
            except Exception:
                continue

            # derive angle from provided position; if (0,0) use a safe default angle
            if abs(ox) < 1e-6 and abs(oz) < 1e-6:
                angle = 90.0
            else:
                angle = math.degrees(math.atan2(oz, ox))

            # Avoid start line region (angle ~ 0 = +X axis where the stripe is drawn)
            norm = ((angle + 180) % 360) - 180
            if abs(norm) < 25:
                angle = 35.0 if norm >= 0 else -35.0

            # Place obstacle on the drivable ring at that angle
            a = (angle + 360) % 360
            inner = (inner_base * (inner_mod(a) if inner_mod else 1.0))
            outer = (outer_base * (outer_mod(a) if outer_mod else 1.0))
            if outer <= inner + 1.0:
                continue
            target_r = inner + (outer - inner) * 0.62

            rad = math.radians(angle)
            ox = math.cos(rad) * target_r
            oz = math.sin(rad) * target_r

            # Keep distance from start grid positions
            for sx, sz, _ in self.start_positions:
                dx = ox - sx
                dz = oz - sz
                if dx * dx + dz * dz < (10.0 ** 2):
                    angle += 22.0
                    rad = math.radians(angle)
                    ox = math.cos(rad) * target_r
                    oz = math.sin(rad) * target_r

            prepared.append({"x": ox, "z": oz, "w": w, "l": l, "h": h, "color": col})

        # quick separation pass so obstacles don't stack
        for _ in range(3):
            changed = False
            for i in range(len(prepared)):
                for j in range(i + 1, len(prepared)):
                    dx = prepared[i]["x"] - prepared[j]["x"]
                    dz = prepared[i]["z"] - prepared[j]["z"]
                    if dx * dx + dz * dz < (7.0 ** 2):
                        # rotate j a bit
                        ang = math.degrees(math.atan2(prepared[j]["z"], prepared[j]["x"])) + 18.0
                        rad = math.radians(ang)
                        rr = math.sqrt(prepared[j]["x"] ** 2 + prepared[j]["z"] ** 2)
                        prepared[j]["x"] = math.cos(rad) * rr
                        prepared[j]["z"] = math.sin(rad) * rr
                        changed = True
            if not changed:
                break

        return prepared

    #  Countdown 
    def update_countdown(self):
        if self.countdown_phase == "paused":
            return
        e = time.time() - self.phase_timer
        if   self.countdown_phase=='idle'  and e>=0.8: self._set_phase('three')
        elif self.countdown_phase=='three' and e>=1.0: self._set_phase('two')
        elif self.countdown_phase=='two'   and e>=1.0: self._set_phase('one')
        elif self.countdown_phase=='one'   and e>=1.0: self._set_phase('go')
        elif self.countdown_phase=='go'    and e>=0.7: self._set_phase('racing')

    def _set_phase(self, phase):
        self.countdown_phase = phase
        self.phase_timer = time.time()
        if phase == 'racing':
            now = time.time()
            for pl in self.players:
                pl.start_time = now
                if pl.rocket_boost:
                    pl.velocity = pl.max_speed*(0.4+pl.boost_amount*0.6)

    def get_countdown_text(self):
        return {'three':'3!','two':'2!','one':'1!','go':'GO!'}.get(self.countdown_phase,'')

    def is_racing(self): return self.countdown_phase=='racing'

    def rb_start_next_round(self):
        """Start next RB round after pause dialog."""
        if self.map_name != "Raeuber & Bulle":
            return
        if self.race_over:
            return
        if not self.rb_between_rounds:
            return

        self.rb_between_rounds = False
        self.rb_last_round_winner = None
        self.rb_last_round_index = None

        # advance to next round number
        self.rb_round_index = int(getattr(self, "rb_round_index", 1) or 1) + 1
        self._rb_swap_teams()
        self.game_timer = float(self.rb_round_time_limit or 180.0)
        self.countdown_phase = 'idle'
        self.phase_timer = time.time()

    def register_rocket(self, key):
        """Rocket-Start bei '2!' fuer alle menschlichen Spieler."""
        if self.countdown_phase != 'two': return
        e = time.time() - self.phase_timer
        for i in range(self.num_humans):
            fwd_key = PLAYER_CONFIGS[i]["keys"][0]
            if key == fwd_key:
                pl = self.players[i]
                pl.rocket_boost = True
                pl.boost_amount = max(pl.boost_amount, e)

    #  GL 
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND)
        glShadeModel(GL_SMOOTH)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.50, 0.68, 0.88, 1)

    def resizeGL(self,w,h): glViewport(0,0,w,h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        now = time.time()
        dt  = min(now-self.last_time, 0.05)
        self.last_time = now
        self.frame_idx += 1

        self.update_countdown()

        if self.map_name == "Raeuber & Bulle" and self.rb_between_rounds:
            # Draw current state, but freeze gameplay logic until user continues.
            self._draw_track()
            for pl in self.players:
                self._draw_car(pl)
            return

        if self.is_racing() and not self.race_over:
            # Timer fuer Raeuber & Bulle
            if self.game_timer is not None:
                self.game_timer -= dt
                if self.game_timer <= 0:
                    self._end_race_raeuber_win()

        if self.is_racing() and not self.race_over:
            # Menschliche Spieler updaten
            for i in range(self.num_humans):
                keys_cfg = PLAYER_CONFIGS[i]["keys"]  # (fwd, bwd, left, right)
                self._update_player(self.players[i], dt, *keys_cfg)

            # KI-Spieler updaten
            for i in range(self.num_humans, len(self.players)):
                self._update_ai(self.players[i], dt)

            # Kollisionen
            for i in range(len(self.players)):
                for j in range(i+1,len(self.players)):
                    self._collision(self.players[i], self.players[j])

            # Raeuber & Bulle: Fangen-Mechanik und Freilassung
            if self.map_name == "Raeuber & Bulle":
                for bulle in self.players:
                    if bulle.team == "bulle":
                        for raeuber in self.players:
                            if raeuber.team == "raeuber" and not raeuber.rb_caught and not raeuber.finished:
                                dx = raeuber.pos[0] - bulle.pos[0]
                                dz = raeuber.pos[2] - bulle.pos[2]
                                dist = math.sqrt(dx**2 + dz**2)
                                if dist < self.rb_catch_radius and now > raeuber.shield_until:
                                    # Raeuber ins Gefaengnis teleportieren
                                    raeuber.rb_caught = True
                                    raeuber.rb_caught_at = now
                                    raeuber.pos[0] = self.rb_jail_pos[0]
                                    raeuber.pos[2] = self.rb_jail_pos[1]
                                    raeuber.rot = 180  # Nach Sden schauen
                                    raeuber.velocity = 0
                                    unlock_badge("rb_catch_robber")
                                    try:
                                        catches = badge_store.inc("rb_catches_total", 1)
                                        if int(catches or 0) >= 5:
                                            unlock_badge("rb_hunter")
                                    except Exception:
                                        pass
                                    # berprfe, ob alle Raeuber gefangen
                                    all_caught = all(getattr(p, "rb_caught", False) for p in self.players if p.team == "raeuber")
                                    if all_caught:
                                        self._end_race_bulle_win()
                
                # Freilassung: Raeuber muss den gruenen Knopf kurz "halten" (Cooldown + Bullen koennen blocken)
                any_caught = any(p.team == "raeuber" and p.rb_caught for p in self.players)
                if not any_caught or now < self.rb_button_cooldown_until:
                    self.rb_button_hold = max(0.0, self.rb_button_hold - dt * 2.0)
                else:
                    button_x, button_z = self.rb_button_pos

                    robber_on_button = False
                    for raeuber in self.players:
                        if raeuber.team != "raeuber" or raeuber.rb_caught or raeuber.finished:
                            continue
                        dx = raeuber.pos[0] - button_x
                        dz = raeuber.pos[2] - button_z
                        if math.sqrt(dx * dx + dz * dz) < self.rb_button_radius:
                            robber_on_button = True
                            break

                    min_bull_dist = float("inf")
                    for bulle in self.players:
                        if bulle.team != "bulle" or bulle.finished:
                            continue
                        dx = bulle.pos[0] - button_x
                        dz = bulle.pos[2] - button_z
                        dist = math.sqrt(dx * dx + dz * dz)
                        if dist < min_bull_dist:
                            min_bull_dist = dist

                    # Block-Logik: Ein Bulle kann den Knopf blocken, aber wenn der Raeuber
                    # den Knopf berhrt, soll direkt befreit werden (kein "Hold").
                    hard_block = min_bull_dist < 2.2

                    if robber_on_button and not hard_block:
                        self.rb_button_hold = 0.0
                        self.rb_button_cooldown_until = now + 12.0
                        unlock_badge("rb_free_someone")
                        try:
                            frees = badge_store.inc("rb_frees_total", 1)
                            if int(frees or 0) >= 3:
                                unlock_badge("rb_rescuer")
                        except Exception:
                            pass

                        def safe_spawn_point():
                            # Versuche, nicht direkt in Bullen zu spawnen.
                            bound = max(25.0, float(getattr(self, "outer_r", 65.0)) - 8.0)
                            for _ in range(40):
                                x = random.uniform(-bound, bound)
                                z = random.uniform(-bound, bound)
                                ok = True
                                for b in self.players:
                                    if b.team != "bulle" or b.finished:
                                        continue
                                    dx = x - b.pos[0]
                                    dz = z - b.pos[2]
                                    if (dx * dx + dz * dz) < (12.0 * 12.0):
                                        ok = False
                                        break
                                if ok:
                                    return x, z
                            return random.uniform(-bound, bound), random.uniform(-bound, bound)

                        # Alle gefangenen Raeuber befreien
                        for raeuber in self.players:
                            if raeuber.team == "raeuber" and raeuber.rb_caught:
                                raeuber.rb_caught = False
                                raeuber.rb_caught_at = None
                                raeuber.pos[0], raeuber.pos[2] = safe_spawn_point()
                                raeuber.rot = random.uniform(0, 360)
                                raeuber.velocity = 0
                                raeuber.shield_until = now + 3.5
                    else:
                        # optional: wenn geblockt oder keiner drauf steht, nichts aufladen
                        self.rb_button_hold = 0.0

            if getattr(self, "powerups_enabled", True):
                # Power-ups spawnen / despawnen
                self._update_powerups(now)
                self._update_oil_slicks(now)

                # Item-Sammlung berprfen
                for pl in self.players:
                    if pl.finished:
                        continue
                    if self.map_name == "Raeuber & Bulle" and getattr(pl, "rb_caught", False):
                        continue
                    for item in self.items:
                        if item.is_active(now) and item.is_nearby(pl.pos, radius=1.5):
                            item.collected = True
                            item.collected_by = pl
                            self._apply_speed_boost(pl)

                # Item-Boxen (feste Pltze, regenerieren)
                for pl in self.players:
                    if pl.finished:
                        continue
                    if self.map_name == "Raeuber & Bulle" and getattr(pl, "rb_caught", False):
                        continue
                    for box in self.item_boxes:
                        if box.is_available(now) and box.is_nearby(pl.pos, radius=1.6):
                            # KI-Abklingzeit: alle 5 Sekunden erst wieder ein Kstchen
                            if pl.is_ai and (now - pl.last_box_collected_time) < 5.0:
                                continue
                            box.consume(now)
                            pl.last_box_collected_time = now
                            self._grant_item(pl, self._choose_item_from_box(), now)

                # Auto-Use Items ausfhren
                self._update_pending_items(now)

                # Verzgerte Angriffe (z.B. Abknaller/Wirbler) ausfhren
                self._process_pending_attacks(now)
                # Incoming-Angriff-Marker abrumen (Anzeige bleibt kurz nach Treffer)
                for pl in self.players:
                    if pl.incoming_attack_until and now >= pl.incoming_attack_until:
                        pl.incoming_attack_type = None
                        pl.incoming_attack_from = None
                        pl.incoming_attack_execute_time = 0.0
                        pl.incoming_attack_until = 0.0

            # berholung-Erkennung
            self._check_overtakes()
            self._update_human_finish_overtime(now)
        elif self.race_over and getattr(self, "result_live_preview", False):
            for pl in self.players:
                if pl.finished:
                    self._update_finish_ghost(pl, dt)
                for p in pl.particles[:]:
                    p.update(dt)
                    if p.life<=0: pl.particles.remove(p)
        else:
            for pl in self.players:
                for p in pl.particles[:]:
                    p.update(dt)
                    if p.life<=0: pl.particles.remove(p)

        self.recorder.record(self.players, self.frame_idx, self._capture_replay_world(now))

        w, h = self.width(), self.height()

        #  Kamera-Split 
        view_idxs = self._view_player_indices()
        if self.show_ai_views:
            # Immer 4 Teile (22)  freie Viewports zeigen KI
            half_w = w // 2
            half_h = h // 2
            rects = [
                (0, half_h, half_w, half_h),         # oueben links
                (half_w, half_h, half_w, half_h),    # oueben rechts
                (0, 0, half_w, half_h),              # unten links
                (half_w, 0, half_w, half_h),         # unten rechts
            ]
            for i, (vx, vy, vw, vh) in enumerate(rects):
                pidx = view_idxs[i] if i < len(view_idxs) else 0
                glViewport(vx, vy, vw, vh)
                self._draw_viewport(self.players[pidx], vw, vh)
        else:
            if self.num_humans <= 1:
                glViewport(0, 0, w, h)
                pidx = view_idxs[0] if view_idxs else 0
                self._draw_viewport(self.players[pidx], w, h)
            elif self.num_humans == 2:
                half_w = w // 2
                glViewport(0, 0, half_w, h)
                self._draw_viewport(self.players[view_idxs[0]], half_w, h)
                glViewport(half_w, 0, half_w, h)
                self._draw_viewport(self.players[view_idxs[1]], half_w, h)
            elif self.num_humans == 3:
                half_w = w // 2
                half_h = h // 2
                glViewport(0, half_h, half_w, half_h)
                self._draw_viewport(self.players[view_idxs[0]], half_w, half_h)
                glViewport(half_w, half_h, half_w, half_h)
                self._draw_viewport(self.players[view_idxs[1]], half_w, half_h)
                glViewport(0, 0, w, half_h)
                self._draw_viewport(self.players[view_idxs[2]], w, half_h)
            else:
                half_w = w // 2
                half_h = h // 2
                glViewport(0, half_h, half_w, half_h)
                self._draw_viewport(self.players[view_idxs[0]], half_w, half_h)
                glViewport(half_w, half_h, half_w, half_h)
                self._draw_viewport(self.players[view_idxs[1]], half_w, half_h)
                glViewport(0, 0, half_w, half_h)
                self._draw_viewport(self.players[view_idxs[2]], half_w, half_h)
                glViewport(half_w, 0, half_w, half_h)
                self._draw_viewport(self.players[view_idxs[3]], half_w, half_h)

        # 2D-Overlay: Item-"Gluecksrad" (oueben rechts je Viewport)
        self._draw_item_roulette_overlays(now, w, h)
        self._draw_minimap_overlay(w, h)

    def cycle_camera_mode(self):
        self.camera_mode = (int(getattr(self, "camera_mode", 0)) + 1) % 3

    def _draw_viewport(self, pl, vw, vh):
        """Zeichnet eine Spieler-Perspektive in den aktuellen Viewport."""
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        far_clip = max(220.0, float(self.outer_r) * 4.2)
        gluPerspective(60, vw / max(vh, 1), 0.1, far_clip)
        glMatrixMode(GL_MODELVIEW);  glLoadIdentity()
        now = time.time()
        lift, hit_axis, hit_angle = self._hit_spin_visual(pl, now)
        yaw = pl.rot + (hit_angle if hit_axis == "y" else 0.0)
        rad = math.radians(yaw)
        mode = int(getattr(self, "camera_mode", 0)) % 3
        if mode == 1:
            cx = pl.pos[0] + math.sin(rad) * 0.5
            cz = pl.pos[2] + math.cos(rad) * 0.5
            cy = pl.pos[1] + 1.5 + lift
            pitch = math.radians(hit_angle if hit_axis == "x" else 0.0)
            forward_x = math.sin(rad) * math.cos(pitch)
            forward_y = -math.sin(pitch)
            forward_z = math.cos(rad) * math.cos(pitch)
            up_x = -math.sin(rad) * math.sin(pitch)
            up_y = math.cos(pitch)
            up_z = -math.cos(rad) * math.sin(pitch)
            tx = cx + forward_x * 14.0
            ty = cy + forward_y * 14.0
            tz = cz + forward_z * 14.0
            gluLookAt(cx, cy, cz, tx, ty, tz, up_x, up_y, up_z)
        elif mode == 2:
            height = max(36.0, float(self.outer_r) * 0.65)
            gluLookAt(pl.pos[0], height, pl.pos[2] + 0.01, pl.pos[0], 0.0, pl.pos[2], 0, 0, -1)
        else:
            cx = pl.pos[0] - math.sin(rad) * 8
            cz = pl.pos[2] - math.cos(rad) * 8
            gluLookAt(cx, 5, cz, pl.pos[0], 0.5, pl.pos[2], 0, 1, 0)
        self._draw_track()
        for p in self.players: self._draw_car(p)
        for item in self.items: item.draw()
        for box in self.item_boxes: box.draw()
        self._draw_oil_slicks(time.time())
        self._draw_item_projectiles(time.time())
        for p in self.players:
            for pt in p.particles: pt.draw()

    #  Track 
    def _draw_track(self):
        # Hole Map-Konfiguration
        outer_mod = self.map_config['outer_mod']
        inner_mod = self.map_config['inner_mod']
        outer_r = self.map_config.get('outer_base', OUTER_R)
        inner_r = self.map_config.get('inner_base', INNER_R)

        _draw_ground(max(140, int(outer_r * 3.0)))
        if self.map_config.get("type") == "open_square":
            half = float(outer_r)
            _gl_box_lit(-half, -0.01, -half, half, 0.02, half, (0.28, 0.28, 0.27))
            for x1, z1, x2, z2 in [
                (-half, -half, half, -half), (half, -half, half, half),
                (half, half, -half, half), (-half, half, -half, -half),
            ]:
                glColor3f(0.86, 0.86, 0.78)
                glBegin(GL_LINES)
                glVertex3f(x1, 0.06, z1); glVertex3f(x2, 0.06, z2)
                glEnd()
        else:
            _draw_track_ribbon(outer_mod, inner_mod, outer_r, inner_r)
            _draw_track_decoration(outer_mod, outer_r)

        # Startlinie und Markierungen
        inner0 = inner_r * (inner_mod(0) if inner_mod else 1.0)
        outer0 = outer_r * (outer_mod(0) if outer_mod else 1.0)
        if outer0 <= inner0 + 0.5:
            inner0, outer0 = inner_r, outer_r
        glColor3f(1.0, 1.0, 1.0)
        for i in range(12):
            x1 = inner0 + i/12 * (outer0 - inner0)
            x2 = inner0 + (i+1)/12 * (outer0 - inner0)
            if i % 2 == 0: glColor3f(1.0, 1.0, 1.0)
            else:           glColor3f(0.1, 0.1, 0.1)
            glBegin(GL_QUADS)
            glVertex3f(x1, 0.02, -1.2); glVertex3f(x2, 0.02, -1.2)
            glVertex3f(x2, 0.02,  1.2); glVertex3f(x1, 0.02,  1.2)
            glEnd()

        # Hindernisse (Map-spezifisch)
        for ob in self.obstacles:
            try:
                ox = float(ob.get("x", 0))
                oz = float(ob.get("z", 0))
                w = float(ob.get("w", 3.0))
                l = float(ob.get("l", 3.0))
                h = float(ob.get("h", 1.0))
                col = ob.get("color", (0.8, 0.2, 0.2))
            except Exception:
                continue

            # Raeuber & Bulle: der "Knopf" wird dynamisch gerendert (raus/rein),
            # deshalb das statische Config-Obstacle berspringen.
            if self.map_name == "Raeuber & Bulle":
                try:
                    bx, bz = self.rb_button_pos
                    is_near_button = (abs(ox - float(bx)) < 0.05) and (abs(oz - float(bz)) < 0.05)
                    r, g, b = col if isinstance(col, (tuple, list)) and len(col) >= 3 else (0, 0, 0)
                    is_greenish = float(g) > 0.75 and float(r) < 0.35 and float(b) < 0.35
                    is_button_shape = (w <= 3.2 and l <= 3.2 and h <= 1.6)
                    if is_near_button and is_greenish and is_button_shape:
                        continue
                except Exception:
                    pass

            glPushMatrix()
            glTranslatef(ox, 0.02, oz)
            _gl_box_lit(-w/2, 0.0, -l/2, w/2, h, l/2, col)
            glPopMatrix()

        if self.map_name == "Raeuber & Bulle":
            self._draw_rb_release_button()

    def _draw_rb_release_button(self):
        """Raeuber & Bulle: Knopf ist nur 'draussen', wenn jemand im Knast ist."""
        try:
            bx, bz = self.rb_button_pos
        except Exception:
            bx, bz = (0.0, 5.0)

        any_caught = any((p.team == "raeuber") and getattr(p, "rb_caught", False) for p in self.players)

        # Immer eine flache grne Flche anzeigen (wenn niemand im Knast: nur die Flche)
        glPushMatrix()
        glTranslatef(float(bx), 0.021, float(bz))
        _gl_box_lit(-1.1, 0.0, -1.1, 1.1, 0.06, 1.1, (0.0, 0.45, 0.0))
        glPopMatrix()

        if not any_caught:
            return

        # Wenn jemand im Knast ist: Knopf "kommt raus"
        glPushMatrix()
        glTranslatef(float(bx), 0.021, float(bz))
        _gl_box_lit(-0.55, 0.0, -0.55, 0.55, 0.95, 0.55, (0.0, 0.85, 0.0))
        glTranslatef(0.0, 0.96, 0.0)
        _gl_box_lit(-0.45, 0.0, -0.45, 0.45, 0.18, 0.45, (0.55, 1.0, 0.55))
        glPopMatrix()

    #  Auto 
    def _hit_spin_visual(self, pl, now=None):
        now = time.time() if now is None else now
        lift = 0.0
        axis = None
        angle = 0.0
        if getattr(pl, "hit_spin_until", 0.0) > now and getattr(pl, "hit_spin_axis", None):
            duration = max(0.01, pl.hit_spin_until - pl.hit_spin_start)
            t = _clamp((now - pl.hit_spin_start) / duration, 0.0, 1.0)
            lift = math.sin(t * math.pi) * getattr(pl, "hit_pop_height", 0.0)
            eased = 1.0 - pow(1.0 - t, 3)
            angle = pl.hit_spin_degrees * eased
            wobble = math.sin(t * math.pi * 8.0) * (1.0 - t) * 10.0
            axis = pl.hit_spin_axis
            angle += wobble
        return lift, axis, angle

    def _draw_car(self, pl):
        glPushMatrix()
        now = time.time()
        lift, hit_axis, hit_angle = self._hit_spin_visual(pl, now)
        glTranslatef(pl.pos[0], pl.pos[1] + lift, pl.pos[2])
        glRotatef(pl.rot,0,1,0)
        if hit_axis:
            if hit_axis == "x":
                glRotatef(hit_angle, 1, 0, 0)
            else:
                glRotatef(hit_angle, 0, 1, 0)
        _draw_kart_model(pl.color, getattr(pl, "style", "Standard"), getattr(pl, "character", None), getattr(pl, "crashed", False))
        glPopMatrix()

    def _draw_driver(self, character, roof_h):
        # Driver drawing is handled by _draw_kart_model.
        return

    #  Mensch-Physik 
    def _update_player(self, pl, dt, fwd_key, bwd_key, lft_key, rgt_key):
        if self.map_name == "Raeuber & Bulle" and getattr(pl, "rb_caught", False):
            return
        if pl.finished:
            self._update_finish_ghost(pl, dt)
            return
        if pl.crash_timer > time.time(): pl.velocity = 0; return
        
        # berprfe Boost-Status
        self._update_boost_status(pl, dt)
        
        fwd = self.keys.get(fwd_key, False); bwd = self.keys.get(bwd_key, False)
        lft = self.keys.get(lft_key, False); rgt = self.keys.get(rgt_key, False)
        if fwd:   pl.velocity += pl.acc * dt
        elif bwd: pl.velocity -= pl.acc * dt
        else:
            if   pl.velocity > 0: pl.velocity -= pl.friction * dt
            elif pl.velocity < 0: pl.velocity += pl.friction * dt
            if abs(pl.velocity) < pl.friction * dt: pl.velocity = 0
        pl.velocity = max(-pl.max_speed, min(pl.max_speed, pl.velocity))
        turning = False
        if abs(pl.velocity) > 0.5:
            if lft: pl.rot += pl.turn_speed * dt; turning = True
            if rgt: pl.rot -= pl.turn_speed * dt; turning = True
        self._physics(pl, dt, turning)

    #  Intelligente AI-Hilfsmethoden 
    
    def _get_nearest_opponent(self, ai_car):
        """Findet den naechsten gegnerischen Gegner vor dem AI-Auto."""
        nearest = None
        nearest_dist = float('inf')
        
        for other in self.players:
            if other is ai_car or other.finished:
                continue
            
            # Berechne relative Position
            dx = other.pos[0] - ai_car.pos[0]
            dz = other.pos[2] - ai_car.pos[2]
            dist = math.sqrt(dx**2 + dz**2)
            
            # berprfe, ob Gegner vor dem Auto liegt (relativ zur Orientierung)
            rad = math.radians(ai_car.rot)
            car_forward_x = math.sin(rad)
            car_forward_z = math.cos(rad)
            
            # Skalarprodukt: positiv = vor dem Auto
            dot_product = dx * car_forward_x + dz * car_forward_z
            
            if dot_product > -1 and dist < nearest_dist:  # -1 um etwas Spielraum zu haueben
                nearest = other
                nearest_dist = dist
        
        return nearest, nearest_dist if nearest else None
    
    def _analyze_opponents(self, ai_car):
        """Analysiert Bedrohung durch gegnerische Autos."""
        threat_level = 0.0
        is_blocked = False
        
        for other in self.players:
            if other is ai_car or other.finished:
                continue
            
            dx = other.pos[0] - ai_car.pos[0]
            dz = other.pos[2] - ai_car.pos[2]
            dist = math.sqrt(dx**2 + dz**2)
            
            if dist < 12:  # Gegner in der Nhe
                # Berechne, ob dieser Gegner auf der idealen Rennlinie liegt
                rad = math.radians(ai_car.rot)
                car_forward_x = math.sin(rad)
                car_forward_z = math.cos(rad)
                dot_product = dx * car_forward_x + dz * car_forward_z
                
                if 1 < dist < 8 and -2 < dot_product < 6:
                    is_blocked = True
                    threat_level = max(threat_level, 1.0 - (dist / 8.0))
                elif dist < 12:
                    threat_level = max(threat_level, 0.5 - (dist / 24.0))
        
        return threat_level, is_blocked
    
    def _compute_optimal_racing_line(self, ai_car):
        """Berechnet die optimale Rennlinie mit bis zu 5 Lookahead-Punkten."""
        d = ai_car.ai_diff
        points = []
        
        depth = int(d['prediction_depth'])
        cur_angle_deg = math.degrees(math.atan2(ai_car.pos[2], ai_car.pos[0]))
        
        for i in range(depth):
            look_ahead_dist = d['look_ahead'] + (i * 8)
            target_angle_rad = math.radians(cur_angle_deg - look_ahead_dist)
            target_angle_deg = (math.degrees(target_angle_rad) + 360.0) % 360.0
            
            # Follow the real map shape instead of a fixed circle.
            inner, outer = self._track_bounds_at_angle(target_angle_deg)
            margin = self._ai_track_margin(inner, outer)
            lane_quality = float(d.get('racing_line_quality', 0.65))
            lane_t = 0.48 + (1.0 - lane_quality) * 0.08
            lane_t = _clamp(lane_t, 0.42, 0.58)
            ideal_radius = inner + (outer - inner) * lane_t
            ideal_radius = _clamp(ideal_radius, inner + margin, outer - margin)
            
            tx = math.cos(target_angle_rad) * ideal_radius
            tz = math.sin(target_angle_rad) * ideal_radius
            
            points.append((tx, tz, look_ahead_dist))
        
        ai_car.ai_target_points = points
        return points[0] if points else (ai_car.pos[0], ai_car.pos[2])
    
    def _predict_brake_point(self, ai_car):
        """Vorhersagt, wo und wann gebremst werden sollte."""
        d = ai_car.ai_diff
        dist_to_center = math.sqrt(ai_car.pos[0]**2 + ai_car.pos[2]**2)
        
        # berprfe naechste 5 Lookahead-Punkte
        predicted_dist = dist_to_center
        
        for tx, tz, _ in ai_car.ai_target_points:
            predicted_dist = math.sqrt(tx**2 + tz**2)
            _, predicted_inner, predicted_outer = self._track_bounds_for_pos(tx, tz)
            margin = self._ai_track_margin(predicted_inner, predicted_outer)
            
            # Bremsenpunkt, wenn wir der inneren oder aeusseren Linie zu nahekommen.
            if predicted_dist > predicted_outer - margin or predicted_dist < predicted_inner + margin:
                return True, predicted_dist
        
        return False, predicted_dist
    
    def _evaluating_overtake_opportunity(self, ai_car, nearest_opponent, opponent_dist):
        """Bewertet berholmglichkeiten und gibt Entscheidung."""
        if not nearest_opponent or opponent_dist > 15:
            return False, None
        
        d = ai_car.ai_diff
        dx = nearest_opponent.pos[0] - ai_car.pos[0]
        dz = nearest_opponent.pos[2] - ai_car.pos[2]
        
        # berholmglichkeit nur wenn:
        # 1. Gegner ist nur wenig schneller oder gleich schnell
        # 2. Aggression ist hoch genug
        # 3. Abstand ist gering genug
        
        speed_diff = ai_car.velocity - nearest_opponent.velocity
        is_faster = speed_diff > 0.5
        can_be_aggressive = d['overtake_aggression'] > 0.4
        is_close_enough = opponent_dist < 6
        
        if is_faster and can_be_aggressive and is_close_enough:
            # Entscheide: Links oder Rechts berholenDown
            car_rot_rad = math.radians(ai_car.rot)
            side_vector_x = math.cos(car_rot_rad)
            side_vector_z = -math.sin(car_rot_rad)
            side_dot = dx * side_vector_x + dz * side_vector_z
            
            overtake_side = "left" if side_dot > 0 else "right"
            return True, overtake_side

        return False, None
    
    def _apply_defensive_positioning(self, ai_car, threat_level):
        """Passt Position an wenn durch schnellere Autos bedroht."""
        if threat_level < 0.3:
            return 0, 0  # Keine Anpassung ntig
        
        # Finde den schnellsten nachfolgenden Gegner
        fastest_chaser = None
        fastest_speed = ai_car.velocity
        
        for other in self.players:
            if other is ai_car or other.finished:
                continue
            
            dx = other.pos[0] - ai_car.pos[0]
            dz = other.pos[2] - ai_car.pos[2]
            dist = math.sqrt(dx**2 + dz**2)
            
            # berprfe ob hinter uns
            rad = math.radians(ai_car.rot)
            dot = dx * math.sin(rad) + dz * math.cos(rad)
            
            if -3 < dot < 1 and dist < 10 and other.velocity > fastest_speed:
                fastest_chaser = other
                fastest_speed = other.velocity
        
        if not fastest_chaser:
            return 0, 0
        
        # Blockiere die Innenlinie oder Auenlinie
        d = ai_car.ai_diff
        defensive_strength = threat_level * d['opponent_awareness'] * 0.5
        
        dx_chaser = fastest_chaser.pos[0] - ai_car.pos[0]
        dz_chaser = fastest_chaser.pos[2] - ai_car.pos[2]
        
        # Wende gegenstzliche Kraft an
        return (-dx_chaser * defensive_strength, -dz_chaser * defensive_strength)
    
    def _emergency_spin(self, ai_car, threat_level):
        """NOTFALL-DREHUNG: Fhrt in panikartigen Wendungen und riskanten Spins aus."""
        d = ai_car.ai_diff
        
        # Nur bei Profi mit Chance
        if d.get('emergency_spin_chance',0) < 0.01:
            return False, 0
        
        if threat_level < 0.5:
            return False, 0
        
        # Chance basierend auf Konfidenz/Bedrohung
        if random.random() < (d['emergency_spin_chance'] * threat_level):
            # Drehung um zuflligen Winkel zwischen 90 und 180 Grad
            angle = random.choice([90, -90, 180, -180])
            return True, angle
        return False, 0
    
    def _emergency_ram(self, ai_car, target_car):
        """NOTFALL-DRUCK: Rammt aggressiv einen Gegner um ihn zu verdrngen."""
        d = ai_car.ai_diff
        
        # Mindest-Aggressivitt fuer rammen
        if d['emergency_ram_chance'] < 0.3:
            return False, 0, 0
        
        # Berechne Ramm-Winkel: direkt auf den Gegner
        dx = target_car.pos[0] - ai_car.pos[0]
        dz = target_car.pos[2] - ai_car.pos[2]
        dist = math.sqrt(dx**2 + dz**2)
        
        if dist < 0.5 or dist > 8:
            return False, 0, 0
        
        # Ziele direkt auf Gegner
        target_rot = math.degrees(math.atan2(dx, dz))
        diff = (target_rot - ai_car.rot + 360) % 360
        if diff > 180:
            diff -= 360
        
        # AGGRESSIVE Beschleunigung fuer Ramm-Angriff
        ram_speed = ai_car.max_speed * (0.8 + d['emergency_ram_chance'] * 0.4)
        
        # Wenn Gegner relativ vor uns, rammen mit voller Kraft
        if abs(diff) < 45:
            # Volle Geschwindigkeit + aggressives Lenkung
            steer = min(1.5, abs(diff) / 8.0) * (1.0 + d['overtake_aggression'] * 0.7)
            return True, ram_speed, steer * diff / abs(diff) if diff != 0 else 0
        
        return False, 0, 0
    
    def _emergency_crash_dodge(self, ai_car, threat_level):
        """NOTFALL-CRASH-AUSWEICH: Macht aggressive Ausweichmanver auch mit Crash-Risiko."""
        d = ai_car.ai_diff
        
        if d['emergency_crash_dodge'] < 0.2:
            return False, 0, 0
        
        # Je hher threat und crash_dodge, desto aggressiver
        dodge_intensity = threat_level * d['emergency_crash_dodge']
        
        # Finde den naechsten Gegner und weiche extrem aus
        nearest = None
        nearest_dist = float('inf')
        
        for other in self.players:
            if other is ai_car or other.finished:
                continue
            
            dx = other.pos[0] - ai_car.pos[0]
            dz = other.pos[2] - ai_car.pos[2]
            dist = math.sqrt(dx**2 + dz**2)
            
            if dist < nearest_dist and dist < 10:
                nearest = other
                nearest_dist = dist
        
        if not nearest or nearest_dist > 8:
            return False, 0, 0
        
        # AGGRESSIVE Ausweichmanver
        dx = nearest.pos[0] - ai_car.pos[0]
        dz = nearest.pos[2] - ai_car.pos[2]
        
        # Waehle Seite fuer aggressiven Ausweich (kann off-track fhren)
        car_rot_rad = math.radians(ai_car.rot)
        side_x = math.cos(car_rot_rad)
        side_z = -math.sin(car_rot_rad)
        side_dot = dx * side_x + dz * side_z
        
        # Aggressive Lenkung (kann ber 90 Grad gehen!)
        aggressive_steer = (dodge_intensity * 150) * (1 if side_dot > 0 else -1)
        
        # Hohe Geschwindigkeit beim Ausweich
        dodge_speed = ai_car.max_speed * (0.7 + dodge_intensity * 0.5)
        
        return True, dodge_speed, aggressive_steer
    
    def _attempt_risky_maneuver(self, ai_car, nearest_opponent, opponent_dist):
        """Versucht risky/riskante berholmanver bei hohem Risiko-Threshold."""
        d = ai_car.ai_diff
        
        if d['risky_maneuver_threshold'] < 0.3:
            return False, None
        
        if not nearest_opponent or opponent_dist > 10:
            return False, None
        
        # Berechne Risiko-Faktor basierend auf Geschwindigkeit, Distanz und Lappen
        speed_ratio = ai_car.velocity / (nearest_opponent.velocity + 0.1)
        gap_safety = max(0, 5 - opponent_dist) / 5
        
        risk_factor = (speed_ratio * gap_safety * d['risky_maneuver_threshold'])
        
        # Wenn risk_factor > 0.5, mache risikantes Manver (auch auf Innenlinie)
        if risk_factor > 0.5 and random.random() < (d['risky_maneuver_threshold'] * 0.6):
            dx = nearest_opponent.pos[0] - ai_car.pos[0]
            dz = nearest_opponent.pos[2] - ai_car.pos[2]
            
            # berhole auf der FALSCHEN Seite (auen statt innen oder umgekehrt)
            dist_to_center = math.sqrt(ai_car.pos[0]**2 + ai_car.pos[2]**2)
            _, track_inner, track_outer = self._track_bounds_for_pos(ai_car.pos[0], ai_car.pos[2])
            on_outside = dist_to_center > (track_inner + track_outer) * 0.5
            
            # Waehle gegenteilige Seite zum normalen berholen
            risky_side = "right" if on_outside else "left"
            return True, risky_side
        
        return False, None

    #  KI-Physik 
    def _update_ai(self, pl, dt):
        """Intelligente KI mit Gegner-Tracking, Multi-Point-Lookahead und berholmanvern."""
        # Fuer Raeuber & Bulle: Spezielle Logik
        if self.map_name == "Raeuber & Bulle":
            if getattr(pl, "rb_caught", False) or pl.finished:
                pl.velocity = 0
                return

            any_caught = any(p.team == "raeuber" and getattr(p, "rb_caught", False) for p in self.players)
            button_x, button_z = self.rb_button_pos

            def dist2(ax, az, bx, bz):
                dx = ax - bx
                dz = az - bz
                return dx * dx + dz * dz

            # "In Reichweite" = wenn wir den Knopf mit wenigen Sekunden erreichen koennen,
            # priorisieren wir ihn (statt nur bei sehr groer Distanz zu warten).
            dist2_button = dist2(pl.pos[0], pl.pos[2], button_x, button_z)

            if pl.team == "bulle":
                # Bulle verfolgt den naechsten Raeuber
                nearest_raeuber = None
                min_dist = float('inf')
                for other in self.players:
                    if other.team == "raeuber" and not getattr(other, "rb_caught", False) and not other.finished:
                        dx = other.pos[0] - pl.pos[0]
                        dz = other.pos[2] - pl.pos[2]
                        dist = math.sqrt(dx**2 + dz**2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_raeuber = other
                
                if nearest_raeuber:
                    # Verfolge den Raeuber
                    dx = nearest_raeuber.pos[0] - pl.pos[0]
                    dz = nearest_raeuber.pos[2] - pl.pos[2]
                    target_rot = math.degrees(math.atan2(dx, dz))
                    diff = (target_rot - pl.rot + 360) % 360
                    if diff > 180: diff -= 360
                    
                    # Geschwindigkeit
                    pl.velocity = min(pl.velocity + pl.acc * dt, pl.max_speed * 0.9)
                    
                    # Lenkung
                    if abs(pl.velocity) > 0.2:
                        steer = min(1.0, abs(diff) / 15.0)
                        pl.rot += math.copysign(pl.turn_speed * dt * steer, diff)
                    
                    self._physics(pl, dt, abs(pl.velocity) > 0.2)
                    return
                else:
                    # Kein freier Raeuber: Knopf bewachen / anlaufen
                    if any_caught:
                        dx = button_x - pl.pos[0]
                        dz = button_z - pl.pos[2]
                        target_rot = math.degrees(math.atan2(dx, dz))
                        diff = (target_rot - pl.rot + 360) % 360
                        if diff > 180: diff -= 360
                        pl.velocity = min(pl.velocity + pl.acc * dt, pl.max_speed * 0.7)
                        if abs(pl.velocity) > 0.2:
                            steer = min(1.0, abs(diff) / 18.0)
                            pl.rot += math.copysign(pl.turn_speed * dt * steer, diff)
                        self._physics(pl, dt, abs(pl.velocity) > 0.2)
                        return
            elif pl.team == "raeuber":
                # Raeuber fliehen vor Bullen
                nearest_bulle = None
                min_dist = float('inf')
                for other in self.players:
                    if other.team == "bulle" and not other.finished:
                        dx = other.pos[0] - pl.pos[0]
                        dz = other.pos[2] - pl.pos[2]
                        dist = math.sqrt(dx**2 + dz**2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_bulle = other

                # Knopf-Prioritt: Wenn jemand gefangen ist, soll mind. ein freier Raeuber
                # gezielt zum Knopf fahren (insb. wenn er in Reichweite ist).
                if any_caught and time.time() >= self.rb_button_cooldown_until:
                    # Waehle den "Knopf-Lufer": der Raeuber, der am naechsten am Knopf ist.
                    best = None
                    best_d2 = float("inf")
                    for r in self.players:
                        if r.team != "raeuber" or getattr(r, "rb_caught", False) or r.finished:
                            continue
                        d2 = dist2(r.pos[0], r.pos[2], button_x, button_z)
                        if d2 < best_d2:
                            best_d2 = d2
                            best = r

                    is_button_runner = (best is pl)

                    # Wenn wir der Knopf-Lufer sind ODER der Knopf ohnehin in Reichweite liegt,
                    # dann priorisieren wir den Knopf (auer es ist akut gefhrlich).
                    in_reach = dist2_button < (42.0 * 42.0)
                    danger_close = (nearest_bulle is not None and min_dist < 10.0)
                    if (is_button_runner or in_reach) and not danger_close:
                        dx = button_x - pl.pos[0]
                        dz = button_z - pl.pos[2]
                        target_rot = math.degrees(math.atan2(dx, dz))
                        diff = (target_rot - pl.rot + 360) % 360
                        if diff > 180:
                            diff -= 360

                        # Nher am Knopf = praeziser und langsamer, damit man ihn "halten" kann.
                        near = math.sqrt(dist2_button)
                        max_speed_factor = 0.95
                        steer_div = 14.0
                        if near < 9.0:
                            max_speed_factor = 0.55
                            steer_div = 10.0
                        elif near < 16.0:
                            max_speed_factor = 0.72
                            steer_div = 12.0

                        pl.velocity = min(pl.velocity + pl.acc * dt, pl.max_speed * max_speed_factor)
                        if abs(pl.velocity) > 0.2:
                            steer = min(1.0, abs(diff) / steer_div)
                            pl.rot += math.copysign(pl.turn_speed * dt * steer, diff)
                        self._physics(pl, dt, abs(pl.velocity) > 0.2)
                        return

                if nearest_bulle and min_dist < 12.0:
                    # Fliehe vor dem Bullen
                    dx = pl.pos[0] - nearest_bulle.pos[0]
                    dz = pl.pos[2] - nearest_bulle.pos[2]
                    target_rot = math.degrees(math.atan2(dx, dz))
                    diff = (target_rot - pl.rot + 360) % 360
                    if diff > 180: diff -= 360
                    
                    # Geschwindigkeit
                    pl.velocity = min(pl.velocity + pl.acc * dt, pl.max_speed)
                    
                    # Lenkung
                    if abs(pl.velocity) > 0.2:
                        steer = min(1.0, abs(diff) / 10.0)
                        pl.rot += math.copysign(pl.turn_speed * dt * steer, diff)
                    
                    self._physics(pl, dt, abs(pl.velocity) > 0.2)
                    return
                else:
                    # Normal fahren
                    pass
        
        # berprfe Boost-Status
        self._update_boost_status(pl, dt)
        # Hindernisse ausweichen (unabhngig von Schwierigkeit)
        if self._avoid_obstacles_ai(pl, dt):
            return
        # Andere Spieler/KIs ausweichen (unabhngig von Schwierigkeit)
        if self._avoid_cars_ai(pl, dt):
            return
        
        # Wenn im Parkhaus, einfach zum Platz fahren
        if pl.moving_to_parking and pl.parking_spot is not None:
            px, pz = pl.parking_spot
            dx, dz = px - pl.pos[0], pz - pl.pos[2]
            avoid_offset_x, avoid_offset_z = 0, 0
            for other in self.players:
                if other is pl or other.finished: continue
                odx = other.pos[0] - pl.pos[0]; odz = other.pos[2] - pl.pos[2]
                odist = math.sqrt(odx**2 + odz**2)
                if odist < 5.0 and odist > 0:
                    avoid_offset_x -= (odx / odist) * (5.0 - odist) * 0.3
                    avoid_offset_z -= (odz / odist) * (5.0 - odist) * 0.3
            target_x = px + avoid_offset_x; target_z = pz + avoid_offset_z
            dx, dz = target_x - pl.pos[0], target_z - pl.pos[2]
            dist_to_parking = math.sqrt(dx**2 + dz**2)
            target_rot = math.degrees(math.atan2(dx, dz))
            diff = (target_rot - pl.rot + 360) % 360
            if diff > 180: diff -= 360
            if dist_to_parking > 1.5:
                pl.velocity = 3.0
                if abs(pl.velocity) > 0.2:
                    steer = min(1.0, abs(diff) / 15.0) * 0.8
                    pl.rot += math.copysign(pl.turn_speed * dt * steer, diff)
            else:
                pl.velocity = 0; pl.moving_to_parking = False
            self._physics(pl, dt, abs(pl.velocity) > 0.2)
            return

        if pl.finished:
            self._update_finish_ghost(pl, dt)
            return
        if pl.crash_timer > time.time():
            pl.velocity *= 0.8; return

        d = pl.ai_diff
        now = time.time()
        time_since_start = now - pl.start_time if pl.start_time else 0
        time_since_last_item = now - pl.last_item_collected_time
        
        #  1. ANALYSE 
        dist_to_center = math.sqrt(pl.pos[0]**2 + pl.pos[2]**2)
        _, track_inner, track_outer = self._track_bounds_for_pos(pl.pos[0], pl.pos[2])
        track_mid = (track_inner + track_outer) * 0.5
        track_margin = self._ai_track_margin(track_inner, track_outer)
        threat_level, is_blocked = self._analyze_opponents(pl)
        nearest_opponent, opponent_dist = self._get_nearest_opponent(pl)
        
        # Position-Historie speichern fuer Lernfhigkeit
        pl.ai_position_history.append(list(pl.pos))
        if len(pl.ai_position_history) > 10:
            pl.ai_position_history.pop(0)
        
        pl.ai_opponent_threat = threat_level
        pl.ai_is_blocking = is_blocked
        
        #  2. ITEM-SAMMLUNG (strategisch) 
        # Nur sammeln wenn: spte Spielphase oder kein Gegner in der Nhe und langsamer
        if time_since_start > 10.0 and pl.pending_item is None:
            # Wenn sehr bedroht, Items ignorieren. Wenn nicht bedroht, Items sammeln
            if threat_level < 0.5:
                nearest_item, item_dist = self._get_nearest_uncollected_item(pl.pos)
                nearest_box, box_dist = self._get_nearest_available_item_box(pl.pos, now)

                target_pos = None
                # gierig nach Kstchen: wenn ein Kstchen hnlich nah ist, bevorzugen
                can_chase_box = (now - pl.last_box_collected_time) >= 5.0
                if can_chase_box and nearest_box and box_dist < 45.0 and (not nearest_item or box_dist <= item_dist * 1.35):
                    target_pos = (nearest_box.pos[0], nearest_box.pos[2])
                elif nearest_item and item_dist < 35.0:
                    target_pos = (nearest_item.pos[0], nearest_item.pos[2])

                if target_pos is not None:
                    tx, tz = target_pos
                    dx_item = tx - pl.pos[0]
                    dz_item = tz - pl.pos[2]
                    item_angle = math.degrees(math.atan2(dx_item, dz_item))
                    car_rot_normalized = (pl.rot + 360) % 360
                    angle_diff = (item_angle - car_rot_normalized + 360) % 360
                    if angle_diff > 180: angle_diff = 360 - angle_diff
                    
                    if angle_diff < 90:
                        dx = dx_item
                        dz = dz_item
                        target_rot = math.degrees(math.atan2(dx, dz))
                        diff = (target_rot - pl.rot + 360) % 360
                        if diff > 180: diff -= 360
                        
                        pl.velocity = pl.max_speed * 0.95
                        if abs(pl.velocity) > 0.2:
                            steer = min(1.0, abs(diff) / 15.0)
                            pl.rot += math.copysign(pl.turn_speed * dt * steer, diff)
                        
                        self._physics(pl, dt, abs(pl.velocity) > 0.2)
                        return
        
        #  3. NOTFALL-MANVER BEWERTEN 
        # Erste Chance: Notfall-Drehung (kann auch zu einem Crash fhren)
        if d.get('emergency_spin_chance',0) > 0.0:
            spin_success, spin_angle = self._emergency_spin(pl, threat_level)
            if spin_success:
                # Notfall-Drehung ausfhren
                pl.rot += spin_angle
                # Geschwindigkeit drastisch reduzieren
                pl.velocity *= 0.3
                self._physics(pl, dt, True)
                return
        
        # Nur auf Schwer/Profi: Ramm-Angriff wenn mglich
        # ZuFallsSatz: Chance fuer spontanen Ramm-Angriff auch ohne perfekte Situation (Profi KI)
        if nearest_opponent and d['emergency_ram_chance'] > 0.2:
            # Spontane Aggression: Profi KI kann auch einfach so rammen wollen (20% Chance wenn sehr aggressiv)
            force_ram = False
            if d['emergency_ram_chance'] > 0.6 and random.random() < (d['emergency_ram_chance'] * 0.15):
                force_ram = True
            
            ram_success, ram_speed, ram_angle = self._emergency_ram(pl, nearest_opponent)
            if ram_success or force_ram:
                # NOTFALL-DRUCK: RAMM-ANGRIFF!
                if force_ram:
                    # Spontaner Ramm-Impuls
                    ram_speed = pl.max_speed * 0.85
                    dx = nearest_opponent.pos[0] - pl.pos[0]
                    dz = nearest_opponent.pos[2] - pl.pos[2]
                    ram_angle = 45 if random.random() > 0.5 else -45
                
                pl.velocity = min(pl.velocity + pl.acc * dt * 2.0, ram_speed)
                pl.rot += pl.turn_speed * dt * ram_angle
                
                pl.ai_overtake_mode = True
                self._physics(pl, dt, True)
                return
        
        # Notfall-Ausweich bei extremer Bedrohung
        if threat_level > 0.7 and d['emergency_crash_dodge'] > 0.3:
            dodge_success, dodge_speed, dodge_steer = self._emergency_crash_dodge(pl, threat_level)
            if dodge_success:
                # NOTFALL-CRASH-AUSWEICH: Aggressive Lenkung!
                pl.velocity = dodge_speed
                pl.rot += pl.turn_speed * dt * (dodge_steer / 100.0)  # Sehr aggressive Lenkung
                
                self._physics(pl, dt, True)
                return
        
        #  4. BERHOLMANVER BEWERTEN 
        # berprfe auf riskante berholmanver
        is_risky, risky_side = self._attempt_risky_maneuver(pl, nearest_opponent, opponent_dist)
        
        should_overtake, overtake_side = self._evaluating_overtake_opportunity(pl, nearest_opponent, opponent_dist)
        
        # Nutze riskante Seite wenn verfgbar, sonst normale
        if is_risky and risky_side:
            overtake_side = risky_side
            should_overtake = True
        
        if should_overtake and overtake_side and not is_blocked:
            # Aggressives berholmanver
            target_offset = 4.0 if overtake_side == "left" else -4.0
            current_angle = math.atan2(pl.pos[2], pl.pos[0])
            perpendicular_x = math.cos(current_angle)
            perpendicular_z = math.sin(current_angle)
            
            target_x = nearest_opponent.pos[0] + perpendicular_x * target_offset
            target_z = nearest_opponent.pos[2] + perpendicular_z * target_offset
            
            dx = target_x - pl.pos[0]
            dz = target_z - pl.pos[2]
            target_rot = math.degrees(math.atan2(dx, dz))
            diff = (target_rot - pl.rot + 360) % 360
            if diff > 180: diff -= 360
            
            # Volle Geschwindigkeit beim berholen
            max_allowed_speed = pl.max_speed * d['speed'] * (1.0 + d['overtake_aggression'] * 0.3)
            pl.velocity = min(pl.velocity + pl.acc * dt * 1.5, max_allowed_speed)
            
            steer = min(1.0, abs(diff) / 10.0) * (1.0 + d['overtake_aggression'] * 0.5)
            pl.rot += math.copysign(pl.turn_speed * dt * steer, diff)
            
            pl.ai_overtake_mode = True
            self._physics(pl, dt, True)
            return
        
        pl.ai_overtake_mode = False
        
        #  4. OPTIMALE RENNLINIE BERECHNEN 
        tx, tz, _ = self._compute_optimal_racing_line(pl)
        
        # Wenn blockiert, etwas ausweichen
        if is_blocked and d['opponent_awareness'] > 0.5:
            # Versuche um den Gegner herumzufahren
            for other in self.players:
                if other is pl or other.finished:
                    continue
                dx_other = other.pos[0] - pl.pos[0]
                dz_other = other.pos[2] - pl.pos[2]
                dist_other = math.sqrt(dx_other**2 + dz_other**2)
                
                if dist_other < 5 and dist_other > 0:
                    # Weiche um 2-3 Einheiten aus
                    avoid_strength = min(1.0, (5 - dist_other) / 5) * d['opponent_awareness']
                    tx += (- dx_other / dist_other) * avoid_strength * 2.5
                    tz += (- dz_other / dist_other) * avoid_strength * 2.5
        
        # Offensive/Defensive Positionierung wenn bedroht
        if threat_level > 0.4 and d['opponent_awareness'] > 0.6:
            def_x, def_z = self._apply_defensive_positioning(pl, threat_level)
            tx += def_x
            tz += def_z
        
        # Auf Profi: Bewusst aggressive Blockade-Positionen einnehmen
        # Verwende die BREITERE Linie wenn schneller Gegner hinter mir ist
        if d['emergency_ram_chance'] > 0.6 and threat_level > 0.5:
            for other in self.players:
                if other is pl or other.finished:
                    continue
                dx_other = other.pos[0] - pl.pos[0]
                dz_other = other.pos[2] - pl.pos[2]
                dist_other = math.sqrt(dx_other**2 + dz_other**2)
                
                # Wenn schnellerer Gegner nah hinter uns, blockiere aggressiv
                if 2 < dist_other < 8 and other.velocity > pl.velocity * 0.9:
                    # Fahre die BREITERE Linie um zu blockieren
                    wider_factor = 1.0 + (d['emergency_ram_chance'] * 0.3)
                    tx *= wider_factor
                    tz *= wider_factor
                    break

        tx, tz = self._clamp_ai_target_to_safe_track(tx, tz)
        
        rad = math.radians(pl.rot)
        predicted_x = pl.pos[0] + math.sin(rad) * pl.velocity * 0.3
        predicted_z = pl.pos[2] + math.cos(rad) * pl.velocity * 0.3
        predicted_dist = math.sqrt(predicted_x**2 + predicted_z**2)
        _, predicted_inner, predicted_outer = self._track_bounds_for_pos(predicted_x, predicted_z)
        predicted_margin = self._ai_track_margin(predicted_inner, predicted_outer)
        
        dx, dz = tx - pl.pos[0], tz - pl.pos[2]
        target_rot = math.degrees(math.atan2(dx, dz))
        diff = (target_rot - pl.rot + 360) % 360
        if diff > 180: diff -= 360
        
        #  5. INTELLIGENTE GESCHWINDIGKEIT 
        max_allowed_speed = pl.max_speed * d['speed']
        
        # Kurvenfaktor basierend auf Abweichung
        curve_factor = max(0.35, 1.0 - (abs(diff) / 35.0))
        
        # Wall-Panik mit besserer Vorhersage
        wall_panic = 1.0
        should_brake, _ = self._predict_brake_point(pl)
        
        if should_brake:
            wall_panic = 0.2
        elif dist_to_center > track_outer - track_margin:
            wall_panic = 0.25
        elif predicted_dist > predicted_outer - predicted_margin or predicted_dist < predicted_inner + predicted_margin:
            wall_panic = 0.45
        elif dist_to_center < track_inner + track_margin:
            wall_panic = 0.45
        elif dist_to_center > track_mid + track_margin * 0.5:
            wall_panic = 0.7
        
        # Gegner-Einfluss auf Geschwindigkeit
        opponent_speed_factor = 1.0 - (threat_level * d['opponent_awareness'] * 0.3)
        
        # Finale Zielgeschwindigkeit
        final_target_speed = max_allowed_speed * curve_factor * wall_panic * opponent_speed_factor
        
        # Adaptive Beschleunigung/Bremsung mit besserer Vorhersage
        if pl.velocity < final_target_speed:
            acceleration = pl.acc * dt * (1.0 + d['brake_predictiveness'] * 0.5)
            pl.velocity = min(pl.velocity + acceleration, final_target_speed)
        else:
            brake_factor = 2.0 if dist_to_center > track_outer - track_margin else (1.5 if dist_to_center > track_outer - track_margin * 0.6 else 1.2)
            brake_factor *= (1.0 + d['brake_predictiveness'] * 0.8)
            pl.velocity -= pl.friction * brake_factor * dt
        
        #  6. LENKUNG MIT INTELLIGENTER SCHRFUNG 
        turning = False
        if abs(pl.velocity) > 0.2:
            dynamic_sharpness = d['sharp']
            
            # Abhngig von Distanz zur Mitte
            if dist_to_center > track_mid + track_margin * 0.5:
                dynamic_sharpness *= 1.8
            elif dist_to_center > track_mid:
                dynamic_sharpness *= 1.3
            
            # Gegner-bewusste Lenkung
            if threat_level > 0.5:
                # Wenn bedroht, weniger aggressive Lenkung
                dynamic_sharpness *= (1.0 - threat_level * d['opponent_awareness'] * 0.4)
            
            steer = min(1.0, abs(diff) / 12.0) * dynamic_sharpness
            pl.rot += math.copysign(pl.turn_speed * dt * steer, diff)
            turning = True

        self._physics(pl, dt, turning)

    #  Gemeinsame Bewegung 
    def _physics(self, pl, dt, turning):
        rad = math.radians(pl.rot)
        nx = pl.pos[0] + math.sin(rad) * pl.velocity * dt
        nz = pl.pos[2] + math.cos(rad) * pl.velocity * dt

        if self._on_track(nx, nz):
            pl.pos[0] = nx; pl.pos[2] = nz
        else:
            if self.map_config.get("type") == "open_square":
                half = float(self.map_config.get("outer_base", self.outer_r))
                pl.pos[0] = _clamp(nx, -half, half)
                pl.pos[2] = _clamp(nz, -half, half)
            else:
                dist = math.sqrt(nx**2 + nz**2)
                _, inner_bound, outer_bound = self._track_bounds_for_pos(nx, nz)
                if dist > outer_bound:
                    factor = outer_bound / dist if dist > 0 else outer_bound
                    pl.pos[0] = nx * factor; pl.pos[2] = nz * factor
                elif dist < inner_bound:
                    factor = inner_bound / dist if dist > 0 else inner_bound
                    pl.pos[0] = nx * factor; pl.pos[2] = nz * factor
            pl.velocity *= -0.5

        if not pl.finished:
            self._collide_obstacles(pl)

        if self.win_laps and self.win_laps > 0 and pl.velocity > 0.5:
            ns = Player._get_sector(pl.pos[0], pl.pos[2])
            if ns != pl.sector:
                pl.sectors_visited.add(pl.sector)
                pl.sector = ns
                if ns == 0 and {1,2,3}.issubset(pl.sectors_visited):
                    pl.laps += 1
                    pl.sectors_visited = set()
                    if pl.laps >= self.win_laps and not pl.finished:
                        pl.finished = True
                        pl.finish_time = time.time()
                        self.finish_counter += 1
                        pl.finish_place = self.finish_counter
                        self.recorder.record_finish(self.frame_idx)
                        pl.moving_to_parking = False
                        pl.parking_spot = None
                        if not self.winner:
                            self.winner = pl
                        if self.num_humans <= 0 and self.finish_counter >= len(self.players) and self.on_race_over:
                            self.race_over = True
                            QTimer.singleShot(1500, self.on_race_over)

        if abs(pl.velocity) > 0.5:
            rad2 = math.radians(pl.rot)
            px = pl.pos[0] - math.sin(rad2) * 1.2; pz = pl.pos[2] - math.cos(rad2) * 1.2
            pl.particles.append(Particle([px,pl.pos[1],pz],color=(0.65,0.65,0.65),speed=0.04,size=0.1))
            if turning:
                pl.particles.append(Particle([px+0.4,pl.pos[1],pz],color=(1,1,1),speed=0.05,size=0.08))
                pl.particles.append(Particle([px-0.4,pl.pos[1],pz],color=(1,1,1),speed=0.05,size=0.08))

        for p in pl.particles[:]:
            p.update(dt)
            if p.life <= 0: pl.particles.remove(p)

    def _all_human_racers_finished(self):
        if self.map_name == "Raeuber & Bulle" or self.num_humans <= 0:
            return False
        humans = self.players[:self.num_humans]
        return bool(humans) and all(pl.finished for pl in humans)

    def _update_human_finish_overtime(self, now):
        if self.race_over or self.map_name == "Raeuber & Bulle":
            return
        if not self._all_human_racers_finished():
            return
        if self.human_finish_overtime_started_at is None:
            self.human_finish_overtime_started_at = now
            return
        if now - self.human_finish_overtime_started_at >= self.human_finish_overtime_duration:
            self._finish_standard_race_after_overtime()

    def _finish_standard_race_after_overtime(self):
        if self.race_over:
            return
        now = time.time()
        for pl in self.get_current_standings():
            if not pl.finished:
                pl.finished = True
                pl.finish_time = now
                self.finish_counter += 1
                pl.finish_place = self.finish_counter
        self.race_over = True
        if self.on_race_over:
            self.on_race_over(self.players, self.recorder, self.recorder.frames, self.recorder.events)

    def _update_finish_ghost(self, pl, dt):
        if self.map_name == "Raeuber & Bulle" or (self.race_over and not getattr(self, "result_live_preview", False)):
            pl.velocity *= 0.96
            return
        if pl.crash_timer > time.time():
            pl.velocity *= 0.9
            return

        if self.map_config.get("type") == "open_square":
            pl.velocity = min(max(pl.velocity, pl.max_speed * 0.45), pl.max_speed * 0.65)
            self._physics(pl, dt, False)
            return

        angle = math.degrees(math.atan2(pl.pos[2], pl.pos[0]))
        look_ahead = angle - 16.0
        inner, outer = self._track_bounds_at_angle(look_ahead)
        margin = self._ai_track_margin(inner, outer)
        target_r = inner + (outer - inner) * 0.55
        target_r = _clamp(target_r, inner + margin, outer - margin)
        rad = math.radians(look_ahead)
        tx = math.cos(rad) * target_r
        tz = math.sin(rad) * target_r
        dx = tx - pl.pos[0]
        dz = tz - pl.pos[2]
        target_rot = math.degrees(math.atan2(dx, dz))
        diff = (target_rot - pl.rot + 360) % 360
        if diff > 180:
            diff -= 360
        steer = min(1.0, abs(diff) / 16.0)
        if abs(diff) > 1.0:
            pl.rot += math.copysign(pl.turn_speed * dt * steer * 0.75, diff)
        target_speed = pl.max_speed * 0.62
        if pl.velocity < target_speed:
            pl.velocity = min(target_speed, pl.velocity + pl.acc * dt * 0.45)
        else:
            pl.velocity = max(target_speed, pl.velocity - pl.friction * dt * 0.35)
        self._physics(pl, dt, abs(diff) > 2.0)

    def get_current_standings(self):
        """Berechne die aktuelle Platzierung basierend auf Runden und Sektor."""
        def key_func(pl):
            if pl.finished:
                return (pl.laps, 4, 0)  # Fertige Spieler haueben hchste Prioritt
            else:
                # Fuer ovale Strecken: hhere Runden zuerst, dann Sektor
                sector_pos = pl.sector  # 0,1,2,3
                # Berechne ungefhre Position im Sektor basierend auf x,z
                x, z = pl.pos[0], pl.pos[2]
                if sector_pos == 0:  # Rechts unten
                    dist = -z  # Je niedriger z, desto weiter
                elif sector_pos == 1:  # Links unten
                    dist = x  # Je hher x, desto weiter
                elif sector_pos == 2:  # Links oueben
                    dist = z  # Je hher z, desto weiter
                else:  # Rechts oueben
                    dist = -x  # Je niedriger x, desto weiter
                return (pl.laps, sector_pos, dist)
        
        sorted_players = sorted(self.players, key=key_func, reverse=True)
        standings = {}
        for place, pl in enumerate(sorted_players, 1):
            standings[pl] = place
        return standings

    #  Kollision 
    def _collision(self, p1, p2):
        if p1.finished or p2.finished:
            return
        dx = p1.pos[0]-p2.pos[0]; dz = p1.pos[2]-p2.pos[2]
        dist = math.sqrt(dx*dx + dz*dz)
        if dist < p1.radius + p2.radius:
            already = p1.crash_timer > time.time()
            if dist != 0: ndx, ndz = dx/dist, dz/dist
            else:         ndx, ndz = 1, 0
            sep = (p1.radius+p2.radius-dist) + 0.5
            p1.pos[0] += ndx*sep/2; p1.pos[2] += ndz*sep/2
            p2.pos[0] -= ndx*sep/2; p2.pos[2] -= ndz*sep/2

            # Raeuber & Bulle: In der Knopf-Zone (Befreiung) soll es kein CRASH! geueben,
            # damit das Drcken/Halten nicht durch Explosions-Crash sabotiert wird.
            if self.map_name == "Raeuber & Bulle":
                bx, bz = self.rb_button_pos
                mx = (p1.pos[0] + p2.pos[0]) * 0.5
                mz = (p1.pos[2] + p2.pos[2]) * 0.5
                if ((mx - bx) ** 2 + (mz - bz) ** 2) <= ((self.rb_button_radius + 2.0) ** 2):
                    p1.velocity *= 0.6
                    p2.velocity *= 0.6
                    return
            if not already:
                p1.velocity = 0; p2.velocity = 0
                p1.crash_timer = time.time()+3; p2.crash_timer = time.time()+3
                mid = [(p1.pos[i]+p2.pos[i])/2 for i in range(3)]
                spawn_explosion(mid, p1.particles)
                spawn_explosion(mid, p2.particles)
                self.recorder.record_explosion(mid, self.frame_idx)

    def _collide_obstacles(self, pl):
        if not self.obstacles:
            return
        now = time.time()
        for ob in self.obstacles:
            try:
                ox = float(ob.get("x", 0))
                oz = float(ob.get("z", 0))
                w = float(ob.get("w", 3.0))
                l = float(ob.get("l", 3.0))
            except Exception:
                continue

            dx = pl.pos[0] - ox
            dz = pl.pos[2] - oz
            half_w = w / 2.0
            half_l = l / 2.0
            if abs(dx) >= (half_w + pl.radius) or abs(dz) >= (half_l + pl.radius):
                continue

            overlap_x = (half_w + pl.radius) - abs(dx)
            overlap_z = (half_l + pl.radius) - abs(dz)
            if overlap_x < overlap_z:
                pl.pos[0] += math.copysign(overlap_x + 0.02, dx)
            else:
                pl.pos[2] += math.copysign(overlap_z + 0.02, dz)

            pl.velocity *= -0.35

            if pl.crash_timer <= now:
                pl.crash_timer = now + 1.2
                mid = [pl.pos[0], pl.pos[1], pl.pos[2]]
                spawn_explosion(mid, pl.particles)
                self.recorder.record_explosion(mid, self.frame_idx)

    def _avoid_obstacles_ai(self, pl, dt):
        """Simple steering avoidance so AI dodges obstacles on all difficulties."""
        if not self.obstacles or pl.finished or pl.crash_timer > time.time() or pl.moving_to_parking:
            return False

        rad = math.radians(pl.rot)
        fwd_x = math.sin(rad)
        fwd_z = math.cos(rad)
        right_x = math.cos(rad)
        right_z = -math.sin(rad)

        best = None
        for ob in self.obstacles:
            ox = float(ob.get("x", 0))
            oz = float(ob.get("z", 0))
            w = float(ob.get("w", 3.0))
            l = float(ob.get("l", 3.0))

            dx = ox - pl.pos[0]
            dz = oz - pl.pos[2]
            ahead = dx * fwd_x + dz * fwd_z
            if ahead <= 0:
                continue
            dist2 = dx * dx + dz * dz
            if dist2 > (14.0 ** 2):
                continue

            side = dx * right_x + dz * right_z
            corridor = (w / 2.0) + pl.radius + 1.2
            if abs(side) > corridor:
                continue

            # Prefer the closest obstacle in front
            if best is None or ahead < best["ahead"]:
                best = {"ahead": ahead, "side": side, "corridor": corridor}

        if best is None:
            return False

        # steer away from obstacle centerline
        steer_dir = -1.0 if best["side"] > 0 else 1.0
        strength = _clamp((best["corridor"] - abs(best["side"])) / max(1.0, best["corridor"]), 0.25, 1.0)
        pl.rot += steer_dir * pl.turn_speed * dt * (0.75 + 0.35 * strength)
        pl.velocity = min(pl.velocity, pl.max_speed * (0.65 + 0.20 * (1.0 - strength)))
        self._physics(pl, dt, True)
        return True

    def _avoid_cars_ai(self, pl, dt):
        """Simple close-range avoidance so AI also dodges other cars (players + AI)."""
        if pl.finished or pl.crash_timer > time.time() or pl.moving_to_parking:
            return False

        rad = math.radians(pl.rot)
        fwd_x = math.sin(rad)
        fwd_z = math.cos(rad)
        right_x = math.cos(rad)
        right_z = -math.sin(rad)

        best = None
        for other in self.players:
            if other is pl or other.finished:
                continue

            dx = other.pos[0] - pl.pos[0]
            dz = other.pos[2] - pl.pos[2]

            ahead = dx * fwd_x + dz * fwd_z
            if ahead <= 0 or ahead > 7.5:
                continue

            side = dx * right_x + dz * right_z
            corridor = pl.radius + other.radius + 0.9
            if abs(side) > corridor:
                continue

            dist2 = dx * dx + dz * dz
            if dist2 > (8.0 ** 2):
                continue

            if best is None or ahead < best["ahead"]:
                best = {"ahead": ahead, "side": side, "corridor": corridor}

        if best is None:
            return False

        steer_dir = -1.0 if best["side"] > 0 else 1.0
        strength = _clamp((best["corridor"] - abs(best["side"])) / max(1.0, best["corridor"]), 0.25, 1.0)
        pl.rot += steer_dir * pl.turn_speed * dt * (0.85 + 0.55 * strength)

        if best["ahead"] < 4.5:
            pl.velocity = min(pl.velocity, pl.max_speed * (0.55 + 0.25 * (1.0 - strength)))

        self._physics(pl, dt, True)
        return True

    def _track_bounds_at_angle(self, angle):
        if self.map_config.get("type") == "open_square":
            half = float(self.map_config.get("outer_base", self.outer_r))
            return 0.0, half

        angle = (float(angle) + 360.0) % 360.0
        outer_mod = self.map_config.get('outer_mod', lambda a: 1.0)
        inner_mod = self.map_config.get('inner_mod', lambda a: 0.65)
        outer = self.outer_r * (outer_mod(angle) if outer_mod else 1.0)
        inner = self.inner_r * (inner_mod(angle) if inner_mod else 1.0)
        if outer < inner:
            inner, outer = outer, inner
        return inner, outer

    def _track_bounds_for_pos(self, x, z):
        angle = math.degrees(math.atan2(z, x))
        inner, outer = self._track_bounds_at_angle(angle)
        return angle, inner, outer

    def _ai_track_margin(self, inner, outer):
        return max(0.8, (outer - inner) / 8.0)

    def _clamp_ai_target_to_safe_track(self, x, z):
        if self.map_config.get("type") == "open_square":
            return x, z
        dist = math.sqrt(x * x + z * z)
        if dist <= 0.001:
            return x, z
        _, inner, outer = self._track_bounds_for_pos(x, z)
        margin = self._ai_track_margin(inner, outer)
        safe_inner = inner + margin
        safe_outer = outer - margin
        if safe_outer <= safe_inner:
            safe_inner = inner
            safe_outer = outer
        safe_dist = _clamp(dist, safe_inner, safe_outer)
        factor = safe_dist / dist
        return x * factor, z * factor

    def _on_track(self, x, z):
        if self.map_config.get("type") == "open_square":
            # Offene quadratische Flche: Begrenzung ber outer_base (Halbseite)
            half = float(self.map_config.get("outer_base", self.outer_r))
            return (abs(x) <= half) and (abs(z) <= half)
        dist = math.sqrt(x*x + z*z)
        _, inner, outer = self._track_bounds_for_pos(x, z)
        return inner < dist < outer

    def _find_free_parking_spot(self):
        for i, spot in enumerate(self.parking_spots):
            if not self.parking_occupied[i]:
                self.parking_occupied[i] = True
                return i
        return None

    def _check_overtakes(self):
        current_order = sorted(
            range(len(self.players)),
            key=lambda i: (-self.players[i].laps, -len(self.players[i].sectors_visited))
        )
        if self.last_positions and current_order != self.last_positions:
            self.recorder.record_overtake(self.frame_idx)
        self.last_positions = current_order

    def _apply_speed_boost(self, player):
        """Aktiviere Speed-Boost fuer einen Spieler (Standard: 10 Sekunden)."""
        self._apply_speed_boost_custom(player, duration=10.0, multiplier=1.5)

    def _apply_speed_boost_custom(self, player, duration=10.0, multiplier=1.5):
        """Aktiviere Speed-Boost mit Parametern (fuer Power-Ups und Items)."""
        player.speed_boost_timer = time.time() + float(duration)
        player.speed_boost_active = True
        player.max_speed = player.base_max_speed * float(multiplier)
        player.last_item_collected_time = time.time()  # Starte Cooldown fuer Item-Verfolgung

    def _update_boost_status(self, player, dt):
        """berprfe ob Boost noch aktiv ist, und setze Geschwindigkeit zurueck."""
        now = time.time()
        if player.speed_boost_active and now > player.speed_boost_timer:
            player.speed_boost_active = False
            player.max_speed = player.base_max_speed

    def _init_item_boxes(self):
        """Platziere Item-Boxen auf festen Positionen oder aus config."""
        self.item_boxes = []
        if self.map_config.get("type") == "open_square" and "item_boxes" in self.map_config:
            for box in self.map_config["item_boxes"]:
                x = box["x"]
                z = box["z"]
                self.item_boxes.append(ItemBox(x, z, respawn_interval=3.5))
        else:
            # Standard: winkelbasierte Positionen
            angles = [15.0, 38.0, 62.0, 86.0, 110.0, 134.0, 158.0, 202.0, 226.0, 250.0, 274.0, 298.0, 322.0, 346.0]
            outer_mod = self.map_config.get('outer_mod')
            inner_mod = self.map_config.get('inner_mod')
            placed_any = False

            for base in angles:
                placed = False
                for off in (0, 8, -8, 16, -16, 24, -24):
                    a = (base + off) % 360.0
                    inner = self.inner_r * (inner_mod(a) if inner_mod else 1.0)
                    outer = self.outer_r * (outer_mod(a) if outer_mod else 1.0)
                    if outer <= inner + 4.0:
                        continue
                    r = inner + (outer - inner) * 0.5
                    rad = math.radians(a)
                    x = math.cos(rad) * r
                    z = math.sin(rad) * r
                    if self._is_point_clear_for_pickup(x, z):
                        self.item_boxes.append(ItemBox(x, z, respawn_interval=3.5))
                        placed = True
                        placed_any = True
                        break

            if not placed_any:
                x, z = self._random_free_track_point()
                if x is not None:
                    self.item_boxes.append(ItemBox(x, z, respawn_interval=3.5))

    def _choose_item_from_box(self):
        # 3 Items: Abknaller (Zielsuch-Crash), Turbo (kurzer Boost), Wirbler (dreht Gegner)
        pool = getattr(self, "item_box_item_pool", None)
        if not pool:
            pool = ["abknaller", "turbo", "wirbler"]
        return random.choice(pool)

    def _grant_item(self, player, item_id, now):
        player.pending_item = item_id
        player.pending_item_execute_time = now + 2.0
        # kleine "Gluecksrad"-Animation oueben rechts
        player.item_roulette_start_time = now
        player.item_roulette_end_time = now + 1.2
        player.item_roulette_show_until = player.pending_item_execute_time
        player.item_roulette_result = item_id

    def _execute_item(self, player, item_id, now):
        if item_id == "abknaller":
            self._execute_abknaller(player, now)
        elif item_id == "turbo":
            self._execute_turbo(player, now)
        elif item_id == "wirbler":
            self._execute_wirbler(player, now)
        elif item_id == "schild":
            self._execute_shield(player, now)
        elif item_id == "frost":
            self._execute_frost(player, now)
        elif item_id == "oelspur":
            self._execute_oil_slick(player, now)
        elif item_id == "boost":
            self._execute_boost(player, now)
        elif item_id == "freeze":
            self._execute_freeze(player, now)

    def _schedule_attack(self, attacker, target, attack_type, delay, now):
        if getattr(attacker, "finished", False) or getattr(target, "finished", False):
            return
        if getattr(target, "shield_until", 0.0) > now:
            self._burst_shield(target, now)
            return
        execute_time = now + float(delay)
        self.pending_attacks.append({
            "start_time": now,
            "execute_time": execute_time,
            "attack_type": attack_type,
            "attacker": attacker,
            "attacker_name": attacker.name,
            "target": target,
            "seed": random.uniform(0.0, 1000.0),
        })
        target.incoming_attack_type = attack_type
        target.incoming_attack_from = attacker.name
        target.incoming_attack_execute_time = execute_time
        # Warnung bleibt auch kurz nach dem Treffer sichtbar
        target.incoming_attack_until = max(target.incoming_attack_until, execute_time + 2.5)

    def _process_pending_attacks(self, now):
        if not self.pending_attacks:
            return
        remaining = []
        for attack in self.pending_attacks:
            if isinstance(attack, dict):
                execute_time = attack.get("execute_time", now)
                attack_type = attack.get("attack_type")
                target = attack.get("target")
            else:
                execute_time, attack_type, attacker_name, target = attack
            if now < execute_time:
                remaining.append(attack)
                continue
            if target is None:
                continue
            if getattr(target, "finished", False):
                continue
            if getattr(target, "shield_until", 0.0) > now:
                self._burst_shield(target, now)
                continue

            if attack_type == "abknaller":
                self._apply_abknaller_effect(target, now)
            elif attack_type == "wirbler":
                self._apply_wirbler_effect(target, now)
            elif attack_type == "frost":
                self._apply_frost_effect(target, now)

        self.pending_attacks = remaining

    def _draw_item_projectiles(self, now):
        if not self.pending_attacks:
            return
        colors = {
            "abknaller": (1.0, 0.18, 0.08),
            "wirbler": (0.75, 0.2, 1.0),
            "frost": (0.35, 0.85, 1.0),
        }
        for attack in self.pending_attacks:
            if not isinstance(attack, dict):
                continue
            attacker = attack.get("attacker")
            target = attack.get("target")
            if attacker is None or target is None:
                continue
            start_time = attack.get("start_time", now)
            execute_time = attack.get("execute_time", now)
            duration = max(0.01, execute_time - start_time)
            t = _clamp((now - start_time) / duration, 0.0, 1.0)
            seed = attack.get("seed", 0.0)

            sx, sy, sz = attacker.pos[0], attacker.pos[1] + 1.2, attacker.pos[2]
            tx, ty, tz = target.pos[0], target.pos[1] + 1.1, target.pos[2]
            x = sx + (tx - sx) * t
            y = sy + (ty - sy) * t + math.sin(t * math.pi) * 2.0
            z = sz + (tz - sz) * t

            wobble = (1.0 - abs(0.5 - t) * 1.4)
            x += math.sin(now * 28.0 + seed) * 0.45 * wobble
            y += math.sin(now * 35.0 + seed * 0.7) * 0.30 * wobble
            z += math.cos(now * 31.0 + seed) * 0.45 * wobble

            col = colors.get(attack.get("attack_type"), (1.0, 0.9, 0.2))
            pulse = 0.75 + 0.25 * math.sin(now * 40.0 + seed)
            s = 0.45 + 0.18 * pulse
            glPushMatrix()
            glTranslatef(x, y, z)
            glRotatef((now * 900.0 + seed) % 360.0, 0, 1, 0)
            _gl_box_lit(-s, -s, -s, s, s, s, col)
            _gl_box_lit(-s * 0.45, -s * 0.45, -s * 0.45, s * 0.45, s * 0.45, s * 0.45, (1.0, 1.0, 0.95))
            glPopMatrix()

    def _projectile_snapshot(self, attack, now):
        attacker = attack.get("attacker")
        target = attack.get("target")
        if attacker is None or target is None:
            return None
        start_time = attack.get("start_time", now)
        execute_time = attack.get("execute_time", now)
        duration = max(0.01, execute_time - start_time)
        t = _clamp((now - start_time) / duration, 0.0, 1.0)
        seed = attack.get("seed", 0.0)
        sx, sy, sz = attacker.pos[0], attacker.pos[1] + 1.2, attacker.pos[2]
        tx, ty, tz = target.pos[0], target.pos[1] + 1.1, target.pos[2]
        wobble = (1.0 - abs(0.5 - t) * 1.4)
        x = sx + (tx - sx) * t + math.sin(now * 28.0 + seed) * 0.45 * wobble
        y = sy + (ty - sy) * t + math.sin(t * math.pi) * 2.0 + math.sin(now * 35.0 + seed * 0.7) * 0.30 * wobble
        z = sz + (tz - sz) * t + math.cos(now * 31.0 + seed) * 0.45 * wobble
        return {
            "type": attack.get("attack_type"),
            "x": x,
            "y": y,
            "z": z,
            "rot": (now * 900.0 + seed) % 360.0,
        }

    def _capture_replay_world(self, now):
        world = {
            "powerups": [],
            "boxes": [],
            "oil": [],
            "projectiles": [],
        }
        for item in getattr(self, "items", []):
            if item.is_active(now):
                world["powerups"].append((item.pos[0], item.pos[1], item.pos[2]))
        for box in getattr(self, "item_boxes", []):
            world["boxes"].append((box.pos[0], box.pos[1], box.pos[2], box.is_available(now)))
        for slick in getattr(self, "oil_slicks", []):
            if now < slick.get("expires", 0.0):
                age = now - slick.get("created", now)
                life = max(0.0, slick.get("expires", now) - now)
                world["oil"].append((slick["x"], slick["z"], age, life))
        for attack in getattr(self, "pending_attacks", []):
            if isinstance(attack, dict):
                snap = self._projectile_snapshot(attack, now)
                if snap:
                    world["projectiles"].append(snap)
        return world

    def _get_nearest_other_car(self, player):
        nearest = None
        nearest_dist2 = float("inf")
        for other in self.players:
            if other is player or other.finished:
                continue
            dx = other.pos[0] - player.pos[0]
            dz = other.pos[2] - player.pos[2]
            dist2 = dx * dx + dz * dz
            if dist2 < nearest_dist2:
                nearest_dist2 = dist2
                nearest = other
        if not nearest:
            return None, float("inf")
        return nearest, math.sqrt(nearest_dist2)

    def _execute_abknaller(self, player, now):
        # Zielt auf den naechsten Gegner und lst bei ihm einen Crash aus (3 Sekunden)
        target, _ = self._get_nearest_other_car(player)
        if not target:
            return
        self._schedule_attack(player, target, "abknaller", delay=0.9, now=now)

    def _apply_abknaller_effect(self, target, now):
        crash_until = now + 3.0
        target.velocity = 0.0
        target.crash_timer = max(target.crash_timer, crash_until)
        target.hit_spin_axis = "y"
        target.hit_spin_start = now
        target.hit_spin_until = now + 1.15
        target.hit_spin_degrees = random.choice([-1.0, 1.0]) * 360.0
        target.hit_pop_height = 1.35
        mid = [target.pos[0], target.pos[1], target.pos[2]]
        spawn_explosion(mid, target.particles)
        self.recorder.record_explosion(mid, self.frame_idx)

    def _execute_turbo(self, player, now):
        # kurzer Boost (fhlt sich anders an als das Map-Powerup)
        self._apply_speed_boost_custom(player, duration=3.5, multiplier=1.8)

    def _execute_wirbler(self, player, now):
        target, _ = self._get_nearest_other_car(player)
        if not target:
            return
        self._schedule_attack(player, target, "wirbler", delay=0.7, now=now)

    def _apply_wirbler_effect(self, target, now):
        target.velocity *= -0.35
        target.crash_timer = max(target.crash_timer, now + 1.2)
        target.hit_spin_axis = "x"
        target.hit_spin_start = now
        target.hit_spin_until = now + 1.0
        target.hit_spin_degrees = random.choice([-1.0, 1.0]) * 900.0
        target.hit_pop_height = 0.0
        spawn_explosion([target.pos[0], target.pos[1], target.pos[2]], target.particles)

    def _execute_boost(self, player, now):
        self._apply_speed_boost_custom(player, duration=5.0, multiplier=1.5)

    def _execute_shield(self, player, now):
        player.shield_until = max(getattr(player, "shield_until", 0.0), now + 8.0)
        for _ in range(18):
            player.particles.append(Particle([player.pos[0], player.pos[1] + 0.8, player.pos[2]], color=(0.25, 0.8, 1.0), speed=0.08, size=0.12, life=0.7))

    def _burst_shield(self, player, now):
        player.shield_until = max(getattr(player, "shield_until", 0.0), now + 0.3)
        player.incoming_attack_until = now + 0.6
        for _ in range(28):
            player.particles.append(Particle([player.pos[0], player.pos[1] + 0.9, player.pos[2]], color=(0.3, 0.9, 1.0), speed=0.16, size=0.10, life=0.45))

    def _execute_frost(self, player, now):
        target, _ = self._get_nearest_other_car(player)
        if not target:
            return
        self._schedule_attack(player, target, "frost", delay=0.75, now=now)

    def _apply_frost_effect(self, target, now):
        target.velocity *= 0.1
        target.crash_timer = max(target.crash_timer, now + 1.8)
        target.hit_spin_axis = "y"
        target.hit_spin_start = now
        target.hit_spin_until = now + 0.7
        target.hit_spin_degrees = random.choice([-1.0, 1.0]) * 180.0
        target.hit_pop_height = 0.15
        for _ in range(24):
            target.particles.append(Particle([target.pos[0], target.pos[1] + 0.6, target.pos[2]], color=(0.45, 0.9, 1.0), speed=0.08, size=0.12, life=0.65))

    def _execute_oil_slick(self, player, now):
        if getattr(player, "finished", False):
            return
        rad = math.radians(player.rot)
        x = player.pos[0] - math.sin(rad) * 2.4
        z = player.pos[2] - math.cos(rad) * 2.4
        self.oil_slicks.append({
            "x": x,
            "z": z,
            "owner": player,
            "created": now,
            "expires": now + 11.0,
            "used": set(),
        })

    def _update_oil_slicks(self, now):
        if not self.oil_slicks:
            return
        active = []
        for slick in self.oil_slicks:
            if now >= slick.get("expires", 0.0):
                continue
            sx, sz = slick["x"], slick["z"]
            used = slick.setdefault("used", set())
            for pl in self.players:
                if pl is slick.get("owner") or pl in used or pl.finished:
                    continue
                dx = pl.pos[0] - sx
                dz = pl.pos[2] - sz
                if (dx * dx + dz * dz) < 3.0 * 3.0:
                    used.add(pl)
                    pl.velocity *= 0.35
                    pl.rot += random.choice([-1.0, 1.0]) * 140.0
                    pl.hit_spin_axis = "y"
                    pl.hit_spin_start = now
                    pl.hit_spin_until = now + 0.85
                    pl.hit_spin_degrees = random.choice([-1.0, 1.0]) * 360.0
                    pl.hit_pop_height = 0.0
                    for _ in range(14):
                        pl.particles.append(Particle([pl.pos[0], pl.pos[1], pl.pos[2]], color=(0.04, 0.04, 0.04), speed=0.05, size=0.14, life=0.8))
            active.append(slick)
        self.oil_slicks = active

    def _draw_oil_slicks(self, now):
        if not self.oil_slicks:
            return
        for slick in self.oil_slicks:
            age = now - slick.get("created", now)
            life = max(0.0, slick.get("expires", now) - now)
            alpha = _clamp(life / 11.0, 0.15, 1.0)
            radius = 1.8 + min(1.0, age * 0.4)
            glPushMatrix()
            glTranslatef(slick["x"], 0.055, slick["z"])
            glColor4f(0.02, 0.02, 0.025, 0.55 * alpha)
            glBegin(GL_TRIANGLE_FAN)
            glVertex3f(0.0, 0.0, 0.0)
            for i in range(25):
                a = i / 24.0 * math.pi * 2.0
                r = radius * (0.78 + 0.22 * math.sin(a * 3.0 + age))
                glVertex3f(math.cos(a) * r, 0.0, math.sin(a) * r)
            glEnd()
            glColor4f(0.18, 0.18, 0.20, 0.50 * alpha)
            glBegin(GL_LINE_LOOP)
            for i in range(24):
                a = i / 24.0 * math.pi * 2.0
                glVertex3f(math.cos(a) * radius, 0.01, math.sin(a) * radius)
            glEnd()
            glPopMatrix()

    def _execute_freeze(self, player, now):
        # Friert den naechsten Gegner ein
        nearest_enemy = None
        min_dist = float('inf')
        for other in self.players:
            if other.team != player.team and not other.finished:
                dx = other.pos[0] - player.pos[0]
                dz = other.pos[2] - player.pos[2]
                dist = math.sqrt(dx**2 + dz**2)
                if dist < min_dist and dist < 15.0:  # Reichweite 15m
                    min_dist = dist
                    nearest_enemy = other
        if nearest_enemy:
            nearest_enemy.crash_timer = max(nearest_enemy.crash_timer, now + 3.0)  # 3 Sekunden einfrieren

    def _update_pending_items(self, now):
        for pl in self.players:
            if not pl.pending_item:
                continue
            if now >= pl.pending_item_execute_time:
                item_id = pl.pending_item
                pl.pending_item = None
                pl.pending_item_execute_time = 0.0
                pl.item_roulette_show_until = 0.0
                pl.item_roulette_result = None
                self._execute_item(pl, item_id, now)

    def _human_viewport_rects(self, w, h):
        """Qt-Rects (top-left origin) for each viewport area."""
        rects = []
        num_views = 4 if self.show_ai_views else self.num_humans
        if num_views <= 1:
            rects.append((0, 0, w, h))
        elif num_views == 2:
            half_w = w // 2
            rects.append((0, 0, half_w, h))
            rects.append((half_w, 0, half_w, h))
        elif num_views == 3:
            half_w = w // 2
            half_h = h // 2
            rects.append((0, 0, half_w, half_h))
            rects.append((half_w, 0, half_w, half_h))
            rects.append((0, half_h, w, half_h))
        else:
            half_w = w // 2
            half_h = h // 2
            rects.append((0, 0, half_w, half_h))
            rects.append((half_w, 0, half_w, half_h))
            rects.append((0, half_h, half_w, half_h))
            rects.append((half_w, half_h, half_w, half_h))
        return rects

    def _view_player_indices(self):
        """Which player index is shown in each viewport slot (0..num_views-1)."""
        if self.show_ai_views:
            idxs = []
            # humans first
            for i in range(min(self.num_humans, 4)):
                idxs.append(i)
            # then fill with AI slots
            for i in range(self.num_humans, 4):
                idxs.append(i)
            return idxs[:4]
        return list(range(self.num_humans))

    def _draw_item_roulette_overlays(self, now, w, h):
        if not getattr(self, "powerups_enabled", True):
            return
        names = {
            "abknaller": "Abknaller",
            "turbo": "Turbo",
            "wirbler": "Wirbler",
            "schild": "Schild",
            "frost": "Frost",
            "oelspur": "Oelspur",
        }
        colors = {
            "abknaller": QColor(255, 90, 90),
            "turbo": QColor(255, 220, 70),
            "wirbler": QColor(200, 90, 255),
            "schild": QColor(75, 210, 255),
            "frost": QColor(120, 230, 255),
            "oelspur": QColor(45, 45, 50),
        }
        pool = getattr(self, "item_box_item_pool", ["abknaller", "turbo", "wirbler", "schild", "frost", "oelspur"])

        view_idxs = self._view_player_indices()
        rects = self._human_viewport_rects(w, h)
        if not rects:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        for i in range(min(len(view_idxs), len(rects))):
            pl = self.players[view_idxs[i]]
            rx, ry, rw, rh = rects[i]
            box_w, box_h = 170, 56
            margin = 10
            x = rx + rw - box_w - margin - 34  # ein bisschen weiter links, aber immer noch rechts oueben
            y = ry + margin

            # incoming-attack warning (left of the roulette box)
            if pl.incoming_attack_until > now and pl.incoming_attack_type:
                warn_w, warn_h = 340, 56
                wx = x - warn_w - 10
                wy = y + 2
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(140, 0, 0, 180))
                p.drawRoundedRect(wx, wy, warn_w, warn_h, 10, 10)

                tname = names.get(pl.incoming_attack_type, str(pl.incoming_attack_type))
                from_txt = f" von {pl.incoming_attack_from}" if pl.incoming_attack_from else ""
                eta = max(0.0, pl.incoming_attack_execute_time - now)
                eta_txt = f"in {eta:.1f}s" if eta > 0 else "JETZT!"

                p.setPen(QColor(255, 235, 235, 245))
                p.setFont(QFont("Arial", 11, QFont.Bold))
                p.drawText(wx + 12, wy + 6, warn_w - 24, 22, Qt.AlignLeft | Qt.AlignVCenter, "DU WIRST ANGEGRIFFEN!")

                p.setPen(QColor(255, 220, 220, 240))
                p.setFont(QFont("Arial", 11))
                p.drawText(wx + 12, wy + 28, warn_w - 24, 22, Qt.AlignLeft | Qt.AlignVCenter, f"{tname}{from_txt}  ({eta_txt})")

            if pl.item_roulette_show_until <= now:
                continue

            # spinning choice while roulette runs
            if now < pl.item_roulette_end_time and pool:
                t = max(0.0, now - pl.item_roulette_start_time)
                display_id = pool[int(t * 12.0) % len(pool)]
            else:
                display_id = pl.item_roulette_result or pl.pending_item

            title = names.get(display_id, str(display_id))
            accent = colors.get(display_id, QColor(230, 230, 230))

            # background
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 150))
            p.drawRoundedRect(x, y, box_w, box_h, 10, 10)

            # wheel icon
            cx = x + 26
            cy = y + box_h // 2
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(255, 255, 255, 210), 2))
            p.drawEllipse(cx - 14, cy - 14, 28, 28)
            angle = (now - pl.item_roulette_start_time) * (720.0 if now < pl.item_roulette_end_time else 60.0)
            rad = math.radians(angle)
            px = cx + math.cos(rad) * 13.0
            py = cy - math.sin(rad) * 13.0
            p.setPen(QPen(accent, 3))
            p.drawLine(cx, cy, int(px), int(py))

            # text
            p.setPen(QColor(255, 255, 255, 235))
            p.setFont(QFont("Arial", 10, QFont.Bold))
            p.drawText(x + 52, y + 8, box_w - 58, 22, Qt.AlignLeft | Qt.AlignVCenter, title)

            remain = max(0.0, pl.pending_item_execute_time - now) if pl.pending_item else 0.0
            p.setPen(QColor(200, 200, 200, 220))
            p.setFont(QFont("Arial", 8))
            if pl.pending_item:
                p.drawText(x + 52, y + 28, box_w - 58, 20, Qt.AlignLeft | Qt.AlignVCenter, f"Auto in {remain:.1f}s")

        p.end()

    def _draw_minimap_overlay(self, w, h):
        size = max(150, min(220, int(min(w, h) * 0.24)))
        margin = 14
        x0 = w - size - margin
        y0 = h - size - margin
        pad = 12

        if self.map_config.get("type") == "open_square":
            extent = float(self.map_config.get("outer_base", self.outer_r)) * 1.12
        else:
            outer_mod = self.map_config.get("outer_mod", lambda a: 1.0)
            extent = max(self.outer_r * (outer_mod(a) if outer_mod else 1.0) for a in range(0, 360, 12)) * 1.12
        extent = max(20.0, extent)

        def mx(x):
            return int(x0 + pad + (float(x) + extent) / (extent * 2.0) * (size - pad * 2))

        def my(z):
            return int(y0 + pad + (extent - float(z)) / (extent * 2.0) * (size - pad * 2))

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setPen(QPen(QColor(255, 220, 80, 210), 2))
        p.setBrush(QColor(0, 0, 0, 145))
        p.drawRoundedRect(x0, y0, size, size, 8, 8)

        if self.map_config.get("type") == "open_square":
            half = float(self.map_config.get("outer_base", self.outer_r))
            p.setPen(QPen(QColor(210, 210, 200, 220), 2))
            p.drawRect(mx(-half), my(half), mx(half) - mx(-half), my(-half) - my(half))
        else:
            outer_mod = self.map_config.get("outer_mod", lambda a: 1.0)
            inner_mod = self.map_config.get("inner_mod", lambda a: 0.65)
            outer_points = []
            inner_points = []
            for a in range(0, 361, 6):
                outer = self.outer_r * (outer_mod(a) if outer_mod else 1.0)
                inner = self.inner_r * (inner_mod(a) if inner_mod else 1.0)
                rad = math.radians(a)
                outer_points.append(QPoint(mx(math.cos(rad) * outer), my(math.sin(rad) * outer)))
                inner_points.append(QPoint(mx(math.cos(rad) * inner), my(math.sin(rad) * inner)))
            p.setPen(QPen(QColor(220, 220, 210, 220), 2))
            for points in (outer_points, inner_points):
                for i in range(len(points) - 1):
                    p.drawLine(points[i], points[i + 1])

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 220, 70, 210))
        for box in getattr(self, "item_boxes", []):
            if box.is_available(time.time()):
                bx = mx(box.pos[0])
                by = my(box.pos[2])
                p.drawRect(bx - 2, by - 2, 4, 4)

        p.setBrush(QColor(120, 230, 255, 190))
        for item in getattr(self, "items", []):
            if item.is_active(time.time()):
                ix = mx(item.pos[0])
                iy = my(item.pos[2])
                p.drawEllipse(ix - 2, iy - 2, 4, 4)

        for idx, pl in enumerate(self.players):
            if getattr(pl, "finished", False):
                col = QColor(180, 180, 180, 210)
            else:
                rgb = getattr(pl, "color", (1.0, 1.0, 1.0))
                col = QColor(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 235)
            px = mx(pl.pos[0])
            py = my(pl.pos[2])
            p.setPen(QPen(QColor(0, 0, 0, 220), 2))
            p.setBrush(col)
            radius = 5 if idx < self.num_humans else 4
            p.drawEllipse(px - radius, py - radius, radius * 2, radius * 2)

        p.end()

    def _is_point_blocked_by_obstacle(self, x, z, buffer=0.0):
        if not self.obstacles:
            return False
        for ob in self.obstacles:
            try:
                ox = float(ob.get("x", 0))
                oz = float(ob.get("z", 0))
                w = float(ob.get("w", 3.0))
                l = float(ob.get("l", 3.0))
            except Exception:
                continue
            if abs(x - ox) < (w / 2.0 + buffer) and abs(z - oz) < (l / 2.0 + buffer):
                return True
        return False

    def _is_point_clear_for_pickup(self, x, z):
        if not self._on_track(x, z):
            return False
        if self._is_point_blocked_by_obstacle(x, z, buffer=1.2):
            return False
        for sx, sz, _ in self.start_positions:
            dx = x - sx
            dz = z - sz
            if dx * dx + dz * dz < (9.0 ** 2):
                return False
        for it in getattr(self, "items", []):
            if not getattr(it, "pos", None):
                continue
            dx = x - it.pos[0]
            dz = z - it.pos[2]
            if dx * dx + dz * dz < (3.0 ** 2):
                return False
        for box in getattr(self, "item_boxes", []):
            dx = x - box.pos[0]
            dz = z - box.pos[2]
            if dx * dx + dz * dz < (3.0 ** 2):
                return False
        return True

    def _random_free_track_point(self):
        if self.map_config.get("type") == "open_square":
            half = float(self.map_config.get("outer_base", self.outer_r))
            margin = 3.0
            for _ in range(120):
                x = random.uniform(-half + margin, half - margin)
                z = random.uniform(-half + margin, half - margin)
                if self._is_point_clear_for_pickup(x, z):
                    return x, z
            return None, None
        outer_mod = self.map_config.get('outer_mod')
        inner_mod = self.map_config.get('inner_mod')
        for _ in range(80):
            a = random.uniform(0.0, 360.0)
            inner = self.inner_r * (inner_mod(a) if inner_mod else 1.0)
            outer = self.outer_r * (outer_mod(a) if outer_mod else 1.0)
            if outer <= inner + 4.0:
                continue
            r = random.uniform(inner + 1.4, outer - 1.4)
            rad = math.radians(a)
            x = math.cos(rad) * r
            z = math.sin(rad) * r
            if self._is_point_clear_for_pickup(x, z):
                return x, z
        return None, None

    def _spawn_random_powerup(self):
        x, z = self._random_free_track_point()
        if x is None:
            return False
        self.items.append(SpeedBoostItem(x=x, z=z, lifetime=28.0))
        return True

    def _update_powerups(self, now):
        if not getattr(self, "powerups_enabled", True):
            return
        # remove expired/unavailable
        if self.items:
            self.items = [it for it in self.items if it.is_active(now)]

        if now < self.next_powerup_spawn_time:
            return

        if len(self.items) >= self.max_powerups:
            self.next_powerup_spawn_time = now + self.powerup_spawn_interval
            return

        self._spawn_random_powerup()
        self.next_powerup_spawn_time = now + self.powerup_spawn_interval

    def _get_nearest_uncollected_item(self, player_pos):
        """Finde das naechste nicht eingesammelte Item fuer die KI."""
        nearest = None
        nearest_dist = float('inf')
        
        for item in self.items:
            if item.collected or not item.is_active():
                continue
            dx = item.pos[0] - player_pos[0]
            dz = item.pos[2] - player_pos[2]
            dist = math.sqrt(dx*dx + dz*dz)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = item
        
        return nearest, nearest_dist if nearest else (None, float('inf'))

    def _get_nearest_available_item_box(self, player_pos, now):
        if not getattr(self, "item_boxes", None):
            return None, float("inf")

        nearest = None
        nearest_dist = float("inf")
        for box in self.item_boxes:
            if not box.is_available(now):
                continue
            dx = box.pos[0] - player_pos[0]
            dz = box.pos[2] - player_pos[2]
            dist = math.sqrt(dx * dx + dz * dz)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = box

        if not nearest:
            return None, float("inf")
        return nearest, nearest_dist

    def _rb_respawn_players_by_team(self):
        """Respawn all players at the color-team start positions (RB mode)."""
        if self.map_name != "Raeuber & Bulle":
            return

        sp = list(self.start_positions) if self.start_positions else []
        rot_spawns = sp[:6]
        blau_spawns = sp[6:12]

        def next_spawn(color_team):
            if color_team == "rot" and rot_spawns:
                return rot_spawns.pop(0)
            if color_team == "blau" and blau_spawns:
                return blau_spawns.pop(0)
            if rot_spawns:
                return rot_spawns.pop(0)
            if blau_spawns:
                return blau_spawns.pop(0)
            return (0, 0, 0)

        for pl in self.players:
            color_team = getattr(pl, "rb_color_team", None) or "blau"
            sx, sz, srot = next_spawn(color_team)
            pl.pos[0] = sx
            pl.pos[2] = sz
            pl.rot = srot
            pl.velocity = 0
            pl.crash_timer = 0
            pl.rb_caught = False
            pl.rb_caught_at = None
            pl.shield_until = time.time() + 1.0

        # Reset button state each round
        self.rb_button_hold = 0.0
        self.rb_button_cooldown_until = 0.0

    def _rb_apply_roles_to_players(self):
        """Apply the current round role mapping (blue/red -> bulle/raeuber) to all players."""
        if self.map_name != "Raeuber & Bulle":
            return

        # Defensive defaults (in case called very early in __init__)
        if not hasattr(self, "rb_role_blau"):
            self.rb_role_blau = "bulle"
        if not hasattr(self, "rb_role_rot"):
            self.rb_role_rot = "raeuber"

        for pl in self.players:
            color_team = getattr(pl, "rb_color_team", None) or "blau"
            role = self.rb_role_blau if color_team == "blau" else self.rb_role_rot
            pl.rb_role = role
            pl.team = role  # keep existing gameplay logic working

    def _rb_swap_teams(self):
        """Swap roles between the color-teams (RB mode). Players keep their color team."""
        if self.map_name != "Raeuber & Bulle":
            return

        self.rb_role_blau, self.rb_role_rot = self.rb_role_rot, self.rb_role_blau
        self._rb_apply_roles_to_players()

        self._rb_respawn_players_by_team()

    def _end_rb_round(self, winner_team):
        """End one RB round, award point, and either start next round or end match."""
        if self.race_over:
            return
        if self.map_name != "Raeuber & Bulle":
            return

        # winner_team is the role that won ("bulle" or "raeuber"). Convert to color-team.
        winner_color = "blau" if winner_team == self.rb_role_blau else "rot"
        if winner_color == "blau":
            self.rb_score_blau += 1
        else:
            self.rb_score_rot += 1

        # Decide whether match ends
        if self.rb_round_index >= (self.rb_total_rounds or 4):
            if self.rb_score_blau != self.rb_score_rot:
                match_winner = "blau" if self.rb_score_blau > self.rb_score_rot else "rot"
                self._end_rb_game(match_winner)
                return

            # Tie after the configured number of rounds:
            # do NOT extend the match (otherwise 4 Runden => 5 Runden feels wrong).
            # Use last-round winner as tiebreaker.
            self.rb_match_tiebreaker = winner_color
            self._end_rb_game(winner_color)
            return

        # Pause between rounds (small menu), then continue via rb_start_next_round().
        self.rb_last_round_winner = winner_team
        self.rb_last_round_index = int(self.rb_round_index or 1)
        self.rb_between_rounds = True
        self.countdown_phase = "paused"
        self.phase_timer = time.time()

        if self.on_rb_round_over:
            round_next = int(self.rb_last_round_index) + 1
            info = {
                "winner_role": winner_team,
                "winner_team": winner_color,
                "round_finished": self.rb_last_round_index,
                "round_next": round_next,
                "total_rounds": self.rb_total_rounds,
                "score_blau": self.rb_score_blau,
                "score_rot": self.rb_score_rot,
            }
            try:
                self.on_rb_round_over(info)
            except Exception:
                pass

    def _end_rb_game(self, winner_team):
        """Beende Raeuber & Bulle Match (winner_team: 'blau' oder 'rot')."""
        if self.race_over:
            return
        self.race_over = True

        if winner_team not in ("blau", "rot"):
            winner_team = "blau" if self.rb_score_blau > self.rb_score_rot else ("rot" if self.rb_score_rot > self.rb_score_blau else None)
        if winner_team not in ("blau", "rot"):
            tb = getattr(self, "rb_match_tiebreaker", None)
            winner_team = tb if tb in ("blau", "rot") else "blau"

        self.rb_winner_team = winner_team

        now = time.time()
        for pl in self.players:
            pl.rb_winner_team = winner_team
            pl.rb_score_blau = self.rb_score_blau
            pl.rb_score_rot = self.rb_score_rot
            pl.rb_total_rounds = self.rb_total_rounds
            pl.rb_match_tiebreaker = getattr(self, "rb_match_tiebreaker", None)

        for pl in self.players:
            if not pl.finished:
                pl.finished = True
                pl.finish_time = now
                self.finish_counter += 1
                pl.finish_place = self.finish_counter

        if self.on_race_over:
            self.on_race_over(self.players, self.recorder, self.recorder.frames, self.recorder.events)

    def _end_race_bulle_win(self):
        if self.map_name == "Raeuber & Bulle":
            self._end_rb_round("bulle")
        else:
            self._end_rb_game("bulle")

    def _end_race_raeuber_win(self):
        if self.map_name == "Raeuber & Bulle":
            self._end_rb_round("raeuber")
        else:
            self._end_rb_game("raeuber")
