"""
Seventh Sky Snap - Main Application
State machine that orchestrates hand-tracking photo capture and puzzle game.

States:
  idle -> camera_ready -> tracking -> capture_countdown
  -> image_processing -> puzzle_mode -> solved -> polaroid_presentation
  -> idle
"""

import os
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
from image_processing.filters import apply_auto_enhance
from puzzle.board import PuzzleBoard
from ui.animation import (
    ParticleSystem, Transition, CountdownAnimation, GestureIndicator,
)
from ui.menu import StartScreen, CameraView, PuzzleView, ResultScreen


class App:
    """Main application class managing state machine and all modules."""

    def __init__(self):
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
        self.save_path = None

    def _load_sounds(self):
        """Load sound effects from assets."""
        for name, filename in {
            "shutter": "shutter.wav",
            "tick": "tick.wav",
            "victory": "victory.wav",
        }.items():
            path = os.path.join(config.SOUND_DIR, filename)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except pygame.error:
                    pass

    def _play_sound(self, name):
        if name in self.sounds:
            try:
                self.sounds[name].play()
            except pygame.error:
                pass

    # ── State Machine ────────────────────────────────────────

    def change_state(self, new_state):
        self.prev_state = self.state
        self.state = new_state
        self.state_time = 0.0

    def update_state_time(self, dt):
        """Track how long the current state has been active."""
        self.state_time += dt

    # ── Main Loop ────────────────────────────────────────────

    def run(self):
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

            if self.state == config.STATE_IDLE:
                if self.start_screen.handle_event(event):
                    self._start_camera()

            elif self.state == config.STATE_PUZZLE_MODE:
                # Mouse events still supported alongside hand gestures
                self.puzzle_board.handle_event(event)

            elif self.state in (config.STATE_SOLVED, config.STATE_POLAROID_PRESENTATION):
                result = self.result_screen.handle_event(event)
                if result == "new_session":
                    self._start_camera()
                elif result == "menu":
                    self._return_to_idle()

    def update(self, dt):
        self.update_state_time(dt)
        self.transition.update(dt)
        self.particles.update(dt)

        if self.state == config.STATE_IDLE:
            self.start_screen.update(dt)

        elif self.state == config.STATE_CAMERA_READY:
            self._update_camera_ready(dt)

        elif self.state == config.STATE_TRACKING:
            self._update_tracking(dt)

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
        self.screen.fill(config.COLOR_BG)

        if self.state == config.STATE_IDLE:
            self.start_screen.draw(self.screen)

        elif self.state in (config.STATE_CAMERA_READY, config.STATE_TRACKING,
                            config.STATE_CAPTURE_COUNTDOWN):
            self._draw_camera_state()

        elif self.state == config.STATE_IMAGE_PROCESSING:
            self._draw_processing()

        elif self.state == config.STATE_PUZZLE_MODE:
            self._draw_puzzle()

        elif self.state in (config.STATE_SOLVED, config.STATE_POLAROID_PRESENTATION,
                            config.STATE_SAVE_COMPLETED):
            self._draw_result()

        self.gesture_indicator.draw(self.screen)
        self.particles.draw(self.screen)
        self.transition.draw(self.screen)

    # ── State Handlers ───────────────────────────────────────

    def _start_camera(self):
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
            self.gesture_recognizer.update(None)
            self.hand_landmarks_px = None
            self.current_gesture = config.GESTURE_NONE
            self.gesture_indicator.update(config.GESTURE_NONE, dt)
            self.change_state(config.STATE_CAMERA_READY)
            return

        self.hand_landmarks_px = self.detector.get_landmark_pixels(
            config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        )

        gesture = self.gesture_recognizer.update(self.detector.landmarks)
        self.current_gesture = gesture
        self.gesture_indicator.update(gesture, dt)

        # Thumbs up to capture (must be held)
        if gesture == config.GESTURE_THUMBS_UP:
            if self.gesture_recognizer.gesture_held_long_enough():
                self._start_countdown()

        # Frame size from pinch
        self.frame_size += (self.target_frame_size - self.frame_size) * min(1.0, dt * 8)
        self.camera_view.set_frame_size(self.frame_size)

    def _start_countdown(self):
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
        """Capture the full camera frame."""
        if self.current_frame_bgr is None:
            self.change_state(config.STATE_TRACKING)
            return

        self._play_sound("shutter")

        # Capture full frame (no cropping)
        self.photo_capture.capture_full(self.current_frame_bgr)
        self.change_state(config.STATE_IMAGE_PROCESSING)

    def _update_image_processing(self, dt):
        if self.state_time < 0.5:
            return

        captured_pil = self.photo_capture.get_pil_image()
        if captured_pil is None:
            self.change_state(config.STATE_TRACKING)
            return

        enhanced = apply_auto_enhance(captured_pil)
        polaroid_pil = create_polaroid(enhanced)

        self.save_path = save_polaroid(polaroid_pil)

        # Convert to pygame surface
        polaroid_rgb = np.array(polaroid_pil)
        polaroid_rgb = np.rot90(polaroid_rgb)
        polaroid_rgb = np.flipud(polaroid_rgb)
        self.polaroid_surface = pygame.surfarray.make_surface(polaroid_rgb)

        # Set up puzzle
        self.puzzle_board.setup(self.polaroid_surface)
        self.puzzle_board.on_solved = self._on_puzzle_solved

        self.particles.emit_sparkle(config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT // 2, 20)
        self.change_state(config.STATE_PUZZLE_MODE)

    def _update_puzzle_mode(self, dt):
        """Update puzzle with hand tracking active."""
        # Keep reading camera for hand tracking
        self._read_camera()

        hand_x, hand_y = 0, 0
        is_grabbing = False
        hand_present = False

        if self.current_frame_rgb is not None:
            self.detector.detect(self.current_frame_rgb)
            if self.detector.hand_present:
                hand_present = True
                self.hand_landmarks_px = self.detector.get_landmark_pixels(
                    config.WINDOW_WIDTH, config.WINDOW_HEIGHT
                )
                gesture = self.gesture_recognizer.update(self.detector.landmarks)
                self.current_gesture = gesture
                self.gesture_indicator.update(gesture, dt)

                # Get index finger position as cursor
                cursor = self.gesture_recognizer.get_index_finger_pixels(
                    config.WINDOW_WIDTH, config.WINDOW_HEIGHT
                )
                if cursor:
                    hand_x, hand_y = cursor

                # Check pinch for grabbing
                is_grabbing = self.gesture_recognizer.is_pinching()
            else:
                self.gesture_recognizer.update(None)
                self.hand_landmarks_px = None
                self.current_gesture = config.GESTURE_NONE
                self.gesture_indicator.update(config.GESTURE_NONE, dt)
        else:
            self.gesture_indicator.update(config.GESTURE_NONE, dt)

        # Update puzzle board with hand data
        self.puzzle_board.update_hand(hand_x, hand_y, is_grabbing, hand_present)
        self.puzzle_board.update(dt)

    def _on_puzzle_solved(self):
        self._play_sound("victory")
        self.particles.emit_confetti(config.WINDOW_WIDTH // 2, 200, 80)
        self.change_state(config.STATE_SOLVED)

    def _update_solved(self, dt):
        self.result_screen.update(dt)
        if self.state_time > 1.5:
            self.change_state(config.STATE_POLAROID_PRESENTATION)

    def _return_to_idle(self):
        self.camera.release()
        self.photo_capture.clear()
        self.puzzle_board.reset()
        self.polaroid_surface = None
        self.save_path = None
        self.hand_landmarks_px = None
        self.current_gesture = config.GESTURE_NONE
        self.gesture_recognizer.update(None)
        self.frame_size = (config.FRAME_SIZE_MIN + config.FRAME_SIZE_MAX) // 2
        self.target_frame_size = self.frame_size
        self.change_state(config.STATE_IDLE)

    # ── Camera Helpers ───────────────────────────────────────

    def _read_camera(self):
        self.current_frame_bgr = self.camera.read_frame()
        self.current_frame_rgb = self.camera.get_frame_rgb()

    # ── Drawing Helpers ──────────────────────────────────────

    def _draw_camera_state(self):
        """Draw camera view with hand landmarks and HUD."""
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        if self.hand_landmarks_px:
            self.camera_view.draw_hand_landmarks(self.screen, self.hand_landmarks_px)

        self.camera_view.draw_hud(self.screen, self.state, self.current_gesture)

        if self.state == config.STATE_CAPTURE_COUNTDOWN:
            number = self.countdown.update()
            progress = self.countdown.get_progress()
            if number > 0:
                self.countdown_anim.update(number, (progress * config.COUNTDOWN_SECONDS) % 1.0)
                self.countdown_anim.draw(self.screen)

    def _draw_processing(self):
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        overlay = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        font = pygame.font.SysFont("arial", 32, bold=True)
        text = font.render("Processing image...", True, config.COLOR_TEXT)
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2
        self.screen.blit(text, (cx - text.get_width() // 2, cy - 20))

        for i in range(8):
            angle = self.state_time * 3 + i * (math.pi / 4)
            dx = math.cos(angle) * 40
            dy = math.sin(angle) * 40
            alpha = int(128 + 127 * math.sin(self.state_time * 5 + i))
            dot = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*config.COLOR_ACCENT[:3], alpha), (4, 4), 4)
            self.screen.blit(dot, (int(cx + dx - 4), int(cy + 30 + dy - 4)))

    def _draw_puzzle(self):
        """Draw puzzle mode: camera feed + white grid + pieces."""
        # Camera feed directly (no overlay)
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        # Hand landmarks
        if self.hand_landmarks_px:
            self.camera_view.draw_hand_landmarks(self.screen, self.hand_landmarks_px)

        # White grid on board area to show where pieces should go
        self._draw_puzzle_grid()

        # Puzzle pieces only (no board background)
        self.puzzle_board.draw(self.screen, draw_board_bg=False)

        # HUD
        solved = self.puzzle_board.get_solved_count()
        total = self.puzzle_board.get_total_count()
        self.puzzle_view.draw(self.screen, solved, total)

        # Gesture indicator
        font = pygame.font.SysFont("arial", 16)
        if self.current_gesture == config.GESTURE_PINCH:
            hint = font.render("Grabbing... move finger to place piece", True, config.COLOR_WARNING)
        elif self.current_gesture == config.GESTURE_POINT:
            hint = font.render("Pinch (thumb+index) to grab a piece", True, config.COLOR_TEXT_DIM)
        else:
            hint = font.render("Point at pieces and pinch to grab | ESC to quit", True, config.COLOR_TEXT_DIM)
        self.screen.blit(hint, (10, config.WINDOW_HEIGHT - 25))

    def _draw_puzzle_grid(self):
        """Draw white grid lines matching actual puzzle piece positions."""
        pieces = self.puzzle_board.pieces
        if not pieces:
            return

        # Find the bounding box of all correct positions
        min_x = min(p.correct_x for p in pieces)
        min_y = min(p.correct_y for p in pieces)
        max_x = max(p.correct_x + p.width for p in pieces)
        max_y = max(p.correct_y + p.height for p in pieces)

        total_w = max_x - min_x
        total_h = max_y - min_y

        grid_color = (255, 255, 255, 80)
        grid_surf = pygame.Surface((total_w, total_h), pygame.SRCALPHA)

        # Draw each piece's cell outline
        for p in pieces:
            rx = p.correct_x - min_x
            ry = p.correct_y - min_y
            pygame.draw.rect(grid_surf, grid_color, (rx, ry, p.width, p.height), 1)

        # Outer border around the whole puzzle area
        pygame.draw.rect(grid_surf, grid_color, (0, 0, total_w, total_h), 2)

        self.screen.blit(grid_surf, (min_x, min_y))

    def _draw_result(self):
        self.result_screen.draw(self.screen, self.polaroid_surface, self.save_path)

    # ── Cleanup ──────────────────────────────────────────────

    def cleanup(self):
        self.camera.release()
        self.detector.release()
        pygame.quit()


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
