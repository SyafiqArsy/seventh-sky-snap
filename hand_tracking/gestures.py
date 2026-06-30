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
            return config.GESTURE_NONE

        # Extract key points
        thumb_tip = landmarks[self.THUMB_TIP]
        index_tip = landmarks[self.INDEX_TIP]
        middle_tip = landmarks[self.MIDDLE_TIP]
        ring_tip = landmarks[self.RING_TIP]
        pinky_tip = landmarks[self.PINKY_TIP]

        thumb_mcp = landmarks[self.THUMB_MCP]
        index_mcp = landmarks[self.INDEX_MCP]
        middle_pip = landmarks[self.MIDDLE_PIP]
        ring_pip = landmarks[self.RING_PIP]
        pinky_pip = landmarks[self.PINKY_PIP]
        wrist = landmarks[self.WRIST]

        # Store index finger tip for puzzle interaction
        self.index_finger_tip = (index_tip[0], index_tip[1])

        # Calculate pinch distance (thumb to index)
        self._pinch_distance = self._euclidean_2d(thumb_tip, index_tip)
        self._pinch_distance_history.append(self._pinch_distance)
        avg_pinch = sum(self._pinch_distance_history) / len(self._pinch_distance_history)

        # Determine finger states (extended or curled)
        fingers = self._check_fingers_extended(landmarks)

        # Gesture Classification
        gesture = config.GESTURE_NONE

        # Check thumbs up: thumb extended up, all other fingers curled
        if self._is_thumbs_up(landmarks, fingers):
            gesture = config.GESTURE_THUMBS_UP

        # Check pinch: thumb and index close together
        elif avg_pinch < 0.06:
            gesture = config.GESTURE_PINCH

        # Check point: only index finger extended
        elif fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
            gesture = config.GESTURE_POINT

        # Check fist: all fingers curled
        elif not any(fingers.values()):
            gesture = config.GESTURE_FIST

        # Check victory: index and middle extended, others curled
        elif fingers["index"] and fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
            gesture = config.GESTURE_VICTORY

        # Check open hand: all fingers extended
        elif all(fingers.values()):
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

    def _check_fingers_extended(self, landmarks):
        """Check which fingers are extended (straight)."""
        # A finger is extended if its tip is farther from wrist than its PIP joint
        wrist = landmarks[self.WRIST]

        def is_extended(tip_idx, pip_idx):
            tip = landmarks[tip_idx]
            pip = landmarks[pip_idx]
            tip_dist = self._euclidean_2d(tip, wrist)
            pip_dist = self._euclidean_2d(pip, wrist)
            return tip_dist > pip_dist

        # Thumb: compare x-distance from MCP (thumb extends sideways)
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        thumb_extended = abs(thumb_tip[0] - thumb_mcp[0]) > 0.05

        return {
            "thumb": thumb_extended,
            "index": is_extended(self.INDEX_TIP, self.INDEX_PIP),
            "middle": is_extended(self.MIDDLE_TIP, self.MIDDLE_PIP),
            "ring": is_extended(self.RING_TIP, self.RING_PIP),
            "pinky": is_extended(self.PINKY_TIP, self.PINKY_PIP),
        }

    def _is_thumbs_up(self, landmarks, fingers):
        """Detect thumbs up gesture: thumb points up, others curled."""
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        wrist = landmarks[self.WRIST]

        # Thumb should be extended upward (tip above MCP in y, since y increases downward)
        thumb_up = thumb_tip[1] < thumb_mcp[1] - 0.03
        # All other fingers curled
        others_curled = not fingers["index"] and not fingers["middle"] and not fingers["ring"] and not fingers["pinky"]

        return thumb_up and others_curled and fingers["thumb"]

    def _smooth_gesture(self):
        """Majority vote over gesture history for smoothing."""
        if not self.gesture_history:
            return config.GESTURE_NONE

        counts = {}
        for g in self.gesture_history:
            counts[g] = counts.get(g, 0) + 1

        return max(counts, key=counts.get)

    def get_pinch_distance_normalized(self):
        """Get the smoothed pinch distance as a value useful for frame sizing.

        Returns:
            float: Average pinch distance (normalized, 0-1 range roughly).
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
