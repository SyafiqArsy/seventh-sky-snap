"""
Seventh Sky Snap - Image Filters
Light image filters for photo enhancement.
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def apply_vintage(image_pil, intensity=0.3):
    """Apply a subtle vintage/warm tone filter.

    Args:
        image_pil: PIL Image (RGB).
        intensity: Filter strength 0.0 to 1.0.

    Returns:
        PIL Image with vintage effect.
    """
    # Slightly warm the image
    r, g, b = image_pil.split()
    r = r.point(lambda x: min(255, int(x * (1 + intensity * 0.1))))
    b = b.point(lambda x: int(x * (1 - intensity * 0.05)))
    result = Image.merge("RGB", (r, g, b))

    # Slight contrast boost
    enhancer = ImageEnhance.Contrast(result)
    result = enhancer.enhance(1 + intensity * 0.1)

    return result


def apply_brightness(image_pil, factor=1.1):
    """Adjust image brightness.

    Args:
        image_pil: PIL Image.
        factor: Brightness multiplier (1.0 = no change).

    Returns:
        PIL Image with adjusted brightness.
    """
    enhancer = ImageEnhance.Brightness(image_pil)
    return enhancer.enhance(factor)


def apply_sharpen(image_pil, factor=1.3):
    """Sharpen the image slightly.

    Args:
        image_pil: PIL Image.
        factor: Sharpness multiplier (1.0 = no change).

    Returns:
        PIL Image with sharpening applied.
    """
    enhancer = ImageEnhance.Sharpness(image_pil)
    return enhancer.enhance(factor)


def apply_auto_enhance(image_pil):
    """Apply a default enhancement pipeline for captured photos.

    Args:
        image_pil: PIL Image (RGB).

    Returns:
        PIL Image with standard enhancements.
    """
    result = apply_brightness(image_pil, 1.05)
    result = apply_sharpen(result, 1.2)
    result = apply_vintage(result, 0.2)
    return result


def bgr_to_pil(bgr_image):
    """Convert OpenCV BGR image to PIL RGB Image.

    Args:
        bgr_image: numpy.ndarray in BGR format.

    Returns:
        PIL Image in RGB.
    """
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def pil_to_bgr(pil_image):
    """Convert PIL RGB Image to OpenCV BGR.

    Args:
        pil_image: PIL Image.

    Returns:
        numpy.ndarray in BGR format.
    """
    rgb = np.array(pil_image)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
