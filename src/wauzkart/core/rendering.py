from ..runtime import *
from ..tracks.maps import CHARACTER_DEFS

def _hud_text_color_for_rgb(rgb, default_hex):
    """Ensure HUD text stays readable on dark background (e.g. black cars)."""
    try:
        r, g, b = rgb
    except Exception:
        return default_hex

    # perceived luminance (0..1)
    lum = 0.2126 * float(r) + 0.7152 * float(g) + 0.0722 * float(b)
    if lum < 0.22:
        return "#ffffff"
    return default_hex

def _gl_box(x1, y1, z1, x2, y2, z2, color):
    r, g, b = color
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    # top
    glVertex3f(x1, y2, z1); glVertex3f(x2, y2, z1); glVertex3f(x2, y2, z2); glVertex3f(x1, y2, z2)
    # bottom
    glVertex3f(x1, y1, z2); glVertex3f(x2, y1, z2); glVertex3f(x2, y1, z1); glVertex3f(x1, y1, z1)
    # front
    glVertex3f(x1, y1, z2); glVertex3f(x2, y1, z2); glVertex3f(x2, y2, z2); glVertex3f(x1, y2, z2)
    # back
    glVertex3f(x2, y1, z1); glVertex3f(x1, y1, z1); glVertex3f(x1, y2, z1); glVertex3f(x2, y2, z1)
    # left
    glVertex3f(x1, y1, z1); glVertex3f(x1, y1, z2); glVertex3f(x1, y2, z2); glVertex3f(x1, y2, z1)
    # right
    glVertex3f(x2, y1, z2); glVertex3f(x2, y1, z1); glVertex3f(x2, y2, z1); glVertex3f(x2, y2, z2)
    glEnd()

def _shade_color(color, factor):
    r, g, b = color
    return (
        max(0.0, min(1.0, r * factor)),
        max(0.0, min(1.0, g * factor)),
        max(0.0, min(1.0, b * factor)),
    )

def _gl_box_lit(x1, y1, z1, x2, y2, z2, color):
    """Box with simple per-face brightness for more depth without real lighting."""
    faces = [
        ((x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2), 1.18),
        ((x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1), 0.55),
        ((x1, y1, z2), (x2, y1, z2), (x2, y2, z2), (x1, y2, z2), 0.98),
        ((x2, y1, z1), (x1, y1, z1), (x1, y2, z1), (x2, y2, z1), 0.78),
        ((x1, y1, z1), (x1, y1, z2), (x1, y2, z2), (x1, y2, z1), 0.68),
        ((x2, y1, z2), (x2, y1, z1), (x2, y2, z1), (x2, y2, z2), 0.88),
    ]
    glBegin(GL_QUADS)
    for v1, v2, v3, v4, factor in faces:
        glColor3f(*_shade_color(color, factor))
        glVertex3f(*v1); glVertex3f(*v2); glVertex3f(*v3); glVertex3f(*v4)
    glEnd()

def _gl_cylinder(radius, width, color, segments=18):
    """Cylinder aligned along the X axis, useful for wheels."""
    glColor3f(*color)
    half = width / 2.0
    glBegin(GL_QUAD_STRIP)
    for i in range(segments + 1):
        a = math.tau * i / segments
        y = math.cos(a) * radius
        z = math.sin(a) * radius
        glVertex3f(-half, y, z)
        glVertex3f(half, y, z)
    glEnd()

    for x in (-half, half):
        glBegin(GL_TRIANGLE_FAN)
        glColor3f(*_shade_color(color, 0.82 if x < 0 else 1.05))
        glVertex3f(x, 0, 0)
        for i in range(segments + 1):
            a = math.tau * i / segments
            glVertex3f(x, math.cos(a) * radius, math.sin(a) * radius)
        glEnd()

def _draw_wheel(x, y, z, radius=0.28, width=0.22):
    glPushMatrix()
    glTranslatef(x, y, z)
    _gl_cylinder(radius, width, (0.02, 0.02, 0.02), 20)
    _gl_cylinder(radius * 0.54, width + 0.02, (0.55, 0.55, 0.50), 16)
    glPopMatrix()

def _draw_kart_model(color, style="Standard", character=None, crashed=False):
    r, g, b = color
    if crashed:
        color = (min(r + 0.18, 1), min(g + 0.18, 1), min(b + 0.18, 1))

    if style == "Sport":
        body_h, roof_h, length = 0.42, 0.55, 2.25
        spoiler_h = 0.72
    elif style == "Offroad":
        body_h, roof_h, length = 0.58, 0.88, 2.35
        spoiler_h = 0.92
    elif style == "Retro":
        body_h, roof_h, length = 0.50, 0.68, 2.10
        spoiler_h = 0.75
    else:
        body_h, roof_h, length = 0.48, 0.72, 2.18
        spoiler_h = 0.78

    # Lower chassis and colored body.
    _gl_box_lit(-0.78, 0.06, -length / 2, 0.78, body_h, length / 2, _shade_color(color, 0.82))
    _gl_box_lit(-0.62, body_h - 0.04, -0.72, 0.62, body_h + 0.25, 0.58, color)

    # Nose, cabin frame and rear deck.
    _gl_box_lit(-0.48, body_h + 0.02, -1.12, 0.48, body_h + 0.28, -0.44, _shade_color(color, 1.08))
    _gl_box_lit(-0.46, roof_h - 0.06, -0.30, 0.46, roof_h + 0.08, 0.36, _shade_color(color, 1.16))
    _gl_box_lit(-0.52, body_h + 0.02, 0.55, 0.52, body_h + 0.22, 1.02, _shade_color(color, 0.92))

    # Glass panels.
    glass = (0.16, 0.32, 0.42)
    _gl_box_lit(-0.40, roof_h + 0.02, -0.43, 0.40, roof_h + 0.13, -0.32, glass)
    _gl_box_lit(-0.40, roof_h + 0.02, 0.36, 0.40, roof_h + 0.13, 0.48, glass)

    # Lights and grille.
    _gl_box_lit(-0.46, body_h + 0.02, -1.16, -0.18, body_h + 0.14, -1.10, (1.0, 0.92, 0.58))
    _gl_box_lit(0.18, body_h + 0.02, -1.16, 0.46, body_h + 0.14, -1.10, (1.0, 0.92, 0.58))
    _gl_box_lit(-0.50, body_h - 0.13, -1.17, 0.50, body_h - 0.02, -1.11, (0.04, 0.04, 0.045))
    _gl_box_lit(-0.52, body_h + 0.00, 1.10, -0.20, body_h + 0.12, 1.16, (0.85, 0.03, 0.02))
    _gl_box_lit(0.20, body_h + 0.00, 1.10, 0.52, body_h + 0.12, 1.16, (0.85, 0.03, 0.02))

    # Axles, wheels and optional offroad clearance.
    tire_r = 0.30 if style != "Offroad" else 0.40
    tire_y = 0.18 if style != "Offroad" else 0.24
    for z in (-0.72, 0.72):
        _gl_box_lit(-0.88, tire_y - 0.05, z - 0.04, 0.88, tire_y + 0.05, z + 0.04, (0.09, 0.09, 0.09))
    for wx, wz in [(-0.88, -0.72), (0.88, -0.72), (-0.88, 0.72), (0.88, 0.72)]:
        _draw_wheel(wx, tire_y, wz, tire_r, 0.24)

    # Spoiler, bumper bars and style details.
    _gl_box_lit(-0.62, spoiler_h, 1.02, 0.62, spoiler_h + 0.09, 1.22, _shade_color(color, 0.72))
    _gl_box_lit(-0.72, 0.18, -1.23, 0.72, 0.30, -1.16, (0.05, 0.05, 0.055))
    _gl_box_lit(-0.72, 0.18, 1.16, 0.72, 0.30, 1.23, (0.05, 0.05, 0.055))
    if style == "Sport":
        _gl_box_lit(-0.12, body_h + 0.18, -1.05, 0.12, body_h + 0.34, -0.58, _shade_color(color, 1.28))
    elif style == "Retro":
        _gl_box_lit(-0.34, roof_h + 0.06, -0.18, 0.34, roof_h + 0.36, -0.10, (0.11, 0.11, 0.12))
    elif style == "Offroad":
        _gl_box_lit(-0.68, body_h + 0.20, -1.04, 0.68, body_h + 0.32, -0.92, (0.08, 0.08, 0.08))

    _draw_character_in_car(character, roof_h)

def _draw_ground(size=140):
    glColor3f(0.12, 0.30, 0.13)
    glBegin(GL_QUADS)
    glVertex3f(-size, -0.03, -size); glVertex3f(size, -0.03, -size)
    glVertex3f(size, -0.03, size); glVertex3f(-size, -0.03, size)
    glEnd()

    glColor3f(0.10, 0.24, 0.10)
    step = 12
    glBegin(GL_LINES)
    for x in range(-size, size + 1, step):
        glVertex3f(x, -0.025, -size); glVertex3f(x, -0.025, size)
    for z in range(-size, size + 1, step):
        glVertex3f(-size, -0.024, z); glVertex3f(size, -0.024, z)
    glEnd()

    _draw_mountain_ring(size)

def _terrain_noise(index, phase=0.0):
    return (
        0.55
        + 0.30 * math.sin(index * 1.73 + phase)
        + 0.15 * math.sin(index * 3.11 + phase * 0.6)
    )

def _draw_mountain_ring(size):
    """Low-poly mountain horizon that hides the hard terrain edge."""
    inner = float(size) * 0.74
    mid = float(size) * 0.94
    outer = float(size) * 1.18
    segments = 96
    base_y = -0.04

    # Distant tall blue-grey wall, like atmospheric mountains.
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(segments + 1):
        a = math.tau * i / segments
        n = _terrain_noise(i, 0.8)
        ridge = 32.0 + n * 34.0
        x_outer = math.cos(a) * outer
        z_outer = math.sin(a) * outer
        glColor3f(0.20, 0.27, 0.34)
        glVertex3f(x_outer, base_y, z_outer)
        glColor3f(0.48, 0.56, 0.64)
        glVertex3f(x_outer, ridge, z_outer)
    glEnd()

    # Mid layer adds sharp rock faces behind the foothills.
    glBegin(GL_TRIANGLES)
    for i in range(segments):
        a1 = math.tau * i / segments
        a2 = math.tau * (i + 1) / segments
        amid = (a1 + a2) * 0.5
        n = _terrain_noise(i, 4.1)
        peak_h = 22.0 + n * 36.0
        r_peak = (mid + outer) * 0.5
        x1, z1 = math.cos(a1) * mid, math.sin(a1) * mid
        x2, z2 = math.cos(a2) * mid, math.sin(a2) * mid
        xp, zp = math.cos(amid) * r_peak, math.sin(amid) * r_peak
        glColor3f(0.24, 0.27, 0.25)
        glVertex3f(x1, base_y, z1)
        glColor3f(0.17, 0.20, 0.22)
        glVertex3f(x2, base_y, z2)
        glColor3f(0.46, 0.45, 0.40)
        glVertex3f(xp, peak_h, zp)
    glEnd()

    # Closer green-brown foothills with uneven peaks.
    glBegin(GL_TRIANGLES)
    for i in range(segments):
        a1 = math.tau * i / segments
        a2 = math.tau * (i + 1) / segments
        amid = (a1 + a2) * 0.5
        n = _terrain_noise(i, 2.4)
        peak_h = 14.0 + n * 24.0
        r_peak = (inner + mid) * 0.5
        x1, z1 = math.cos(a1) * inner, math.sin(a1) * inner
        x2, z2 = math.cos(a2) * inner, math.sin(a2) * inner
        xp, zp = math.cos(amid) * r_peak, math.sin(amid) * r_peak
        glColor3f(0.13, 0.26, 0.13)
        glVertex3f(x1, base_y, z1)
        glColor3f(0.09, 0.20, 0.10)
        glVertex3f(x2, base_y, z2)
        glColor3f(0.34, 0.42, 0.26)
        glVertex3f(xp, peak_h, zp)
    glEnd()

    # Bright snow caps on both visible layers.
    glBegin(GL_TRIANGLES)
    for layer, phase, radius, base_h, scale_h, threshold, drop in [
        ("mid", 4.1, (mid + outer) * 0.5, 22.0, 36.0, 0.58, 8.5),
        ("front", 2.4, (inner + mid) * 0.5, 14.0, 24.0, 0.70, 5.5),
    ]:
        for i in range(0, segments, 2):
            n = _terrain_noise(i, phase)
            if n < threshold:
                continue
            a1 = math.tau * i / segments
            a2 = math.tau * (i + 1) / segments
            amid = (a1 + a2) * 0.5
            peak_h = base_h + n * scale_h
            cap_w = float(size) * (0.020 if layer == "mid" else 0.015)
            xp, zp = math.cos(amid) * radius, math.sin(amid) * radius
            sx, sz = -math.sin(amid) * cap_w, math.cos(amid) * cap_w
            glColor3f(0.94, 0.96, 0.92)
            glVertex3f(xp, peak_h, zp)
            glColor3f(0.76, 0.82, 0.84)
            glVertex3f(xp - sx, peak_h - drop, zp - sz)
            glVertex3f(xp + sx, peak_h - drop, zp + sz)
    glEnd()

def _draw_track_ribbon(outer_mod, inner_mod, outer_r, inner_r):
    # Asphalt.
    glBegin(GL_TRIANGLE_STRIP)
    for a in range(0, 361, 2):
        r = math.radians(a)
        outer = outer_r * outer_mod(a)
        inner = inner_r * inner_mod(a)
        shade = 0.31 + 0.04 * math.sin(math.radians(a * 3))
        glColor3f(shade, shade, shade)
        glVertex3f(math.cos(r) * outer, 0.0, math.sin(r) * outer)
        glVertex3f(math.cos(r) * inner, 0.0, math.sin(r) * inner)
    glEnd()

    # Red/white kerbs.
    for outer_side in (True, False):
        glBegin(GL_QUAD_STRIP)
        for a in range(0, 361, 4):
            r = math.radians(a)
            base = outer_r * outer_mod(a) if outer_side else inner_r * inner_mod(a)
            direction = 1.0 if outer_side else -1.0
            r1 = base
            r2 = base + direction * 1.0
            if (a // 12) % 2 == 0:
                glColor3f(0.88, 0.05, 0.04)
            else:
                glColor3f(0.92, 0.92, 0.86)
            glVertex3f(math.cos(r) * r1, 0.025, math.sin(r) * r1)
            glVertex3f(math.cos(r) * r2, 0.025, math.sin(r) * r2)
        glEnd()

    # Dashed center line.
    glColor3f(0.95, 0.82, 0.25)
    for a in range(0, 360, 14):
        if (a // 14) % 2:
            continue
        a2 = min(a + 8, 360)
        glBegin(GL_QUAD_STRIP)
        for aa in (a, a2):
            r = math.radians(aa)
            mid = (outer_r * outer_mod(aa) + inner_r * inner_mod(aa)) * 0.5
            glVertex3f(math.cos(r) * (mid - 0.22), 0.035, math.sin(r) * (mid - 0.22))
            glVertex3f(math.cos(r) * (mid + 0.22), 0.035, math.sin(r) * (mid + 0.22))
        glEnd()

def _draw_track_decoration(outer_mod, outer_r):
    # Simple low-poly trees and guard posts around the circuit.
    for a in range(0, 360, 24):
        r = math.radians(a)
        radius = outer_r * outer_mod(a) + 8.0
        x = math.cos(r) * radius
        z = math.sin(r) * radius
        glPushMatrix()
        glTranslatef(x, 0, z)
        _gl_box_lit(-0.18, 0.0, -0.18, 0.18, 1.1, 0.18, (0.34, 0.20, 0.09))
        _gl_box_lit(-0.75, 1.0, -0.75, 0.75, 2.1, 0.75, (0.05, 0.35, 0.09))
        glPopMatrix()

    for a in range(0, 360, 18):
        r = math.radians(a)
        radius = outer_r * outer_mod(a) + 2.0
        x = math.cos(r) * radius
        z = math.sin(r) * radius
        glPushMatrix()
        glTranslatef(x, 0, z)
        _gl_box_lit(-0.10, 0.0, -0.10, 0.10, 0.65, 0.10, (0.75, 0.75, 0.68))
        glPopMatrix()

def _gl_face_quad(x1, y1, z1, x2, y2, z2, color):
    # single quad in X/Y plane (z constant = z2)
    r, g, b = color
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex3f(x1, y1, z2); glVertex3f(x2, y1, z2); glVertex3f(x2, y2, z2); glVertex3f(x1, y2, z2)
    glEnd()

def _draw_character_in_car(character, roof_h):
    """
    Draw a simple, recognizable 3D-ish character sitting in the car cabin.
    Assumes model space is already in car coordinates (after translate/rotate).
    """
    if not character or character not in CHARACTER_DEFS:
        return
    d = CHARACTER_DEFS[character]
    main = d["main"]
    accent = d["accent"]

    # Seat / cabin position (visible through roof opening)
    base_y = roof_h - 0.22
    base_y = max(0.18, base_y)
    glPushMatrix()
    glTranslatef(0.0, base_y, 0.05)

    # torso
    _gl_box(-0.16, 0.00, -0.10, 0.16, 0.16, 0.12, main)
    # arms reaching forward
    _gl_box(-0.22, 0.06,  0.04, -0.16, 0.12, 0.15, main)
    _gl_box( 0.16, 0.06,  0.04,  0.22, 0.12, 0.15, main)
    # steering wheel bar (simple)
    _gl_box(-0.18, 0.07, 0.15, 0.18, 0.09, 0.18, accent)

    # head
    head_top = 0.36
    _gl_box(-0.15, 0.16, -0.10, 0.15, head_top, 0.14, main)

    # eyes (front face)
    _gl_face_quad(-0.08, 0.27, -0.01, -0.03, 0.31, 0.141, accent)
    _gl_face_quad( 0.03, 0.27, -0.01,  0.08, 0.31, 0.141, accent)

    # per-character features
    if character in ("Mauz", "Wauz", "Fuchs", "Hase"):
        # ears: different shapes
        if character == "Hase":
            _gl_box(-0.14, head_top, -0.06, -0.06, head_top + 0.24, 0.02, accent)
            _gl_box( 0.06, head_top, -0.06,  0.14, head_top + 0.24, 0.02, accent)
        else:
            _gl_box(-0.16, head_top, -0.06, -0.06, head_top + 0.14, 0.02, accent)
            _gl_box( 0.06, head_top, -0.06,  0.16, head_top + 0.14, 0.02, accent)

        # snout for dog/fox
        if character in ("Wauz", "Fuchs"):
            _gl_box(-0.06, 0.22, 0.14, 0.06, 0.28, 0.20, accent)
        # whiskers for cat
        if character == "Mauz":
            _gl_box(-0.18, 0.24, 0.13, -0.15, 0.25, 0.20, accent)
            _gl_box( 0.15, 0.24, 0.13,  0.18, 0.25, 0.20, accent)

    elif character == "Baer":
        # round-ish ears (small cubes)
        _gl_box(-0.18, head_top - 0.02, -0.06, -0.12, head_top + 0.08, 0.02, accent)
        _gl_box( 0.12, head_top - 0.02, -0.06,  0.18, head_top + 0.08, 0.02, accent)
        # snout
        _gl_box(-0.07, 0.22, 0.14, 0.07, 0.29, 0.20, accent)

    elif character == "Bot":
        # face plate
        _gl_face_quad(-0.12, 0.22, -0.01, 0.12, 0.33, 0.141, accent)
        # antenna
        _gl_box(-0.01, head_top, -0.02, 0.01, head_top + 0.18, 0.00, accent)
        _gl_box(-0.03, head_top + 0.18, -0.04, 0.03, head_top + 0.22, 0.02, main)

    glPopMatrix()
