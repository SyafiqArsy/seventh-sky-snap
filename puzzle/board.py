"""
Seventh Sky Snap - Puzzle Board
Manages the puzzle board state with hand gesture and mouse interaction.
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

        # Hand tracking state
        self.hand_cursor = None      # (x, y) pixel position of index finger
        self.hand_grabbing = False   # True when pinch gesture active
        self._prev_grabbing = False  # Previous frame grab state
        self._hand_active = False    # Whether hand is currently tracked

    def setup(self, polaroid_surface):
        """Initialize puzzle from a polaroid surface."""
        self.pieces = generate_pieces(polaroid_surface)
        self.pieces = shuffle_pieces(self.pieces)
        self.solved = False
        self.dragging_piece = None
        self.hand_cursor = None
        self.hand_grabbing = False
        self._prev_grabbing = False
        self._hand_active = False

    def update_hand(self, cursor_x, cursor_y, is_grabbing, hand_present):
        """Update hand tracking state for puzzle interaction.

        Args:
            cursor_x: Index finger X in window pixels.
            cursor_y: Index finger Y in window pixels.
            is_grabbing: True if pinch/grab gesture detected.
            hand_present: True if hand is detected at all.
        """
        self.hand_cursor = (cursor_x, cursor_y) if hand_present else None
        self._hand_active = hand_present

        if self.solved:
            self.hand_grabbing = False
            return

        was_grabbing = self.hand_grabbing
        self.hand_grabbing = is_grabbing and hand_present

        # While grabbing, move the piece first (before checking release)
        if self.hand_grabbing and self.dragging_piece:
            self.dragging_piece.update_drag(cursor_x, cursor_y)

        # Grab transition: not grabbing -> grabbing
        if self.hand_grabbing and not was_grabbing:
            self._hand_grab(cursor_x, cursor_y)

        # Release transition: was grabbing -> now not grabbing
        # This covers: pinch released, hand disappeared, hand lost tracking
        if was_grabbing and not self.hand_grabbing:
            self._hand_release()

    def _hand_grab(self, x, y):
        """Try to grab a piece at the given position."""
        for piece in reversed(self.pieces):
            if not piece.is_locked and piece.contains_point(x, y):
                piece.start_drag(x, y)
                self.dragging_piece = piece
                # Move to top of draw order
                self.pieces.remove(piece)
                self.pieces.append(piece)
                return

    def _hand_release(self):
        """Release the currently grabbed piece and check snap."""
        if self.dragging_piece:
            self.dragging_piece.stop_drag()
            if self.dragging_piece.is_near_correct():
                self.dragging_piece.snap_to_correct()
                if self.on_piece_locked:
                    self.on_piece_locked(self.dragging_piece)
                if check_all_solved(self.pieces):
                    self.solved = True
                    if self.on_solved:
                        self.on_solved()
            self.dragging_piece = None

    def handle_event(self, event):
        """Handle a pygame event for mouse-based puzzle interaction."""
        if self.solved:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for piece in reversed(self.pieces):
                if not piece.is_locked and piece.contains_point(mx, my):
                    piece.start_drag(mx, my)
                    self.dragging_piece = piece
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
        """Update puzzle animations."""
        for piece in self.pieces:
            piece.update_animation(dt)

    def draw(self, surface, draw_board_bg=True):
        """Draw the puzzle board and all pieces.

        Args:
            surface: pygame.Surface to draw on.
            draw_board_bg: Whether to draw the board background rectangle.
        """
        if draw_board_bg:
            board_rect = pygame.Rect(
                config.PUZZLE_BOARD_X, config.PUZZLE_BOARD_Y,
                config.PUZZLE_BOARD_WIDTH, config.PUZZLE_BOARD_HEIGHT,
            )
            pygame.draw.rect(surface, config.COLOR_PUZZLE_BG, board_rect, border_radius=8)
            pygame.draw.rect(surface, config.COLOR_PIECE_BORDER, board_rect, 2, border_radius=8)

            tray_rect = pygame.Rect(
                config.PUZZLE_TRAY_X, config.PUZZLE_TRAY_Y,
                config.PUZZLE_TRAY_WIDTH, config.PUZZLE_TRAY_HEIGHT,
            )
            pygame.draw.rect(surface, (25, 25, 40), tray_rect, border_radius=8)
            pygame.draw.rect(surface, config.COLOR_PIECE_BORDER, tray_rect, 2, border_radius=8)

            font = pygame.font.SysFont("arial", 16)
            label = font.render("Pinch to grab, move to place", True, config.COLOR_TEXT_DIM)
            surface.blit(label, (tray_rect.centerx - label.get_width() // 2, tray_rect.bottom - 30))
        else:
            # Minimal white border for tray area (no fill)
            tray_rect = pygame.Rect(
                config.PUZZLE_TRAY_X, config.PUZZLE_TRAY_Y,
                config.PUZZLE_TRAY_WIDTH, config.PUZZLE_TRAY_HEIGHT,
            )
            tray_surf = pygame.Surface((tray_rect.w, tray_rect.h), pygame.SRCALPHA)
            pygame.draw.rect(tray_surf, (255, 255, 255, 40), tray_surf.get_rect(), 1, border_radius=4)
            surface.blit(tray_surf, tray_rect.topleft)

            font = pygame.font.SysFont("arial", 14)
            label = font.render("Pieces", True, (255, 255, 255, 120))
            label.set_alpha(120)
            surface.blit(label, (tray_rect.centerx - label.get_width() // 2, tray_rect.bottom - 22))

        # Draw pieces
        for piece in self.pieces:
            piece.draw(surface)

        # Draw hand cursor if active
        if self.hand_cursor and self._hand_active:
            cx, cy = self.hand_cursor
            color = config.COLOR_WARNING if self.hand_grabbing else config.COLOR_ACCENT_LIGHT
            pygame.draw.circle(surface, color, (cx, cy), 12, 2)
            pygame.draw.circle(surface, color, (cx, cy), 3)
            if self.hand_grabbing:
                pygame.draw.circle(surface, config.COLOR_SUCCESS, (cx, cy), 16, 2)

        # Draw hand cursor if active
        if self.hand_cursor and self._hand_active:
            cx, cy = self.hand_cursor
            # Cursor ring
            color = config.COLOR_WARNING if self.hand_grabbing else config.COLOR_ACCENT_LIGHT
            pygame.draw.circle(surface, color, (cx, cy), 12, 2)
            pygame.draw.circle(surface, color, (cx, cy), 3)
            # Grab indicator
            if self.hand_grabbing:
                pygame.draw.circle(surface, config.COLOR_SUCCESS, (cx, cy), 16, 2)

    def get_solved_count(self):
        return sum(1 for p in self.pieces if p.is_locked)

    def get_total_count(self):
        return len(self.pieces)

    def get_completion_image(self):
        """Get the completed puzzle as a single surface."""
        if not self.solved or not self.pieces:
            return None

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
        self.pieces.clear()
        self.dragging_piece = None
        self.solved = False
        self.hand_cursor = None
        self.hand_grabbing = False
