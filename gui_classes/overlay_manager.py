from gui_classes.overlay import OverlayCountdown, OverlayLoading
from PySide6.QtCore import QObject, QThread, Signal
import time

class CountdownOverlayManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.overlays = {}
        self._thread = None
        self._user_on_finished = None

    def start(self, on_finished, start_value=3):
        """Démarre un overlay de compte à rebours et appelle on_finished à la fin."""
        print("[DEBUG] CountdownManager.start appelé")
        print(f"[DEBUG] Callback fourni: {on_finished}")
        self.show_overlay(start_value, on_finished=on_finished)

    def show_overlay(self, start_value, on_finished=None):
        print("[DEBUG] CountdownManager.show_overlay")
        self.clear_overlay("countdown")
        overlay = OverlayCountdown(self.parent, start=start_value)
        overlay.show_overlay()
        self.overlays["countdown"] = overlay
        self._user_on_finished = on_finished
        print(f"[DEBUG] Callback stocké: {self._user_on_finished}")

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

        if self._thread and self._thread.isRunning():
            self._thread.stop()
            self._thread.wait()
        self._thread = CountdownThread(start_value)

        # Moved to instance method
        self._current_overlay = overlay
        self._thread.tick.connect(self._on_tick)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.start()
        return overlay

    def _on_tick(self, value):
        if self._current_overlay:
            if value > 0:
                self._current_overlay.show_number(value)
            elif value == 0:
                self._current_overlay.show_number(0)
                self._current_overlay.set_full_white()

    def _on_thread_finished(self):
        print("[DEBUG] Thread countdown terminé")
        if self._user_on_finished:
            print("[DEBUG] Appel du callback utilisateur")
            try:
                self._user_on_finished()
            except Exception as e:
                print(f"[ERROR] Exception dans le callback: {e}")
        else:
            print("[DEBUG] Pas de callback à appeler")
        self.clear_overlay("countdown")
        self._thread = None
        self._current_overlay = None
        self._user_on_finished = None

    def clear_overlay(self, name):
        overlay = self.overlays.get(name)
        if overlay:
            overlay.clean_overlay()
            self.overlays[name] = None
        if name == "countdown" and self._thread:
            self._thread.stop()
            self._thread.wait()
            self._thread = None
            self._user_on_finished = None

    def clear_all(self):
        for name in list(self.overlays.keys()):
            self.clear_overlay(name)
        self.overlays.clear()
        if self._thread:
            self._thread.stop()
            self._thread.wait()
            self._thread = None
            self._user_on_finished = None

class GenerationOverlayManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.overlays = {}
        self._thread = None
        self._worker = None
        self._user_on_finished = None

    def start(self, worker, on_finished):
        """Affiche l'overlay de chargement, lance le worker dans un thread, appelle on_finished(result) à la fin."""
        self.show_overlay(worker, on_finished=on_finished)

    def show_overlay(self, worker, on_finished=None):
        self.clear_overlay("loading")
        overlay = OverlayLoading(self.parent)
        overlay.show_overlay()
        self.overlays["loading"] = overlay

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
        self.clear_overlay("loading")
        if self._user_on_finished:
            self._user_on_finished(result)
        self._thread = None
        self._worker = None
        self._user_on_finished = None

    def clear_overlay(self, name):
        overlay = self.overlays.get(name)
        if overlay:
            overlay.clean_overlay()
            self.overlays[name] = None
        if name == "loading":
            self._thread = None
            self._worker = None
            self._user_on_finished = None

    def clear_all(self):
        for name in list(self.overlays.keys()):
            self.clear_overlay(name)
        self.overlays.clear()
        self._thread = None
        self._worker = None
        self._user_on_finished = None
