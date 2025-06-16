# timer_sleep.py
from PySide6.QtCore import QTimer
from constante import DEBUG, SLEEP_TIMER_SECONDS

class TimerSleep:
    def __init__(self, main_window, callback=None):
        """
        main_window: the QMainWindow or main widget to control
        callback: optional function to call when timer triggers (defaults to self.restore_welcome)
        """
        self.main_window = main_window
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self._duration = SLEEP_TIMER_SECONDS if 'SLEEP_TIMER_SECONDS' in globals() else 60
        self._callback = callback if callback else self.restore_welcome
        self.timer.timeout.connect(self._callback)
        if DEBUG:
            print(f"[TIMER_SLEEP] Initialized with duration {self._duration}s")

    def restore_welcome(self):
        """Restore the main window to the WelcomeWidget view."""
        if DEBUG:
            print("[TIMER_SLEEP] Timer triggered: restoring WelcomeWidget")
        if hasattr(self.main_window, 'set_view'):
            self.main_window.set_view(0)  # 0 = WelcomeWidget (convention)

    def set_timer(self, seconds):
        """Set the timer duration in seconds."""
        self._duration = seconds
        if DEBUG:
            print(f"[TIMER_SLEEP] Timer duration set to {self._duration}s")

    def set_timer_from_constante(self):
        """Set the timer duration from constante.py (SLEEP_TIMER_SECONDS)."""
        from constante import SLEEP_TIMER_SECONDS
        self._duration = SLEEP_TIMER_SECONDS
        if DEBUG:
            print(f"[TIMER_SLEEP] Timer duration set from constante: {self._duration}s")

    def start(self):
        """Start the timer with the current duration."""
        if DEBUG:
            print(f"[TIMER_SLEEP] Starting timer for {self._duration}s")
        self.timer.start(self._duration * 1000)

    def set_and_start(self, seconds=None):
        """Set the timer (optionally with a new duration) and start it."""
        if seconds is not None:
            self.set_timer(seconds)
        self.start()

    def stop(self):
        """Stop the timer if running."""
        if self.timer.isActive():
            self.timer.stop()
            if DEBUG:
                print("[TIMER_SLEEP] Timer stopped")

    def is_active(self):
        return self.timer.isActive()
