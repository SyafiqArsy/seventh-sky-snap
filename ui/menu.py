"""
Seventh Sky Snap - UI Menu System
Handles all UI screens: camera view, puzzle view, status bar, and info panels.
Enhanced with smooth animations, glow effects, and polished visuals.
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


class StatusBar:
    """Dynamic status bar at the top center of the screen."""

    def __init__(self):
        self.font = None
        self.text = ""
        self.alpha = 0
        self._target_alpha = 0
        self._dot_phase = 0.0

    def _get_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 18, bold=True)
        return self.font

    def update(self, state, dt, countdown_number=0):
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
        self._dot_phase += dt * 3

    def draw(self, surface):
        if self.alpha <= 0 or not self.text:
            return

        font = self._get_font()
        text_surf = font.render(self.text, True, config.COLOR_STATUS_ACTIVE)
        text_surf.set_alpha(int(self.alpha))

        cx = config.WINDOW_WIDTH // 2
        tx = cx - text_surf.get_width() // 2
        ty = 12

        # Background pill with gradient
        pad_x, pad_y = 20, 8
        bg_w = text_surf.get_width() + pad_x * 2
        bg_h = text_surf.get_height() + pad_y * 2
        bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        # Gradient background
        for row in range(bg_h):
            t = row / bg_h
            a = int(self.alpha * 0.4 * (0.8 + 0.2 * t))
            pygame.draw.line(bg_surf, (0, 0, 0, a), (0, row), (bg_w, row))
        pygame.draw.rect(bg_surf, (0, 0, 0, 0), (0, 0, bg_w, bg_h), border_radius=10)
        surface.blit(bg_surf, (tx - pad_x, ty - pad_y))

        # Animated dot indicator
        dot_x = tx - 12
        dot_y = ty + text_surf.get_height() // 2
        dot_alpha = int(self.alpha * (0.5 + 0.5 * math.sin(self._dot_phase)))
        dot_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(dot_surf, (*config.COLOR_STATUS_ACTIVE[:3], dot_alpha), (3, 3), 3)
        surface.blit(dot_surf, (dot_x - 3, dot_y - 3))

        surface.blit(text_surf, (tx, ty))


class InfoPanel:
    """Lightweight info display at bottom corners."""

    def __init__(self, side="left"):
        self.font = None
        self.side = side
        self.lines = []
        self.alpha = 150

    def _get_font(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 13)
        return self.font

    def update(self, lines):
        self.lines = lines

    def draw(self, surface):
        if not self.lines:
            return

        font = self._get_font()
        line_h = 18
        total_h = len(self.lines) * line_h + 8

        if self.side == "left":
            x = 15
        else:
            max_w = max(font.render(l, True, (255, 255, 255)).get_width() for l in self.lines)
            x = config.WINDOW_WIDTH - max_w - 15

        y = config.WINDOW_HEIGHT - total_h - 8

        # Background with rounded corners
        max_w = max(font.render(l, True, (255, 255, 255)).get_width() for l in self.lines)
        bg_surf = pygame.Surface((max_w + 12, total_h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, int(self.alpha * 0.4)),
                         (0, 0, max_w + 12, total_h), border_radius=6)
        surface.blit(bg_surf, (x - 6, y - 4))

        for i, line in enumerate(self.lines):
            text_surf = font.render(line, True, config.COLOR_INFO_TEXT)
            text_surf.set_alpha(self.alpha)
            surface.blit(text_surf, (x, y + i * line_h))


class CameraView:
    """Camera view with frame overlay and hand tracking visualization."""

    def __init__(self):
        self.font = None
        self.small_font = None

        # Frame defined by two corners
        self.frame_x1 = 0
        self.frame_y1 = 0
        self.frame_x2 = 0
        self.frame_y2 = 0
        self.frame_visible = False

        # Animation
        self._dash_offset = 0
        self._frame_alpha = 0
        self._frame_scale = 0.0
        self._instruction_alpha = 0
        self._prev_instruction = ""

    def _get_fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 20, bold=True)
            self.small_font = pygame.font.SysFont("arial", 16)
        return self.font, self.small_font

    def set_frame_corners(self, x1, y1, x2, y2):
        self.frame_x1 = min(x1, x2)
        self.frame_y1 = min(y1, y2)
        self.frame_x2 = max(x1, x2)
        self.frame_y2 = max(y1, y2)
        self.frame_visible = True

    def hide_frame(self):
        self.frame_visible = False

    def get_frame_rect(self):
        w = max(0, self.frame_x2 - self.frame_x1)
        h = max(0, self.frame_y2 - self.frame_y1)
        return (self.frame_x1, self.frame_y1, w, h)

    def get_frame_size_label(self):
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
        x, y, w, h = rect
        self._draw_dashed_line(surface, (x, y), (x + w, y), color, dash_len, gap_len, width)
        self._draw_dashed_line(surface, (x, y + h), (x + w, y + h), color, dash_len, gap_len, width)
        self._draw_dashed_line(surface, (x, y), (x, y + h), color, dash_len, gap_len, width)
        self._draw_dashed_line(surface, (x + w, y), (x + w, y + h), color, dash_len, gap_len, width)

    def _draw_dashed_line(self, surface, start, end, color, dash_len, gap_len, width):
        sx, sy = start
        ex, ey = end
        dx = ex - sx
        dy = ey - sy
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return

        ux, uy = dx / length, dy / length
        total_len = dash_len + gap_len

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
        self._dash_offset += dt * 30

    def update_frame_animation(self, dt):
        if self.frame_visible:
            self._frame_alpha = min(255, self._frame_alpha + 600 * dt)
            self._frame_scale = min(1.0, self._frame_scale + 5.0 * dt)
        else:
            self._frame_alpha = max(0, self._frame_alpha - 400 * dt)
            self._frame_scale = max(0.0, self._frame_scale - 3.0 * dt)

    def draw_frame_overlay(self, surface):
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

        # Apply scale animation
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
        for cx_c, cy_c, dx, dy in corners:
            pygame.draw.line(surface, accent_color,
                             (cx_c, cy_c), (cx_c + corner_len * dx, cy_c), 3)
            pygame.draw.line(surface, accent_color,
                             (cx_c, cy_c), (cx_c, cy_c + corner_len * dy), 3)

        # Frame size label
        size_label = self.get_frame_size_label()
        size_text = small_font.render(f"Frame: {size_label} ({fw}x{fh})", True, config.COLOR_STATUS_DIM)
        size_text.set_alpha(alpha)
        surface.blit(size_text, (fx1, max(5, fy1 - 25)))

    def draw_instructions(self, surface, state, hand_count=0):
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

        # Animate instruction text fade
        instruction_key = "|".join(lines)
        if instruction_key != self._prev_instruction:
            self._prev_instruction = instruction_key
            self._instruction_alpha = 0
        self._instruction_alpha = min(255, self._instruction_alpha + 500 * (1.0 / config.FPS))

        y = config.WINDOW_HEIGHT - 60
        for line in lines:
            text = small_font.render(line, True, config.COLOR_TEXT)
            text.set_alpha(int(min(180, self._instruction_alpha)))
            surface.blit(text, (config.WINDOW_WIDTH // 2 - text.get_width() // 2, y))
            y += 22

    def draw_camera_frame(self, surface, frame_bgr):
        if frame_bgr is None:
            return

        fh, fw = frame_bgr.shape[:2]
        scale = min(config.WINDOW_WIDTH / fw, config.WINDOW_HEIGHT / fh)
        new_w = int(fw * scale)
        new_h = int(fh * scale)
        frame_resized = cv2.resize(frame_bgr, (new_w, new_h))

        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))

        x = (config.WINDOW_WIDTH - new_w) // 2
        y = (config.WINDOW_HEIGHT - new_h) // 2
        surface.blit(frame_surface, (x, y))

    def draw_hand_landmarks(self, surface, landmarks_px, alpha=170):
        """Draw hand landmarks with glow effect on fingertips."""
        if landmarks_px is None:
            return

        skeleton_surf = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)

        # Draw connections
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (0, 9), (9, 10), (10, 11), (11, 12),
            (0, 13), (13, 14), (14, 15), (15, 16),
            (0, 17), (17, 18), (18, 19), (19, 20),
            (5, 9), (9, 13), (13, 17),
        ]
        line_color = (*config.COLOR_HAND_SKELETON_LINE[:3], alpha)
        for (i, j) in connections:
            if i < len(landmarks_px) and j < len(landmarks_px):
                pygame.draw.line(skeleton_surf, line_color,
                                 landmarks_px[i], landmarks_px[j], 1)

        # Draw points with glow on fingertips
        fingertip_indices = {4, 8, 12, 16, 20}  # Thumb, Index, Middle, Ring, Pinky tips
        dot_color = (*config.COLOR_HAND_SKELETON_DOT[:3], int(alpha * 0.9))

        for idx, (px, py) in enumerate(landmarks_px):
            if idx in fingertip_indices:
                # Glow effect on fingertips
                glow_r = config.FINGERTIP_GLOW_RADIUS
                glow_a = int(config.FINGERTIP_GLOW_ALPHA * (alpha / 255))
                glow_surf = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
                for gr in range(glow_r, 0, -1):
                    ga = int(glow_a * (gr / glow_r))
                    pygame.draw.circle(glow_surf, (*config.COLOR_SKY_BLUE[:3], ga),
                                       (glow_r * 2, glow_r * 2), gr)
                skeleton_surf.blit(glow_surf, (px - glow_r * 2, py - glow_r * 2))
                # Bright dot
                pygame.draw.circle(skeleton_surf, (*config.COLOR_SKY_BLUE[:3], alpha), (px, py), 4)
            else:
                pygame.draw.circle(skeleton_surf, dot_color, (px, py), 3)

        surface.blit(skeleton_surf, (0, 0))


class PuzzleView:
    """UI overlay for puzzle mode instructions and info."""

    def __init__(self):
        self.font = None
        self.small_font = None
        self._prev_solved = 0
        self._pulse_timer = 0.0
        self._pulse_active = False

    def _get_fonts(self):
        if self.font is None:
            self.font = pygame.font.SysFont("arial", 24, bold=True)
            self.small_font = pygame.font.SysFont("arial", 18)
        return self.font, self.small_font

    def draw(self, surface, solved_count, total_count):
        font, small_font = self._get_fonts()

        # Detect progress change for pulse effect
        if solved_count != self._prev_solved:
            self._prev_solved = solved_count
            self._pulse_active = True
            self._pulse_timer = 0.0

        if self._pulse_active:
            self._pulse_timer += 1.0 / config.FPS
            if self._pulse_timer > 0.4:
                self._pulse_active = False

        # Header
        header = font.render("Puzzle Mode", True, config.COLOR_ACCENT_LIGHT)
        surface.blit(header, (config.WINDOW_WIDTH // 2 - header.get_width() // 2, 8))

        # Progress bar with gradient
        if total_count > 0:
            progress = solved_count / total_count
            bar_w = 220
            bar_h = 8
            bar_x = config.WINDOW_WIDTH // 2 - bar_w // 2
            bar_y = 42

            # Background
            pygame.draw.rect(surface, (40, 40, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)

            if progress > 0:
                fill_w = int(bar_w * progress)
                # Gradient fill
                fill_surf = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
                for col in range(fill_w):
                    t = col / max(1, fill_w)
                    r = int(config.COLOR_ACCENT[0] * (1 - t) + config.COLOR_SUCCESS[0] * t)
                    g = int(config.COLOR_ACCENT[1] * (1 - t) + config.COLOR_SUCCESS[1] * t)
                    b = int(config.COLOR_ACCENT[2] * (1 - t) + config.COLOR_SUCCESS[2] * t)
                    pygame.draw.line(fill_surf, (r, g, b, 220), (col, 0), (col, bar_h))
                surface.blit(fill_surf, (bar_x, bar_y))

                # Pulse glow on progress tip
                if self._pulse_active:
                    pulse_alpha = int(100 * (1.0 - self._pulse_timer / 0.4))
                    pulse_r = int(12 + 8 * (self._pulse_timer / 0.4))
                    pulse_surf = pygame.Surface((pulse_r * 2, pulse_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(pulse_surf, (*config.COLOR_SUCCESS[:3], pulse_alpha),
                                       (pulse_r, pulse_r), pulse_r)
                    surface.blit(pulse_surf, (bar_x + fill_w - pulse_r,
                                              bar_y + bar_h // 2 - pulse_r))

            # Percentage text
            pct_text = small_font.render(f"{int(progress * 100)}%", True, config.COLOR_TEXT_DIM)
            surface.blit(pct_text, (bar_x + bar_w + 10, bar_y - 3))
