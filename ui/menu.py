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


class StatusBar:
    """Dynamic status bar at the top center of the screen."""

    def __init__(self):
        self.font = None
        self.text = ""
        self.alpha = 0
        self._target_alpha = 0

    def _get_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 18, bold=True)
        return self.font

    def update(self, state, dt, countdown_number=0):
        """Update status text based on current state.

        Args:
            state: Current application state string.
            dt: Delta time in seconds.
            countdown_number: Current countdown number (for countdown state).
        """
        msg = config.STATUS_MESSAGES.get(state, "")
        if state == config.STATE_CAPTURE_COUNTDOWN and countdown_number > 0:
            msg = f"Hold Gesture — Capture in {countdown_number}"
        self.text = msg
        self._target_alpha = 255 if msg else 0
        # Smooth alpha transition
        if self.alpha < self._target_alpha:
            self.alpha = min(self._target_alpha, self.alpha + 600 * dt)
        elif self.alpha > self._target_alpha:
            self.alpha = max(self._target_alpha, self.alpha - 400 * dt)

    def draw(self, surface):
        """Draw the status bar on the surface."""
        if self.alpha <= 0 or not self.text:
            return

        font = self._get_font()
        text_surf = font.render(self.text, True, config.COLOR_STATUS_ACTIVE)
        text_surf.set_alpha(int(self.alpha))

        # Center horizontally, near top
        cx = config.WINDOW_WIDTH // 2
        tx = cx - text_surf.get_width() // 2
        ty = 12

        # Background pill
        pad_x, pad_y = 16, 6
        bg_rect = pygame.Rect(tx - pad_x, ty - pad_y,
                              text_surf.get_width() + pad_x * 2,
                              text_surf.get_height() + pad_y * 2)
        bg_surf = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, int(self.alpha * 0.5)))
        surface.blit(bg_surf, bg_rect.topleft)
        surface.blit(text_surf, (tx, ty))


class InfoPanel:
    """Lightweight info display at bottom corners."""

    def __init__(self, side="left"):
        self.font = None
        self.side = side  # "left" or "right"
        self.lines = []
        self.alpha = 150

    def _get_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 13)
        return self.font

    def update(self, lines):
        """Update the info lines to display.

        Args:
            lines: list of str, each line of info text.
        """
        self.lines = lines

    def draw(self, surface):
        """Draw info panel at the bottom corner."""
        if not self.lines:
            return

        font = self._get_font()
        line_h = 18
        total_h = len(self.lines) * line_h + 8

        if self.side == "left":
            x = 15
        else:
            # Right-align: find max width
            max_w = max(font.render(l, True, (255, 255, 255)).get_width() for l in self.lines)
            x = config.WINDOW_WIDTH - max_w - 15

        y = config.WINDOW_HEIGHT - total_h - 8

        # Background
        max_w = max(font.render(l, True, (255, 255, 255)).get_width() for l in self.lines)
        bg_surf = pygame.Surface((max_w + 12, total_h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, int(self.alpha * 0.4)))
        surface.blit(bg_surf, (x - 6, y - 4))

        for i, line in enumerate(self.lines):
            text_surf = font.render(line, True, config.COLOR_INFO_TEXT)
            text_surf.set_alpha(self.alpha)
            surface.blit(text_surf, (x, y + i * line_h))


class CameraView:
    """Camera view with frame overlay and hand tracking visualization.

    The frame is controlled by two corners:
      - top_left (x1, y1) controlled by left hand
      - bottom_right (x2, y2) controlled by right hand
    """

    def __init__(self):
        self.font = None
        self.small_font = None

        # Frame defined by two corners (in pixel coords)
        self.frame_x1 = 0
        self.frame_y1 = 0
        self.frame_x2 = 0
        self.frame_y2 = 0
        self.frame_visible = False

        # Animation
        self._dash_offset = 0
        self._frame_alpha = 0        # For fade-in animation
        self._frame_scale = 0.0      # For scale-in animation

    def _get_fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 20, bold=True)
            self.small_font = pygame.font.SysFont("arial", 16)
        return self.font, self.small_font

    def set_frame_corners(self, x1, y1, x2, y2):
        """Set frame position from two corner points.

        Args:
            x1, y1: Top-left corner (controlled by left hand).
            x2, y2: Bottom-right corner (controlled by right hand).
        """
        # Ensure x1 < x2 and y1 < y2
        self.frame_x1 = min(x1, x2)
        self.frame_y1 = min(y1, y2)
        self.frame_x2 = max(x1, x2)
        self.frame_y2 = max(y1, y2)
        self.frame_visible = True

    def hide_frame(self):
        """Hide the capture frame."""
        self.frame_visible = False

    def get_frame_rect(self):
        """Get the frame as (x, y, w, h)."""
        w = max(0, self.frame_x2 - self.frame_x1)
        h = max(0, self.frame_y2 - self.frame_y1)
        return (self.frame_x1, self.frame_y1, w, h)

    def get_frame_size_label(self):
        """Get a human-readable size label."""
        w = self.frame_x2 - self.frame_x1
        h = self.frame_y2 - self.frame_y1
        area = w * h
        if area < 200 * 200:
            return "Small"
        elif area < 400 * 400:
            return "Medium"
        else:
            return "Large"

    def _draw_dashed_rect(self, surface, rect, color, dash_len=8, gap_len=6, width=1):
        """Draw a rectangle with dashed (putus-putus) lines.

        Args:
            surface: pygame.Surface to draw on.
            rect: pygame.Rect defining the rectangle.
            color: RGB or RGBA color tuple.
            dash_len: Length of each dash in pixels.
            gap_len: Length of each gap in pixels.
            width: Line width.
        """
        x, y, w, h = rect
        total_len = dash_len + gap_len

        # Top edge
        self._draw_dashed_line(surface, (x, y), (x + w, y), color, dash_len, gap_len, width)
        # Bottom edge
        self._draw_dashed_line(surface, (x, y + h), (x + w, y + h), color, dash_len, gap_len, width)
        # Left edge
        self._draw_dashed_line(surface, (x, y), (x, y + h), color, dash_len, gap_len, width)
        # Right edge
        self._draw_dashed_line(surface, (x + w, y), (x + w, y + h), color, dash_len, gap_len, width)

    def _draw_dashed_line(self, surface, start, end, color, dash_len, gap_len, width):
        """Draw a single dashed line segment."""
        sx, sy = start
        ex, ey = end
        dx = ex - sx
        dy = ey - sy
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return

        ux, uy = dx / length, dy / length  # unit vector
        total_len = dash_len + gap_len

        # Apply animated offset
        offset = self._dash_offset % total_len
        pos = -offset

        while pos < length:
            dash_start = max(0, pos)
            dash_end = min(length, pos + dash_len)
            if dash_end > dash_start:
                p1 = (int(sx + ux * dash_start), int(sy + uy * dash_start))
                p2 = (int(sx + ux * dash_end), int(sy + uy * dash_end))
                pygame.draw.line(surface, color, p1, p2, width)
            pos += total_len

    def update_animation(self, dt):
        """Update dashed line animation offset."""
        self._dash_offset += dt * 30  # Speed of dash animation

    def update_frame_animation(self, dt):
        """Update frame appearance animation (fade + scale)."""
        if self.frame_visible:
            self._frame_alpha = min(255, self._frame_alpha + 600 * dt)
            self._frame_scale = min(1.0, self._frame_scale + 5.0 * dt)
        else:
            self._frame_alpha = max(0, self._frame_alpha - 400 * dt)
            self._frame_scale = max(0.0, self._frame_scale - 3.0 * dt)

    def draw_frame_overlay(self, surface):
        """Draw the capture frame overlay with dashed lines and sky blue accents."""
        if self._frame_alpha <= 0 or self._frame_scale <= 0:
            return

        font, small_font = self._get_fonts()
        alpha = int(self._frame_alpha)

        fx1, fy1 = self.frame_x1, self.frame_y1
        fx2, fy2 = self.frame_x2, self.frame_y2
        fw = fx2 - fx1
        fh = fy2 - fy1

        if fw < 10 or fh < 10:
            return

        # Apply scale animation (scale from center of frame)
        if self._frame_scale < 1.0:
            cx = (fx1 + fx2) / 2
            cy = (fy1 + fy2) / 2
            s = self._frame_scale
            fx1 = int(cx - (cx - fx1) * s)
            fy1 = int(cy - (cy - fy1) * s)
            fx2 = int(cx + (fx2 - cx) * s)
            fy2 = int(cy + (fy2 - cy) * s)
            fw = fx2 - fx1
            fh = fy2 - fy1

        # Semi-transparent overlay outside the frame
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(100 * alpha / 255)))
        # Cut out the frame area
        pygame.draw.rect(overlay, (0, 0, 0, 0), (fx1, fy1, fw, fh))
        surface.blit(overlay, (0, 0))

        # Dashed white frame border
        frame_color = (*config.COLOR_DASHED_FRAME[:3], alpha)
        self._draw_dashed_rect(surface, (fx1, fy1, fw, fh), frame_color,
                               dash_len=10, gap_len=7, width=2)

        # Corner accents with sky blue
        corner_len = 25
        accent_color = (*config.COLOR_SKY_BLUE[:3], alpha)
        corners = [
            (fx1, fy1, 1, 1),
            (fx2, fy1, -1, 1),
            (fx1, fy2, 1, -1),
            (fx2, fy2, -1, -1),
        ]
        for cx, cy, dx, dy in corners:
            pygame.draw.line(surface, accent_color,
                             (cx, cy), (cx + corner_len * dx, cy), 3)
            pygame.draw.line(surface, accent_color,
                             (cx, cy), (cx, cy + corner_len * dy), 3)

        # Frame size label
        size_label = self.get_frame_size_label()
        size_text = small_font.render(f"Frame: {size_label} ({fw}x{fh})", True, config.COLOR_STATUS_DIM)
        size_text.set_alpha(alpha)
        surface.blit(size_text, (fx1, max(5, fy1 - 25)))

    def draw_instructions(self, surface, state, hand_count=0):
        """Draw instruction text for the current state.

        Args:
            surface: pygame.Surface.
            state: Current application state.
            hand_count: Number of detected hands.
        """
        font, small_font = self._get_fonts()

        if state == config.STATE_IDLE:
            if hand_count == 0:
                lines = ["Show both hands to begin"]
            elif hand_count == 1:
                lines = ["Show both hands to begin", "Need two hands detected"]
            else:
                lines = ["Pinch both hands to create frame"]
        elif state == config.STATE_FRAME_CREATION:
            lines = ["Adjust frame with both pinching hands",
                     "Open both palms to capture"]
        else:
            return

        # Draw instruction lines centered
        y = config.WINDOW_HEIGHT - 60
        for line in lines:
            text = small_font.render(line, True, config.COLOR_TEXT)
            text.set_alpha(180)
            surface.blit(text, (config.WINDOW_WIDTH // 2 - text.get_width() // 2, y))
            y += 22

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

    def draw_hand_landmarks(self, surface, landmarks_px, alpha=170):
        """Draw hand landmarks with transparent white skeleton style.

        Args:
            surface: pygame.Surface.
            landmarks_px: list of (int, int) pixel coordinates for 21 landmarks.
            alpha: Transparency level (0-255). Default 170 (~67%).
        """
        if landmarks_px is None:
            return

        # Create a separate surface for transparency
        skeleton_surf = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)

        # Draw connections — thin white lines with transparency
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),       # Index
            (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
            (0, 13), (13, 14), (14, 15), (15, 16), # Ring
            (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
            (5, 9), (9, 13), (13, 17),             # Palm
        ]
        line_color = (*config.COLOR_HAND_SKELETON_LINE[:3], alpha)
        for (i, j) in connections:
            if i < len(landmarks_px) and j < len(landmarks_px):
                pygame.draw.line(skeleton_surf, line_color,
                                 landmarks_px[i], landmarks_px[j], 1)

        # Draw points — small white dots with transparency
        dot_color = (*config.COLOR_HAND_SKELETON_DOT[:3], int(alpha * 0.9))
        for (px, py) in landmarks_px:
            pygame.draw.circle(skeleton_surf, dot_color, (px, py), 3)

        surface.blit(skeleton_surf, (0, 0))

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

        # State indicator (top-left) — kept for backward compatibility
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
