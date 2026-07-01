# Seventh Sky Snap

An interactive desktop photo experience powered by hand tracking and computer vision.

## Overview

Seventh Sky Snap combines **hand tracking**, **image processing**, and an **interactive puzzle game** into a seamless, touchless photography experience. Control the entire application using only your hand gestures detected through your webcam.

### Features

- **Hand Tracking**: Real-time hand detection using MediaPipe with 21 landmark points per hand
- **Two-Hand Detection**: Simultaneous tracking of both hands for interactive polaroid manipulation
- **Gesture Control**: Pinch to resize frame, thumbs up to capture
- **Polaroid Photos**: Automatic polaroid-style framing with vintage filters
- **Puzzle Game**: Solve a sliding puzzle made from your captured photo
- **Interactive Polaroid Mode**: After solving the puzzle, manipulate the polaroid with two hands — move, rotate, and scale
- **Premium UI**: Dashed frame lines, transparent hand skeleton, dynamic status bar, info panels
- **Visual Effects**: Shutter flash, confetti, particle effects, smooth animations, and countdown timers
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
│   ├── animation.py        # Particles, transitions, easing, shutter flash, polaroid reveal
│   ├── menu.py             # All UI screens (start, camera, puzzle, result, status bar, info panels)
│   └── polaroid_interaction.py  # Interactive polaroid mode with two-hand gestures
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
idle (camera on, show instructions)
  → frame_creation (both pinching, frame corners follow hands)
  → capture_countdown (both open palms, frame locked, countdown)
  → image_processing → puzzle_mode → solved
  → polaroid_presentation → interactive_polaroid
  → save_completed → idle
```

| State | Description |
|-------|-------------|
| **idle** | Camera active, "Show both hands to begin" — waiting for two hands |
| **frame_creation** | Both hands pinching — frame corners follow left/right hand positions |
| **capture_countdown** | Both open palms detected — frame locked, 3-2-1 countdown |
| **image_processing** | Camera freeze, crop frame area, enhance, create polaroid |
| **puzzle_mode** | Drag puzzle pieces (raw photo) to reconstruct the image |
| **solved** | Puzzle completed, border fade animation, confetti celebration |
| **polaroid_presentation** | Polaroid slides up from bottom with reveal animation |
| **interactive_polaroid** | Two-hand mode: move, rotate, and scale the polaroid |
| **save_completed** | Photo saved, "Photo Saved!" notification |

## Gesture Controls

### Camera / Frame Creation Mode

| Gesture | Action |
|---------|--------|
| **Show both hands** | Enter frame creation mode |
| **Both hands pinch** | Create and adjust capture frame — left hand = top-left corner, right hand = bottom-right corner |
| **Both hands open palm** | Lock frame and start 3-2-1 countdown |

### Puzzle Mode

| Gesture | Action |
|---------|--------|
| **Point** (index finger) | Move cursor over puzzle pieces |
| **Pinch** (thumb + index) | Grab and drag a puzzle piece |

### Interactive Polaroid Mode (Two Hands)

| Gesture | Action |
|---------|--------|
| **Move both hands** | Translate/move the polaroid on screen |
| **Tilt hands** (angle between hands) | Rotate the polaroid |
| **Spread/close hands** | Scale the polaroid larger/smaller |

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

1. **Launch**: App opens with camera active, showing "Show both hands to begin"
2. **Detect**: Show both hands to the webcam — system detects 21 landmark points per hand
3. **Frame**: Pinch with both hands — left hand controls top-left corner, right hand controls bottom-right corner. The frame follows your fingers in real-time
4. **Capture**: Open both palms to lock the frame — 3-2-1 countdown starts
5. **Crop & Process**: Camera captures and crops the frame area, enhances the photo, creates a polaroid version
6. **Puzzle**: Solve the 3x3 puzzle using the raw photo pieces scattered around the screen
7. **Celebrate**: Puzzle borders fade, confetti explodes, polaroid slides up from below
8. **Interact**: Use both hands to move, rotate, and scale the polaroid in free space
9. **Save**: After 5 seconds of inactivity, the polaroid returns to center and saves automatically
10. **Repeat**: ESC to return and start a new session

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
- [x] Hand gesture puzzle interaction (not just mouse)
- [ ] Music and ambient sound effects
- [x] Multi-hand gesture support (Interactive Polaroid Mode)

## License

This project is created for educational purposes.
