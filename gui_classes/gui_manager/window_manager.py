from typing import Optional, Callable
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QResizeEvent
from gui_classes.gui_window.main_window import MainWindow
from gui_classes.gui_window.sleepscreen_window import SleepScreenWindow
from gui_classes.gui_object.scroll_widget import ScrollOverlay

import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constante import DEBUG, DEBUG_FULL

DEBUG_TimerUpdateDisplay: bool = DEBUG
DEBUG_TimerUpdateDisplay_FULL: bool = DEBUG_FULL
DEBUG_WindowManager: bool = DEBUG
DEBUG_WindowManager_FULL: bool = DEBUG_FULL

class TimerUpdateDisplay:
    def __init__(self, window_manager: QWidget, fps: int = 60) -> None:
        """
        Initialize the TimerUpdateDisplay with a window manager and frames per second.
        """
        if DEBUG_TimerUpdateDisplay:
            logger.info(f"[DEBUG][TimerUpdateDisplay] Entering __init__: args={{'window_manager':{window_manager!r}, 'fps':{fps!r}}}")
        self.window_manager: QWidget = window_manager
        interval_ms: int = int(1000 / fps) if fps > 0 else 1000 // 60
        self._timer: QTimer = QTimer(self.window_manager)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.update_frame)
        self._timer.start()
        self._fps: int = fps if fps > 0 else 60
        self._subscribers = []  
        if DEBUG_TimerUpdateDisplay:
            logger.info(f"[DEBUG][TimerUpdateDisplay] Exiting __init__: return=None")

    def subscribe(self, func: Callable[[], None]) -> None:
        """
        Subscribe a callback function to be called on each timer tick.
        """
        if func not in self._subscribers:
            self._subscribers.append(func)
            if DEBUG_TimerUpdateDisplay:
                logger.info(f"[DEBUG][TimerUpdateDisplay] Subscribed: {func}")

    def unsubscribe(self, func: Callable[[], None]) -> None:
        """
        Unsubscribe a previously subscribed callback function.
        """
        if func in self._subscribers:
            self._subscribers.remove(func)
            if DEBUG_TimerUpdateDisplay:
                logger.info(f"[DEBUG][TimerUpdateDisplay] Unsubscribed: {func}")

    def set_fps(self, fps: int) -> None:
        """
        Set the frames per second for the timer.
        """
        if DEBUG_TimerUpdateDisplay:
            logger.info(f"[DEBUG][TimerUpdateDisplay] Entering set_fps: args={{'fps':{fps!r}}}")
        fps_value: int = fps if fps > 0 else 60
        interval_ms: int = int(1000 / fps_value)
        self._timer.setInterval(interval_ms)
        self._fps = fps_value
        if DEBUG_TimerUpdateDisplay:
            logger.info(f"[DEBUG][TimerUpdateDisplay] Exiting set_fps: return=None")

    def get_fps(self) -> int:
        """
        Get the current frames per second value.
        """
        if DEBUG_TimerUpdateDisplay:
            logger.info(f"[DEBUG][TimerUpdateDisplay] Entering get_fps: args={{}}")
        result: int = self._fps
        if DEBUG_TimerUpdateDisplay:
            logger.info(f"[DEBUG][TimerUpdateDisplay] Exiting get_fps: return={result!r}")
        return result

    def update_frame(self) -> None:
        """
        Call all subscribed callback functions for each timer tick.
        """
        if DEBUG_TimerUpdateDisplay_FULL:
            logger.info(f"[DEBUG][TimerUpdateDisplay] Entering update_frame: args={{}}")
        for func in self._subscribers:
            try:
                func()
            except Exception as e:
                if DEBUG_TimerUpdateDisplay_FULL:
                    logger.info(f"[DEBUG][TimerUpdateDisplay] Exception in subscriber {func}: {e}")
        if DEBUG_TimerUpdateDisplay_FULL:
            logger.info(f"[DEBUG][TimerUpdateDisplay] Exiting update_frame: return=None")

class WindowManager(QWidget):
    def __init__(self) -> None:
        """
        Initialize the WindowManager and set up the main application windows and overlays.
        """
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Entering __init__: args={{}}")
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.showFullScreen()
        layout: QVBoxLayout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack: QStackedWidget = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        layout.addWidget(self.stack)
        self.widgets = {
            0: SleepScreenWindow(self),
            1: MainWindow(self)
        }
        for w in self.widgets.values():
            self.stack.addWidget(w)
        self._pending_index: Optional[int] = None
        self.scroll_overlay: ScrollOverlay = ScrollOverlay(self)
        self.scroll_overlay.hide_overlay()
        self.display_timer: TimerUpdateDisplay = TimerUpdateDisplay(self, fps=20)
        
        if hasattr(self, 'scroll_overlay') and hasattr(self.scroll_overlay, 'update_frame'):
            self.display_timer.subscribe(self.scroll_overlay.update_frame)
        self.set_view(0)
        self.scroll_overlay.lower_overlay(on_lowered=lambda: self.scroll_overlay.show_overlay())

        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Exiting __init__: return=None")

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handle window resize events and update overlay geometry.
        """
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Entering resizeEvent: args={{'event':{event!r}}}")
        super().resizeEvent(event)
        if hasattr(self, 'scroll_overlay') and self.scroll_overlay:
            self.scroll_overlay.setGeometry(0, 0, self.width(), self.height())
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Exiting resizeEvent: return=None")

    def start(self) -> None:
        """
        Show the main window in full screen mode.
        """
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Entering start: args={{}}")
        self.showFullScreen()
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Exiting start: return=None")

    def set_view(self, index: int) -> None:
        """
        Set the current view to the widget at the given index.
        """
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Entering set_view: args={{'index':{index!r}}}")
        new_widget = self.widgets[index]
        self.stack.setCurrentWidget(new_widget)
        self.showFullScreen()
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Exiting set_view: return=None")

    def transition_window(self, index: int) -> None:
        """
        Transition to a different window, handling animations and callbacks.
        """
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Entering transition_window: args={{'index':{index!r}}}")
        current_index = self.stack.currentIndex()
        if index != current_index:
            new_widget = self.widgets[index]
            if hasattr(new_widget, 'preset'):
                if DEBUG_WindowManager:
                    logger.info(f"[DEBUG][WindowManager] Calling preset on {type(new_widget).__name__}")
                new_widget.preset()
            current_widget = self.stack.currentWidget()
            if hasattr(current_widget, 'on_leave'):
                if DEBUG_WindowManager:
                    logger.info(f"[DEBUG][WindowManager] Calling on_leave on {type(current_widget).__name__}")
                current_widget.on_leave()
            if DEBUG_WindowManager:
                logger.info(f"[DEBUG][WindowManager] Calling raise_overlay on scroll_overlay")
            self.scroll_overlay.raise_overlay()
            if DEBUG_WindowManager:
                logger.info(f"[DEBUG][WindowManager] Calling set_view({index})")
            self.set_view(index)
            new_widget = self.stack.currentWidget()
            if hasattr(new_widget, 'on_enter'):
                if DEBUG_WindowManager:
                    logger.info(f"[DEBUG][WindowManager] Calling scroll_animation({index}, on_enter of {type(new_widget).__name__})")
                self.scroll_animation(index, new_widget.on_enter)
            else:
                if DEBUG_WindowManager:
                    logger.info(f"[DEBUG][WindowManager] Calling scroll_animation({index}) (no on_enter)")
                self.scroll_animation(index)
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Exiting transition_window: return=None")

    def scroll_animation(self, index: int, callback: Optional[Callable[[], None]] = None) -> None:
        """
        Perform a scroll animation when switching views, with an optional
        """
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Entering scroll_animation: args={{'index':{index!r}, 'callback':{callback!r}}}")
        if index == 1:
            if DEBUG_WindowManager:
                logger.info(f"[DEBUG][WindowManager] scroll_animation: index==1, starting scroll animation with stop_speed=30")
            self.display_timer.set_fps(80)
            self.scroll_overlay.start_scroll_animation(
                stop_speed=30,
                on_finished=lambda: self.scroll_overlay.hide_overlay(
                    on_hidden=lambda: self.scroll_overlay.clean_scroll(
                        on_cleaned=lambda: (
                            callback() if callback else None,
                            
                            self.display_timer.unsubscribe(self.scroll_overlay.update_frame) if hasattr(self.display_timer, 'unsubscribe') and hasattr(self.scroll_overlay, 'update_frame') else None
                        )
                    )
                )
            )
            if callback:
                if DEBUG_WindowManager:
                    logger.info(f"[DEBUG][WindowManager] scroll_animation: index==1, calling callback directement après animation trigger")
                callback()
        elif index == 0:
            if DEBUG_WindowManager:
                logger.info(f"[DEBUG][WindowManager] scroll_animation: index==0, restart scroll animation")
                
            if hasattr(self.display_timer, 'subscribe') and hasattr(self.scroll_overlay, 'update_frame'):
                self.display_timer.subscribe(self.scroll_overlay.update_frame)
            self.scroll_overlay.restart_scroll_animation(
                start_speed=30,
                on_finished=lambda: (
                    (callback() if callback else None),
                    self.display_timer.set_fps(20)
                )
            )
        if DEBUG_WindowManager:
            logger.info(f"[DEBUG][WindowManager] Exiting scroll_animation: return=None")
