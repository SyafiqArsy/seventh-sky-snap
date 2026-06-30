"""
Seventh Sky Snap - Camera Module
Manages webcam capture using OpenCV.
"""

import cv2
import numpy as np
import config


class Camera:
    """Handles webcam initialization, frame reading, and resource management."""

    def __init__(self):
        self.cap = None
        self.is_opened = False
        self.frame_width = config.CAMERA_WIDTH
        self.frame_height = config.CAMERA_HEIGHT
        self._last_frame = None

    def open(self):
        """Open the webcam and set resolution."""
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera at index {config.CAMERA_INDEX}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)

        # Read actual resolution (camera may not support requested)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.is_opened = True

    def read_frame(self):
        """Read a single frame from the webcam.

        Returns:
            numpy.ndarray: BGR frame from camera, or last successful frame on failure.
        """
        if not self.is_opened or self.cap is None:
            return None

        ret, frame = self.cap.read()
        if ret and frame is not None:
            # Flip horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            self._last_frame = frame
            return frame
        return self._last_frame

    def get_frame_rgb(self):
        """Read frame and convert to RGB (for MediaPipe compatibility).

        Returns:
            numpy.ndarray: RGB frame, or None if camera unavailable.
        """
        frame = self.read_frame()
        if frame is not None:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    def release(self):
        """Release the webcam resource."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_opened = False
        self._last_frame = None

    @property
    def resolution(self):
        """Return current camera resolution as (width, height)."""
        return (self.frame_width, self.frame_height)

    def __del__(self):
        self.release()
