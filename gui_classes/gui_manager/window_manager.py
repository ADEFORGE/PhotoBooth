from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QResizeEvent
from gui_classes.gui_window.main_window import MainWindow
from gui_classes.gui_window.sleepscreen_window import SleepScreenWindow
from gui_classes.gui_object.scroll_widget import ScrollOverlay

DEBUG_TimerUpdateDisplay = False
DEBUG_WindowManager = False

class TimerUpdateDisplay:
    def __init__(self, window_manager: QWidget, fps: int = 60) -> None:
        if DEBUG_TimerUpdateDisplay:
            print(f"[DEBUG][TimerUpdateDisplay] Entering __init__: args={{'window_manager':{window_manager}, 'fps':{fps}}}")
        self.window_manager = window_manager
        interval_ms = int(1000 / fps) if fps > 0 else 1000 // 60
        self._timer = QTimer(self.window_manager)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self.update_frame)
        self._timer.start()
        self._fps = fps if fps > 0 else 60
        if DEBUG_TimerUpdateDisplay:
            print(f"[DEBUG][TimerUpdateDisplay] Exiting __init__: return=None")

    def set_fps(self, fps: int) -> None:
        """
        Change dynamiquement le nombre de FPS du timer d'affichage.
        """
        if fps <= 0:
            fps = 60
        interval_ms = int(1000 / fps)
        self._timer.setInterval(interval_ms)
        self._fps = fps
        if DEBUG_TimerUpdateDisplay:
            print(f"[DEBUG][TimerUpdateDisplay] FPS changed to {fps} (interval {interval_ms} ms)")

    def get_fps(self) -> int:
        """
        Retourne le FPS courant du timer.
        """
        return self._fps

    def update_frame(self) -> None:
        if DEBUG_TimerUpdateDisplay:
            print(f"[DEBUG][TimerUpdateDisplay] Entering update_frame: args={{}}")
        wm = self.window_manager
        if hasattr(wm, 'scroll_overlay') and wm.scroll_overlay.isVisible():
            wm.scroll_overlay.update_frame()
        current_widget = wm.stack.currentWidget()
        if hasattr(current_widget, 'background_manager'):
            current_widget.background_manager.update_background()
        if DEBUG_TimerUpdateDisplay:
            print(f"[DEBUG][TimerUpdateDisplay] Exiting update_frame: return=None")

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
        self.scroll_overlay = ScrollOverlay(self)
        self.scroll_overlay.hide_overlay()
        self.set_view(0, initial=True)
        self.display_timer = TimerUpdateDisplay(self, fps=60)
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
        def after_set_view():
            if DEBUG_WindowManager:
                print(f"[DEBUG][WindowManager] Exiting after_set_view: return=None")
            self.scroll_overlay.start_scroll_animation(
                stop_speed=30,
                on_finished=lambda: self.scroll_overlay.hide_overlay(
                    on_hidden=lambda: self.scroll_overlay.clean_scroll(on_cleaned=after_animation)
                )
            )
            # Réactive le gradient après le changement de vue
            if 1 in self.widgets and hasattr(self.widgets[1], 'set_background_gradient'):
                self.widgets[1].set_background_gradient(True)
        def after_animation():
            # Désactive le gradient uniquement après la fin de l'animation
            if 1 in self.widgets and hasattr(self.widgets[1], 'set_background_gradient'):
                self.widgets[1].set_background_gradient(False)
            if callback:
                callback()
        self.scroll_overlay.raise_overlay(on_raised=lambda: self.set_view(index, callback=after_set_view))
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
