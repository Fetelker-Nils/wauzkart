from ..runtime import *
from ..core.rendering import (
    _draw_ground,
    _draw_kart_model,
    _draw_track_decoration,
    _draw_track_ribbon,
    _gl_box_lit,
    _set_perspective,
)
from ..game.highlights import HighlightRecorder
from ..tracks.maps import *

# 
# Highlight-Replay-Widget
# 
class ReplayWidget(QOpenGLWidget):
    def __init__(self, frames, events, parent=None, map_name=None):
        super().__init__(parent)
        self.frames  = frames
        self.events  = events
        self.idx     = 0
        self.playing = True
        self.fps = int(getattr(HighlightRecorder, "FPS", 60) or 60)
        self.timer   = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(max(1, int(1000 / max(1, self.fps))))
        self.cam_angle = 30.0

        self.map_name = map_name
        self.map_config = MAPS.get(map_name, MAPS.get("Oval", {})).get("config", {})
        self.outer_r = float(self.map_config.get("outer_base", OUTER_R))
        self.inner_r = float(self.map_config.get("inner_base", INNER_R))
        self.start_positions = list(self.map_config.get("start_positions", START_POSITIONS))
        self.obstacles = self._prepare_obstacles_for_map(
            self.map_config,
            self.map_config.get("obstacles", []),
            self.start_positions,
        )

        self.focus_index = 0
        self.follow_camera = True

    @staticmethod
    def _prepare_obstacles_for_map(map_config, obstacles, start_positions):
        """Prepare obstacles for replay so they match the in-game placement."""
        if not obstacles:
            return []

        # Open-square maps use absolute obstacle coordinates from the config.
        if map_config.get("type") == "open_square":
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

        outer_mod = map_config.get("outer_mod")
        inner_mod = map_config.get("inner_mod")
        outer_base = float(map_config.get("outer_base", OUTER_R))
        inner_base = float(map_config.get("inner_base", INNER_R))

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
            for sx, sz, _ in start_positions:
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

    def set_focus_index(self, idx):
        try:
            self.focus_index = max(0, int(idx))
        except Exception:
            self.focus_index = 0

    def set_follow_camera(self, enabled):
        self.follow_camera = bool(enabled)

    def set_frame_index(self, idx):
        try:
            i = int(idx)
        except Exception:
            i = 0
        if not self.frames:
            self.idx = 0
            return
        self.idx = max(0, min(len(self.frames) - 1, i))

    def _tick(self):
        if self.playing:
            if self.idx < max(0, len(self.frames) - 1):
                self.idx += 1
            else:
                self.idx = 0
            self.cam_angle += 0.12
        self.update()

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST); glEnable(GL_BLEND)
        glShadeModel(GL_SMOOTH)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.50, 0.68, 0.88, 1)

    def resizeGL(self,w,h): glViewport(0,0,w,h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        if not self.frames: return
        w,h = self.width(), self.height()
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        _set_perspective(60, w/max(h,1), 0.1, 900)
        glMatrixMode(GL_MODELVIEW);  glLoadIdentity()

        snap = self.frames[self.idx]
        cars, world = self._split_replay_frame(snap)
        camera = world.get("camera", {}) if isinstance(world, dict) else {}
        camera_focus = camera.get("focus", self.focus_index)
        try:
            camera_focus = max(0, int(camera_focus))
        except Exception:
            camera_focus = self.focus_index
        camera_mode = camera.get("mode", "follow")
        fx, fy, fz, frot = 0.0, 0.0, 0.0, 0.0
        if cars and 0 <= camera_focus < len(cars):
            car = cars[camera_focus]
            try:
                fx, fy, fz, frot = float(car[0]), float(car[1]), float(car[2]), float(car[3])
            except Exception:
                fx, fy, fz, frot = 0.0, 0.0, 0.0, 0.0

        if camera_mode == "finish_line":
            outer0 = float(self.map_config.get("outer_base", self.outer_r or OUTER_R))
            inner0 = float(self.map_config.get("inner_base", self.inner_r or INNER_R))
            target_x = (outer0 + inner0) * 0.5
            gluLookAt(target_x + 7.5, 3.2, -9.5, target_x, 0.9, 0.0, 0, 1, 0)
        elif self.follow_camera and cars and 0 <= camera_focus < len(cars):
            rad = math.radians(frot)
            back = max(10.0, min(18.0, self.outer_r * 0.12))
            cx = fx - math.sin(rad) * back
            cz = fz - math.cos(rad) * back
            cy = 5.8
            gluLookAt(cx, cy, cz, fx, 1.0, fz, 0, 1, 0)
        else:
            cam_r = max(65.0, self.outer_r * 0.95)
            cx = fx + math.cos(math.radians(self.cam_angle)) * cam_r
            cz = fz + math.sin(math.radians(self.cam_angle)) * cam_r
            gluLookAt(cx, 28, cz, fx, 0, fz, 0, 1, 0)
        self._draw_track()
        self._draw_replay_world(world)
        for car in cars:
            if len(car) >= 8:
                x,y,z,rot,color,crashed,style,character = car[:8]
            else:
                x,y,z,rot,color,crashed = car
                style, character = "Standard", None
            self._draw_replay_car(x,y,z,rot,color,crashed,style,character)
        self._draw_fade_overlay(camera.get("fade", 0.0))

    @staticmethod
    def _split_replay_frame(snap):
        if isinstance(snap, dict):
            cars = snap.get("cars", [])
            world = snap.get("world", {})
            return cars or [], world or {}
        return snap or [], {}

    def _draw_track(self):
        cfg = self.map_config or {}
        outer_hint = float(cfg.get("outer_base", self.outer_r or OUTER_R))
        _draw_ground(max(140, int(outer_hint * 3.0)))

        # Open square / arena style map
        if cfg.get("type") == "open_square":
            half = outer_hint
            _gl_box_lit(-half, -0.01, -half, half, 0.02, half, (0.28, 0.28, 0.27))
            glColor3f(0.86, 0.86, 0.78)
            for x1, z1, x2, z2 in [
                (-half, -half, half, -half), (half, -half, half, half),
                (half, half, -half, half), (-half, half, -half, -half),
            ]:
                glBegin(GL_LINES)
                glVertex3f(x1, 0.06, z1); glVertex3f(x2, 0.06, z2)
                glEnd()
        else:
            outer_mod = cfg.get("outer_mod", lambda a: 1.0)
            inner_mod = cfg.get("inner_mod", lambda a: 0.65)
            outer_r = float(cfg.get("outer_base", self.outer_r or OUTER_R))
            inner_r = float(cfg.get("inner_base", self.inner_r or INNER_R))
            _draw_track_ribbon(outer_mod, inner_mod, outer_r, inner_r)
            _draw_track_decoration(outer_mod, outer_r)

            inner0 = inner_r * (inner_mod(0) if inner_mod else 1.0)
            outer0 = outer_r * (outer_mod(0) if outer_mod else 1.0)
            if outer0 <= inner0 + 0.5:
                inner0, outer0 = inner_r, outer_r

            glColor3f(1.0, 1.0, 1.0)
            for i in range(12):
                x1 = inner0 + i / 12 * (outer0 - inner0)
                x2 = inner0 + (i + 1) / 12 * (outer0 - inner0)
                if i % 2 == 0:
                    glColor3f(1.0, 1.0, 1.0)
                else:
                    glColor3f(0.1, 0.1, 0.1)
                glBegin(GL_QUADS)
                glVertex3f(x1, 0.02, -1.2); glVertex3f(x2, 0.02, -1.2)
                glVertex3f(x2, 0.02,  1.2); glVertex3f(x1, 0.02,  1.2)
                glEnd()

        # Obstacles / walls
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
            glPushMatrix()
            glTranslatef(ox, 0.02, oz)
            _gl_box_lit(-w/2, 0.0, -l/2, w/2, h, l/2, col)
            glPopMatrix()

    def _draw_replay_car(self,x,y,z,rot,color,crashed,style="Standard",character=None):
        glPushMatrix(); glTranslatef(x,y,z); glRotatef(rot,0,1,0)
        _draw_kart_model(color, style, character, crashed)
        glPopMatrix()

    def _draw_replay_world(self, world):
        if not world:
            return
        for item in world.get("powerups", []):
            try:
                x, y, z = item[:3]
            except Exception:
                continue
            self._draw_replay_powerup(x, y, z)
        for box in world.get("boxes", []):
            try:
                x, y, z, available = box[:4]
            except Exception:
                continue
            self._draw_replay_item_box(x, y, z, bool(available))
        for slick in world.get("oil", []):
            try:
                x, z, age, life = slick[:4]
            except Exception:
                continue
            self._draw_replay_oil(x, z, age, life)
        for projectile in world.get("projectiles", []):
            if isinstance(projectile, dict):
                self._draw_replay_projectile(projectile)

    def _draw_replay_powerup(self, x, y, z):
        glPushMatrix()
        glTranslatef(float(x), float(y) + 0.15, float(z))
        s = 0.45
        _gl_box_lit(-s, -s, -s, s, s, s, (1.0, 0.85, 0.05))
        _gl_box_lit(-s * 0.45, -s * 0.45, -s * 0.45, s * 0.45, s * 0.45, s * 0.45, (1.0, 1.0, 0.55))
        glPopMatrix()

    def _draw_replay_item_box(self, x, y, z, available):
        col = (0.25, 0.65, 1.0) if available else (0.12, 0.18, 0.25)
        inner = (0.95, 0.95, 1.0) if available else (0.20, 0.24, 0.30)
        s = 1.2
        glPushMatrix()
        glTranslatef(float(x), float(y), float(z))
        _gl_box_lit(-s / 2, 0.0, -s / 2, s / 2, 0.55, s / 2, col)
        _gl_box_lit(-s / 3, 0.12, -s / 3, s / 3, 0.68, s / 3, inner)
        glPopMatrix()

    def _draw_replay_oil(self, x, z, age, life):
        alpha = max(0.15, min(1.0, float(life) / 11.0))
        radius = 1.8 + min(1.0, float(age) * 0.4)
        glPushMatrix()
        glTranslatef(float(x), 0.055, float(z))
        glColor4f(0.02, 0.02, 0.025, 0.55 * alpha)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, 0.0, 0.0)
        for i in range(25):
            a = i / 24.0 * math.pi * 2.0
            r = radius * (0.78 + 0.22 * math.sin(a * 3.0 + float(age)))
            glVertex3f(math.cos(a) * r, 0.0, math.sin(a) * r)
        glEnd()
        glColor4f(0.18, 0.18, 0.20, 0.50 * alpha)
        glBegin(GL_LINE_LOOP)
        for i in range(24):
            a = i / 24.0 * math.pi * 2.0
            glVertex3f(math.cos(a) * radius, 0.01, math.sin(a) * radius)
        glEnd()
        glPopMatrix()

    def _draw_replay_projectile(self, projectile):
        typ = projectile.get("type")
        colors = {
            "abknaller": (1.0, 0.18, 0.08),
            "wirbler": (0.75, 0.2, 1.0),
            "frost": (0.35, 0.85, 1.0),
        }
        col = colors.get(typ, (1.0, 0.9, 0.2))
        try:
            x = float(projectile.get("x", 0.0))
            y = float(projectile.get("y", 1.0))
            z = float(projectile.get("z", 0.0))
            rot = float(projectile.get("rot", 0.0))
        except Exception:
            return
        s = 0.56
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(rot, 0, 1, 0)
        _gl_box_lit(-s, -s, -s, s, s, s, col)
        _gl_box_lit(-s * 0.45, -s * 0.45, -s * 0.45, s * 0.45, s * 0.45, s * 0.45, (1.0, 1.0, 0.95))
        glPopMatrix()

    def _draw_fade_overlay(self, fade):
        try:
            amount = max(0.0, min(1.0, float(fade)))
        except Exception:
            amount = 0.0
        if amount <= 0.01:
            return
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, int(255 * amount)))
        painter.drawRect(0, 0, self.width(), self.height())
        painter.end()
