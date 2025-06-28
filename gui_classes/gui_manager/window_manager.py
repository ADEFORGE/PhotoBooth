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

    def update_mode(self, update_scroll: bool = True, update_background: bool = True) -> None:
        """
        Permet d'activer ou désactiver dynamiquement l'update du scroll_overlay et du background_manager.
        - update_scroll : active/désactive l'update du scroll_overlay
        - update_background : active/désactive l'update du background_manager
        """
        self._update_scroll = update_scroll
        self._update_background = update_background

    def update_frame(self) -> None:
        if DEBUG_TimerUpdateDisplay:
            print(f"[DEBUG][TimerUpdateDisplay] Entering update_frame: args={{}}")
        wm = self.window_manager
        if getattr(self, '_update_scroll', True):
            if hasattr(wm, 'scroll_overlay') and wm.scroll_overlay.isVisible():
                wm.scroll_overlay.update_frame()
        if getattr(self, '_update_background', True):
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
        self.display_timer = TimerUpdateDisplay(self, fps=90)
        self.set_view(0)
        self.scroll_overlay.lower_overlay(on_lowered=lambda: self.scroll_overlay.show_overlay())
        
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting __init__: return=None")


    def resizeEvent(self, event: QResizeEvent) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering resizeEvent: args={{'event':{event}}}")
        super().resizeEvent(event)
        if hasattr(self, 'scroll_overlay') and self.scroll_overlay:
            self.scroll_overlay.setGeometry(0, 0, self.width(), self.height())
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting resizeEvent: return=None")


    def start(self) -> None:
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Entering start: args={{}}")
        self.showFullScreen()
        if DEBUG_WindowManager:
            print(f"[DEBUG][WindowManager] Exiting start: return=None")


    def set_view(self, index: int) -> None:
        new_widget = self.widgets[index]
        self.stack.setCurrentWidget(new_widget)
        self.showFullScreen()

    def transition_window(self, index: int) -> None:
        """
        Effectue une transition animée vers la fenêtre d'index donné.
        Si l'index est différent de la fenêtre courante :
        - on_leave de l'appelante
        - raise_overlay (sans callback)
        - set_view vers l'index
        - scroll_animation
        - en callback de scroll_animation : on_enter de la nouvelle fenêtre
        """
        current_index = self.stack.currentIndex()
        print(f"[DEBUG][WindowManager] transition_window appelé avec index={index}, current_index={current_index}")
        
        if not index == current_index:        
            current_widget = self.stack.currentWidget()

            # On_leave de l'appelante
            if hasattr(current_widget, 'on_leave'):
                current_widget.on_leave()

            # Animation overlay (sans callback)
            self.scroll_overlay.raise_overlay()

            # Changement de vue
            self.set_view(index)

            new_widget = self.stack.currentWidget()
            if hasattr(new_widget, 'on_enter'):
                self.scroll_animation(1, index, new_widget.on_enter)
            else:
                self.scroll_animation(1, index)


    def scroll_animation(self, mode: int, index: int, callback=None):
        """
        Lance l'animation de scroll, puis le nettoyage, puis le callback utilisateur.
        Si mode == 1 : lance l'animation complète (comportement actuel).
        Sinon : appelle directement le callback sans animation.
        """
        if mode == 1:
            self.scroll_overlay.start_scroll_animation(
                stop_speed=30,
                on_finished=lambda: self.scroll_overlay.hide_overlay(
                    on_hidden=lambda: self.scroll_overlay.clean_scroll(
                        on_cleaned=callback
                    )
                )
            )
        elif mode == 0:
            self.scroll_overlay.lower_overlay(on_lowered=lambda: self.scroll_overlay.show_overlay(on_shown=callback))
        
        if callback:
            callback()