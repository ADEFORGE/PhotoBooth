from gui_classes.overlay import OverlayCountdown, OverlayLoading
from PySide6.QtCore import QObject, QThread, Signal

import time

class CountdownOverlayManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.overlays = {}
        self._countdown_thread = None

    def start_countdown(self, on_finished, start_value=3):
        """Démarre un overlay de compte à rebours et appelle on_finished à la fin."""
        self.show_countdown_overlay(start_value, on_finished=on_finished)

    def show_countdown_overlay(self, start_value, on_finished=None):
        self.clear_overlay("countdown")
        overlay = OverlayCountdown(self.parent, start=start_value)
        overlay.show_overlay()
        self.overlays["countdown"] = overlay

        # Internal countdown thread
        class CountdownThread(QThread):
            tick = Signal(int)
            finished = Signal()
            def __init__(self, start):
                super().__init__()
                self._start = start
                self._running = True
            def run(self):
                count = self._start
                while self._running and count >= 0:
                    self.tick.emit(count)
                    time.sleep(1)
                    count -= 1
                if self._running:
                    self.finished.emit()
            def stop(self):
                self._running = False

        # Stop previous thread if any
        if self._countdown_thread and self._countdown_thread.isRunning():
            self._countdown_thread.stop()
            self._countdown_thread.wait()
        self._countdown_thread = CountdownThread(start_value)

        def on_tick(value):
            if overlay:
                if value > 0:
                    overlay.show_number(value)
                elif value == 0:
                    overlay.show_number(0)
                    overlay.set_full_white()

        def on_thread_finished():
            self.clear_overlay("countdown")
            self._countdown_thread = None
            if on_finished:
                on_finished()

        self._countdown_thread.tick.connect(on_tick)
        self._countdown_thread.finished.connect(on_thread_finished)
        self._countdown_thread.start()
        return overlay

    def clear_overlay(self, name):
        overlay = self.overlays.get(name)
        if overlay:
            overlay.clean_overlay()
            self.overlays[name] = None
        if name == "countdown" and self._countdown_thread:
            self._countdown_thread.stop()
            self._countdown_thread.wait()
            self._countdown_thread = None

    def clear_all(self):
        for name in list(self.overlays.keys()):
            self.clear_overlay(name)
        self.overlays.clear()
        if self._countdown_thread:
            self._countdown_thread.stop()
            self._countdown_thread.wait()
            self._countdown_thread = None

class GenerationOverlayManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.overlay = None
        self._thread = None
        self._worker = None
        self._user_on_finished = None

    def start_generation(self, worker, on_finished):
        """Affiche l'overlay de chargement, lance le worker dans un thread, appelle on_finished(result) à la fin."""
        self.clear_overlay()
        self.overlay = OverlayLoading(self.parent)
        self.overlay.show_overlay()

        self._thread = QThread()
        self._worker = worker
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._user_on_finished = on_finished
        self._thread.start()

    def _on_worker_finished(self, result):
        self.clear_overlay()
        if self._user_on_finished:
            self._user_on_finished(result)
        self._thread = None
        self._worker = None
        self._user_on_finished = None

    def clear_overlay(self):
        if self.overlay:
            self.overlay.clean_overlay()
            self.overlay = None
