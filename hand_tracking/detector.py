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
    """Detects hands and extracts 21 landmarks using MediaPipe Tasks API.

    Supports both single-hand and two-hand detection. When two hands are
    detected, ``all_hands`` contains one dict per hand and the legacy
    ``landmarks`` / ``handedness`` attributes point to the first hand.
    """

    def __init__(self, num_hands=2):
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
            num_hands=num_hands,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.landmarker = HandLandmarker.create_from_options(options)

        # Legacy single-hand attributes (backward compatibility)
        self.landmarks = None
        self.handedness = None  # "Left" or "Right"
        self.hand_present = False

        # Multi-hand data: list of dicts with 'landmarks', 'handedness', 'landmarks_px'
        self.all_hands = []
        self._timestamp_ms = 0

    def detect(self, frame_rgb):
        """Process an RGB frame and detect hand landmarks.

        Args:
            frame_rgb: numpy.ndarray in RGB format.

        Returns:
            bool: True if at least one hand was detected.
        """
        # Reset
        self.landmarks = None
        self.hand_present = False
        self.handedness = None
        self.all_hands = []

        h, w = frame_rgb.shape[:2]

        # Convert to MediaPipe Image format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Detect with timestamp for video mode
        self._timestamp_ms += 33  # ~30fps
        result = self.landmarker.detect_for_video(mp_image, self._timestamp_ms)

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            for i, hand_lm in enumerate(result.hand_landmarks):
                # Convert to list of (x, y, z) tuples
                landmarks = []
                for lm in hand_lm:
                    landmarks.append((lm.x, lm.y, lm.z))

                # Get handedness
                handedness = None
                if result.handedness and i < len(result.handedness) and len(result.handedness[i]) > 0:
                    handedness = result.handedness[i][0].category_name

                # Compute pixel landmarks
                pixels = []
                for (lx, ly, lz) in landmarks:
                    pixels.append((int(lx * w), int(ly * h)))

                self.all_hands.append({
                    'landmarks': landmarks,
                    'handedness': handedness,
                    'landmarks_px': pixels,
                })

            # Legacy: populate single-hand attributes from first hand
            self.landmarks = self.all_hands[0]['landmarks']
            self.handedness = self.all_hands[0]['handedness']
            self.hand_present = True

        return self.hand_present

    def get_hand_by_label(self, label):
        """Get hand data by handedness label ('Left' or 'Right').

        Note: MediaPipe mirrors handedness — 'Left' in the model
        corresponds to the user's right hand.

        Args:
            label: 'Left' or 'Right'.

        Returns:
            dict or None: Hand data dict, or None if not found.
        """
        for hand in self.all_hands:
            if hand['handedness'] == label:
                return hand
        return None

    def get_landmark_pixels(self, frame_width, frame_height):
        """Convert normalized landmarks to pixel coordinates.

        Uses the first detected hand for backward compatibility.

        Args:
            frame_width: Width of the frame in pixels.
            frame_height: Height of the frame in pixels.

        Returns:
            list of (int, int) or None: Pixel coordinates for each of 21 landmarks.
        """
        if self.all_hands:
            return self.all_hands[0]['landmarks_px']

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

        Draws all detected hands.

        Args:
            frame_bgr: numpy.ndarray in BGR format.
            frame_width: Optional override for frame width.
            frame_height: Optional override for frame height.
        """
        if not self.hand_present:
            return

        for hand in self.all_hands:
            pixels = hand['landmarks_px']
            if not pixels:
                continue

            # Draw connections
            for (start_idx, end_idx) in HAND_CONNECTIONS:
                if start_idx < len(pixels) and end_idx < len(pixels):
                    cv2.line(frame_bgr, pixels[start_idx], pixels[end_idx],
                             config.COLOR_HAND_CONNECTIONS, 2)

            # Draw landmark points
            for (px, py) in pixels:
                cv2.circle(frame_bgr, (px, py), 5, config.COLOR_HAND_LANDMARK, -1)
                cv2.circle(frame_bgr, (px, py), 7, config.COLOR_HAND_LANDMARK, 1)

    def get_landmark(self, index, hand_index=0):
        """Get a specific landmark by index (0-20).

        Args:
            index: MediaPipe landmark index.
            hand_index: Which hand (0 = first detected).

        Returns:
            tuple (x, y, z) normalized or None.
        """
        if hand_index < len(self.all_hands):
            lm = self.all_hands[hand_index]['landmarks']
            if index < len(lm):
                return lm[index]
        if self.landmarks is None or index >= len(self.landmarks):
            return None
        return self.landmarks[index]

    def get_all_landmark_pixels(self, frame_width, frame_height):
        """Get pixel landmarks for all detected hands.

        Returns:
            list of list of (int, int): One list per hand, or empty list.
        """
        result = []
        for hand in self.all_hands:
            pixels = hand.get('landmarks_px')
            if pixels:
                result.append(pixels)
            else:
                # Fallback: compute from normalized
                fallback = []
                for (x, y, z) in hand['landmarks']:
                    fallback.append((int(x * frame_width), int(y * frame_height)))
                result.append(fallback)
        return result

    def release(self):
        """Release MediaPipe resources."""
        if self.landmarker:
            self.landmarker.close()
