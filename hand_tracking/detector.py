"""
Seventh Sky Snap - Hand Detector
MediaPipe Tasks API-based hand detection and landmark extraction.
"""

import os

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

import config

# Hand landmark connections for drawing
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),       # Index
    (0, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17),             # Palm
]

# Path to the hand landmarker model
MODEL_PATH = os.path.join(config.ASSETS_DIR, "hand_landmarker.task")


class HandDetector:
    """Detects hands and extracts 21 landmarks using MediaPipe Tasks API."""

    def __init__(self):
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Hand landmarker model not found at {MODEL_PATH}. "
                "Run: python -c \"import urllib.request, os; "
                "os.makedirs('assets', exist_ok=True); "
                "urllib.request.urlretrieve("
                "'https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task',"
                " 'assets/hand_landmarker.task')\""
            )

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        self.landmarks = None
        self.handedness = None  # "Left" or "Right"
        self.hand_present = False
        self._timestamp_ms = 0

    def detect(self, frame_rgb):
        """Process an RGB frame and detect hand landmarks.

        Args:
            frame_rgb: numpy.ndarray in RGB format.

        Returns:
            bool: True if a hand was detected.
        """
        self.landmarks = None
        self.hand_present = False
        self.handedness = None

        h, w = frame_rgb.shape[:2]

        # Convert to MediaPipe Image format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Detect with timestamp for video mode
        self._timestamp_ms += 33  # ~30fps
        result = self.landmarker.detect_for_video(mp_image, self._timestamp_ms)

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            hand_lm = result.hand_landmarks[0]

            # Convert to list of (x, y, z) tuples
            self.landmarks = []
            for lm in hand_lm:
                self.landmarks.append((lm.x, lm.y, lm.z))

            # Get handedness
            if result.handedness and len(result.handedness) > 0:
                self.handedness = result.handedness[0][0].category_name

            self.hand_present = True

        return self.hand_present

    def get_landmark_pixels(self, frame_width, frame_height):
        """Convert normalized landmarks to pixel coordinates.

        Args:
            frame_width: Width of the frame in pixels.
            frame_height: Height of the frame in pixels.

        Returns:
            list of (int, int) or None: Pixel coordinates for each of 21 landmarks.
        """
        if self.landmarks is None:
            return None

        pixels = []
        for (x, y, z) in self.landmarks:
            px = int(x * frame_width)
            py = int(y * frame_height)
            pixels.append((px, py))
        return pixels

    def draw_landmarks(self, frame_bgr, frame_width=None, frame_height=None):
        """Draw hand landmarks and connections on a BGR frame.

        Args:
            frame_bgr: numpy.ndarray in BGR format.
            frame_width: Optional override for frame width.
            frame_height: Optional override for frame height.
        """
        if not self.hand_present or self.landmarks is None:
            return

        h, w = frame_bgr.shape[:2]
        if frame_width:
            w = frame_width
        if frame_height:
            h = frame_height

        pixels = self.get_landmark_pixels(w, h)
        if pixels is None:
            return

        # Draw connections
        for (start_idx, end_idx) in HAND_CONNECTIONS:
            if start_idx < len(pixels) and end_idx < len(pixels):
                cv2.line(frame_bgr, pixels[start_idx], pixels[end_idx],
                         config.COLOR_HAND_CONNECTIONS, 2)

        # Draw landmark points
        for (px, py) in pixels:
            cv2.circle(frame_bgr, (px, py), 5, config.COLOR_HAND_LANDMARK, -1)
            cv2.circle(frame_bgr, (px, py), 7, config.COLOR_HAND_LANDMARK, 1)

    def get_landmark(self, index):
        """Get a specific landmark by index (0-20).

        Args:
            index: MediaPipe landmark index.

        Returns:
            tuple (x, y, z) normalized or None.
        """
        if self.landmarks is None or index >= len(self.landmarks):
            return None
        return self.landmarks[index]

    def release(self):
        """Release MediaPipe resources."""
        if self.landmarker:
            self.landmarker.close()
