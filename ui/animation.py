"""
Seventh Sky Snap - UI Animations
Handles visual animations, transitions, and particle effects.
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


class Particle:
    """A single particle for confetti and effects."""

    def __init__(self, x, y, color, velocity_x, velocity_y, lifetime, size=4):
        self.x = x
        self.y = y
        self.color = color
        self.vx = velocity_x
        self.vy = velocity_y
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.alive = True
        self.gravity = 200
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-300, 300)

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
        alpha = max(0, int(255 * (self.lifetime / self.max_lifetime)))
        s = max(1, int(self.size * (self.lifetime / self.max_lifetime)))

        # Draw as a small rotated rectangle
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
            self.particles.append(Particle(
                x=x + random.uniform(-20, 20),
                y=y + random.uniform(-20, 20),
                color=color,
                velocity_x=math.cos(angle) * speed,
                velocity_y=math.sin(angle) * speed - 200,
                lifetime=random.uniform(1.5, 3.0),
                size=random.randint(3, 7),
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
    """Visual countdown display (3, 2, 1) with scaling effect."""

    def __init__(self):
        self.number = 0
        self.progress = 0.0  # 0 to 1 within each number
        self.font_large = None
        self.font_small = None

    def _get_fonts(self):
        if self.font_large is None:
            self.font_large = pygame.font.SysFont("arial", 120, bold=True)
            self.font_small = pygame.font.SysFont("arial", 40)
        return self.font_large, self.font_small

    def update(self, number, progress):
        self.number = number
        self.progress = progress

    def draw(self, surface):
        if self.number <= 0:
            return

        font_large, font_small = self._get_fonts()
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2

        # Scale animation: starts big, shrinks to normal
        scale = 1.0 + 0.5 * (1.0 - self.progress)
        alpha = int(255 * (0.5 + 0.5 * self.progress))

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

        # "Get ready!" text
        if self.number > 0:
            ready = font_small.render("Get ready!", True, config.COLOR_TEXT_DIM)
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

        # Gesture name mapping
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

        # Draw in bottom-left area
        x = 20
        y = config.WINDOW_HEIGHT - 50

        # Background pill
        bg_rect = pygame.Rect(x - 8, y - 4, text.get_width() + 16, text.get_height() + 8)
        bg_surf = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, int(self.alpha * 0.5)))
        surface.blit(bg_surf, bg_rect.topleft)

        surface.blit(text, (x, y))
