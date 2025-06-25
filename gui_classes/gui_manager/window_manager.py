from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QApplication
from PySide6.QtGui import QResizeEvent
from PySide6.QtCore import Qt, QTimer
from gui_classes.gui_window.main_window import MainWindow
from gui_classes.gui_window.sleepscreen_window import SleepScreenWindow
from gui_classes.gui_object.scroll_widget import ScrollOverlay
from gui_classes.gui_object.constante import WINDOW_STYLE, DEBUG
import sys

DEBUG_WindowManager = False

class TimerUpdateDisplay:
    def __init__(self, window_manager, interval_ms=1000 // 60):
        self.window_manager = window_manager
        self._timer = QTimer()
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.update_frame)
        self._timer.start()

    def update_frame(self):
        wm = self.window_manager
        # Met à jour le scroll overlay si visible
        if hasattr(wm, 'scroll_overlay') and wm.scroll_overlay.isVisible():
            wm.scroll_overlay.update_frame()
        # Met à jour la caméra du PhotoBooth si visible
        current_widget = wm.stack.currentWidget()
        if hasattr(current_widget, 'background_manager'):
            current_widget.background_manager.update_camera_frame()

class WindowManager(QWidget):
    def __init__(self) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering __init__: args={{}}")
        super().__init__()
        self.setWindowTitle("PhotoBooth")
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        layout.addWidget(self.stack)
        self.widgets = {
            0: SleepScreenWindow(self),
            1: MainWindow(self)
        }
        for w in self.widgets.values():
            self.stack.addWidget(w)
        self._pending_index = None
        # Création de l'overlay de scroll, caché au démarrage
        self.scroll_overlay = ScrollOverlay(self)
        self.scroll_overlay.hide_overlay()
        self.set_view(0, initial=True)
        self.display_timer = TimerUpdateDisplay(self)
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting __init__: return=None")

    def set_view(self, index: int, initial: bool = False, callback=None) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering set_view: args={{'index':{index}, 'initial':{initial}, 'callback':{callback}}}")
        new_widget = self.widgets[index]
        self.stack.setCurrentWidget(new_widget)
        self.showFullScreen()
        if hasattr(new_widget, 'on_enter'):
            new_widget.on_enter()
        if index == 0:
            # Affiche l'overlay de scroll en fond
            self.scroll_overlay.lower_overlay(on_lowered=lambda: self.scroll_overlay.show_overlay(on_shown=callback))
        if callback:
            callback()
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
        # Nouvelle logique : overlay devant, set_view, animation, hide, clean
        def after_set_view():
            print(f"[DEBUG][WindowManager] Exiting after_set_view")
            self.scroll_overlay.start_scroll_animation(
                stop_speed=30,
                on_finished=lambda: self.scroll_overlay.hide_overlay(
                    on_hidden=lambda: self.scroll_overlay.clean_scroll(
                        on_cleaned=callback
                    )
                )
            )
        self.scroll_overlay.raise_overlay(
            on_raised=lambda: self.set_view(index, callback=after_set_view)
        )
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting start_change_view: return=None")

    def resizeEvent(self, event: QResizeEvent) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering resizeEvent: args={{'event':{event}}}")
        super().resizeEvent(event)
        if hasattr(self, 'scroll_overlay') and self.scroll_overlay:
            self.scroll_overlay.setGeometry(0, 0, self.width(), self.height())
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting resizeEvent: return=None")
