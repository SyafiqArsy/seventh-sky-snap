"""
Generate placeholder assets for Seventh Sky Snap.
Run once to create default sounds, icons, and frames.
"""

import os
import struct
import wave
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FRAME_DIR = os.path.join(ASSETS_DIR, "frame")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
SOUND_DIR = os.path.join(ASSETS_DIR, "sound")
SAVED_DIR = os.path.join(BASE_DIR, "saved")


def ensure_dirs():
    for d in [FRAME_DIR, ICONS_DIR, SOUND_DIR, SAVED_DIR]:
        os.makedirs(d, exist_ok=True)


def generate_wav(filepath, frequency, duration, sample_rate=44100, volume=0.5):
    """Generate a simple sine wave WAV file."""
    n_samples = int(sample_rate * duration)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            val = int(volume * 32767 * math.sin(2 * math.pi * frequency * t))
            wf.writeframes(struct.pack("<h", val))


def generate_ascending_wav(filepath, freq_start, freq_end, duration, sample_rate=44100, volume=0.5):
    """Generate an ascending tone WAV file."""
    n_samples = int(sample_rate * duration)
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            freq = freq_start + (freq_end - freq_start) * (t / duration)
            val = int(volume * 32767 * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack("<h", val))


def generate_sounds():
    """Generate placeholder sound effects."""
    generate_wav(os.path.join(SOUND_DIR, "shutter.wav"), 1000, 0.08, volume=0.6)
    generate_wav(os.path.join(SOUND_DIR, "tick.wav"), 800, 0.05, volume=0.4)
    generate_ascending_wav(os.path.join(SOUND_DIR, "victory.wav"), 400, 900, 0.6, volume=0.5)
    print("  [OK] Sound effects generated")


def generate_gesture_icons():
    """Generate simple gesture indicator icons."""
    icons = {
        "open_hand": ("Open", (0, 200, 160)),
        "pinch": ("Pinch", (255, 180, 50)),
        "thumbs_up": ("Capture", (80, 220, 120)),
        "point": ("Point", (130, 80, 220)),
        "fist": ("Fist", (220, 80, 80)),
    }
    size = 64
    for name, (label, color) in icons.items():
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, size - 4, size - 4], fill=(*color, 180), outline=(*color, 255), width=2)
        try:
            font = ImageFont.truetype("arial.ttf", 11)
        except (IOError, OSError):
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) / 2, (size - th) / 2), label, fill=(255, 255, 255), font=font)
        img.save(os.path.join(ICONS_DIR, f"{name}.png"))
    print("  [OK] Gesture icons generated")


def generate_polaroid_frame():
    """Generate a polaroid-style frame overlay."""
    w, h = 640, 740
    border_top = 20
    border_sides = 20
    border_bottom = 80

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w - 1, h - 1], fill=(255, 255, 255, 230), outline=(200, 200, 200, 255), width=1)
    draw.rectangle(
        [border_sides, border_top, w - border_sides, h - border_bottom],
        fill=(0, 0, 0, 0),
    )
    for i in range(5):
        alpha = int(30 - i * 6)
        draw.line([(border_sides, h - border_bottom + i), (w - border_sides, h - border_bottom + i)],
                  fill=(0, 0, 0, max(0, alpha)))
    img.save(os.path.join(FRAME_DIR, "polaroid_frame.png"))
    print("  [OK] Polaroid frame generated")


def generate_gitkeep():
    """Create .gitkeep in saved directory."""
    keep_path = os.path.join(SAVED_DIR, ".gitkeep")
    if not os.path.exists(keep_path):
        with open(keep_path, "w") as f:
            pass
    print("  [OK] .gitkeep created in saved/")


def main():
    print("Seventh Sky Snap - Generating assets...")
    ensure_dirs()
    generate_sounds()
    generate_gesture_icons()
    generate_polaroid_frame()
    generate_gitkeep()
    print("All assets generated successfully!")


if __name__ == "__main__":
    main()
