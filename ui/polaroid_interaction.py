"""
Seventh Sky Snap - Interactive Polaroid Mode (Post-Puzzle)
Handles single-hand gesture interaction with the polaroid photo:
  - Polaroid stays centered, not movable
  - Open hand + swipe left/right rotates the polaroid around X-axis (3D flip)
  - Fist gesture saves the polaroid and returns to idle
Simulates 3D X-axis rotation by scaling Y-dimension and showing back face.
"""

import math
import os
import time
from collections import deque

import pygame

import config
from ui.animation import Easing


class PolaroidInteraction:
    """Manages interactive polaroid 3D rotation via single-hand gestures.

    After puzzle completion, the polaroid is displayed centered on screen.
    The user can rotate it around the X-axis by showing an open hand and
    swiping left/right. This creates a 3D card-flip effect where the user
    can see the back of the polaroid. Showing a fist triggers save.
    """

    def __init__(self):
        # Position is always centered (not movable)
        self.x = config.WINDOW_WIDTH // 2
        self.y = config.WINDOW_HEIGHT // 2
        self.rotation = 0.0      # degrees, X-axis rotation
        self.target_rotation = 0.0

        # Source polaroid surface
        self.polaroid_surface = None
        self.display_surf = None
        self.back_surf = None    # Back face of the polaroid
        self.base_width = 0
        self.base_height = 0

        # State
        self.active = False
        self._wrist_history = deque(maxlen=5)

        # Animation state for entry
        self._entry_active = False
        self._entry_progress = 0.0
        self._entry_duration = 0.5
        self._entry_elapsed = 0.0

        # Smoothing factor
        self._smooth = config.POLAROID_SMOOTH_FACTOR

        # Font for status display
        self._font = None

    def _get_font(self):
        if self._font is None:
            self._font = pygame.font.SysFont("arial", 16, bold=True)
        return self._font

    def start(self, polaroid_surface):
        """Activate interactive polaroid mode.

        Args:
            polaroid_surface: pygame.Surface of the completed polaroid.
        """
        self.polaroid_surface = polaroid_surface
        self.active = True

        # Scale polaroid to a comfortable default size
        if polaroid_surface:
            pw, ph = polaroid_surface.get_size()
            self.base_width = pw
            self.base_height = ph
            self._update_display_surf()

        # Always centered
        self.x = config.WINDOW_WIDTH // 2
        self.y = config.WINDOW_HEIGHT // 2
        self.rotation = 0.0
        self.target_rotation = 0.0

        # Entry animation
        self._entry_active = True
        self._entry_progress = 0.0
        self._entry_elapsed = 0.0

        # Reset wrist tracking
        self._wrist_history.clear()

    def _update_display_surf(self):
        """Recreate the display surface and back face."""
        if self.polaroid_surface is None:
            return
        # Apply a base scale to fit nicely on screen
        fit_scale = min(500 / self.base_width, 450 / self.base_height)
        w = int(self.base_width * fit_scale)
        h = int(self.base_height * fit_scale)
        self.display_surf = pygame.transform.smoothscale(self.polaroid_surface, (w, h))
        self.base_width = w
        self.base_height = h

        # Create back face — white/cream surface with subtle border
        self.back_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        self.back_surf.fill((245, 240, 230))  # Cream color
        # Subtle border
        pygame.draw.rect(self.back_surf, (200, 195, 185), (0, 0, w, h), 2)
        # Small label
        font = pygame.font.SysFont("arial", 14)
        label = font.render("Seventh Sky Snap", True, (180, 175, 165))
        self.back_surf.blit(label, (w // 2 - label.get_width() // 2,
                                     h // 2 - label.get_height() // 2))

    def update(self, dt, rotation_delta=None):
        """Update polaroid rotation from gesture data.

        Args:
            dt: Delta time in seconds.
            rotation_delta: Rotation degrees to add this frame, or None.
                            Positive = rotate right, negative = rotate left.

        Returns:
            bool: True if a fist gesture was detected (save trigger).
        """
        if not self.active:
            return False

        # Entry animation
        if self._entry_active:
            self._entry_elapsed += dt
            t = min(1.0, self._entry_elapsed / self._entry_duration)
            self._entry_progress = Easing.ease_out_cubic(t)
            if t >= 1.0:
                self._entry_active = False
            return False

        if rotation_delta is not None:
            self.target_rotation += rotation_delta
            # Allow full 360° rotation for X-axis flip
            self.target_rotation = max(-180.0, min(180.0, self.target_rotation))
        else:
            # No open hand — gradually return rotation toward 0
            self.target_rotation *= 0.97
            if abs(self.target_rotation) < 0.5:
                self.target_rotation = 0.0

        # Smooth interpolation toward target rotation
        lerp = min(1.0, self._smooth * dt * 60)  # Frame-rate independent
        angle_diff = self.target_rotation - self.rotation
        # Normalize to [-180, 180]
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        self.rotation += angle_diff * lerp

        return False

    def update_with_hand(self, dt, wrist_x=None, gesture=None):
        """Update with single-hand gesture data.

        Args:
            dt: Delta time in seconds.
            wrist_x: Normalized wrist x position (0-1), or None if no hand.
            gesture: Current gesture string from GestureRecognizer.

        Returns:
            bool: True if a fist gesture was detected (save trigger).
        """
        if not self.active:
            return False

        # Entry animation
        if self._entry_active:
            self._entry_elapsed += dt
            t = min(1.0, self._entry_elapsed / self._entry_duration)
            self._entry_progress = Easing.ease_out_cubic(t)
            if t >= 1.0:
                self._entry_active = False
            return False

        # Fist gesture → save trigger
        if gesture == config.GESTURE_FIST:
            return True

        if gesture == config.GESTURE_OPEN_HAND and wrist_x is not None:
            self._wrist_history.append(wrist_x)

            if len(self._wrist_history) >= 2:
                wrist_list = list(self._wrist_history)
                dx = wrist_list[-1] - wrist_list[0]
                n = len(wrist_list)
                rotation_velocity = dx * 800 / n
                self.target_rotation += rotation_velocity * dt * 60
                # Allow full 180° range for X-axis flip
                self.target_rotation = max(-180.0, min(180.0, self.target_rotation))
        else:
            self._wrist_history.clear()
            # Gradually return rotation toward 0
            self.target_rotation *= 0.97
            if abs(self.target_rotation) < 0.5:
                self.target_rotation = 0.0

        # Smooth interpolation toward target rotation
        lerp = min(1.0, self._smooth * dt * 60)
        angle_diff = self.target_rotation - self.rotation
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        self.rotation += angle_diff * lerp

        return False

    def draw(self, surface):
        """Draw the interactive polaroid with 3D X-axis rotation.

        Simulates 3D rotation by scaling the Y-dimension based on
        cos(rotation). When |rotation| > 90°, shows the back face.

        Args:
            surface: pygame.Surface to draw on.
        """
        if not self.active or self.display_surf is None:
            return

        # Apply entry animation scale
        entry_scale = self._entry_progress if self._entry_active else 1.0
        effective_scale = config.POLAROID_DEFAULT_SCALE * entry_scale

        # Base dimensions
        w = max(1, int(self.base_width * effective_scale))
        h = max(1, int(self.base_height * effective_scale))

        # X-axis rotation: scale Y by cos(angle)
        rad = math.radians(self.rotation)
        y_scale = math.cos(rad)  # 1.0 at 0°, 0.0 at 90°, -1.0 at 180°
        abs_y_scale = abs(y_scale)

        # Minimum height to avoid zero-height surface
        scaled_h = max(2, int(h * abs_y_scale))

        # Determine front or back face
        show_back = y_scale < 0

        if show_back:
            source = self.back_surf
        else:
            source = self.display_surf

        # Scale to current dimensions
        scaled = pygame.transform.smoothscale(source, (w, scaled_h))

        # Back face: flip vertically (mirror effect when viewed from behind)
        if show_back:
            scaled = pygame.transform.flip(scaled, False, True)

        # Get dimensions for centering
        rw, rh = scaled.get_size()

        # Shadow: also compressed by y_scale for 3D effect
        shadow_h = max(2, int((rh + 4) * 1.0))  # Shadow doesn't compress as much
        shadow_offset_x = 6
        shadow_offset_y = int(6 * abs_y_scale)
        shadow_alpha = int(35 * entry_scale * abs_y_scale)
        if shadow_alpha > 0:
            shadow = pygame.Surface((rw + 4, shadow_h), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, shadow_alpha))
            surface.blit(shadow, (int(self.x - rw // 2 - 2 + shadow_offset_x),
                                   int(self.y - rh // 2 - 2 + shadow_offset_y)))

        # Draw polaroid centered
        surface.blit(scaled, (int(self.x - rw // 2), int(self.y - rh // 2)))

    def draw_status(self, surface, gesture=None):
        """Draw interaction status indicators.

        Shows rotation hint when open hand is detected, save hint for fist.
        """
        if not self.active or self._entry_active:
            return

        font = self._get_font()

        # Show current gesture hint
        if gesture == config.GESTURE_OPEN_HAND:
            hint = "Swipe left/right to rotate"
            color = config.COLOR_STATUS_ACTIVE
        elif gesture == config.GESTURE_FIST:
            hint = "Saving..."
            color = config.COLOR_SUCCESS
        else:
            hint = "Show open hand to rotate | Fist to save"
            color = config.COLOR_STATUS_DIM

        text_surf = font.render(hint, True, color)
        text_surf.set_alpha(180)
        cx = config.WINDOW_WIDTH // 2
        surface.blit(text_surf, (cx - text_surf.get_width() // 2,
                                  config.WINDOW_HEIGHT - 35))

    def get_final_surface(self):
        """Render the final polaroid with rotation applied.

        Returns:
            pygame.Surface: The polaroid with rotation applied,
                            or None if not active.
        """
        if not self.active or self.display_surf is None:
            return None

        w = max(1, int(self.base_width * config.POLAROID_DEFAULT_SCALE))
        h = max(1, int(self.base_height * config.POLAROID_DEFAULT_SCALE))
        scaled = pygame.transform.smoothscale(self.display_surf, (w, h))

        if abs(self.rotation) > 0.5:
            return pygame.transform.rotate(scaled, -self.rotation)
        return scaled

    def save_result(self, save_path=None):
        """Save the final polaroid image.

        Args:
            save_path: Optional path override. If None, generates timestamp filename.

        Returns:
            str: Path to saved file.
        """
        if self.polaroid_surface is None:
            return None

        os.makedirs(config.SAVED_DIR, exist_ok=True)

        if save_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"interactive_polaroid_{timestamp}.png"
            save_path = os.path.join(config.SAVED_DIR, filename)

        # Save the original high-quality polaroid (not the transformed version)
        pygame.image.save(self.polaroid_surface, save_path)
        return save_path

    def stop(self):
        """Deactivate interactive polaroid mode."""
        self.active = False
        self._entry_active = False

    def reset(self):
        """Reset all state."""
        self.stop()
        self.x = config.WINDOW_WIDTH // 2
        self.y = config.WINDOW_HEIGHT // 2
        self.rotation = 0.0
        self.target_rotation = 0.0
        self.polaroid_surface = None
        self.display_surf = None
        self.back_surf = None
        self._wrist_history.clear()
