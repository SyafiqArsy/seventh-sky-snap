"""
Seventh Sky Snap - Interactive Polaroid Mode
Handles two-hand gesture interaction with the polaroid photo:
  - Translation (move) based on midpoint between two hands
  - Rotation based on angle between two hands
  - Scale based on distance between two hands
All transforms use smooth interpolation for premium feel.
"""

import math
import os
import time

import pygame

import config
from ui.animation import Easing


class PolaroidInteraction:
    """Manages interactive polaroid manipulation via two-hand gestures.

    The polaroid can be moved, rotated, and scaled using two hands
    detected by MediaPipe. All transforms are smoothed via interpolation
    to avoid jitter.
    """

    def __init__(self):
        # Current transform state
        self.x = config.WINDOW_WIDTH // 2
        self.y = config.WINDOW_HEIGHT // 2
        self.rotation = 0.0      # degrees
        self.scale = config.POLAROID_DEFAULT_SCALE

        # Target values (updated from gesture data)
        self.target_x = self.x
        self.target_y = self.y
        self.target_rotation = 0.0
        self.target_scale = config.POLAROID_DEFAULT_SCALE

        # Source polaroid surface
        self.polaroid_surface = None
        self.display_surf = None
        self.base_width = 0
        self.base_height = 0

        # State
        self.active = False
        self._idle_time = 0.0
        self._last_interaction_time = 0.0
        self._returning_to_center = False
        self._center_progress = 0.0

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

        # Start at center
        self.x = config.WINDOW_WIDTH // 2
        self.y = config.WINDOW_HEIGHT // 2
        self.target_x = self.x
        self.target_y = self.y
        self.rotation = 0.0
        self.target_rotation = 0.0
        self.scale = config.POLAROID_DEFAULT_SCALE
        self.target_scale = config.POLAROID_DEFAULT_SCALE

        # Entry animation
        self._entry_active = True
        self._entry_progress = 0.0
        self._entry_elapsed = 0.0

        # Reset idle tracking
        self._idle_time = 0.0
        self._last_interaction_time = time.time()
        self._returning_to_center = False

    def _update_display_surf(self):
        """Recreate the display surface based on current base dimensions."""
        if self.polaroid_surface is None:
            return
        # Apply a base scale to fit nicely on screen
        fit_scale = min(500 / self.base_width, 450 / self.base_height)
        w = int(self.base_width * fit_scale)
        h = int(self.base_height * fit_scale)
        self.display_surf = pygame.transform.smoothscale(self.polaroid_surface, (w, h))
        self.base_width = w
        self.base_height = h

    def update(self, dt, midpoint=None, angle=None, distance=None):
        """Update polaroid transform from gesture data.

        Args:
            dt: Delta time in seconds.
            midpoint: (float, float) normalized midpoint between hands, or None.
            angle: Rotation angle in degrees, or None.
            distance: Normalized hand distance, or None.
        """
        if not self.active:
            return

        # Entry animation
        if self._entry_active:
            self._entry_elapsed += dt
            t = min(1.0, self._entry_elapsed / self._entry_duration)
            self._entry_progress = Easing.ease_out_cubic(t)
            if t >= 1.0:
                self._entry_active = False
            return

        # Check if we have gesture data
        has_input = midpoint is not None

        if has_input:
            self._last_interaction_time = time.time()
            self._idle_time = 0.0
            self._returning_to_center = False

            # Translation: map normalized midpoint to screen position
            mx, my = midpoint
            # Add a range factor so small hand movements map to larger screen movement
            range_factor = 1.5
            self.target_x = config.WINDOW_WIDTH * 0.5 + (mx - 0.5) * config.WINDOW_WIDTH * range_factor
            self.target_y = config.WINDOW_HEIGHT * 0.5 + (my - 0.5) * config.WINDOW_HEIGHT * range_factor

            # Clamp to keep polaroid partially visible
            margin = 100
            self.target_x = max(-margin, min(config.WINDOW_WIDTH + margin, self.target_x))
            self.target_y = max(-margin, min(config.WINDOW_HEIGHT + margin, self.target_y))

            # Rotation
            if angle is not None:
                self.target_rotation = angle

            # Scale from distance
            if distance is not None:
                # Map normalized distance to scale range
                # Typical hand distance is 0.1 - 0.6
                normalized_dist = max(0.0, min(1.0, (distance - 0.05) / 0.5))
                self.target_scale = (
                    config.POLAROID_SCALE_MIN +
                    normalized_dist * (config.POLAROID_SCALE_MAX - config.POLAROID_SCALE_MIN)
                )
                self.target_scale = max(config.POLAROID_SCALE_MIN,
                                        min(config.POLAROID_SCALE_MAX, self.target_scale))
        else:
            # No input — track idle time
            self._idle_time = time.time() - self._last_interaction_time

            # After timeout, return to center
            if self._idle_time > config.POLAROID_IDLE_TIMEOUT:
                if not self._returning_to_center:
                    self._returning_to_center = True
                    self._center_progress = 0.0
                self.target_x = config.WINDOW_WIDTH // 2
                self.target_y = config.WINDOW_HEIGHT // 2
                self.target_rotation = 0.0
                self.target_scale = config.POLAROID_DEFAULT_SCALE

        # Smooth interpolation toward targets
        lerp = min(1.0, self._smooth * dt * 60)  # Frame-rate independent
        self.x += (self.target_x - self.x) * lerp
        self.y += (self.target_y - self.y) * lerp

        # Angle interpolation needs special handling for wraparound
        angle_diff = self.target_rotation - self.rotation
        # Normalize to [-180, 180]
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        self.rotation += angle_diff * lerp

        self.scale += (self.target_scale - self.scale) * lerp

    def draw(self, surface):
        """Draw the interactive polaroid with current transforms.

        Args:
            surface: pygame.Surface to draw on.
        """
        if not self.active or self.display_surf is None:
            return

        # Apply entry animation scale
        entry_scale = self._entry_progress if self._entry_active else 1.0
        effective_scale = self.scale * entry_scale

        # Apply scale
        w = max(1, int(self.base_width * effective_scale))
        h = max(1, int(self.base_height * effective_scale))
        scaled = pygame.transform.smoothscale(self.display_surf, (w, h))

        # Apply rotation
        if abs(self.rotation) > 0.5:
            rotated = pygame.transform.rotate(scaled, -self.rotation)
        else:
            rotated = scaled

        # Get rect for centering
        rw, rh = rotated.get_size()

        # Shadow
        shadow_offset = 6
        shadow_alpha = int(35 * entry_scale)
        shadow = pygame.Surface((rw + 4, rh + 4), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, shadow_alpha))
        surface.blit(shadow, (int(self.x - rw // 2 - 2 + shadow_offset),
                               int(self.y - rh // 2 - 2 + shadow_offset)))

        # Draw polaroid
        surface.blit(rotated, (int(self.x - rw // 2), int(self.y - rh // 2)))

    def draw_status(self, surface):
        """Draw interaction status indicators.

        Shows "Move", "Tilt", "Scale" hints based on current gesture activity.
        """
        if not self.active or self._entry_active:
            return

        font = self._get_font()
        hints = []
        if self._idle_time < 0.5:
            hints.append("Move")
            hints.append("Tilt")
            hints.append("Scale")

        if hints:
            hint_text = " | ".join(hints)
            text_surf = font.render(hint_text, True, config.COLOR_STATUS_ACTIVE)
            text_surf.set_alpha(150)
            cx = config.WINDOW_WIDTH // 2
            surface.blit(text_surf, (cx - text_surf.get_width() // 2,
                                     config.WINDOW_HEIGHT - 35))

        # Show "Returning..." when going back to center
        if self._returning_to_center:
            ret_text = font.render("Returning to center...", True, config.COLOR_STATUS_DIM)
            cx = config.WINDOW_WIDTH // 2
            surface.blit(ret_text, (cx - ret_text.get_width() // 2,
                                    config.WINDOW_HEIGHT - 55))

    def is_idle_timeout(self):
        """Check if the polaroid has been idle long enough to trigger save.

        Returns:
            bool: True if idle timeout reached and returned to center.
        """
        return (self._returning_to_center and
                abs(self.x - config.WINDOW_WIDTH // 2) < 5 and
                abs(self.y - config.WINDOW_HEIGHT // 2) < 5 and
                abs(self.rotation) < 1.0)

    def get_final_surface(self):
        """Render the final polaroid with transforms applied.

        Returns:
            pygame.Surface: The polaroid with rotation and scale applied,
                            or None if not active.
        """
        if not self.active or self.display_surf is None:
            return None

        w = max(1, int(self.base_width * self.scale))
        h = max(1, int(self.base_height * self.scale))
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
        self._returning_to_center = False

    def reset(self):
        """Reset all state."""
        self.stop()
        self.x = config.WINDOW_WIDTH // 2
        self.y = config.WINDOW_HEIGHT // 2
        self.rotation = 0.0
        self.scale = config.POLAROID_DEFAULT_SCALE
        self.polaroid_surface = None
        self.display_surf = None
