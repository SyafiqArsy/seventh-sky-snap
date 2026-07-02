"""
Seventh Sky Snap - Main Application
State machine that orchestrates hand-tracking photo capture and puzzle game.

Flow:
  idle (camera on, show instructions)
  -> frame_creation (both hands pinching, frame corners follow hands)
  -> capture_countdown (both open palms, frame locked, countdown)
  -> image_processing -> puzzle_mode -> solved
  -> polaroid_presentation -> interactive_polaroid -> save_completed -> idle
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
    ShutterFlash, PolaroidReveal, PuzzleBorderFade,
)
from ui.menu import CameraView, PuzzleView, ResultScreen, StatusBar, InfoPanel
from ui.polaroid_interaction import PolaroidInteraction


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
        self.camera_view = CameraView()
        self.puzzle_view = PuzzleView()
        self.result_screen = ResultScreen()
        self.particles = ParticleSystem()
        self.transition = Transition()
        self.countdown_anim = CountdownAnimation()
        self.gesture_indicator = GestureIndicator()
        self.status_bar = StatusBar()
        self.info_panel_left = InfoPanel("left")
        self.info_panel_right = InfoPanel("right")
        self.shutter_flash = ShutterFlash()
        self.polaroid_reveal = PolaroidReveal()
        self.puzzle_border_fade = PuzzleBorderFade()
        self.polaroid_interaction = PolaroidInteraction()

        # ── Sound ──
        self.sounds = {}
        self._load_sounds()

        # ── Camera data ──
        self.current_frame_bgr = None
        self.current_frame_rgb = None
        self.hand_landmarks_px = None
        self.current_gesture = config.GESTURE_NONE

        # ── Frame corners (smoothed pixel coords) ──
        # Left hand controls top-left, right hand controls bottom-right
        self._frame_x1 = 0.0
        self._frame_y1 = 0.0
        self._frame_x2 = 0.0
        self._frame_y2 = 0.0
        self._target_x1 = 0.0
        self._target_y1 = 0.0
        self._target_x2 = 0.0
        self._target_y2 = 0.0

        # ── Capture ──
        self.polaroid_surface = None
        self._raw_photo_surface = None
        self.save_path = None
        self._frozen_frame = None
        self._freeze_duration = 0.5

        # ── Two-hand tracking ──
        self._left_hand_landmarks = None
        self._right_hand_landmarks = None
        self._both_pinching = False
        self._both_open = False

        # ── FPS tracking ──
        self._fps = 0
        self._fps_timer = 0
        self._fps_count = 0

        # Auto-start camera
        self._start_camera()

    # ── Sound ─────────────────────────────────────────────────

    def _load_sounds(self):
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

    # ── State Machine ─────────────────────────────────────────

    def change_state(self, new_state):
        self.prev_state = self.state
        self.state = new_state
        self.state_time = 0.0

    # ── Main Loop ─────────────────────────────────────────────

    def run(self):
        try:
            while self.running:
                dt = self.clock.tick(config.FPS) / 1000.0
                self._update_fps(dt)
                self.handle_events()
                self.update(dt)
                self.draw()
                pygame.display.flip()
        finally:
            self.cleanup()

    def _update_fps(self, dt):
        self._fps_count += 1
        self._fps_timer += dt
        if self._fps_timer >= 1.0:
            self._fps = self._fps_count
            self._fps_count = 0
            self._fps_timer -= 1.0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in (config.STATE_PUZZLE_MODE, config.STATE_SOLVED,
                                      config.STATE_POLAROID_PRESENTATION,
                                      config.STATE_INTERACTIVE_POLAROID):
                        self._return_to_idle()
                    else:
                        self.running = False
                    return

            elif self.state == config.STATE_PUZZLE_MODE:
                self.puzzle_board.handle_event(event)

            elif self.state in (config.STATE_SOLVED, config.STATE_POLAROID_PRESENTATION):
                result = self.result_screen.handle_event(event)
                if result == "new_session":
                    self._return_to_idle()
                elif result == "menu":
                    self._return_to_idle()

    def update(self, dt):
        self.state_time += dt
        self.transition.update(dt)
        self.particles.update(dt)
        self.shutter_flash.update(dt)
        self.camera_view.update_frame_animation(dt)

        if self.state == config.STATE_IDLE:
            self._update_idle(dt)

        elif self.state == config.STATE_FRAME_CREATION:
            self._update_frame_creation(dt)

        elif self.state == config.STATE_CAPTURE_COUNTDOWN:
            self._update_capture_countdown(dt)

        elif self.state == config.STATE_IMAGE_PROCESSING:
            self._update_image_processing(dt)

        elif self.state == config.STATE_PUZZLE_MODE:
            self._update_puzzle_mode(dt)

        elif self.state == config.STATE_SOLVED:
            self._update_solved(dt)

        elif self.state == config.STATE_POLAROID_PRESENTATION:
            self._update_polaroid_presentation(dt)

        elif self.state == config.STATE_INTERACTIVE_POLAROID:
            self._update_interactive_polaroid(dt)

        elif self.state == config.STATE_SAVE_COMPLETED:
            if self.state_time > 2.0:
                self._return_to_idle()

    def draw(self):
        self.screen.fill(config.COLOR_BG)

        # Camera states: idle, frame_creation, capture_countdown
        if self.state in (config.STATE_IDLE, config.STATE_FRAME_CREATION,
                          config.STATE_CAPTURE_COUNTDOWN):
            self._draw_camera_state()

        elif self.state == config.STATE_IMAGE_PROCESSING:
            self._draw_processing()

        elif self.state == config.STATE_PUZZLE_MODE:
            self._draw_puzzle()

        elif self.state in (config.STATE_SOLVED, config.STATE_POLAROID_PRESENTATION):
            self._draw_result()

        elif self.state == config.STATE_SAVE_COMPLETED:
            self._draw_save_completed()

        elif self.state == config.STATE_INTERACTIVE_POLAROID:
            self._draw_interactive_polaroid()

        # Global overlays
        self.shutter_flash.draw(self.screen)
        self.gesture_indicator.draw(self.screen)
        self.particles.draw(self.screen)
        self.transition.draw(self.screen)

    # ── Camera Startup ────────────────────────────────────────

    def _start_camera(self):
        try:
            self.camera.open()
        except RuntimeError as e:
            print(f"Camera error: {e}")
            return
        self.change_state(config.STATE_IDLE)

    # ── State: IDLE ───────────────────────────────────────────
    # Camera on, show instructions, wait for two hands.

    def _update_idle(self, dt):
        self._read_camera()
        if self.current_frame_rgb is None:
            return

        self.detector.detect(self.current_frame_rgb)
        hand_count = len(self.detector.all_hands) if self.detector.hand_present else 0

        if self.detector.hand_present:
            self.hand_landmarks_px = self.detector.get_landmark_pixels(
                config.WINDOW_WIDTH, config.WINDOW_HEIGHT
            )
        else:
            self.hand_landmarks_px = None

        # Need two hands to proceed
        if hand_count >= 2:
            self.change_state(config.STATE_FRAME_CREATION)

    # ── State: FRAME CREATION ─────────────────────────────────
    # Both hands detected. If both pinch → frame corners follow hands.

    def _update_frame_creation(self, dt):
        self._read_camera()
        if self.current_frame_rgb is None:
            return

        self.detector.detect(self.current_frame_rgb)
        hand_count = len(self.detector.all_hands) if self.detector.hand_present else 0

        # Lost hands → back to idle
        if hand_count < 2:
            self.hand_landmarks_px = None
            self._both_pinching = False
            self.camera_view.hide_frame()
            self.change_state(config.STATE_IDLE)
            return

        self.hand_landmarks_px = self.detector.get_landmark_pixels(
            config.WINDOW_WIDTH, config.WINDOW_HEIGHT
        )

        # Identify left and right hands (MediaPipe mirrors: 'Right' = user's left)
        left_hand = self.detector.get_hand_by_label('Right')
        right_hand = self.detector.get_hand_by_label('Left')

        if left_hand is None or right_hand is None:
            return

        # Check gestures for each hand
        left_gesture = self._classify_hand_gesture(left_hand['landmarks'])
        right_gesture = self._classify_hand_gesture(right_hand['landmarks'])

        self._both_pinching = (left_gesture == config.GESTURE_PINCH
                               and right_gesture == config.GESTURE_PINCH)
        self._both_open = (left_gesture == config.GESTURE_OPEN_HAND
                           and right_gesture == config.GESTURE_OPEN_HAND)

        # Get index finger tip positions for each hand (frame corners)
        left_index = left_hand['landmarks'][8]   # INDEX_TIP
        right_index = right_hand['landmarks'][8]

        # Convert to pixel coords
        li_x = int(left_index[0] * config.WINDOW_WIDTH)
        li_y = int(left_index[1] * config.WINDOW_HEIGHT)
        ri_x = int(right_index[0] * config.WINDOW_WIDTH)
        ri_y = int(right_index[1] * config.WINDOW_HEIGHT)

        if self._both_pinching:
            # Frame corners follow index fingers with smoothing
            self._target_x1 = li_x
            self._target_y1 = li_y
            self._target_x2 = ri_x
            self._target_y2 = ri_y

            # Smooth interpolation
            s = config.FRAME_SMOOTH_FACTOR
            self._frame_x1 += (self._target_x1 - self._frame_x1) * s
            self._frame_y1 += (self._target_y1 - self._frame_y1) * s
            self._frame_x2 += (self._target_x2 - self._frame_x2) * s
            self._frame_y2 += (self._target_y2 - self._frame_y2) * s

            # Ensure minimum frame size
            if abs(self._frame_x2 - self._frame_x1) > config.FRAME_MIN_SIZE and \
               abs(self._frame_y2 - self._frame_y1) > config.FRAME_MIN_SIZE:
                self.camera_view.set_frame_corners(
                    int(self._frame_x1), int(self._frame_y1),
                    int(self._frame_x2), int(self._frame_y2)
                )

        elif self._both_open:
            # Both open palms → lock frame and start countdown
            if self.camera_view.frame_visible:
                # Lock the current frame position
                self.camera_view.set_frame_corners(
                    int(self._frame_x1), int(self._frame_y1),
                    int(self._frame_x2), int(self._frame_y2)
                )
                self._start_countdown()

    def _classify_hand_gesture(self, landmarks):
        """Quick gesture classification for a single hand.

        Returns GESTURE_PINCH or GESTURE_OPEN_HAND or GESTURE_NONE.
        """
        if landmarks is None or len(landmarks) < 21:
            return config.GESTURE_NONE

        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        index_pip = landmarks[6]
        middle_tip = landmarks[12]
        middle_pip = landmarks[10]
        ring_tip = landmarks[16]
        ring_pip = landmarks[14]
        pinky_tip = landmarks[20]
        pinky_pip = landmarks[18]

        # Pinch: thumb and index tips close
        dist = math.sqrt((thumb_tip[0] - index_tip[0]) ** 2 +
                         (thumb_tip[1] - index_tip[1]) ** 2)
        if dist < config.PINCH_GRAB_THRESHOLD:
            return config.GESTURE_PINCH

        # Open hand: all fingers extended
        all_extended = (
            index_tip[1] < index_pip[1] - 0.02
            and middle_tip[1] < middle_pip[1] - 0.02
            and ring_tip[1] < ring_pip[1] - 0.02
            and pinky_tip[1] < pinky_pip[1] - 0.02
        )
        if all_extended:
            return config.GESTURE_OPEN_HAND

        return config.GESTURE_NONE

    # ── State: CAPTURE COUNTDOWN ──────────────────────────────
    # Frame locked, both open palms held, countdown 3-2-1.

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

    # ── Capture & Processing ──────────────────────────────────

    def _capture_photo(self):
        """Capture the region inside the frame from the camera."""
        if self.current_frame_bgr is None:
            self.change_state(config.STATE_IDLE)
            return

        self._play_sound("shutter")
        self._frozen_frame = self.current_frame_bgr.copy()
        self.shutter_flash.trigger()

        # Crop the frame area from the camera image
        fh, fw = self.current_frame_bgr.shape[:2]
        win_w, win_h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT

        # Scale frame pixel coords back to camera coords
        scale_x = fw / win_w
        scale_h = fh / win_h

        x1 = max(0, int(min(self._frame_x1, self._frame_x2) * scale_x))
        y1 = max(0, int(min(self._frame_y1, self._frame_y2) * scale_h))
        x2 = min(fw, int(max(self._frame_x1, self._frame_x2) * scale_x))
        y2 = min(fh, int(max(self._frame_y1, self._frame_y2) * scale_h))

        if x2 - x1 < 10 or y2 - y1 < 10:
            # Frame too small, capture full frame as fallback
            self.photo_capture.capture_full(self.current_frame_bgr)
        else:
            cropped = self.current_frame_bgr[y1:y2, x1:x2].copy()
            self.photo_capture.captured_image = cropped
            self.photo_capture.captured_pil = __import__('PIL', fromlist=['Image']).Image.fromarray(
                cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
            )
            self.photo_capture.capture_time = __import__('time').time()

        self.change_state(config.STATE_IMAGE_PROCESSING)

    def _update_image_processing(self, dt):
        if self.state_time < self._freeze_duration:
            return

        captured_pil = self.photo_capture.get_pil_image()
        if captured_pil is None:
            self.change_state(config.STATE_IDLE)
            return

        enhanced = apply_auto_enhance(captured_pil)

        # Create polaroid for final result
        polaroid_pil = create_polaroid(enhanced)
        self.save_path = save_polaroid(polaroid_pil)

        # Convert polaroid to pygame surface
        polaroid_rgb = np.array(polaroid_pil)
        polaroid_rgb = np.rot90(polaroid_rgb)
        polaroid_rgb = np.flipud(polaroid_rgb)
        self.polaroid_surface = pygame.surfarray.make_surface(polaroid_rgb)

        # Convert RAW photo to pygame surface (for puzzle)
        raw_rgb = np.array(enhanced)
        raw_rgb = np.rot90(raw_rgb)
        raw_rgb = np.flipud(raw_rgb)
        self._raw_photo_surface = pygame.surfarray.make_surface(raw_rgb)

        # Set up puzzle using RAW photo
        self.puzzle_board.setup(self._raw_photo_surface)
        self.puzzle_board.on_solved = self._on_puzzle_solved

        self.camera_view.hide_frame()
        self.particles.emit_sparkle(config.WINDOW_WIDTH // 2, config.WINDOW_HEIGHT // 2, 20)
        self.change_state(config.STATE_PUZZLE_MODE)

    # ── State: PUZZLE MODE ────────────────────────────────────

    def _update_puzzle_mode(self, dt):
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

                cursor = self.gesture_recognizer.get_index_finger_pixels(
                    config.WINDOW_WIDTH, config.WINDOW_HEIGHT
                )
                if cursor:
                    hand_x, hand_y = cursor

                is_grabbing = self.gesture_recognizer.is_pinching()
            else:
                self.gesture_recognizer.update(None)
                self.hand_landmarks_px = None
                self.current_gesture = config.GESTURE_NONE
                self.gesture_indicator.update(config.GESTURE_NONE, dt)
        else:
            self.gesture_indicator.update(config.GESTURE_NONE, dt)

        self.puzzle_board.update_hand(hand_x, hand_y, is_grabbing, hand_present)
        self.puzzle_board.update(dt)
        self.puzzle_border_fade.update(dt)

    # ── State: SOLVED → POLAROID → INTERACTIVE ────────────────

    def _on_puzzle_solved(self):
        self._play_sound("victory")
        self.particles.emit_confetti(config.WINDOW_WIDTH // 2, 200, 80)
        self.puzzle_border_fade.start()
        self.change_state(config.STATE_SOLVED)

    def _update_solved(self, dt):
        self.result_screen.update(dt)
        self.puzzle_border_fade.update(dt)

        if self.state_time > 1.5:
            if not self.polaroid_reveal.active and self.polaroid_surface:
                self.polaroid_reveal.start(self.polaroid_surface)
                self._play_sound("shutter")
                self.shutter_flash.trigger()
            self.change_state(config.STATE_POLAROID_PRESENTATION)

    def _update_polaroid_presentation(self, dt):
        self.polaroid_reveal.update(dt)

        if self.polaroid_reveal.is_complete and self.state_time > 3.0:
            self._start_interactive_polaroid()

    def _start_interactive_polaroid(self):
        self.polaroid_interaction.start(self.polaroid_surface)
        self.change_state(config.STATE_INTERACTIVE_POLAROID)

    def _update_interactive_polaroid(self, dt):
        self._read_camera()

        wrist_x = None
        gesture = config.GESTURE_NONE

        if self.current_frame_rgb is not None:
            self.detector.detect(self.current_frame_rgb)
            if self.detector.hand_present:
                self.hand_landmarks_px = self.detector.get_landmark_pixels(
                    config.WINDOW_WIDTH, config.WINDOW_HEIGHT
                )

                # Use single-hand gesture detection
                gesture = self.gesture_recognizer.update(self.detector.landmarks)
                self.current_gesture = gesture

                # Get wrist position for rotation tracking
                if len(self.detector.landmarks) >= 21:
                    wrist = self.detector.landmarks[0]
                    wrist_x = wrist[0]
            else:
                self.hand_landmarks_px = None
                self.gesture_recognizer.update(None)
                gesture = config.GESTURE_NONE
                self.current_gesture = config.GESTURE_NONE

        # Update polaroid with single-hand data; fist triggers save
        save_triggered = self.polaroid_interaction.update_with_hand(
            dt, wrist_x, gesture
        )

        if save_triggered:
            saved = self.polaroid_interaction.save_result()
            if saved:
                self.save_path = saved
            self.polaroid_interaction.stop()
            self.change_state(config.STATE_SAVE_COMPLETED)

    # ── Return to Idle ────────────────────────────────────────

    def _return_to_idle(self):
        self.camera.release()
        self.photo_capture.clear()
        self.puzzle_board.reset()
        self.polaroid_surface = None
        self._raw_photo_surface = None
        self.save_path = None
        self.hand_landmarks_px = None
        self.current_gesture = config.GESTURE_NONE
        self.gesture_recognizer.update(None)
        self.gesture_recognizer.reset_two_hand()
        self._frozen_frame = None
        self._left_hand_landmarks = None
        self._right_hand_landmarks = None
        self._both_pinching = False
        self._both_open = False
        self._frame_x1 = self._frame_y1 = 0
        self._frame_x2 = self._frame_y2 = 0
        self.camera_view.hide_frame()
        self.polaroid_interaction.reset()
        self.polaroid_reveal.stop()
        self.puzzle_border_fade.active = False

        # Re-open camera and go to idle
        self._start_camera()

    # ── Camera Helpers ────────────────────────────────────────

    def _read_camera(self):
        self.current_frame_bgr = self.camera.read_frame()
        self.current_frame_rgb = self.camera.get_frame_rgb()

    # ── Drawing Helpers ───────────────────────────────────────

    def _draw_camera_state(self):
        """Draw camera view with hand landmarks, frame, and instructions."""
        # Camera feed
        if self._frozen_frame is not None and self.state == config.STATE_IMAGE_PROCESSING:
            self.camera_view.draw_camera_frame(self.screen, self._frozen_frame)
        elif self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        # Animation tick
        self.camera_view.update_animation(1.0 / config.FPS)

        # Hand landmarks
        if self.hand_landmarks_px:
            alpha = 170 if self.state != config.STATE_CAPTURE_COUNTDOWN else 150
            self.camera_view.draw_hand_landmarks(self.screen, self.hand_landmarks_px, alpha=alpha)

        # Frame overlay (only when visible)
        self.camera_view.draw_frame_overlay(self.screen)

        # Instructions for idle / frame creation
        hand_count = len(self.detector.all_hands) if self.detector.hand_present else 0
        self.camera_view.draw_instructions(self.screen, self.state, hand_count)

        # Status bar
        countdown_num = 0
        if self.state == config.STATE_CAPTURE_COUNTDOWN:
            countdown_num = self.countdown.current_number
        self.status_bar.update(self.state, 1.0 / config.FPS, countdown_num)
        self.status_bar.draw(self.screen)

        # Info panels
        gesture_name = self.current_gesture.replace("_", " ").title()
        if self.current_gesture == config.GESTURE_NONE:
            gesture_name = "None"

        self.info_panel_left.update([
            f"Gesture: {gesture_name}",
            f"Hands: {hand_count} Detected",
            f"Frame: {'Visible' if self.camera_view.frame_visible else 'Hidden'}",
        ])
        self.info_panel_left.draw(self.screen)

        self.info_panel_right.update([
            f"FPS: {self._fps}",
            f"Resolution: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT}",
        ])
        self.info_panel_right.draw(self.screen)

        # Countdown animation
        if self.state == config.STATE_CAPTURE_COUNTDOWN:
            number = self.countdown.update()
            progress = self.countdown.get_progress()
            if number > 0:
                self.countdown_anim.update(number, (progress * config.COUNTDOWN_SECONDS) % 1.0)
                self.countdown_anim.draw(self.screen)

    def _draw_processing(self):
        if self._frozen_frame is not None:
            self.camera_view.draw_camera_frame(self.screen, self._frozen_frame)
        elif self.current_frame_bgr is not None:
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
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        if self.hand_landmarks_px:
            self.camera_view.draw_hand_landmarks(self.screen, self.hand_landmarks_px, alpha=170)

        self._draw_puzzle_grid()
        self.puzzle_board.draw(self.screen, draw_board_bg=False)

        self.status_bar.update(self.state, 1.0 / config.FPS)
        self.status_bar.draw(self.screen)

        solved = self.puzzle_board.get_solved_count()
        total = self.puzzle_board.get_total_count()
        self.puzzle_view.draw(self.screen, solved, total)

        gesture_name = self.current_gesture.replace("_", " ").title()
        if self.current_gesture == config.GESTURE_NONE:
            gesture_name = "None"
        hand_count = len(self.detector.all_hands) if self.detector.hand_present else 0
        self.info_panel_left.update([
            f"Gesture: {gesture_name}",
            f"Hands: {hand_count} Detected",
            f"Progress: {solved}/{total}",
        ])
        self.info_panel_left.draw(self.screen)

        self.info_panel_right.update([f"FPS: {self._fps}"])
        self.info_panel_right.draw(self.screen)

        font = pygame.font.SysFont("arial", 16)
        if self.current_gesture == config.GESTURE_PINCH:
            hint = font.render("Grabbing... move finger to place piece", True, config.COLOR_WARNING)
        elif self.current_gesture == config.GESTURE_POINT:
            hint = font.render("Pinch (thumb+index) to grab a piece", True, config.COLOR_TEXT_DIM)
        else:
            hint = font.render("Point at pieces and pinch to grab | ESC to quit", True, config.COLOR_TEXT_DIM)
        self.screen.blit(hint, (10, config.WINDOW_HEIGHT - 25))

    def _draw_puzzle_grid(self):
        pieces = self.puzzle_board.pieces
        if not pieces:
            return

        min_x = min(p.correct_x for p in pieces)
        min_y = min(p.correct_y for p in pieces)
        max_x = max(p.correct_x + p.width for p in pieces)
        max_y = max(p.correct_y + p.height for p in pieces)

        total_w = max_x - min_x
        total_h = max_y - min_y

        grid_color = (255, 255, 255, 80)
        grid_surf = pygame.Surface((total_w, total_h), pygame.SRCALPHA)

        for p in pieces:
            rx = p.correct_x - min_x
            ry = p.correct_y - min_y
            pygame.draw.rect(grid_surf, grid_color, (rx, ry, p.width, p.height), 1)

        pygame.draw.rect(grid_surf, grid_color, (0, 0, total_w, total_h), 2)
        self.screen.blit(grid_surf, (min_x, min_y))

    def _draw_result(self):
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        if self.puzzle_border_fade.active:
            self.puzzle_board.draw(self.screen, draw_board_bg=False)

        self.polaroid_reveal.draw(self.screen)

        if not self.polaroid_reveal.active:
            self.result_screen.draw(self.screen, self.polaroid_surface, self.save_path)

    def _draw_interactive_polaroid(self):
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        if self.hand_landmarks_px:
            self.camera_view.draw_hand_landmarks(self.screen, self.hand_landmarks_px, alpha=150)

        self.polaroid_interaction.draw(self.screen)

        self.status_bar.update(self.state, 1.0 / config.FPS)
        self.status_bar.draw(self.screen)

        self.polaroid_interaction.draw_status(self.screen, self.current_gesture)

    def _draw_save_completed(self):
        if self.current_frame_bgr is not None:
            self.camera_view.draw_camera_frame(self.screen, self.current_frame_bgr)

        font = pygame.font.SysFont("arial", 36, bold=True)
        text = font.render("Photo Saved!", True, config.COLOR_SUCCESS)
        cx = config.WINDOW_WIDTH // 2
        cy = config.WINDOW_HEIGHT // 2

        pad = 20
        bg_rect = pygame.Rect(cx - text.get_width() // 2 - pad,
                               cy - text.get_height() // 2 - pad,
                               text.get_width() + pad * 2,
                               text.get_height() + pad * 2)
        bg_surf = pygame.Surface((bg_rect.w, bg_rect.h), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 150))
        self.screen.blit(bg_surf, bg_rect.topleft)
        self.screen.blit(text, (cx - text.get_width() // 2, cy - text.get_height() // 2))

        self.status_bar.update(self.state, 1.0 / config.FPS)
        self.status_bar.draw(self.screen)

    # ── Cleanup ───────────────────────────────────────────────

    def cleanup(self):
        self.camera.release()
        self.detector.release()
        pygame.quit()


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
