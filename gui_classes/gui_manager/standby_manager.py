from PySide6.QtCore import QTimer
from gui_classes.gui_object.constante import DEBUG, SLEEP_TIMER_SECONDS

DEBUG_StandbyManager = True

class StandbyManager:
    def __init__(self, main_window):
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering __init__: args=({main_window!r})")
        self.main_window = main_window
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self._duration = SLEEP_TIMER_SECONDS
        self.timer.timeout.connect(self.set_standby)
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting __init__: return=None")

    def set_standby(self) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering set_standby: args=()")
        if hasattr(self.main_window, 'set_view'):
            self.main_window.set_view(0)
            ret = None
        else:
            print("[StandbyManager] main_window has no set_view method!")
            ret = None
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting set_standby: return={ret}")

    def set_timer(self, seconds: int) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering set_timer: args=({seconds})")
        self._duration = seconds
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting set_timer: return=None")

    def set_timer_from_constante(self) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering set_timer_from_constante: args=()")
        self._duration = SLEEP_TIMER_SECONDS
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting set_timer_from_constante: return=None")

    def start_standby_timer(self) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering start_standby_timer: args=()")
        self.timer.start(self._duration * 1000)
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting start_standby_timer: return=None")

    def reset_standby_timer(self, seconds: int = None) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering reset_standby_timer: args=({seconds})")
        if seconds is not None:
            self.set_timer(seconds)
        self.stop_standby_timer()
        self.start_standby_timer()
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting reset_standby_timer: return=None")

    def stop_standby_timer(self) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering stop_standby_timer: args=()")
        if self.timer.isActive():
            self.timer.stop()
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting stop_standby_timer: return=None")

    def is_active(self) -> bool:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering is_active: args=()")
        result = self.timer.isActive()
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting is_active: return={result}")
        return result
