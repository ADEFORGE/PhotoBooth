from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QResizeEvent
from gui_classes.photobooth import PhotoBooth
from gui_classes.sleepscreen_window import SleepScreenWindow
from gui_classes.background_manager import BackgroundManager
from constante import WINDOW_STYLE, DEBUG
import sys

DEBUG_WindowManager = True

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
        # Création de l'overlay de scroll, caché au démarrage
        self.background_manager.create_scroll_overlay(self, on_created=lambda: self.background_manager.hide_scroll_overlay())
        self.set_view(0, initial=True)
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
            self.background_manager.lower_scroll_overlay(on_lowered=lambda: self.background_manager.show_scroll_overlay(on_shown=callback))
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
            self.background_manager.start_scroll_animation(
                
                stop_speed=30,
                on_finished=lambda: self.background_manager.hide_scroll_overlay(
                    on_hidden=lambda: self.background_manager.clean_scroll_overlay(
                        on_cleaned=callback
                    )
                )
            )
        self.background_manager.raise_scroll_overlay(
            on_raised=lambda: self.set_view(index, callback=after_set_view)
        )
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
