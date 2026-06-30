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


def shuffle_pieces(pieces, tray_x=None, tray_y=None, tray_w=None, tray_h=None):
    """Shuffle piece positions randomly within the tray area.

    Args:
        pieces: list of PuzzlePiece.
        tray_x: Tray area X. Defaults to config.
        tray_y: Tray area Y. Defaults to config.
        tray_w: Tray area width. Defaults to config.
        tray_h: Tray area height. Defaults to config.

    Returns:
        list of PuzzlePiece: Same pieces with shuffled positions.
    """
    if tray_x is None:
        tray_x = config.PUZZLE_TRAY_X
    if tray_y is None:
        tray_y = config.PUZZLE_TRAY_Y
    if tray_w is None:
        tray_w = config.PUZZLE_TRAY_WIDTH
    if tray_h is None:
        tray_h = config.PUZZLE_TRAY_HEIGHT

    random.shuffle(pieces)

    # Arrange pieces in a grid within the tray
    n = len(pieces)
    cols = max(1, int(n ** 0.5))
    rows = (n + cols - 1) // cols

    margin = 10
    cell_w = (tray_w - margin * (cols + 1)) // cols
    cell_h = (tray_h - margin * (rows + 1)) // rows

    for i, piece in enumerate(pieces):
        r = i // cols
        c = i % cols
        piece.x = tray_x + margin + c * (cell_w + margin)
        piece.y = tray_y + margin + r * (cell_h + margin)

    return pieces
