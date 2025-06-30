from PySide6.QtCore import QTimer, QObject, QEvent
from gui_classes.gui_object.constante import DEBUG, SLEEP_TIMER_SECONDS

DEBUG_StandbyManager = True

class StandbyManager(QObject):
    def __init__(self, main_window):
        super().__init__()
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering __init__: args=({main_window!r})")
        self.main_window = main_window
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self._duration = SLEEP_TIMER_SECONDS
        self.timer.timeout.connect(self.set_standby)
        self._standby_enabled = True  # Flag d'activation du standby
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting __init__: return=None")

    def put_standby(self, enable: bool):
        """Active ou désactive le standby. Reset le timer si activé, stop si désactivé."""
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] put_standby({enable})")
        self._standby_enabled = bool(enable)
        if self._standby_enabled:
            self.reset_standby_timer()
        else:
            self.stop_standby_timer()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            print(f"[StandbyManager] Clic détecté sur {obj} à la position {event.pos()}")
            self.reset_standby_timer()
        return super().eventFilter(obj, event)

    def set_standby(self) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering set_standby: args=()")
        if hasattr(self.main_window, 'transition_window'):
            self.main_window.transition_window(0)
            ret = None
        else:
            print("[StandbyManager] main_window has no transition_window method!")
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
        if self._standby_enabled:
            self.timer.start(self._duration * 1000)
            if DEBUG_StandbyManager:
                print(f"[DEBUG][StandbyManager] Timer started (standby enabled)")
        else:
            if DEBUG_StandbyManager:
                print(f"[DEBUG][StandbyManager] Standby désactivé, timer non démarré")
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting start_standby_timer: return=None")

    def reset_standby_timer(self, seconds: int = None) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering reset_standby_timer: args=({seconds})")
        if not self._standby_enabled:
            if DEBUG_StandbyManager:
                print(f"[DEBUG][StandbyManager] Standby désactivé, reset ignoré")
            return
        if seconds is not None:
            self.set_timer(seconds)
        self.stop_standby_timer()
        self.start_standby_timer()
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Exiting reset_standby_timer: return=None")

    def stop_standby_timer(self) -> None:
        if DEBUG_StandbyManager:
            print(f"[DEBUG][StandbyManager] Entering stop_standby_timer: args=()")
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
