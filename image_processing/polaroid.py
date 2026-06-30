"""
Seventh Sky Snap - Polaroid Frame
Creates polaroid-style framed photos.
"""

import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config
from image_processing.crop import resize_to_fit


def create_polaroid(photo_pil, output_width=None, output_height=None):
    """Create a polaroid-framed image from a photo.

    The photo is placed inside a white polaroid border with extra space
    at the bottom for captions.

    Args:
        photo_pil: PIL Image (RGB) of the captured photo.
        output_width: Optional output width. Defaults to config value.
        output_height: Optional output height. Defaults to config value.

    Returns:
        PIL Image: Polaroid-framed photo.
    """
    border_top = config.POLAROID_BORDER_TOP
    border_sides = config.POLAROID_BORDER_SIDES
    border_bottom = config.POLAROID_BORDER_BOTTOM
    bg_color = config.POLAROID_BG_COLOR

    if output_width is None:
        output_width = config.OUTPUT_MAX_WIDTH
    if output_height is None:
        output_height = config.OUTPUT_MAX_HEIGHT

    # Calculate available space for the photo
    photo_max_w = output_width - 2 * border_sides
    photo_max_h = output_height - border_top - border_bottom

    # Resize photo to fit within the available area
    photo_resized = photo_pil.copy()
    photo_resized.thumbnail((photo_max_w, photo_max_h), Image.LANCZOS)

    pw, ph = photo_resized.size

    # Create the polaroid canvas
    polaroid = Image.new("RGB", (output_width, output_height), bg_color)
    draw = ImageDraw.Draw(polaroid)

    # Center the photo within the border area
    photo_x = (output_width - pw) // 2
    photo_y = border_top

    # Paste the photo
    polaroid.paste(photo_resized, (photo_x, photo_y))

    # Draw subtle shadow below photo
    shadow_y = photo_y + ph
    for i in range(4):
        alpha_color = tuple(max(0, c - 30 - i * 10) for c in bg_color)
        draw.line(
            [(border_sides, shadow_y + i), (output_width - border_sides, shadow_y + i)],
            fill=alpha_color,
        )

    # Add a subtle border around the photo
    draw.rectangle(
        [photo_x - 1, photo_y - 1, photo_x + pw, photo_y + ph],
        outline=(200, 200, 200),
        width=1,
    )

    return polaroid


def save_polaroid(polaroid_pil, filename=None):
    """Save a polaroid image to the saved directory.

    Args:
        polaroid_pil: PIL Image.
        filename: Optional filename. Uses timestamp if None.

    Returns:
        str: Path to saved file.
    """
    import time

    os.makedirs(config.SAVED_DIR, exist_ok=True)

    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"polaroid_{timestamp}.png"

    filepath = os.path.join(config.SAVED_DIR, filename)
    polaroid_pil.save(filepath, "PNG")
    return filepath


def create_polaroid_from_bgr(bgr_image, output_width=None, output_height=None):
    """Convenience: create polaroid directly from a BGR numpy image.

    Args:
        bgr_image: numpy.ndarray in BGR format.
        output_width: Optional output width.
        output_height: Optional output height.

    Returns:
        PIL Image: Polaroid-framed photo.
    """
    rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    photo_pil = Image.fromarray(rgb)
    return create_polaroid(photo_pil, output_width, output_height)
