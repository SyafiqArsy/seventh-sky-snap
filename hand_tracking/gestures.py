"""
Seventh Sky Snap - Gesture Recognition
Recognizes hand gestures from MediaPipe landmarks.
"""

import math
from collections import deque

import config


class GestureRecognizer:
    """Recognizes gestures from hand landmark data."""

    # MediaPipe landmark indices
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    def __init__(self):
        self.current_gesture = config.GESTURE_NONE
        self.gesture_history = deque(maxlen=config.GESTURE_SMOOTHING)
        self.gesture_hold_counter = 0
        self._pinch_distance = 0.0
        self._pinch_distance_history = deque(maxlen=config.GESTURE_SMOOTHING)
        self.index_finger_tip = None  # (x, y) normalized
        self._hand_detected_frames = 0

    def update(self, landmarks):
        """Analyze landmarks and determine the current gesture.

        Args:
            landmarks: List of 21 (x, y, z) tuples (normalized 0-1).

        Returns:
            str: The recognized gesture type from config constants.
        """
        if landmarks is None or len(landmarks) < 21:
            self.current_gesture = config.GESTURE_NONE
            self.gesture_history.append(config.GESTURE_NONE)
            self.index_finger_tip = None
            self._hand_detected_frames = 0
            return config.GESTURE_NONE

        self._hand_detected_frames += 1

        # Skip gesture recognition for first few frames to avoid false triggers
        if self._hand_detected_frames < 8:
            self.current_gesture = config.GESTURE_NONE
            self.gesture_history.append(config.GESTURE_NONE)
            index_tip = landmarks[self.INDEX_TIP]
            self.index_finger_tip = (index_tip[0], index_tip[1])
            return config.GESTURE_NONE

        # Extract key points
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        index_tip = landmarks[self.INDEX_TIP]
        index_pip = landmarks[self.INDEX_PIP]
        index_mcp = landmarks[self.INDEX_MCP]
        middle_tip = landmarks[self.MIDDLE_TIP]
        middle_pip = landmarks[self.MIDDLE_PIP]
        ring_tip = landmarks[self.RING_TIP]
        ring_pip = landmarks[self.RING_PIP]
        pinky_tip = landmarks[self.PINKY_TIP]
        pinky_pip = landmarks[self.PINKY_PIP]
        wrist = landmarks[self.WRIST]

        # Store index finger tip for puzzle interaction
        self.index_finger_tip = (index_tip[0], index_tip[1])

        # Calculate pinch distance (thumb to index)
        self._pinch_distance = self._euclidean_2d(thumb_tip, index_tip)
        self._pinch_distance_history.append(self._pinch_distance)
        avg_pinch = sum(self._pinch_distance_history) / len(self._pinch_distance_history)

        # Determine finger states using strict y-position check
        # In normalized coords, y=0 is top, y=1 is bottom
        # A finger is extended if its TIP is ABOVE (less y) its PIP joint
        fingers = {
            "index": index_tip[1] < index_pip[1] - 0.02,
            "middle": middle_tip[1] < middle_pip[1] - 0.02,
            "ring": ring_tip[1] < ring_pip[1] - 0.02,
            "pinky": pinky_tip[1] < pinky_pip[1] - 0.02,
        }

        # Thumb: check if tip is away from palm center horizontally
        palm_center_x = (index_mcp[0] + wrist[0]) / 2
        thumb_extended = abs(thumb_tip[0] - palm_center_x) > 0.06

        # Gesture Classification
        gesture = config.GESTURE_NONE

        # Check thumbs up FIRST (most specific):
        # - thumb tip clearly above thumb MCP (y decreases going up)
        # - thumb tip above wrist
        # - ALL other fingers clearly curled (tips below their PIPs)
        thumb_points_up = (
            thumb_tip[1] < thumb_mcp[1] - 0.05
            and thumb_tip[1] < wrist[1] - 0.05
        )
        all_others_curled = (
            not fingers["index"]
            and not fingers["middle"]
            and not fingers["ring"]
            and not fingers["pinky"]
        )

        if thumb_points_up and all_others_curled and thumb_extended:
            gesture = config.GESTURE_THUMBS_UP

        # Check pinch: thumb and index tips very close
        elif avg_pinch < config.PINCH_GRAB_THRESHOLD:
            gesture = config.GESTURE_PINCH

        # Check point: ONLY index finger extended, rest curled
        elif (
            fingers["index"]
            and not fingers["middle"]
            and not fingers["ring"]
            and not fingers["pinky"]
        ):
            gesture = config.GESTURE_POINT

        # Check fist: ALL fingers curled, thumb not extended
        elif (
            not fingers["index"]
            and not fingers["middle"]
            and not fingers["ring"]
            and not fingers["pinky"]
            and not thumb_extended
        ):
            gesture = config.GESTURE_FIST

        # Check victory: index + middle extended, ring + pinky curled
        elif (
            fingers["index"]
            and fingers["middle"]
            and not fingers["ring"]
            and not fingers["pinky"]
        ):
            gesture = config.GESTURE_VICTORY

        # Check open hand: ALL fingers extended
        elif (
            fingers["index"]
            and fingers["middle"]
            and fingers["ring"]
            and fingers["pinky"]
        ):
            gesture = config.GESTURE_OPEN_HAND

        # Smooth gesture with history
        self.gesture_history.append(gesture)
        smoothed = self._smooth_gesture()

        # Track hold duration
        if smoothed == self.current_gesture:
            self.gesture_hold_counter += 1
        else:
            self.gesture_hold_counter = 0
            self.current_gesture = smoothed

        return self.current_gesture

    def is_pinching(self):
        """Check if currently in a pinch gesture (for grab detection)."""
        return self._pinch_distance < config.PINCH_GRAB_THRESHOLD

    def _smooth_gesture(self):
        """Majority vote over gesture history for smoothing."""
        if not self.gesture_history:
            return config.GESTURE_NONE

        counts = {}
        for g in self.gesture_history:
            counts[g] = counts.get(g, 0) + 1

        return max(counts, key=counts.get)

    def get_pinch_distance_normalized(self):
        """Get the smoothed pinch distance.

        Returns:
            float: Average pinch distance (normalized).
        """
        if not self._pinch_distance_history:
            return 0.0
        return sum(self._pinch_distance_history) / len(self._pinch_distance_history)

    def gesture_held_long_enough(self):
        """Check if the current gesture has been held for enough frames.

        Returns:
            bool: True if held for GESTURE_HOLD_FRAMES or more.
        """
        return self.gesture_hold_counter >= config.GESTURE_HOLD_FRAMES

    @staticmethod
    def _euclidean_2d(p1, p2):
        """Calculate 2D Euclidean distance between two points."""
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def get_index_finger_pixels(self, frame_width, frame_height):
        """Get index finger tip in pixel coordinates.

        Returns:
            tuple (int, int) or None.
        """
        if self.index_finger_tip is None:
            return None
        return (
            int(self.index_finger_tip[0] * frame_width),
            int(self.index_finger_tip[1] * frame_height),
        )
