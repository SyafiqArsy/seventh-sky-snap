"""
Seventh Sky Snap - Image Cropping
Handles cropping and resizing of captured images.
"""

import cv2
import numpy as np
from PIL import Image

import config


def crop_to_square(image):
    """Crop an image to a square from the center.

    Args:
        image: numpy.ndarray (BGR) or PIL Image.

    Returns:
        numpy.ndarray: Square-cropped image.
    """
    if isinstance(image, Image.Image):
        image = np.array(image)
        if image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        else:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    h, w = image.shape[:2]
    size = min(h, w)

    start_x = (w - size) // 2
    start_y = (h - size) // 2

    return image[start_y:start_y + size, start_x:start_x + size].copy()


def resize_to_fit(image, max_width, max_height):
    """Resize an image to fit within max dimensions while preserving aspect ratio.

    Args:
        image: numpy.ndarray (BGR) or PIL Image.
        max_width: Maximum width.
        max_height: Maximum height.

    Returns:
        numpy.ndarray: Resized image.
    """
    if isinstance(image, Image.Image):
        image = np.array(image)
        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        elif len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    h, w = image.shape[:2]
    scale = min(max_width / w, max_height / h)

    if scale >= 1.0:
        return image

    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def crop_center_region(image, cx, cy, width, height):
    """Crop a centered region from an image.

    Args:
        image: numpy.ndarray (BGR).
        cx: Center X coordinate.
        cy: Center Y coordinate.
        width: Crop width.
        height: Crop height.

    Returns:
        numpy.ndarray: Cropped region, clamped to image bounds.
    """
    h, w = image.shape[:2]
    half_w = width // 2
    half_h = height // 2

    x1 = max(0, cx - half_w)
    y1 = max(0, cy - half_h)
    x2 = min(w, x1 + width)
    y2 = min(h, y1 + height)

    return image[y1:y2, x1:x2].copy()
