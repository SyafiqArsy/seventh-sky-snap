"""
Seventh Sky Snap - Puzzle Generator
Splits a polaroid image into puzzle pieces.
"""

import random

import numpy as np
import pygame

import config
from puzzle.pieces import PuzzlePiece


def generate_pieces(polaroid_surface, rows=None, cols=None,
                    board_x=None, board_y=None, board_w=None, board_h=None):
    """Split a pygame Surface into puzzle pieces.

    Args:
        polaroid_surface: pygame.Surface of the polaroid image.
        rows: Number of rows. Defaults to config.
        cols: Number of columns. Defaults to config.
        board_x: Board offset X. Defaults to config.
        board_y: Board offset Y. Defaults to config.
        board_w: Board width. Defaults to config.
        board_h: Board height. Defaults to config.

    Returns:
        list of PuzzlePiece: The generated puzzle pieces (unshuffled positions).
    """
    if rows is None:
        rows = config.PUZZLE_ROWS
    if cols is None:
        cols = config.PUZZLE_COLS
    if board_x is None:
        board_x = config.PUZZLE_BOARD_X
    if board_y is None:
        board_y = config.PUZZLE_BOARD_Y
    if board_w is None:
        board_w = config.PUZZLE_BOARD_WIDTH
    if board_h is None:
        board_h = config.PUZZLE_BOARD_HEIGHT

    # Scale the polaroid to fit the board
    img_w, img_h = polaroid_surface.get_size()
    scale = min(board_w / img_w, board_h / img_h)
    scaled_w = int(img_w * scale)
    scaled_h = int(img_h * scale)
    scaled_img = pygame.transform.smoothscale(polaroid_surface, (scaled_w, scaled_h))

    # Center within board
    offset_x = board_x + (board_w - scaled_w) // 2
    offset_y = board_y + (board_h - scaled_h) // 2

    piece_w = scaled_w // cols
    piece_h = scaled_h // rows

    pieces = []
    for row in range(rows):
        for col in range(cols):
            piece_id = row * cols + col

            # Crop the piece from the scaled image
            src_x = col * piece_w
            src_y = row * piece_h
            # Last piece in row/col gets remainder
            pw = piece_w if col < cols - 1 else scaled_w - src_x
            ph = piece_h if row < rows - 1 else scaled_h - src_y

            piece_surface = pygame.Surface((pw, ph), pygame.SRCALPHA)
            piece_surface.blit(scaled_img, (0, 0), (src_x, src_y, pw, ph))

            # Correct position on the board
            correct_x = offset_x + src_x
            correct_y = offset_y + src_y

            piece = PuzzlePiece(
                piece_id=piece_id,
                image_surface=piece_surface,
                correct_x=correct_x,
                correct_y=correct_y,
                width=pw,
                height=ph,
            )
            pieces.append(piece)

    return pieces


def shuffle_pieces(pieces, board_x=None, board_y=None, board_w=None, board_h=None):
    """Shuffle piece positions randomly within the puzzle board area.

    All pieces are placed inside the board area in the center of the screen,
    arranged in a grid but with randomized order so they don't match
    their correct positions.

    Args:
        pieces: list of PuzzlePiece.
        board_x: Board area X. Defaults to config.
        board_y: Board area Y. Defaults to config.
        board_w: Board area width. Defaults to config.
        board_h: Board area height. Defaults to config.

    Returns:
        list of PuzzlePiece: Same pieces with shuffled positions.
    """
    if board_x is None:
        board_x = config.PUZZLE_BOARD_X
    if board_y is None:
        board_y = config.PUZZLE_BOARD_Y
    if board_w is None:
        board_w = config.PUZZLE_BOARD_WIDTH
    if board_h is None:
        board_h = config.PUZZLE_BOARD_HEIGHT

    n = len(pieces)
    if n == 0:
        return pieces

    # Find the bounding box of all correct positions (the target image area)
    min_cx = min(p.correct_x for p in pieces)
    min_cy = min(p.correct_y for p in pieces)
    max_cx = max(p.correct_x + p.width for p in pieces)
    max_cy = max(p.correct_y + p.height for p in pieces)
    img_w = max_cx - min_cx
    img_h = max_cy - min_cy

    # Calculate grid layout within the board area
    # We want all pieces to fit inside the board area
    cols = max(1, int(n ** 0.5))
    rows = max(1, (n + cols - 1) // cols)

    margin = 6
    cell_w = (board_w - margin * (cols + 1)) // cols
    cell_h = (board_h - margin * (rows + 1)) // rows

    # Build a list of grid slot positions (centered in board area)
    total_grid_w = cols * cell_w + (cols - 1) * margin
    total_grid_h = rows * cell_h + (rows - 1) * margin
    start_x = board_x + (board_w - total_grid_w) // 2
    start_y = board_y + (board_h - total_grid_h) // 2

    slots = []
    for r in range(rows):
        for c in range(cols):
            sx = start_x + c * (cell_w + margin)
            sy = start_y + r * (cell_h + margin)
            slots.append((sx, sy))

    # Shuffle the pieces randomly
    random.shuffle(pieces)

    # Assign each piece to a shuffled slot
    for i, piece in enumerate(pieces):
        if i < len(slots):
            px, py = slots[i]
        else:
            # Fallback: random position within board
            px = board_x + random.randint(0, max(0, board_w - piece.width))
            py = board_y + random.randint(0, max(0, board_h - piece.height))

        piece.x = px
        piece.y = py

    return pieces
