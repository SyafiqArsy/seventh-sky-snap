"""
Seventh Sky Snap - Main Application
State machine that orchestrates hand-tracking photo capture and puzzle game.

States:
  idle -> camera_ready -> tracking -> resize_mode -> capture_countdown
  -> image_processing -> puzzle_mode -> solved -> polaroid_presentation
  -> save_completed -> idle
"""

import os
import sys
import time
import math

import cv2
import numpy as np
import pygame

import config
from camera.camera import Camera
from hand_tracking.detector import HandDetector
from hand_tracking.gestures import GestureRecognizer
from capture.capture import PhotoCapture
from capture.countdown import CountdownTimer
from image_processing.polaroid import create_polaroid, save_polaroid
from image_processing.filters import apply_auto_enhance, bgr_to_pil
from puzzle.board import PuzzleBoard
from ui.animation import (
    ParticleSystem, Transition, CountdownAnimation, GestureIndicator,
)
from ui.menu import StartScreen, CameraView, PuzzleView, ResultScreen


class App:
    """Main application class managing state machine and all modules."""

    def __init__(self):
        # ── Pygame Setup ──
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT))
        pygame.display.set_caption(config.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # ── State ──
        self.state = config.STATE_IDLE
        self.prev_state = None
        self.state_time = 0.0

        # ── Modules ──
        self.camera = Camera()
        self.detector = HandDetector()
        self.gesture_recognizer = GestureRecognizer()
        self.photo_capture = PhotoCapture()
        self.countdown = CountdownTimer()
        self.puzzle_board = PuzzleBoard()

        # ── UI Components ──
        self.start_screen = StartScreen()
        self.camera_view = CameraView()
        self.puzzle_view = PuzzleView()
        self.result_screen = ResultScreen()
        self.particles = ParticleSystem()
        self.transition = Transition()
        self.countdown_anim = CountdownAnimation()
        self.gesture_indicator = GestureIndicator()

        # ── Sound ──
        self.sounds = {}
        self._load_sounds()

        # ── Data ──
        self.current_frame_bgr = None
        self.current_frame_rgb = None
        self.hand_landmarks_px = None
        self.current_gesture = config.GESTURE_NONE
        self.frame_size = (config.FRAME_SIZE_MIN + config.FRAME_SIZE_MAX) // 2
        self.target_frame_size = self.frame_size
        self.polaroid_surface = None
        self.polaroid_path = None
        self.save_path = None

    def _load_sounds(self):
        """Load sound effects from assets."""
        sound_files = {
            "shutter": "shutter.wav",
            "tick": "tick.wav",
            "victory": "victory.wav",
        }
        for name, filename in sound_files.items():
            path = os.path.join(config.SOUND_DIR, filename)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except pygame.error:
                    pass

    def _play_sound(self, name):
        """Play a loaded sound effect."""
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except pygame.error:
                pass

    # ── State Machine ────────────────────────────────────────

    def change_state(self, new_state):
        """Transition to a new state."""
        self.prev_state = self.state
        self.state = new_state
        self.state_time = 0.0

    def update_state_time(self, dt):
        self.state_time += dt

    # ── Main Loop ────────────────────────────────────────────

    def run(self):
        """Main application loop."""
        try:
            while self.running:
                dt = self.clock.tick(config.FPS) / 1000.0
                self.handle_events()
                self.update(dt)
                self.draw()
                pygame.display.flip()
        finally:
            self.cleanup()

    def handle_events(self):
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in (config.STATE_PUZZLE_MODE, config.STATE_SOLVED,
                                      config.STATE_POLAROID_PRESENTATION):
                        self._return_to_idle()
                    else:
                        self.running = False
                    return

            # State-specific event handling
            if self.state == config.STATE_IDLE:
                if self.start_screen.handle_event(event):
                    self._start_camera()

            elif self.state == config.STATE_PUZZLE_MODE:
                self.puzzle_board.handle_event(event)

            elif self.state in (config.STATE_SOLVED, config.STATE_POLAROID_PRESENTATION):
                result = self.result_screen.handle_event(event)
                if result == "new_session":
                    self._start_camera()
                elif result == "menu":
                    self._return_to_idle()

    def update(self, dt):
        """Update current state logic."""
        self.update_state_time(dt)
        self.transition.update(dt)
        self.particles.update(dt)

        if self.state == config.STATE_IDLE:
            self.start_screen.update(dt)

        elif self.state == config.STATE_CAMERA_READY:
            self._update_camera_ready(dt)

        elif self.state == config.STATE_TRACKING:
            self._update_tracking(dt)

        elif self.state == config.STATE_RESIZE_MODE:
            self._update_resize_mode(dt)

        elif self.state == config.STATE_CAPTURE_COUNTDOWN:
            self._update_capture_countdown(dt)

        elif self.state == config.STATE_IMAGE_PROCESSING:
            self._update_image_processing(dt)

        elif self.state == config.STATE_PUZZLE_MODE:
            self._update_puzzle_mode(dt)

        elif self.state == config.STATE_SOLVED:
            self._update_solved(dt)

        elif self.state == config.STATE_POLAROID_PRESENTATION:
            self.result_screen.update(dt)

    def draw(self):
        """Render current state."""
        self.screen.fill(config.COLOR_BG)

        if self.state == config.STATE_IDLE:
            self.start_screen.draw(self.screen)

        elif self.state in (config.STATE_CAMERA_READY, config.STATE_TRACKING,
                            config.STATE_RESIZE_MODE, config.STATE_CAPTURE_COUNTDOWN):
            self._draw_camera_state()

        elif self.state == config.STATE_IMAGE_PROCESSING:
            self._draw_processing()

        elif self.state == config.STATE_PUZZLE_MODE:
            self._draw_puzzle()

        elif self.state in (config.STATE_SOLVED, config.STATE_POLAROID_PRESENTATION,
                            config.STATE_SAVE_COMPLETED):
            self._draw_result()

        # Overlays
        self.gesture_indicator.draw(self.screen)
        self.particles.draw(self.screen)
        self.transition.draw(self.screen)

    # ── State Handlers ───────────────────────────────────────

    def _start_camera(self):
        """Initialize camera and transition to camera_ready."""
        try:
            self.camera.open()
        except RuntimeError as e:
            print(f"Camera error: {e}")
            return
        self.change_state(config.STATE_CAMERA_READY)

    def _update_camera_ready(self, dt):
        self._read_camera()
        if self.current_frame_rgb is not None:
            self.detector.detect(self.current_frame_rgb)
            if self.detector.hand_present:
                self.change_state(config.STATE_TRACKING)

    def _update_tracking(self, dt):
        self._read_camera()
        if self.current_frame_rgb is None:
            return

        self.detector.detect(self.current_frame_rgb)
        if not self.detector.hand_present:
            self.change_state(config.STATE_CAMERA_READY)
            return

        # Get landmarks
        self.hand_landmarks_px = self.detector.get_landmark_pixels(
            config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        )

        # Gesture recognition
        gesture = self.gesture_recognizer.update(self.detector.landmarks)
        self.current_gesture = gesture
        self.gesture_indicator.update(gesture, dt)

        # Pinch to resize
        if gesture == config.GESTURE_PINCH:
            pinch_dist = self.gesture_recognizer.get_pinch_distance_normalized()
            # Map normalized pinch distance to frame size
            normalized = (pinch_dist - 0.01) / (0.12 - 0.01)
            normalized = max(0.0, min(1.0, normalized))
            self.target_frame_size = int(
                config.FRAME_SIZE_MIN + normalized * (config.FRAME_SIZE_MAX - config.FRAME_SIZE_MIN)
            )
            if self.state != config.STATE_RESIZE_MODE:
                self.change_state(config.STATE_RESIZE_MODE)

        # Thumbs up to capture
        elif gesture == config.GESTURE_THUMBS_UP:
            if self.gesture_recognizer.gesture_held_long_enough():
                self._start_countdown()

        # Smooth frame size interpolation
        self.frame_size += (self.target_frame_size - self.frame_size) * min(1.0, dt * 8)
        self.camera_view.set_frame_size(self.frame_size)

    def _update_resize_mode(self, dt):
        self._read_camera()
        if self.current_frame_rgb is None:
            return

        self.detector.detect(self.current_frame_rgb)
        if not self.detector.hand_present:
            self.change_state(config.STATE_CAMERA_READY)
            return

        self.hand_landmarks_px = self.detector.get_landmark_pixels(
            config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        )

        gesture = self.gesture_recognizer.update(self.detector.landmarks)
        self.current_gesture = gesture
        self.gesture_indicator.update(gesture, dt)

        if gesture == config.GESTURE_PINCH:
            pinch_dist = self.gesture_recognizer.get_pinch_distance_normalized()
            normalized = (pinch_dist - 0.01) / (0.12 - 0.01)
            normalized = max(0.0, min(1.0, normalized))
            self.target_frame_size = int(
                config.FRAME_SIZE_MIN + normalized * (config.FRAME_SIZE_MAX - config.FRAME_SIZE_MIN)
            )
        else:
            # Pinch released, return to tracking
            self.change_state(config.STATE_TRACKING)

        # Smooth interpolation
        self.frame_size += (self.target_frame_size - self.frame_size) * min(1.0, dt * 8)
        self.camera_view.set_frame_size(self.frame_size)

    def _start_countdown(self):
        """Start the capture countdown."""
        self.change_state(config.STATE_CAPTURE_COUNTDOWN)
        self.countdown.start()
        self._play_sound("tick")

    def _update_capture_countdown(self, dt):
        self._read_camera()
        if self.current_frame_rgb is not None:
            self.detector.detect(self.current_frame_rgb)
            self.hand_landmarks_px = self.detector.get_landmark_pixels(
                config.WINDOW_WIDTH, config.WINDOW_HEIGHT
            )
            self.gesture_indicator.update(config.GESTURE_NONE, dt)

        self.countdown.update()

        if self.countdown.is_finished:
            self._capture_photo()

    def _capture_photo(self):
        """Capture the photo and transition to image processing."""
        if self.current_frame_bgr is None:
            self.change_state(config.STATE_TRACKING)
            return

        self._play_sound("shutter")

        # Scale frame rect from window coords to camera coords
        fx, fy, fw, fh = self.camera_view.get_frame_rect()
        cam_w, cam_h = self.camera.resolution
        scale_x = cam_w / config.WINDOW_WIDTH
        scale_y = cam_h / config.WINDOW_HEIGHT

        cam_fx = int(fx * scale_x)
        cam_fy = int(fy * scale_y)
        cam_fw = int(fw * scale_x)
        cam_fh = int(fh * scale_y)

        self.photo_capture.set_frame_rect(cam_fx, cam_fy, cam_fw, cam_fh)
        cropped = self.photo_capture.capture(self.current_frame_bgr)

        if cropped is None:
            self.change_state(config.STATE_TRACKING)
            return

        self.change_state(config.STATE_IMAGE_PROCESSING)

    def _update_image_processing(self, dt):
        """Process captured image into polaroid and set up puzzle."""
        # Brief delay for visual feedback
        if self.state_time < 0.5:
            return

        # Create polaroid
        captured_pil = self.photo_capture.get_pil_image()
        if captured_pil is None:
            self.change_state(config.STATE_TRACKING)
            return

        # Apply enhancements
        enhanced = apply_auto_enhance(captured_pil)
        polaroid_pil = create_polaroid(enhanced)

        # Save polaroid
        self.save_path = save_polaroid(polaroid_pil)

        # Convert to pygame surface
        polaroid_rgb = np.array(polaroid_pil)
        polaroid_rgb = np.rot90(polaroid_rgb)
        polaroid_rgb = np.flipud(polaroid_rgb)
        self.polaroid_surface = pygame.surfarray.make_surface(polaroid_rgb)

        # Set up puzzle
        self.puzzle_board.setup(self.polaroid_surface)
        self.puzzle_board.on_solved = self._on_puzzle_solved

        # Flash effect
        self.particles.emit_sparkle(config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT // 2, 20)

        self.change_state(config.STATE_PUZZLE_MODE)

    def _update_puzzle_mode(self, dt):
        self.puzzle_board.update(dt)

    def _on_puzzle_solved(self):
        """Callback when puzzle is completed."""
        self._play_sound("victory")
        self.particles.emit_confetti(config.WINDOW_WIDTH // 2, 200, 80)
        self.change_state(config.STATE_SOLVED)

    def _update_solved(self, dt):
        self.result_screen.update(dt)
        # Auto-transition to presentation after animation
        if self.state_time > 1.5:
            self.change_state(config.STATE_POLAROID_PRESENTATION)

    def _return_to_idle(self):
        """Return to idle/start screen."""
        self.camera.release()
        self.photo_capture.clear()
        self.puzzle_board.reset()
        self.polaroid_surface = None
        self.polaroid_path = None
        self.save_path = None
        self.hand_landmarks_px = None
        self.current_gesture = config.GESTURE_NONE
        self.frame_size = (config.FRAME_SIZE_MIN + config.FRAME_SIZE_MAX) // 2
        self.target_frame_size = self.frame_size
        self.change_state(config.STATE_IDLE)

    # ── Camera Helpers ───────────────────────────────────────

    def _read_camera(self):
        """Read a frame from the camera."""
        self.current_frame_bgr = self.camera.read_frame()
        self.current_frame_rgb = self.camera.get_frame_rgb()

    # ── Drawing Helpers ──────────────────────────────────────

    def _draw_camera_state(self):
        """Draw camera view with overlays."""
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        # Hand landmarks
        if self.hand_landmarks_px:
            self.camera_view.draw_hand_landmarks(self.screen, self.hand_landmarks_px)

        # Frame overlay
        self.camera_view.draw_frame_overlay(self.screen)

        # HUD
        self.camera_view.draw_hud(
            self.screen, self.state, self.current_gesture
        )

        # Countdown overlay
        if self.state == config.STATE_CAPTURE_COUNTDOWN:
            number = self.countdown.update()
            progress = self.countdown.get_progress()
            if number > 0:
                self.countdown_anim.update(number, (progress * config.COUNTDOWN_SECONDS) % 1.0)
                self.countdown_anim.draw(self.screen)

    def _draw_processing(self):
        """Draw image processing state."""
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        # Processing overlay
        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        font = pygame.font.SysFont("arial", 32, bold=True)
        text = font.render("Processing image...", True, config.COLOR_TEXT)
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.screen.blit(text, (cx - text.get_width() // 2, cy - 20))

        # Spinning dots
        for i in range(8):
            angle = self.state_time * 3 + i * (math.pi / 4)
            dx = math.cos(angle) * 40
            dy = math.sin(angle) * 40
            alpha = int(128 + 127 * math.sin(self.state_time * 5 + i))
            dot = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*config.COLOR_ACCENT[:3], alpha), (4, 4), 4)
            self.screen.blit(dot, (int(cx + dx - 4), int(cy + 30 + dy - 4)))

    def _draw_puzzle(self):
        """Draw puzzle mode."""
        # Background
        self.screen.fill(config.COLOR_PUZZLE_BG)

        # Puzzle board and pieces
        self.puzzle_board.draw(self.screen)

        # Puzzle view overlay
        solved = self.puzzle_board.get_solved_count()
        total = self.puzzle_board.get_total_count()
        self.puzzle_view.draw(self.screen, solved, total)

        # Instructions
        font = pygame.font.SysFont("arial", 16)
        hint = font.render("ESC to quit", True, config.COLOR_TEXT_DIM)
        self.screen.blit(hint, (10, config.WINDOW_HEIGHT - 25))

    def _draw_result(self):
        """Draw result/polaroid presentation screen."""
        self.result_screen.draw(self.screen, self.polaroid_surface, self.save_path)

    # ── Cleanup ──────────────────────────────────────────────

    def cleanup(self):
        """Release all resources."""
        self.camera.release()
        self.detector.release()
        pygame.quit()


def main():
    """Entry point."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
