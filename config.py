"""
Seventh Sky Snap - Application Configuration
Central configuration for all modules.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Window ──────────────────────────────────────────────────
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Seventh Sky Snap"
FPS = 30

# ── Camera ──────────────────────────────────────────────────
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# ── Hand Tracking ───────────────────────────────────────────
PINCH_DISTANCE_MIN = 30.0
PINCH_DISTANCE_MAX = 250.0
FRAME_SIZE_MIN = 150
FRAME_SIZE_MAX = 500
GESTURE_SMOOTHING = 5
GESTURE_HOLD_FRAMES = 25
PINCH_GRAB_THRESHOLD = 0.05

# ── Capture ─────────────────────────────────────────────────
COUNTDOWN_SECONDS = 3
CAPTURE_COOLDOWN = 2.0

# ── Image Processing ────────────────────────────────────────
POLAROID_BORDER_TOP = 20
POLAROID_BORDER_SIDES = 20
POLAROID_BORDER_BOTTOM = 80
POLAROID_BG_COLOR = (255, 255, 255)
OUTPUT_MAX_WIDTH = 600
OUTPUT_MAX_HEIGHT = 700

# ── Puzzle ──────────────────────────────────────────────────
PUZZLE_ROWS = 3
PUZZLE_COLS = 3
SNAP_THRESHOLD = 100

# ── Colors (RGB) ────────────────────────────────────────────
COLOR_BG = (15, 15, 25)
COLOR_BG_GRADIENT = (25, 20, 45)
COLOR_ACCENT = (130, 80, 220)
COLOR_ACCENT_LIGHT = (180, 130, 255)
COLOR_TEXT = (240, 240, 245)
COLOR_TEXT_DIM = (150, 150, 165)
COLOR_SUCCESS = (80, 220, 120)
COLOR_WARNING = (255, 180, 50)
COLOR_ERROR = (220, 80, 80)
COLOR_FRAME_OVERLAY = (130, 80, 220, 60)
COLOR_FRAME_BORDER = (130, 80, 220)
COLOR_COUNTDOWN = (255, 255, 255)
COLOR_PUZZLE_BG = (20, 20, 35)
COLOR_PIECE_BORDER = (60, 60, 80)
COLOR_PIECE_HIGHLIGHT = (130, 80, 220, 100)
COLOR_BUTTON = (130, 80, 220)
COLOR_BUTTON_HOVER = (160, 110, 250)
COLOR_BUTTON_TEXT = (255, 255, 255)
COLOR_HAND_LANDMARK = (0, 255, 200)
COLOR_HAND_CONNECTIONS = (0, 200, 160)

# ── Paths ───────────────────────────────────────────────────
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FRAME_DIR = os.path.join(ASSETS_DIR, "frame")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
SOUND_DIR = os.path.join(ASSETS_DIR, "sound")
SAVED_DIR = os.path.join(BASE_DIR, "saved")

# ── State Machine ───────────────────────────────────────────
STATE_IDLE = "idle"
STATE_CAMERA_READY = "camera_ready"
STATE_TRACKING = "tracking"
STATE_RESIZE_MODE = "resize_mode"
STATE_CAPTURE_COUNTDOWN = "capture_countdown"
STATE_IMAGE_PROCESSING = "image_processing"
STATE_PUZZLE_MODE = "puzzle_mode"
STATE_SOLVED = "solved"
STATE_POLAROID_PRESENTATION = "polaroid_presentation"
STATE_SAVE_COMPLETED = "save_completed"

# ── Gesture Types ───────────────────────────────────────────
GESTURE_NONE = "none"
GESTURE_OPEN_HAND = "open_hand"
GESTURE_PINCH = "pinch"
GESTURE_THUMBS_UP = "thumbs_up"
GESTURE_POINT = "point"
GESTURE_FIST = "fist"
GESTURE_VICTORY = "victory"

# ── Puzzle Board Layout ─────────────────────────────────────
PUZZLE_BOARD_X = 40
PUZZLE_BOARD_Y = 40
PUZZLE_BOARD_WIDTH = 800
PUZZLE_BOARD_HEIGHT = 640
PUZZLE_TRAY_X = 880
PUZZLE_TRAY_Y = 40
PUZZLE_TRAY_WIDTH = 360
PUZZLE_TRAY_HEIGHT = 640
