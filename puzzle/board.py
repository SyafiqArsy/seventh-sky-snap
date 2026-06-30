"""
Seventh Sky Snap - Puzzle Board
Manages the puzzle board state and user interaction.
"""

import pygame

import config
from puzzle.generator import generate_pieces, shuffle_pieces
from puzzle.validator import check_all_solved


class PuzzleBoard:
    """Manages the puzzle board, piece interactions, and game state."""

    def __init__(self):
        self.pieces = []
        self.dragging_piece = None
        self.solved = False
        self.on_piece_locked = None  # callback(piece)
        self.on_solved = None       # callback()

    def setup(self, polaroid_surface):
        """Initialize puzzle from a polaroid surface.

        Args:
            polaroid_surface: pygame.Surface of the completed polaroid.
        """
        self.pieces = generate_pieces(polaroid_surface)
        self.pieces = shuffle_pieces(self.pieces)
        self.solved = False
        self.dragging_piece = None

    def handle_event(self, event):
        """Handle a pygame event for puzzle interaction.

        Args:
            event: pygame.event.Event.

        Returns:
            bool: True if the event was consumed.
        """
        if self.solved:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Find topmost piece under cursor (search in reverse for z-order)
            for piece in reversed(self.pieces):
                if not piece.is_locked and piece.contains_point(mx, my):
                    piece.start_drag(mx, my)
                    self.dragging_piece = piece
                    # Move to top of draw order
                    self.pieces.remove(piece)
                    self.pieces.append(piece)
                    return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_piece:
                self.dragging_piece.stop_drag()
                if self.dragging_piece.is_near_correct():
                    self.dragging_piece.snap_to_correct()
                    if self.on_piece_locked:
                        self.on_piece_locked(self.dragging_piece)
                    # Check if puzzle is complete
                    if check_all_solved(self.pieces):
                        self.solved = True
                        if self.on_solved:
                            self.on_solved()
                self.dragging_piece = None
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_piece:
                self.dragging_piece.update_drag(*event.pos)
                return True

        return False

    def update(self, dt):
        """Update puzzle animations.

        Args:
            dt: Delta time in seconds.
        """
        for piece in self.pieces:
            piece.update_animation(dt)

    def draw(self, surface):
        """Draw the puzzle board and all pieces.

        Args:
            surface: pygame.Surface to draw on.
        """
        # Draw board background
        board_rect = pygame.Rect(
            config.PUZZLE_BOARD_X, config.PUZZLE_BOARD_Y,
            config.PUZZLE_BOARD_WIDTH, config.PUZZLE_BOARD_HEIGHT,
        )
        pygame.draw.rect(surface, config.COLOR_PUZZLE_BG, board_rect, border_radius=8)
        pygame.draw.rect(surface, config.COLOR_PIECE_BORDER, board_rect, 2, border_radius=8)

        # Draw tray area
        tray_rect = pygame.Rect(
            config.PUZZLE_TRAY_X, config.PUZZLE_TRAY_Y,
            config.PUZZLE_TRAY_WIDTH, config.PUZZLE_TRAY_HEIGHT,
        )
        pygame.draw.rect(surface, (25, 25, 40), tray_rect, border_radius=8)
        pygame.draw.rect(surface, config.COLOR_PIECE_BORDER, tray_rect, 2, border_radius=8)

        # Draw tray label
        font = pygame.font.SysFont("arial", 16)
        label = font.render("Drag pieces to the board", True, config.COLOR_TEXT_DIM)
        surface.blit(label, (tray_rect.centerx - label.get_width() // 2, tray_rect.bottom - 30))

        # Draw pieces
        for piece in self.pieces:
            piece.draw(surface)

    def get_solved_count(self):
        """Get the number of correctly placed pieces."""
        return sum(1 for p in self.pieces if p.is_locked)

    def get_total_count(self):
        """Get total number of pieces."""
        return len(self.pieces)

    def get_completion_image(self):
        """Get the completed puzzle as a single surface.

        Returns:
            pygame.Surface or None: The assembled image if solved.
        """
        if not self.solved or not self.pieces:
            return None

        # Find bounding box of all pieces
        min_x = min(p.correct_x for p in self.pieces)
        min_y = min(p.correct_y for p in self.pieces)
        max_x = max(p.correct_x + p.width for p in self.pieces)
        max_y = max(p.correct_y + p.height for p in self.pieces)

        w = max_x - min_x
        h = max_y - min_y
        result = pygame.Surface((w, h), pygame.SRCALPHA)

        for piece in self.pieces:
            result.blit(piece.image, (piece.correct_x - min_x, piece.correct_y - min_y))

        return result

    def reset(self):
        """Reset the puzzle board."""
        self.pieces.clear()
        self.dragging_piece = None
        self.solved = False
