from PySide6.QtCore import QTimer, QObject, QEvent
from gui_classes.gui_object.constante import DEBUG, SLEEP_TIMER_SECONDS

import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constante import DEBUG, DEBUG_FULL

DEBUG_StandbyManager = DEBUG
DEBUG_StandbyManager_FULL = DEBUG_FULL

class StandbyManager(QObject):
    def __init__(self, main_window) -> None:
        """
        Initialize the StandbyManager with the given main window.
        """
        super().__init__()
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Entering __init__: args=({main_window!r})")
        self.main_window = main_window
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self._duration = SLEEP_TIMER_SECONDS
        self.timer.timeout.connect(self.set_standby)
        self._standby_enabled = True  
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Exiting __init__: return=None")

    def put_standby(self, enable: bool) -> None:
        """
        Enable or disable standby mode. Resets or stops the timer accordingly.
        """
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] put_standby({enable})")
        self._standby_enabled = bool(enable)
        if self._standby_enabled:
            self.reset_standby_timer()
        else:
            self.stop_standby_timer()
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] put_standby: standby_enabled={self._standby_enabled}")

    def eventFilter(self, obj, event) -> bool:
        """
        Filter events to reset the standby timer on mouse press events.
        """
        if event.type() == QEvent.MouseButtonPress:
            if DEBUG_StandbyManager:
                logger.info(f"[StandbyManager] Clic détecté sur {obj} à la position {event.pos()}")
            self.reset_standby_timer()
        return super().eventFilter(obj, event)

    def set_standby(self) -> None:
        """
        Trigger the standby action if enabled, calling the main window's transition if available.
        """
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Entering set_standby: args={self._standby_enabled}")
        if self._standby_enabled:
            if DEBUG_StandbyManager:
                logger.info(f"[DEBUG][StandbyManager] Standby activé, timer expiré")
            if hasattr(self.main_window, 'transition_window'):
                self.main_window.transition_window(0)
                ret = None
            else:
                logger.info("[StandbyManager] main_window has no transition_window method!")
                ret = None
        else:
            if DEBUG_StandbyManager:
                logger.info(f"[DEBUG][StandbyManager] Standby désactivé, timer non démarré")
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Exiting set_standby: return={ret}")

    def set_timer(self, seconds: int) -> None:
        """
        Set the standby timer duration in seconds.
        """
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Entering set_timer: args=({seconds})")
        self._duration = seconds
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Exiting set_timer: return=None")

    def set_timer_from_constante(self) -> None:
        """
        Set the standby timer duration from the constant value.
        """
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Entering set_timer_from_constante: args=()")
        self._duration = SLEEP_TIMER_SECONDS
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Exiting set_timer_from_constante: return=None")

    def start_standby_timer(self) -> None:
        """
        Start the standby timer if standby is enabled.
        """
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Entering start_standby_timer: args=()")
        if self._standby_enabled:
            self.timer.start(self._duration * 1000)
            if DEBUG_StandbyManager:
                logger.info(f"[DEBUG][StandbyManager] Timer started (standby enabled)")
        else:
            if DEBUG_StandbyManager:
                logger.info(f"[DEBUG][StandbyManager] Standby désactivé, timer non démarré")
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Exiting start_standby_timer: return=None")

    def reset_standby_timer(self, seconds: int = None) -> None:
        """
        Reset the standby timer, optionally with a new duration.
        """
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Entering reset_standby_timer: args=({seconds})")
        if not self._standby_enabled:
            if DEBUG_StandbyManager:
                logger.info(f"[DEBUG][StandbyManager] Standby désactivé, reset ignoré")
            return
        if seconds is not None:
            self.set_timer(seconds)
        else:
            self.set_timer_from_constante()
        self.stop_standby_timer()
        self.start_standby_timer()
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Exiting reset_standby_timer: return=None")

    def stop_standby_timer(self) -> None:
        """
        Stop the standby timer.
        """
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Entering stop_standby_timer: args=()")
        self.timer.stop()
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Exiting stop_standby_timer: return=None")

    def is_active(self) -> bool:
        """
        Return True if the standby timer is active, otherwise False.
        """
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Entering is_active: args=()")
        result = self.timer.isActive()
        if DEBUG_StandbyManager:
            logger.info(f"[DEBUG][StandbyManager] Exiting is_active: return={result}")
        return result
