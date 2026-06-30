"""
Seventh Sky Snap - Puzzle Piece
Represents a single puzzle piece with position and state tracking.
"""

import pygame

import config


class PuzzlePiece:
    """A single puzzle piece that can be dragged and snapped into place."""

    def __init__(self, piece_id, image_surface, correct_x, correct_y, width, height):
        """
        Args:
            piece_id: Unique identifier (row * cols + col).
            image_surface: pygame.Surface of this piece's image.
            correct_x: Correct X position on the board.
            correct_y: Correct Y position on the board.
            width: Piece width.
            height: Piece height.
        """
        self.piece_id = piece_id
        self.image = image_surface
        self.correct_x = correct_x
        self.correct_y = correct_y
        self.width = width
        self.height = height

        # Current position (may differ from correct)
        self.x = correct_x
        self.y = correct_y

        # State
        self.is_locked = False  # True when placed correctly
        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # Animation
        self.lock_animation_progress = 0.0
        self.highlight = False

    @property
    def rect(self):
        """Get the current bounding rect."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    @property
    def correct_rect(self):
        """Get the correct bounding rect."""
        return pygame.Rect(self.correct_x, self.correct_y, self.width, self.height)

    @property
    def center(self):
        """Get current center position."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    def contains_point(self, px, py):
        """Check if a point is inside this piece."""
        return self.rect.collidepoint(px, py)

    def start_drag(self, mouse_x, mouse_y):
        """Begin dragging this piece."""
        if self.is_locked:
            return False
        self.is_dragging = True
        self.drag_offset_x = mouse_x - self.x
        self.drag_offset_y = mouse_y - self.y
        return True

    def update_drag(self, mouse_x, mouse_y):
        """Update position during drag."""
        if not self.is_dragging:
            return
        self.x = mouse_x - self.drag_offset_x
        self.y = mouse_y - self.drag_offset_y

    def stop_drag(self):
        """Stop dragging."""
        self.is_dragging = False

    def is_near_correct(self, threshold=None):
        """Check if piece is close enough to snap to correct position.

        Args:
            threshold: Snap distance in pixels. Uses config default if None.

        Returns:
            bool: True if within threshold.
        """
        if threshold is None:
            threshold = config.SNAP_THRESHOLD

        dx = abs(self.x - self.correct_x)
        dy = abs(self.y - self.correct_y)
        return dx <= threshold and dy <= threshold

    def snap_to_correct(self):
        """Snap piece to its correct position and lock it."""
        self.x = self.correct_x
        self.y = self.correct_y
        self.is_locked = True
        self.is_dragging = False
        self.lock_animation_progress = 0.0

    def update_animation(self, dt):
        """Update lock animation.

        Args:
            dt: Delta time in seconds.
        """
        if self.is_locked and self.lock_animation_progress < 1.0:
            self.lock_animation_progress = min(1.0, self.lock_animation_progress + dt * 3.0)

    def draw(self, surface):
        """Draw this piece onto a surface.

        Args:
            surface: pygame.Surface to draw on.
        """
        # Draw the piece image
        surface.blit(self.image, (self.x, self.y))

        # Draw border
        border_color = config.COLOR_PIECE_BORDER
        if self.is_locked:
            # Green tint for locked pieces
            border_color = config.COLOR_SUCCESS
        elif self.highlight:
            border_color = config.COLOR_ACCENT_LIGHT

        pygame.draw.rect(surface, border_color, self.rect, 2)

        # Lock glow animation
        if self.is_locked and self.lock_animation_progress < 1.0:
            alpha = int(100 * (1.0 - self.lock_animation_progress))
            glow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            glow.fill((*config.COLOR_SUCCESS[:3], alpha))
            surface.blit(glow, (self.x, self.y))
