# Seventh Sky Snap

An interactive desktop photo experience powered by hand tracking and computer vision.

## Overview

Seventh Sky Snap combines **hand tracking**, **image processing**, and an **interactive puzzle game** into a seamless, touchless photography experience. Control the entire application using only your hand gestures detected through your webcam.

### Features

- **Hand Tracking**: Real-time hand detection using MediaPipe with 21 landmark points
- **Gesture Control**: Pinch to resize frame, thumbs up to capture
- **Polaroid Photos**: Automatic polaroid-style framing with vintage filters
- **Puzzle Game**: Solve a sliding puzzle made from your captured photo
- **Visual Effects**: Confetti, particle effects, smooth animations, and countdown timers
- **Sound Effects**: Camera shutter, countdown ticks, and victory fanfare

## Tech Stack

| Library | Purpose |
|---------|---------|
| **Python** | Main programming language |
| **OpenCV** | Webcam capture and frame processing |
| **MediaPipe** | Hand landmark detection (21 points per hand) |
| **Pillow** | Image manipulation (crop, resize, polaroid frame, filters) |
| **Pygame** | Interactive UI, rendering, animations, and puzzle mechanics |
| **NumPy** | Numerical operations for image and sound processing |

## Project Structure

```
seventh-sky-snap/
├── app.py                  # Main application entry point & state machine
├── config.py               # Central configuration constants
├── generate_assets.py      # Asset generation script (run once)
├── requirements.txt        # Python dependencies
│
├── camera/
│   └── camera.py           # Webcam capture with OpenCV
│
├── hand_tracking/
│   ├── detector.py         # MediaPipe hand detection & landmarks
│   └── gestures.py         # Gesture recognition (pinch, thumbs up, etc.)
│
├── capture/
│   ├── capture.py          # Photo capture & frame cropping
│   └── countdown.py        # Countdown timer for capture
│
├── image_processing/
│   ├── crop.py             # Image cropping & resizing utilities
│   ├── filters.py          # Image filters (vintage, sharpen, brightness)
│   └── polaroid.py         # Polaroid frame creation & saving
│
├── puzzle/
│   ├── board.py            # Puzzle board management & interaction
│   ├── generator.py        # Puzzle piece generation from polaroid
│   ├── pieces.py           # Individual puzzle piece with drag & snap
│   └── validator.py        # Puzzle completion validation
│
├── ui/
│   ├── animation.py        # Particles, transitions, easing, countdown visuals
│   └── menu.py             # All UI screens (start, camera, puzzle, result)
│
├── assets/
│   ├── frame/              # Polaroid frame overlays
│   ├── icons/              # Gesture indicator icons
│   └── sound/              # Sound effects (shutter, tick, victory)
│
└── saved/                  # Captured photos stored here
```

## State Machine

The application flows through these states:

```
idle → camera_ready → tracking → resize_mode → capture_countdown
     → image_processing → puzzle_mode → solved
     → polaroid_presentation → save_completed → idle
```

| State | Description |
|-------|-------------|
| **idle** | Start screen with "Start Camera" button |
| **camera_ready** | Camera active, waiting for hand detection |
| **tracking** | Hand detected, tracking gestures in real-time |
| **resize_mode** | Pinch gesture active, resizing capture frame |
| **capture_countdown** | 3-2-1 countdown before photo capture |
| **image_processing** | Cropping, enhancing, and creating polaroid |
| **puzzle_mode** | Drag puzzle pieces to reconstruct the photo |
| **solved** | Puzzle completed, confetti celebration |
| **polaroid_presentation** | Display final polaroid result |
| **save_completed** | Photo saved to local storage |

## Gesture Controls

| Gesture | Action |
|---------|--------|
| **Open Hand** | Default tracking state |
| **Pinch** (thumb + index) | Resize the capture frame |
| **Thumbs Up** | Trigger photo capture (hold for 0.5s) |
| **Point** (index finger) | Available for puzzle interaction |

## Setup & Installation

### Prerequisites

- Python 3.9 or higher
- Webcam connected to your computer

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/seventh-sky-snap.git
cd seventh-sky-snap

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Generate placeholder assets (run once)
python generate_assets.py

# Launch the application
python app.py
```

### Controls

- **Mouse**: Click buttons, drag puzzle pieces
- **Hand Gestures**: Control camera frame and capture
- **ESC**: Return to menu / quit application

## How It Works

1. **Start**: Launch the app and click "Start Camera"
2. **Track**: Show your hand to the webcam — the system detects 21 landmark points
3. **Frame**: Use pinch gesture (thumb + index finger) to resize the capture frame
4. **Capture**: Show thumbs up and hold for the countdown
5. **Process**: The photo is cropped, enhanced, and framed as a polaroid
6. **Puzzle**: Solve the 3x3 puzzle by dragging pieces to correct positions
7. **Celebrate**: Enjoy confetti and see your completed polaroid!
8. **Save**: Photo is saved locally in the `saved/` directory
9. **Repeat**: Start a new session or return to the main menu

## Configuration

All settings are centralized in `config.py`:

- **Window**: Resolution, FPS, title
- **Camera**: Index, resolution
- **Hand Tracking**: Detection confidence, smoothing, gesture hold time
- **Capture**: Countdown duration, cooldown between captures
- **Puzzle**: Grid size (rows × columns), snap threshold
- **Colors**: Full color palette for UI theming
- **Paths**: Asset directories, save directory

## Future Enhancements

- [ ] AI-powered filters and effects
- [ ] Multiple polaroid templates and themes
- [ ] Photo gallery with browsing
- [ ] Cloud storage integration
- [ ] Multiple puzzle difficulty levels
- [ ] Hand gesture puzzle interaction (not just mouse)
- [ ] Music and ambient sound effects
- [ ] Multi-hand gesture support

## License

This project is created for educational purposes.
