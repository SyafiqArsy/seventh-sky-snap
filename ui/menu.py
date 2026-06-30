"""
Seventh Sky Snap - UI Menu System
Handles all UI screens: start menu, camera view, puzzle view, and results.
"""

import math
import time

import cv2
import numpy as np
import pygame

import config


class Button:
    """A clickable UI button."""

    def __init__(self, x, y, width, height, text, color=None, hover_color=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color or config.COLOR_BUTTON
        self.hover_color = hover_color or config.COLOR_BUTTON_HOVER
        self.is_hovered = False
        self.font = None
        self._click_time = 0

    def _get_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 22, bold=True)
        return self.font

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._click_time = time.time()
                return True
        return False

    def draw(self, surface):
        font = self._get_font()
        color = self.hover_color if self.is_hovered else self.color

        # Background with rounded corners
        pygame.draw.rect(surface, color, self.rect, border_radius=10)

        # Subtle highlight on hover
        if self.is_hovered:
            highlight = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, 25))
            surface.blit(highlight, self.rect.topleft)

        # Text
        text_surf = font.render(self.text, True, config.COLOR_BUTTON_TEXT)
        text_x = self.rect.centerx - text_surf.get_width() // 2
        text_y = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (text_x, text_y))


class StartScreen:
    """The initial start/welcome screen."""

    def __init__(self):
        self.title_font = None
        self.subtitle_font = None
        self.info_font = None
        self.start_button = Button(
            config.WINDOW_WIDTH // 2 - 120,
            config.WINDOW_HEIGHT // 2 + 60,
            240, 55, "Start Camera",
        )
        self._anim_time = 0

    def _get_fonts(self):
        if self.title_font is None:
            self.title_font = pygame.font.SysFont("arial", 64, bold=True)
            self.subtitle_font = pygame.font.SysFont("arial", 24)
            self.info_font = pygame.font.SysFont("arial", 18)
        return self.title_font, self.subtitle_font, self.info_font

    def handle_event(self, event):
        return self.start_button.handle_event(event)

    def update(self, dt):
        self._anim_time += dt

    def draw(self, surface):
        title_font, subtitle_font, info_font = self._get_fonts()

        # Background gradient
        for y in range(config.WINDOW_HEIGHT):
            t = y / config.WINDOW_HEIGHT
            r = int(config.COLOR_BG[0] * (1 - t) + config.COLOR_BG_GRADIENT[0] * t)
            g = int(config.COLOR_BG[1] * (1 - t) + config.COLOR_BG_GRADIENT[1] * t)
            b = int(config.COLOR_BG[2] * (1 - t) + config.COLOR_BG_GRADIENT[2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (config.WINDOW_WIDTH, y))

        cx = config.WINDOW_WIDTH // 2

        # Floating particles effect
        for i in range(15):
            px = cx + math.sin(self._anim_time * 0.5 + i * 0.8) * (150 + i * 20)
            py = config.WINDOW_HEIGHT // 2 - 80 + math.cos(self._anim_time * 0.3 + i * 1.1) * (50 + i * 10)
            alpha = int(40 + 30 * math.sin(self._anim_time + i))
            size = 2 + int(2 * math.sin(self._anim_time * 0.7 + i))
            dot = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*config.COLOR_ACCENT[:3], alpha), (size, size), size)
            surface.blit(dot, (int(px), int(py)))

        # Title with glow effect
        glow_alpha = int(30 + 20 * math.sin(self._anim_time * 2))
        glow_surf = title_font.render("Seventh Sky Snap", True, config.COLOR_ACCENT)
        glow_surf.set_alpha(glow_alpha)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            surface.blit(glow_surf, (cx - glow_surf.get_width() // 2 + dx, 200 + dy))

        title = title_font.render("Seventh Sky Snap", True, config.COLOR_TEXT)
        surface.blit(title, (cx - title.get_width() // 2, 200))

        # Subtitle
        subtitle = subtitle_font.render(
            "Interactive Photo Experience with Hand Tracking", True, config.COLOR_TEXT_DIM
        )
        surface.blit(subtitle, (cx - subtitle.get_width() // 2, 285))

        # Instructions
        instructions = [
            "Use hand gestures to control the camera frame",
            "Thumbs up to capture a photo",
            "Solve the puzzle with your captured image!",
        ]
        for i, line in enumerate(instructions):
            txt = info_font.render(line, True, config.COLOR_TEXT_DIM)
            surface.blit(txt, (cx - txt.get_width() // 2, 360 + i * 30))

        # Start button
        self.start_button.draw(surface)

        # Version
        ver = info_font.render("v1.0", True, (80, 80, 100))
        surface.blit(ver, (config.WINDOW_WIDTH - 60, config.WINDOW_HEIGHT - 30))


class CameraView:
    """Camera view with frame overlay and hand tracking visualization."""

    def __init__(self):
        self.font = None
        self.small_font = None
        self.frame_size = (config.FRAME_SIZE_MIN + config.FRAME_SIZE_MAX) // 2
        self.frame_x = 0
        self.frame_y = 0
        self._update_frame_rect()

    def _get_fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 20, bold=True)
            self.small_font = pygame.font.SysFont("arial", 16)
        return self.font, self.small_font

    def _update_frame_rect(self):
        """Recalculate frame rectangle based on current size."""
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.frame_x = cx - self.frame_size // 2
        self.frame_y = cy - self.frame_size // 2

    def set_frame_size(self, size):
        self.frame_size = max(config.FRAME_SIZE_MIN, min(config.FRAME_SIZE_MAX, int(size)))
        self._update_frame_rect()

    def get_frame_rect(self):
        return (self.frame_x, self.frame_y, self.frame_size, self.frame_size)

    def draw_frame_overlay(self, surface):
        """Draw the capture frame overlay on the camera view."""
        font, small_font = self._get_fonts()

        # Semi-transparent overlay outside the frame
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)

        # Darken outside the frame
        overlay.fill((0, 0, 0, 100))
        # Cut out the frame area
        pygame.draw.rect(overlay, (0, 0, 0, 0),
                         (self.frame_x, self.frame_y, self.frame_size, self.frame_size))
        surface.blit(overlay, (0, 0))

        # Frame border with animated dash effect
        border_rect = pygame.Rect(self.frame_x, self.frame_y, self.frame_size, self.frame_size)
        pygame.draw.rect(surface, config.COLOR_FRAME_BORDER, border_rect, 3, border_radius=4)

        # Corner accents
        corner_len = 20
        corners = [
            (self.frame_x, self.frame_y, 1, 1),
            (self.frame_x + self.frame_size, self.frame_y, -1, 1),
            (self.frame_x, self.frame_y + self.frame_size, 1, -1),
            (self.frame_x + self.frame_size, self.frame_y + self.frame_size, -1, -1),
        ]
        for cx, cy, dx, dy in corners:
            pygame.draw.line(surface, config.COLOR_ACCENT_LIGHT,
                             (cx, cy), (cx + corner_len * dx, cy), 3)
            pygame.draw.line(surface, config.COLOR_ACCENT_LIGHT,
                             (cx, cy), (cx, cy + corner_len * dy), 3)

        # Frame size label
        size_text = small_font.render(f"Frame: {self.frame_size}px", True, config.COLOR_TEXT_DIM)
        surface.blit(size_text, (self.frame_x, self.frame_y - 25))

    def draw_camera_frame(self, surface, frame_bgr):
        """Convert and draw a BGR camera frame onto the pygame surface.

        Args:
            surface: pygame.Surface to draw on.
            frame_bgr: numpy.ndarray in BGR format from OpenCV.
        """
        if frame_bgr is None:
            return

        # Resize to fit window
        fh, fw = frame_bgr.shape[:2]
        scale = min(config.WINDOW_WIDTH / fw, config.WINDOW_HEIGHT / fh)
        new_w = int(fw * scale)
        new_h = int(fh * scale)
        frame_resized = cv2.resize(frame_bgr, (new_w, new_h))

        # Convert BGR to RGB for pygame
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

        # Create pygame surface
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))

        # Center on screen
        x = (config.WINDOW_WIDTH - new_w) // 2
        y = (config.WINDOW_HEIGHT - new_h) // 2
        surface.blit(frame_surface, (x, y))

    def draw_hand_landmarks(self, surface, landmarks_px):
        """Draw hand landmarks on the surface.

        Args:
            surface: pygame.Surface.
            landmarks_px: list of (int, int) pixel coordinates for 21 landmarks.
        """
        if landmarks_px is None:
            return

        # Draw connections
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),       # Index
            (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
            (0, 13), (13, 14), (14, 15), (15, 16), # Ring
            (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
            (5, 9), (9, 13), (13, 17),             # Palm
        ]
        for (i, j) in connections:
            if i < len(landmarks_px) and j < len(landmarks_px):
                pygame.draw.line(surface, config.COLOR_HAND_CONNECTIONS,
                                 landmarks_px[i], landmarks_px[j], 2)

        # Draw points
        for (px, py) in landmarks_px:
            pygame.draw.circle(surface, config.COLOR_HAND_LANDMARK, (px, py), 5)
            pygame.draw.circle(surface, (255, 255, 255), (px, py), 2)

    def draw_hud(self, surface, state, gesture="none", pieces_solved=0, pieces_total=0):
        """Draw heads-up display information.

        Args:
            surface: pygame.Surface.
            state: Current application state string.
            gesture: Current detected gesture name.
            pieces_solved: Number of solved puzzle pieces.
            pieces_total: Total puzzle pieces.
        """
        font, small_font = self._get_fonts()

        # State indicator (top-left)
        state_labels = {
            config.STATE_CAMERA_READY: "Starting camera...",
            config.STATE_TRACKING: "Hand detected - Adjust frame size",
            config.STATE_RESIZE_MODE: "Resizing frame...",
            config.STATE_CAPTURE_COUNTDOWN: "Capturing...",
            config.STATE_IMAGE_PROCESSING: "Processing image...",
        }
        label = state_labels.get(state, state)
        state_text = font.render(label, True, config.COLOR_TEXT)
        bg_rect = pygame.Rect(15, 10, state_text.get_width() + 20, 30)
        bg_surf = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 120))
        surface.blit(bg_surf, bg_rect.topleft)
        surface.blit(state_text, (25, 15))

        # Instructions (top-right)
        instructions = {
            config.STATE_TRACKING: "Pinch to resize | Thumbs up to capture",
            config.STATE_RESIZE_MODE: "Open/close fingers to adjust frame",
        }
        instr = instructions.get(state, "")
        if instr:
            instr_text = small_font.render(instr, True, config.COLOR_TEXT_DIM)
            surface.blit(instr_text, (config.WINDOW_WIDTH - instr_text.get_width() - 20, 15))

        # Puzzle progress (if in puzzle mode)
        if pieces_total > 0:
            prog_text = font.render(f"Puzzle: {pieces_solved}/{pieces_total}", True, config.COLOR_ACCENT_LIGHT)
            surface.blit(prog_text, (config.WINDOW_WIDTH - prog_text.get_width() - 20, config.WINDOW_HEIGHT - 40))


class PuzzleView:
    """UI overlay for puzzle mode instructions and info."""

    def __init__(self):
        self.font = None
        self.small_font = None

    def _get_fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 24, bold=True)
            self.small_font = pygame.font.SysFont("arial", 18)
        return self.font, self.small_font

    def draw(self, surface, solved_count, total_count):
        font, small_font = self._get_fonts()

        # Header
        header = font.render("Puzzle Mode", True, config.COLOR_ACCENT_LIGHT)
        surface.blit(header, (config.WINDOW_WIDTH // 2 - header.get_width() // 2, 8))

        # Progress bar
        if total_count > 0:
            progress = solved_count / total_count
            bar_w = 200
            bar_h = 6
            bar_x = config.WINDOW_WIDTH // 2 - bar_w // 2
            bar_y = 42
            pygame.draw.rect(surface, (40, 40, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            if progress > 0:
                fill_w = int(bar_w * progress)
                pygame.draw.rect(surface, config.COLOR_SUCCESS, (bar_x, bar_y, fill_w, bar_h), border_radius=3)


class ResultScreen:
    """Displays the completed polaroid and action buttons."""

    def __init__(self):
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.new_session_btn = Button(
            config.WINDOW_WIDTH // 2 - 130, config.WINDOW_HEIGHT - 100,
            120, 45, "New Session",
        )
        self.menu_btn = Button(
            config.WINDOW_WIDTH // 2 + 10, config.WINDOW_HEIGHT - 100,
            120, 45, "Main Menu",
        )
        self._anim_time = 0

    def _get_fonts(self):
        if self.font_large is None:
            self.font_large = pygame.font.SysFont("arial", 48, bold=True)
            self.font_medium = pygame.font.SysFont("arial", 28)
            self.font_small = pygame.font.SysFont("arial", 18)
        return self.font_large, self.font_medium, self.font_small

    def handle_event(self, event):
        if self.new_session_btn.handle_event(event):
            return "new_session"
        if self.menu_btn.handle_event(event):
            return "menu"
        return None

    def update(self, dt):
        self._anim_time += dt

    def draw(self, surface, polaroid_surface=None, save_path=None):
        font_large, font_medium, font_small = self._get_fonts()

        # Background
        for y in range(config.WINDOW_HEIGHT):
            t = y / config.WINDOW_HEIGHT
            r = int(config.COLOR_BG[0] * (1 - t) + config.COLOR_BG_GRADIENT[0] * t)
            g = int(config.COLOR_BG[1] * (1 - t) + config.COLOR_BG_GRADIENT[1] * t)
            b = int(config.COLOR_BG[2] * (1 - t) + config.COLOR_BG_GRADIENT[2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (config.WINDOW_WIDTH, y))

        cx = config.WINDOW_WIDTH // 2

        # Title
        title = font_large.render("Puzzle Complete!", True, config.COLOR_SUCCESS)
        title_y = 30 + math.sin(self._anim_time * 2) * 3
        surface.blit(title, (cx - title.get_width() // 2, int(title_y)))

        # Polaroid display
        if polaroid_surface:
            pw, ph = polaroid_surface.get_size()
            scale = min(500 / pw, 400 / ph)
            display_w = int(pw * scale)
            display_h = int(ph * scale)
            display = pygame.transform.smoothscale(polaroid_surface, (display_w, display_h))

            # Shadow
            shadow = pygame.Surface((display_w + 10, display_h + 10), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 40))
            surface.blit(shadow, (cx - display_w // 2 - 5, 105))

            # Subtle floating animation
            float_y = int(math.sin(self._anim_time * 1.5) * 4)
            surface.blit(display, (cx - display_w // 2, 100 + float_y))

        # Save info
        if save_path:
            save_text = font_small.render(f"Saved to: {save_path}", True, config.COLOR_TEXT_DIM)
            surface.blit(save_text, (cx - save_text.get_width() // 2, config.WINDOW_HEIGHT - 140))

        # Buttons
        self.new_session_btn.draw(surface)
        self.menu_btn.draw(surface)
