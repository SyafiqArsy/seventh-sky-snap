"""
Seventh Sky Snap - Puzzle Validator
Validates puzzle completion state.
"""


def check_all_solved(pieces):
    """Check if all puzzle pieces are locked in correct positions.

    Args:
        pieces: list of PuzzlePiece.

    Returns:
        bool: True if every piece is locked.
    """
    if not pieces:
        return False
    return all(piece.is_locked for piece in pieces)


def get_solved_count(pieces):
    """Count how many pieces are correctly placed.

    Args:
        pieces: list of PuzzlePiece.

    Returns:
        int: Number of locked pieces.
    """
    return sum(1 for piece in pieces if piece.is_locked)


def get_progress(pieces):
    """Get puzzle completion progress as a fraction.

    Args:
        pieces: list of PuzzlePiece.

    Returns:
        float: 0.0 to 1.0.
    """
    if not pieces:
        return 0.0
    return get_solved_count(pieces) / len(pieces)


def find_misplaced_pieces(pieces):
    """Find pieces that are not yet correctly placed.

    Args:
        pieces: list of PuzzlePiece.

    Returns:
        list of PuzzlePiece: Pieces not locked.
    """
    return [piece for piece in pieces if not piece.is_locked]
