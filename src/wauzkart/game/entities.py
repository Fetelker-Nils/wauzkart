from ..runtime import *
from ..core.rendering import _gl_box, _gl_box_lit
from ..tracks.maps import *

# 
# Player
# 
class Player:
    def __init__(self, x, z, rot, color, name, is_ai=False, ai_diff=None, style="Standard", character=None, team=None):
        self.pos    = [x, 0.5, z]
        self.rot    = rot
        self.velocity = 0
        self.style = style
        self.character = character or (CHARACTER_NAMES[0] if CHARACTER_NAMES else None)
        self.acc      = 12
        self.max_speed= 14
        self.friction = 6
        self.turn_speed = 180
        self.radius   = 1
        self.color    = color
        self.name     = name
        self.is_ai    = is_ai
        self.laps     = 0
        self.sector   = self._get_sector(x, z)
        self.sectors_visited = set()
        self.start_time  = None
        self.finish_time = None
        self.finished    = False
        self.finish_place= None
        self.crash_timer = 0
        self.particles   = []
        self.rocket_boost  = False
        self.boost_amount  = 0.0
        self.ai_diff     = ai_diff or AI_DIFFICULTIES["Mittel"]
        self.ai_wobble_t = random.uniform(0, 100)
        self.ai_stuck_timer = 0
        self.parking_spot = None
        self.moving_to_parking = False
        self.speed_boost_timer = 0  # Zeit wann Boost endet
        self.speed_boost_active = False
        self.base_max_speed = self.max_speed
        self.drift_charge = 0.0
        self.drift_spark_level = 0
        self.drift_boost_flash_until = 0.0
        self.last_item_collected_time = -float('inf')  # Cooldown fuer Item-Verfolgung
        self.last_box_collected_time = -float('inf')   # KI-Abklingzeit fuer Kstchen

        # Item-Box Items (werden automatisch nach kurzer Zeit ausgelst)
        self.pending_item = None
        self.pending_item_execute_time = 0.0
        self.item_roulette_start_time = 0.0
        self.item_roulette_end_time = 0.0
        self.item_roulette_show_until = 0.0
        self.item_roulette_result = None

        # Incoming-Attack Anzeige (wenn jemand dich anvisiert)
        self.incoming_attack_type = None
        self.incoming_attack_from = None
        self.incoming_attack_execute_time = 0.0
        self.incoming_attack_until = 0.0

        # Treffer-Animationen fuer Item-Angriffe.
        self.hit_spin_axis = None
        self.hit_spin_start = 0.0
        self.hit_spin_until = 0.0
        self.hit_spin_degrees = 0.0
        self.hit_pop_height = 0.0
        
        #  Intelligente KI Attribute 
        self.ai_position_history = []  # Letzten 10 Frames der Position
        self.team = team
        self.shield_until = 0.0

        # Raeuber & Bulle (Modus-Status)
        self.rb_caught = False
        self.rb_caught_at = None
        self.rb_winner_team = None
        self.rb_color_team = None  # "blau" / "rot" (feste Team-Zugehrigkeit im Match)
        self.rb_role = None        # "bulle" / "raeuber" (Rolle pro Runde)
        self.ai_target_points = []     # Mehrere Lookahead-Punkte
        self.ai_opponent_threat = 0.0  # Wie bedroht ist dieses Auto (0-1)
        self.ai_is_blocking = False    # Wird das Auto gerade blockiertDown
        self.ai_overtake_mode = False  # Versucht gerade zu berholenDown
        self.ai_expected_brake_point = None  # Wo sollte gebremst werdenDown
        self.ai_ideal_speed = 0        # Ideale Geschwindigkeit fuer naechsten Punkt
        self.ai_last_decision_time = time.time()  # Fuer Entscheidungs-Timing
        self.ai_adaptive_aggressive = 1.0  # Passt sich an (1.0 = normal)
        self.ai_track_confidence = 0.5    # Vertrauen in eigene Rennlinie (0-1)
        self.ai_decision_timer = 0     # Timer fuer periodische Entscheidungen

    @staticmethod
    def _get_sector(x, z):
        if x >= 0 and z <  0: return 0
        if x <  0 and z <  0: return 1
        if x <  0 and z >= 0: return 2
        return 3

# 
# Partikel
# 
class Particle:
    def __init__(self, pos, color=(0.8,0.8,0.8), speed=0.05, size=0.1, life=None, gravity=0.0):
        self.pos  = pos[:]
        s = speed
        self.vel  = [random.uniform(-s,s), random.uniform(s*0.2,s*1.5), random.uniform(-s,s)]
        self.life = life if life is not None else random.uniform(0.3, 0.8)
        self.max_life = self.life
        self.color  = color
        self.size   = size
        self.gravity= gravity

    def update(self, dt):
        self.life      -= dt
        self.vel[1]    -= self.gravity * dt
        for i in range(3): self.pos[i] += self.vel[i]

    def draw(self):
        if self.life <= 0: return
        alpha = max(0, self.life / self.max_life)
        glColor4f(*self.color, alpha)
        glPushMatrix(); glTranslatef(*self.pos)
        s = self.size
        glBegin(GL_QUADS)
        glVertex3f(-s,-s,-s); glVertex3f(s,-s,-s)
        glVertex3f( s, s,-s); glVertex3f(-s,s,-s)
        glEnd(); glPopMatrix()

def spawn_explosion(pos, plist):
    cx,cy,cz = pos
    for _ in range(40):
        plist.append(Particle([cx,cy,cz],
            color=(random.uniform(0.9,1.0), random.uniform(0.2,0.6), 0.0),
            speed=random.uniform(0.08,0.18), size=random.uniform(0.15,0.35),
            life=random.uniform(0.4,0.9), gravity=0.05))
    for _ in range(25):
        g = random.uniform(0.2,0.5)
        plist.append(Particle([cx,cy+0.5,cz], color=(g,g,g),
            speed=random.uniform(0.03,0.08), size=random.uniform(0.2,0.5),
            life=random.uniform(0.8,1.5), gravity=-0.01))
    for _ in range(30):
        plist.append(Particle([cx,cy,cz],
            color=(1.0, random.uniform(0.8,1.0), 0.2),
            speed=random.uniform(0.15,0.30), size=random.uniform(0.05,0.12),
            life=random.uniform(0.2,0.5), gravity=0.12))

# 
# Speed-Boost-Items
# 
class SpeedBoostItem:
    def __init__(self, angle=None, radius=MID_R, x=None, z=None, lifetime=20.0):
        """Erstelle ein Speed-Boost-Item auf der Strecke.
        angle: Position im Kreis (0-360 Grad)
        """
        self.angle = angle
        self.radius = radius
        if x is not None and z is not None:
            self.pos = [float(x), 0.3, float(z)]
        else:
            angle = 0 if angle is None else angle
            self.pos = [
                math.cos(math.radians(angle)) * radius,
                0.3,
                math.sin(math.radians(angle)) * radius
            ]
        self.size = 0.5
        self.color = (1.0, 0.85, 0.0)  # Gold
        self.collected = False
        self.collected_by = None
        self.spawn_time = time.time()
        self.despawn_time = self.spawn_time + float(lifetime)
        self.rotation = 0
        self.bob_offset = 0
        self.bob_time = 0

    def is_active(self, now=None):
        if self.collected:
            return False
        now = time.time() if now is None else now
        return now <= self.despawn_time

    def draw(self):
        """Zeichne das Item mit Rotation und Bobbing."""
        if not self.is_active():
            return
        
        # Bobbing-Animation
        self.bob_time += 0.03
        self.bob_offset = math.sin(self.bob_time) * 0.15
        
        # Rotation fuer Animation
        self.rotation += 2
        
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1] + self.bob_offset, self.pos[2])
        glRotatef(self.rotation, 0, 1, 0)
        
        # Low-poly glowing crystal.
        s = self.size
        top = (0.0, s * 1.25, 0.0)
        bottom = (0.0, -s * 1.05, 0.0)
        pts = [(-s, 0, -s), (s, 0, -s), (s, 0, s), (-s, 0, s)]
        glBegin(GL_TRIANGLES)
        for i in range(4):
            a = pts[i]
            b = pts[(i + 1) % 4]
            glColor3f(1.0, 0.92, 0.25)
            glVertex3f(*top); glVertex3f(*a); glVertex3f(*b)
            glColor3f(0.95, 0.55, 0.04)
            glVertex3f(*bottom); glVertex3f(*b); glVertex3f(*a)
        glEnd()
        glColor3f(1.0, 0.95, 0.45)
        glBegin(GL_LINE_LOOP)
        for p in pts:
            glVertex3f(*p)
        glEnd()
        
        glPopMatrix()

    def is_nearby(self, pos, radius=2.0):
        """berprfe, ob ein Spieler das Item hat berhrt."""
        if not self.is_active():
            return False
        dx = pos[0] - self.pos[0]
        dz = pos[2] - self.pos[2]
        dist = math.sqrt(dx*dx + dz*dz)
        return dist < radius


# 
# Item-Boxen (fester Platz, regenerieren, Auto-Use)
# 
class ItemBox:
    def __init__(self, x, z, respawn_interval=5.0):
        self.pos = [float(x), 0.02, float(z)]
        self.size = 1.2
        self.respawn_interval = float(respawn_interval)
        self.next_available_time = 0.0
        self.rotation = random.uniform(0.0, 360.0)

    def is_available(self, now=None):
        now = time.time() if now is None else now
        return now >= self.next_available_time

    def consume(self, now=None):
        now = time.time() if now is None else now
        self.next_available_time = now + self.respawn_interval

    def is_nearby(self, pos, radius=2.0):
        dx = pos[0] - self.pos[0]
        dz = pos[2] - self.pos[2]
        return (dx * dx + dz * dz) < (radius * radius)

    def draw(self):
        now = time.time()
        available = self.is_available(now)
        self.rotation = (self.rotation + (3.0 if available else 1.2)) % 360.0

        # Blue when available, dim when on cooldown
        col = (0.25, 0.65, 1.0) if available else (0.12, 0.18, 0.25)
        s = self.size
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        glRotatef(self.rotation, 0, 1, 0)
        _gl_box_lit(-s / 2, 0.0, -s / 2, s / 2, 0.55, s / 2, col)
        _gl_box_lit(-s / 3, 0.12, -s / 3, s / 3, 0.68, s / 3, (0.95, 0.95, 1.0) if available else (0.20, 0.24, 0.30))
        glPopMatrix()
