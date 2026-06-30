"""
Seventh Sky Snap - Photo Capture
Handles photo capture logic: cropping frame area and saving.
"""

import os
import time

import cv2
import numpy as np
from PIL import Image

import config


class PhotoCapture:
    """Manages the photo capture process."""

    def __init__(self):
        self.captured_image = None  # BGR numpy array of cropped photo
        self.captured_pil = None    # PIL Image of cropped photo
        self.capture_time = 0
        self.cooldown = config.CAPTURE_COOLDOWN
        self.frame_rect = None      # (x, y, w, h) of the capture frame

    def can_capture(self):
        """Check if enough time has passed since last capture."""
        return (time.time() - self.capture_time) >= self.cooldown

    def set_frame_rect(self, x, y, w, h):
        """Set the capture frame rectangle (from hand tracking resize)."""
        self.frame_rect = (x, y, w, h)

    def capture(self, frame_bgr):
        """Capture a photo by cropping the frame area.

        Args:
            frame_bgr: The current camera frame (BGR, already flipped).

        Returns:
            numpy.ndarray: The cropped image, or None on failure.
        """
        if frame_bgr is None or self.frame_rect is None:
            return None

        if not self.can_capture():
            return None

        x, y, w, h = self.frame_rect
        fh, fw = frame_bgr.shape[:2]

        # Clamp to frame bounds
        x = max(0, min(x, fw - 1))
        y = max(0, min(y, fh - 1))
        w = max(10, min(w, fw - x))
        h = max(10, min(h, fh - y))

        # Crop the image
        cropped = frame_bgr[y:y + h, x:x + w].copy()

        self.captured_image = cropped
        self.captured_pil = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
        self.capture_time = time.time()

        return cropped

    def save_temp(self, filename=None):
        """Save captured image to the saved directory.

        Args:
            filename: Optional filename. If None, uses timestamp.

        Returns:
            str: Path to saved file, or None.
        """
        if self.captured_image is None:
            return None

        os.makedirs(config.SAVED_DIR, exist_ok=True)

        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.png"

        filepath = os.path.join(config.SAVED_DIR, filename)
        cv2.imwrite(filepath, self.captured_image)
        return filepath

    def get_pil_image(self):
        """Get captured image as PIL Image."""
        return self.captured_pil

    def clear(self):
        """Clear captured image data."""
        self.captured_image = None
        self.captured_pil = None
        self.frame_rect = None

    @staticmethod
    def compute_frame_rect(center_x, center_y, frame_size, cam_width, cam_height):
        """Compute a centered frame rectangle given center and size.

        Args:
            center_x: Center X of the frame.
            center_y: Center Y of the frame.
            frame_size: Width/height of the square frame.
            cam_width: Camera frame width.
            cam_height: Camera frame height.

        Returns:
            tuple (x, y, w, h) clamped to camera bounds.
        """
        half = frame_size // 2
        x = center_x - half
        y = center_y - half
        w = frame_size
        h = frame_size

        # Clamp
        x = max(0, min(x, cam_width - w))
        y = max(0, min(y, cam_height - h))

        return (x, y, w, h)
