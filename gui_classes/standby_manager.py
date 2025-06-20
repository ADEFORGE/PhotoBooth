# standby_manager.py
from PySide6.QtCore import QTimer
from constante import DEBUG, SLEEP_TIMER_SECONDS

class StandbyManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self._duration = SLEEP_TIMER_SECONDS if 'SLEEP_TIMER_SECONDS' in globals() else 60
        self.timer.timeout.connect(self.set_standby)
        if DEBUG:
            print(f"[STANDBY_MANAGER] Initialized with duration {self._duration}s")

    def set_standby(self):
        """Passe en mode veille (retour à l'accueil/WelcomeWidget)."""
        if DEBUG:
            print("[STANDBY_MANAGER] Standby triggered: restoring WelcomeWidget")
        if hasattr(self.main_window, 'set_view'):
            self.main_window.set_view(0)
        else:
            print("[STANDBY_MANAGER] main_window has no set_view method!")

    def set_timer(self, seconds):
        self._duration = seconds
        if DEBUG:
            print(f"[STANDBY_MANAGER] Timer duration set to {self._duration}s")

    def set_timer_from_constante(self):
        from constante import SLEEP_TIMER_SECONDS
        self._duration = SLEEP_TIMER_SECONDS
        if DEBUG:
            print(f"[STANDBY_MANAGER] Timer duration set from constante: {self._duration}s")

    def start_standby_timer(self):
        if DEBUG:
            print(f"[STANDBY_MANAGER] Starting standby timer for {self._duration}s")
        self.timer.start(self._duration * 1000)

    def reset_standby_timer(self, seconds=None):
        if seconds is not None:
            self.set_timer(seconds)
        self.stop_standby_timer()
        self.start_standby_timer()

    def stop_standby_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            if DEBUG:
                print("[STANDBY_MANAGER] Standby timer stopped")

    def is_active(self):
        return self.timer.isActive()
