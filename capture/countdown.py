"""
Seventh Sky Snap - Countdown Timer
Manages countdown before photo capture.
"""

import time

import config


class CountdownTimer:
    """Manages a countdown sequence for photo capture."""

    def __init__(self, seconds=config.COUNTDOWN_SECONDS):
        self.total_seconds = seconds
        self.start_time = None
        self.is_active = False
        self.is_finished = False
        self.current_number = 0
        self._on_tick = None
        self._on_complete = None

    def start(self):
        """Start the countdown."""
        self.start_time = time.time()
        self.is_active = True
        self.is_finished = False
        self.current_number = self.total_seconds

    def stop(self):
        """Stop/cancel the countdown."""
        self.is_active = False
        self.is_finished = False
        self.start_time = None

    def update(self):
        """Update countdown state. Call each frame.

        Returns:
            int: Current countdown number (3, 2, 1), or 0 when finished.
        """
        if not self.is_active or self.start_time is None:
            return 0

        elapsed = time.time() - self.start_time
        remaining = self.total_seconds - elapsed

        if remaining <= 0:
            self.is_active = False
            self.is_finished = True
            self.current_number = 0
            if self._on_complete:
                self._on_complete()
            return 0

        new_number = int(remaining) + 1
        if new_number != self.current_number:
            self.current_number = new_number
            if self._on_tick:
                self._on_tick(self.current_number)

        return self.current_number

    def get_progress(self):
        """Get countdown progress as 0.0 to 1.0.

        Returns:
            float: Progress (1.0 = finished).
        """
        if self.start_time is None:
            return 0.0
        elapsed = time.time() - self.start_time
        return min(1.0, elapsed / self.total_seconds)

    def get_remaining(self):
        """Get remaining time in seconds.

        Returns:
            float: Seconds remaining.
        """
        if self.start_time is None:
            return float(self.total_seconds)
        elapsed = time.time() - self.start_time
        return max(0.0, self.total_seconds - elapsed)

    def on_tick(self, callback):
        """Register a callback for each countdown tick."""
        self._on_tick = callback

    def on_complete(self, callback):
        """Register a callback when countdown completes."""
        self._on_complete = callback

    def reset(self):
        """Reset to initial state."""
        self.stop()
        self.current_number = 0
