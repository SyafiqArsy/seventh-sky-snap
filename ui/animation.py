"""
Seventh Sky Snap - UI Animations
Handles visual animations, transitions, and particle effects.
Enhanced with smooth easing, glow effects, shatter animation, and ambient particles.
"""

import random
import math

import pygame

import config


class Easing:
    """Easing functions for smooth animations."""

    @staticmethod
    def ease_out_cubic(t):
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_out_bounce(t):
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375

    @staticmethod
    def ease_in_out_sine(t):
        return -(math.cos(math.pi * t) - 1) / 2

    @staticmethod
    def ease_out_elastic(t):
        if t == 0 or t == 1:
            return t
        return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

    @staticmethod
    def ease_out_back(t):
        """Overshoot easing — goes past target then settles."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

    @staticmethod
    def ease_in_out_cubic(t):
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - (-2 * t + 2) ** 3 / 2

    @staticmethod
    def ease_out_quart(t):
        return 1 - (1 - t) ** 4


class Particle:
    """A single particle for confetti and effects."""

    def __init__(self, x, y, color, velocity_x, velocity_y, lifetime, size=4,
                 gravity=200, shape="rect"):
        self.x = x
        self.y = y
        self.color = color
        self.vx = velocity_x
        self.vy = velocity_y
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.alive = True
        self.gravity = gravity
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-300, 300)
        self.shape = shape  # "rect", "circle", "star"

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.lifetime -= dt
        self.rotation += self.rotation_speed * dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        life_ratio = max(0, self.lifetime / self.max_lifetime)
        alpha = max(0, int(255 * life_ratio))
        s = max(1, int(self.size * life_ratio))

        if self.shape == "circle":
            dot = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*self.color[:3], alpha), (s, s), s)
            surface.blit(dot, (int(self.x - s), int(self.y - s)))
        elif self.shape == "star":
            star_surf = pygame.Surface((s * 4, s * 4), pygame.SRCALPHA)
            points = []
            cx, cy = s * 2, s * 2
            for i in range(5):
                angle = math.radians(self.rotation + i * 72 - 90)
                points.append((cx + math.cos(angle) * s * 1.5,
                               cy + math.sin(angle) * s * 1.5))
                inner_angle = math.radians(self.rotation + i * 72 + 36 - 90)
                points.append((cx + math.cos(inner_angle) * s * 0.6,
                               cy + math.sin(inner_angle) * s * 0.6))
            if len(points) >= 3:
                pygame.draw.polygon(star_surf, (*self.color[:3], alpha), points)
            surface.blit(star_surf, (int(self.x - s * 2), int(self.y - s * 2)))
        else:
            particle_surf = pygame.Surface((s * 2, s), pygame.SRCALPHA)
            particle_surf.fill((*self.color[:3], alpha))
            rotated = pygame.transform.rotate(particle_surf, self.rotation)
            surface.blit(rotated, (int(self.x - rotated.get_width() // 2),
                                    int(self.y - rotated.get_height() // 2)))


class ParticleSystem:
    """Manages a collection of particles."""

    def __init__(self):
        self.particles = []

    def emit_confetti(self, x, y, count=50):
        """Emit confetti particles at a position."""
        colors = [
            (255, 100, 100), (100, 255, 100), (100, 100, 255),
            (255, 255, 100), (255, 100, 255), (100, 255, 255),
            config.COLOR_ACCENT, config.COLOR_ACCENT_LIGHT,
        ]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 400)
            color = random.choice(colors)
            shape = random.choice(["rect", "circle", "star"])
            self.particles.append(Particle(
                x=x + random.uniform(-20, 20),
                y=y + random.uniform(-20, 20),
                color=color,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed - 200,
                lifetime=random.uniform(1.5, 3.0),
                size=random.randint(3, 7),
                shape=shape,
            ))

    def emit_sparkle(self, x, y, count=15):
        """Emit sparkle particles at a position."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 120)
            self.particles.append(Particle(
                x=x, y=y,
                color=(255, 255, 200),
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.3, 0.8),
                size=random.randint(2, 4),
                shape="circle",
            ))

    def emit_puzzle_snap(self, x, y, count=10):
        """Emit a small burst when a puzzle piece snaps into place."""
        colors = [config.COLOR_SUCCESS, (100, 255, 180), (200, 255, 220)]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 150)
            color = random.choice(colors)
            self.particles.append(Particle(
                x=x, y=y,
                color=color,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed,
                lifetime=random.uniform(0.3, 0.6),
                size=random.randint(2, 4),
                gravity=50,
                shape="circle",
            ))

    def emit_save_sparkle(self, x, y, count=30):
        """Emit golden sparkles for the save moment."""
        colors = [(255, 215, 0), (255, 235, 100), (255, 255, 200), (255, 200, 50)]
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            color = random.choice(colors)
            self.particles.append(Particle(
                x=x + random.uniform(-30, 30),
                y=y + random.uniform(-30, 30),
                color=color,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed - 100,
                lifetime=random.uniform(0.8, 1.5),
                size=random.randint(2, 5),
                gravity=100,
                shape="star",
            ))

    def emit_ambient(self, count=1):
        """Emit subtle ambient floating particles."""
        for _ in range(count):
            x = random.uniform(0, config.WINDOW_WIDTH)
            y = random.uniform(0, config.WINDOW_HEIGHT)
            self.particles.append(Particle(
                x=x, y=y,
                color=config.COLOR_ACCENT_LIGHT,
                velocity_x=random.uniform(-10, 10),
                velocity_y=random.uniform(-20, -5),
                lifetime=random.uniform(3.0, 6.0),
                size=random.randint(1, 3),
                gravity=-5,  # Float upward
                shape="circle",
            ))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    @property
    def active(self):
        return len(self.particles) > 0


class Transition:
    """Fade transition between screens."""

    def __init__(self):
        self.alpha = 0
        self.target_alpha = 0
        self.speed = 400  # alpha units per second
        self.color = (0, 0, 0)
        self.surface = None
        self._on_complete = None
        self._phase = "none"  # "fade_out", "fade_in", "none"

    def fade_out(self, color=(0, 0, 0), speed=400, on_complete=None):
        """Start fading to black."""
        self.color = color
        self.speed = speed
        self.target_alpha = 255
        self._phase = "fade_out"
        self._on_complete = on_complete
        if self.surface is None:
            self.surface = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.surface.fill(color)

    def fade_in(self, speed=400, on_complete=None):
        """Start fading from black."""
        self.speed = speed
        self.target_alpha = 0
        self._phase = "fade_in"
        self._on_complete = on_complete
        if self.surface is None:
            self.surface = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        self.surface.fill(self.color)

    def update(self, dt):
        if self._phase == "fade_out":
            self.alpha = min(255, self.alpha + self.speed * dt)
            if self.alpha >= 255:
                self._phase = "none"
                if self._on_complete:
                    cb = self._on_complete
                    self._on_complete = None
                    cb()
        elif self._phase == "fade_in":
            self.alpha = max(0, self.alpha - self.speed * dt)
            if self.alpha <= 0:
                self._phase = "none"
                if self._on_complete:
                    cb = self._on_complete
                    self._on_complete = None
                    cb()

    def draw(self, surface):
        if self.alpha > 0 and self.surface:
            self.surface.set_alpha(int(self.alpha))
            surface.blit(self.surface, (0, 0))

    @property
    def is_active(self):
        return self._phase != "none"


class CountdownAnimation:
    """Visual countdown display (3, 2, 1) with scaling and pulse ring effect."""

    def __init__(self):
        self.number = 0
        self.progress = 0.0  # 0 to 1 within each number
        self.font_large = None
        self.font_small = None
        self._pulse_rings = []  # Expanding rings

    def _get_fonts(self):
        if self.font_large is None:
            self.font_large = pygame.font.SysFont("arial", 120, bold=True)
            self.font_small = pygame.font.SysFont("arial", 40)
        return self.font_large, self.font_small

    def update(self, number, progress):
        if number != self.number and number > 0:
            # New number — spawn pulse ring
            self._pulse_rings.append({
                "radius": 40, "alpha": 150, "speed": 200,
            })
        self.number = number
        self.progress = progress

        # Update pulse rings
        dt = 1.0 / config.FPS
        for ring in self._pulse_rings:
            ring["radius"] += ring["speed"] * dt
            ring["alpha"] = max(0, ring["alpha"] - 300 * dt)
        self._pulse_rings = [r for r in self._pulse_rings if r["alpha"] > 0]

    def draw(self, surface):
        if self.number <= 0:
            return

        font_large, font_small = self._get_fonts()
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2

        # Draw pulse rings
        for ring in self._pulse_rings:
            r = int(ring["radius"])
            a = int(ring["alpha"])
            if r > 0 and a > 0:
                ring_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (*config.COLOR_ACCENT[:3], a),
                                   (r, r), r, 2)
                surface.blit(ring_surf, (cx - r, cy - r))

        # Scale animation: elastic easing
        t = self.progress
        scale = 1.0 + 0.4 * Easing.ease_out_elastic(1.0 - t)
        alpha = int(255 * (0.5 + 0.5 * t))

        # Render number
        text = str(self.number)
        text_surf = font_large.render(text, True, config.COLOR_COUNTDOWN)

        # Scale it
        orig_w, orig_h = text_surf.get_size()
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        scaled = pygame.transform.smoothscale(text_surf, (new_w, new_h))
        scaled.set_alpha(alpha)

        # Center
        surface.blit(scaled, (cx - new_w // 2, cy - new_h // 2))

        # Ring effect
        ring_radius = int(80 * (1 + (1 - self.progress) * 0.5))
        ring_alpha = int(100 * (1 - self.progress))
        ring_surf = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*config.COLOR_ACCENT[:3], ring_alpha),
                           (ring_radius, ring_radius), ring_radius, 3)
        surface.blit(ring_surf, (cx - ring_radius, cy - ring_radius))

        # "Get ready!" text with fade
        if self.number > 0:
            ready = font_small.render("Get ready!", True, config.COLOR_TEXT_DIM)
            ready.set_alpha(int(180 * (0.5 + 0.5 * math.sin(self.progress * math.pi))))
            surface.blit(ready, (cx - ready.get_width() // 2, cy + 80))


class GestureIndicator:
    """Shows current detected gesture as a visual indicator."""

    def __init__(self):
        self.gesture = config.GESTURE_NONE
        self.alpha = 0
        self.font = None

    def _get_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 20, bold=True)
        return self.font

    def update(self, gesture, dt):
        if gesture != config.GESTURE_NONE:
            self.gesture = gesture
            self.alpha = min(255, self.alpha + 600 * dt)
        else:
            self.alpha = max(0, self.alpha - 400 * dt)

    def draw(self, surface):
        if self.alpha <= 0:
            return

        font = self._get_font()

        names = {
            config.GESTURE_OPEN_HAND: "Open Hand",
            config.GESTURE_PINCH: "Pinch",
            config.GESTURE_THUMBS_UP: "Thumbs Up",
            config.GESTURE_POINT: "Pointing",
            config.GESTURE_FIST: "Fist",
            config.GESTURE_VICTORY: "Victory",
        }
        name = names.get(self.gesture, "")
        if not name:
            return

        colors = {
            config.GESTURE_OPEN_HAND: config.COLOR_HAND_LANDMARK,
            config.GESTURE_PINCH: config.COLOR_WARNING,
            config.GESTURE_THUMBS_UP: config.COLOR_SUCCESS,
            config.GESTURE_POINT: config.COLOR_ACCENT,
            config.GESTURE_FIST: config.COLOR_ERROR,
            config.GESTURE_VICTORY: config.COLOR_ACCENT_LIGHT,
        }
        color = colors.get(self.gesture, config.COLOR_TEXT)

        text = font.render(name, True, color)
        text.set_alpha(int(self.alpha))

        x = 20
        y = config.WINDOW_HEIGHT - 50

        # Background pill with rounded corners
        bg_rect = pygame.Rect(x - 8, y - 4, text.get_width() + 16, text.get_height() + 8)
        bg_surf = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, int(self.alpha * 0.5)),
                         (0, 0, bg_rect.w, bg_rect.h), border_radius=8)
        surface.blit(bg_surf, bg_rect.topleft)

        surface.blit(text, (x, y))


class ShutterFlash:
    """Camera shutter flash effect — white overlay that fades out quickly."""

    def __init__(self):
        self.alpha = 0
        self.active = False
        self._duration = 0.3  # seconds
        self._elapsed = 0.0

    def trigger(self):
        """Start the flash effect."""
        self.active = True
        self.alpha = 220
        self._elapsed = 0.0

    def update(self, dt):
        """Update flash fade-out."""
        if not self.active:
            return
        self._elapsed += dt
        t = min(1.0, self._elapsed / self._duration)
        self.alpha = int(220 * (1.0 - Easing.ease_out_cubic(t)))
        if t >= 1.0:
            self.active = False
            self.alpha = 0

    def draw(self, surface):
        """Draw the white flash overlay with radial gradient."""
        if not self.active or self.alpha <= 0:
            return
        flash_surf = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        # Radial gradient: brighter in center, fading at edges
        cx, cy = config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT // 2
        max_r = int(math.sqrt(cx * cx + cy * cy))
        for r in range(max_r, 0, max_r // 8):
            t = r / max_r
            a = int(self.alpha * (1.0 - t * 0.6))
            pygame.draw.circle(flash_surf, (255, 255, 255, a), (cx, cy), r)
        surface.blit(flash_surf, (0, 0))

    @property
    def is_active(self):
        return self.active


class PolaroidReveal:
    """Animation for polaroid sliding up from the bottom with smooth easing."""

    def __init__(self):
        self.active = False
        self.progress = 0.0
        self._duration = 1.0  # Slightly longer for smoother feel
        self._elapsed = 0.0
        self.polaroid_surface = None
        self.target_y = 0
        self.start_y = 0
        self.display_surf = None
        self.display_w = 0
        self.display_h = 0
        # Wobble effect
        self._wobble_angle = 0.0
        self._wobble_speed = 0.0

    def start(self, polaroid_surface):
        """Begin the polaroid reveal animation."""
        self.active = True
        self.progress = 0.0
        self._elapsed = 0.0
        self.polaroid_surface = polaroid_surface
        self._wobble_angle = random.uniform(-5, 5)
        self._wobble_speed = random.uniform(2, 4)

        if polaroid_surface:
            pw, ph = polaroid_surface.get_size()
            scale = min(500 / pw, 450 / ph)
            self.display_w = int(pw * scale)
            self.display_h = int(ph * scale)
            self.display_surf = pygame.transform.smoothscale(
                polaroid_surface, (self.display_w, self.display_h)
            )
            self.target_y = (config.WINDOW_HEIGHT - self.display_h) // 2
            self.start_y = config.WINDOW_HEIGHT + 50

    def update(self, dt):
        """Update the slide-up animation with back easing."""
        if not self.active:
            return
        self._elapsed += dt
        t = min(1.0, self._elapsed / self._duration)
        # Use ease_out_back for slight overshoot
        self.progress = Easing.ease_out_back(t)
        # Wobble decays over time
        self._wobble_angle *= 0.96

    def draw(self, surface):
        """Draw the polaroid at its current animated position."""
        if not self.active or self.polaroid_surface is None:
            return

        # Interpolate Y position (clamp progress for position)
        pos_t = max(0, min(1.2, self.progress))
        current_y = int(self.start_y + (self.target_y - self.start_y) * min(1.0, pos_t))
        cx = config.WINDOW_WIDTH // 2

        # Glow effect behind polaroid (appears as it rises)
        if self.progress > 0.2:
            glow_alpha = int(30 * min(1.0, (self.progress - 0.2) / 0.5))
            glow_r = int(max(self.display_w, self.display_h) * 0.6)
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            for gr in range(glow_r, 0, -4):
                ga = int(glow_alpha * (gr / glow_r))
                pygame.draw.circle(glow_surf, (*config.COLOR_ACCENT[:3], ga),
                                   (glow_r, glow_r), gr)
            surface.blit(glow_surf, (cx - glow_r, current_y + self.display_h // 2 - glow_r))

        # Shadow (appears as polaroid rises)
        if self.progress > 0.2:
            shadow_alpha = int(40 * min(1.0, (self.progress - 0.2) / 0.5))
            shadow = pygame.Surface((self.display_w + 10, self.display_h + 10), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, shadow_alpha))
            surface.blit(shadow, (cx - self.display_w // 2 - 5, current_y + 5))

        # Apply wobble rotation
        wobble = self._wobble_angle * (1.0 - min(1.0, self._elapsed / self._duration))
        if abs(wobble) > 0.3:
            rotated = pygame.transform.rotate(self.display_surf, wobble)
            rw, rh = rotated.get_size()
            surface.blit(rotated, (cx - rw // 2, current_y - (rh - self.display_h) // 2))
        else:
            surface.blit(self.display_surf, (cx - self.display_w // 2, current_y))

    @property
    def is_complete(self):
        return self.active and self._elapsed >= self._duration

    def stop(self):
        self.active = False


class PuzzleBorderFade:
    """Animation for fading puzzle piece borders when puzzle is solved."""

    def __init__(self):
        self.active = False
        self.alpha = 255
        self._duration = 1.0
        self._elapsed = 0.0

    def start(self):
        self.active = True
        self.alpha = 255
        self._elapsed = 0.0

    def update(self, dt):
        if not self.active:
            return
        self._elapsed += dt
        t = min(1.0, self._elapsed / self._duration)
        self.alpha = int(255 * (1.0 - Easing.ease_out_cubic(t)))
        if t >= 1.0:
            self.active = False
            self.alpha = 0

    @property
    def is_complete(self):
        return self.active and self.alpha <= 0

    def get_border_alpha(self):
        return max(0, self.alpha)


class GlowRing:
    """Expanding ring effect that fades as it grows."""

    def __init__(self, x, y, color=None, max_radius=None, duration=None):
        self.x = x
        self.y = y
        self.color = color or config.COLOR_ACCENT
        self.max_radius = max_radius or config.GLOW_RING_MAX_RADIUS
        self.duration = duration or config.GLOW_RING_DURATION
        self.active = True
        self._elapsed = 0.0

    def update(self, dt):
        if not self.active:
            return
        self._elapsed += dt
        if self._elapsed >= self.duration:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        t = self._elapsed / self.duration
        radius = int(self.max_radius * Easing.ease_out_cubic(t))
        alpha = int(120 * (1.0 - t))
        if radius > 0 and alpha > 0:
            ring_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*self.color[:3], alpha),
                               (radius, radius), radius, 2)
            surface.blit(ring_surf, (int(self.x - radius), int(self.y - radius)))


class PolaroidShatter:
    """Shatter animation — polaroid breaks into fragments that fly outward."""

    def __init__(self):
        self.active = False
        self.fragments = []
        self._elapsed = 0.0
        self._duration = config.SHATTER_DURATION

    def start(self, polaroid_surface, cx, cy):
        """Start shatter animation from a polaroid surface at position."""
        self.active = True
        self._elapsed = 0.0
        self.fragments = []

        if polaroid_surface is None:
            return

        pw, ph = polaroid_surface.get_size()
        # Scale to display size
        fit_scale = min(500 / pw, 450 / ph)
        dw = int(pw * fit_scale)
        dh = int(ph * fit_scale)
        display = pygame.transform.smoothscale(polaroid_surface, (dw, dh))

        # Cut into grid fragments
        cols = 4
        rows = 4
        frag_w = dw // cols
        frag_h = dh // rows

        for r in range(rows):
            for c in range(cols):
                # Extract fragment
                fx = c * frag_w
                fy = r * frag_h
                fw = frag_w if c < cols - 1 else dw - fx
                fh = frag_h if r < rows - 1 else dh - fy

                if fw <= 0 or fh <= 0:
                    continue

                frag_surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                frag_surf.blit(display, (0, 0), (fx, fy, fw, fh))

                # Fragment center relative to polaroid center
                frag_cx = cx - dw // 2 + fx + fw // 2
                frag_cy = cy - dh // 2 + fy + fh // 2

                # Velocity: outward from center
                dx = frag_cx - cx
                dy = frag_cy - cy
                dist = max(1, math.sqrt(dx * dx + dy * dy))
                speed = random.uniform(config.SHATTER_SPEED_MIN, config.SHATTER_SPEED_MAX)

                self.fragments.append({
                    "surf": frag_surf,
                    "x": float(frag_cx),
                    "y": float(frag_cy),
                    "vx": (dx / dist) * speed + random.uniform(-50, 50),
                    "vy": (dy / dist) * speed + random.uniform(-100, -30),
                    "rotation": random.uniform(-20, 20),
                    "rot_speed": random.uniform(-config.SHATTER_ROTATION_SPEED,
                                                 config.SHATTER_ROTATION_SPEED),
                    "alpha": 255,
                    "w": fw,
                    "h": fh,
                })

    def update(self, dt):
        if not self.active:
            return
        self._elapsed += dt
        t = min(1.0, self._elapsed / self._duration)

        for f in self.fragments:
            f["x"] += f["vx"] * dt
            f["y"] += f["vy"] * dt
            f["vy"] += config.SHATTER_GRAVITY * dt
            f["rotation"] += f["rot_speed"] * dt
            f["vx"] *= 0.99  # Air resistance
            f["alpha"] = max(0, int(255 * (1.0 - Easing.ease_in_out_cubic(t))))

        if t >= 1.0:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        for f in self.fragments:
            if f["alpha"] <= 0:
                continue
            # Apply rotation
            rotated = pygame.transform.rotate(f["surf"], f["rotation"])
            rotated.set_alpha(f["alpha"])
            rw, rh = rotated.get_size()
            surface.blit(rotated, (int(f["x"] - rw // 2), int(f["y"] - rh // 2)))


class SaveToast:
    """Animated toast notification that slides up from the bottom."""

    def __init__(self):
        self.active = False
        self._elapsed = 0.0
        self._duration = config.SAVE_TOAST_DURATION
        self._slide_progress = 0.0
        self._font = None
        self._font_small = None
        self._save_path = ""

    def _get_fonts(self):
        if self._font is None:
            self._font = pygame.font.SysFont("arial", 28, bold=True)
            self._font_small = pygame.font.SysFont("arial", 16)
        return self._font, self._font_small

    def start(self, save_path=""):
        self.active = True
        self._elapsed = 0.0
        self._save_path = save_path

    def update(self, dt):
        if not self.active:
            return
        self._elapsed += dt
        # Slide in during first 0.3s, hold, slide out during last 0.3s
        if self._elapsed < 0.3:
            self._slide_progress = Easing.ease_out_cubic(self._elapsed / 0.3)
        elif self._elapsed > self._duration - 0.3:
            t = (self._elapsed - (self._duration - 0.3)) / 0.3
            self._slide_progress = 1.0 - Easing.ease_in_out_cubic(min(1.0, t))
        else:
            self._slide_progress = 1.0

        if self._elapsed >= self._duration:
            self.active = False

    def draw(self, surface):
        if not self.active or self._slide_progress <= 0:
            return

        font, font_small = self._get_fonts()

        # Toast content
        checkmark = "✓"
        main_text = "Photo Saved!"
        sub_text = self._save_path if self._save_path else ""

        main_surf = font.render(main_text, True, config.COLOR_SUCCESS)
        check_surf = font.render(checkmark, True, (255, 255, 255))

        # Toast dimensions
        pad_x, pad_y = 24, 14
        toast_w = check_surf.get_width() + 12 + main_surf.get_width() + pad_x * 2
        toast_h = main_surf.get_height() + pad_y * 2

        if sub_text:
            sub_surf = font_small.render(sub_text, True, config.COLOR_TEXT_DIM)
            toast_h += sub_surf.get_height() + 4
            toast_w = max(toast_w, sub_surf.get_width() + pad_x * 2)

        # Position: slides up from bottom
        toast_x = config.WINDOW_WIDTH // 2 - toast_w // 2
        target_y = config.WINDOW_HEIGHT - 80
        start_y = config.WINDOW_HEIGHT + 20
        toast_y = int(start_y + (target_y - start_y) * self._slide_progress)

        # Background with rounded corners and gradient
        bg_surf = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
        # Dark background with subtle gradient
        for row in range(toast_h):
            t = row / toast_h
            r = int(20 + 10 * t)
            g = int(20 + 10 * t)
            b = int(30 + 15 * t)
            a = int(220 * self._slide_progress)
            pygame.draw.line(bg_surf, (r, g, b, a), (0, row), (toast_w, row))
        # Rounded corners
        pygame.draw.rect(bg_surf, (0, 0, 0, 0), (0, 0, toast_w, toast_h), border_radius=12)
        # Border glow
        border_alpha = int(80 * self._slide_progress)
        pygame.draw.rect(bg_surf, (*config.COLOR_SUCCESS[:3], border_alpha),
                         (0, 0, toast_w, toast_h), 1, border_radius=12)

        surface.blit(bg_surf, (toast_x, toast_y))

        # Checkmark with green circle
        cx_check = toast_x + pad_x + check_surf.get_width() // 2
        cy_check = toast_y + pad_y + check_surf.get_height() // 2
        circle_surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(circle_surf, (*config.COLOR_SUCCESS[:3], int(200 * self._slide_progress)),
                           (16, 16), 14)
        surface.blit(circle_surf, (cx_check - 16, cy_check - 16))
        surface.blit(check_surf, (toast_x + pad_x, toast_y + pad_y))

        # Main text
        surface.blit(main_surf, (toast_x + pad_x + check_surf.get_width() + 12,
                                  toast_y + pad_y))

        # Sub text (path)
        if sub_text:
            sub_surf = font_small.render(sub_text, True, config.COLOR_TEXT_DIM)
            sub_surf.set_alpha(int(150 * self._slide_progress))
            surface.blit(sub_surf, (toast_x + pad_x,
                                     toast_y + pad_y + main_surf.get_height() + 4))


class VignetteOverlay:
    """Subtle dark vignette effect around screen edges."""

    def __init__(self):
        self._surface = None
        self._alpha = 40  # Subtle by default

    def _ensure_surface(self):
        if self._surface is None:
            w, h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
            self._surface = pygame.Surface((w, h), pygame.SRCALPHA)
            cx, cy = w // 2, h // 2
            max_r = int(math.sqrt(cx * cx + cy * cy))
            for r in range(max_r, 0, -2):
                t = r / max_r
                # Vignette: darker at edges, transparent in center
                a = int(self._alpha * max(0, (t - 0.4) / 0.6) ** 1.5)
                if a > 0:
                    pygame.draw.circle(self._surface, (0, 0, 0, a), (cx, cy), r)

    def draw(self, surface):
        self._ensure_surface()
        surface.blit(self._surface, (0, 0))


class AmbientParticles:
    """Subtle floating particles for idle/background ambiance."""

    def __init__(self):
        self._particles = []
        self._spawn_timer = 0.0

    def update(self, dt):
        # Spawn new particles periodically
        self._spawn_timer += dt
        if self._spawn_timer > 0.5 and len(self._particles) < config.AMBIENT_PARTICLE_COUNT:
            self._spawn_timer = 0.0
            self._particles.append({
                "x": random.uniform(0, config.WINDOW_WIDTH),
                "y": config.WINDOW_HEIGHT + 10,
                "vx": random.uniform(-config.AMBIENT_PARTICLE_SPEED,
                                       config.AMBIENT_PARTICLE_SPEED),
                "vy": random.uniform(-40, -15),
                "size": random.uniform(1.5, 3.0),
                "alpha": random.uniform(0.2, 0.5),
                "phase": random.uniform(0, math.pi * 2),
            })

        # Update existing
        for p in self._particles:
            p["x"] += p["vx"] * dt + math.sin(p["phase"] + self._spawn_timer * 2) * 0.3
            p["y"] += p["vy"] * dt
            p["alpha"] *= 0.998  # Slowly fade

        # Remove dead particles
        self._particles = [p for p in self._particles
                           if p["y"] > -20 and p["alpha"] > 0.05]

    def draw(self, surface):
        for p in self._particles:
            a = int(p["alpha"] * 255)
            if a <= 0:
                continue
            s = int(p["size"])
            dot = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*config.COLOR_ACCENT_LIGHT[:3], a), (s, s), s)
            surface.blit(dot, (int(p["x"] - s), int(p["y"] - s)))
