from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from gui_classes.photobooth import PhotoBooth
from gui_classes.sleepscreen_window import SleepScreenWindow
from gui_classes.background_manager import BackgroundManager
from constante import WINDOW_STYLE, DEBUG
import sys

DEBUG_WindowManager = False

class WindowManager(QWidget):
    def __init__(self) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering __init__: args={{}}")
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.background_manager = BackgroundManager()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        layout.addWidget(self.stack)
        self.widgets = {
            0: SleepScreenWindow(self),
            1: PhotoBooth(self)
        }
        for w in self.widgets.values():
            self.stack.addWidget(w)
        self._pending_index = None
        self.set_view(0, initial=True)
        self.background_manager.start_scroll(self, on_started=None)
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting __init__: return=None")

    def set_view(self, index: int, initial: bool = False) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering set_view: args={{'index':{index}, 'initial':{initial}}}")
        if not initial:
            current = self.stack.currentWidget()
            if hasattr(current, 'on_leave'):
                current.on_leave()
            if hasattr(current, 'cleanup'):
                current.cleanup()
        new_widget = self.widgets[index]
        self.stack.setCurrentWidget(new_widget)
        self.showFullScreen()
        if hasattr(new_widget, 'on_enter'):
            new_widget.on_enter()
        if index == 0:
            self.background_manager.start_scroll(self)
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting set_view: return=None")

    def start(self) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering start: args={{}}")
        self.showFullScreen()
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting start: return=None")

    def start_change_view(self, index: int = 0, callback=None) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering start_change_view: args={{'index':{index}, 'callback':{callback}}}")
        current_index = self.stack.currentIndex()
        if index == current_index or index not in self.widgets:
            if DEBUG_WindowManager:
                print(f"[DEBUG][WindowManager] Exiting start_change_view: return=None")
            return
        self._pending_index = index
        self.background_manager.stop_scroll(set_view=lambda: self.set_view(index))
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting start_change_view: return=None")

    def resizeEvent(self, event: QResizeEvent) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering resizeEvent: args={{'event':{event}}}")
        super().resizeEvent(event)
        if hasattr(self.background_manager, 'scroll_overlay') and self.background_manager.scroll_overlay:
            self.background_manager.scroll_overlay.setGeometry(0, 0, self.width(), self.height())
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting resizeEvent: return=None")
