from gui_classes.overlay import OverlayCountdown, OverlayLoading
from PySide6.QtCore import QObject, QThread, Signal, QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from comfy_classes.comfy_class_API import ImageGeneratorAPIWrapper
from constante import dico_styles
import os
import glob
import cv2
from gui_classes.toolbox import ImageUtils
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
        print(f"[GEN_TASK] clear_overlay: appelé pour {name}")
        overlay = self.overlays.get(name)
        if overlay:
            print(f"[GEN_TASK] clear_overlay: appel clean_overlay sur {overlay}")
            overlay.hide()
            overlay.clean_overlay()
            overlay.setParent(None)
            overlay.deleteLater()
            QApplication.processEvents()
            self.overlays[name] = None
        else:
            print(f"[GEN_TASK] clear_overlay: aucun overlay à nettoyer pour {name}")
        if name == "loading":
            print("[GEN_TASK] clear_overlay: reset _worker et _user_on_finished pour loading")
            self._worker = None
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

class ImageGenerationTask(QObject):
    finished = Signal(object)  # QImage ou None

    def __init__(self, style, input_image, parent=None):
        super().__init__(parent)
        self.api = ImageGeneratorAPIWrapper()
        self.input_image = input_image
        self.style = style
        self._running = True
        self._thread = None
        self._worker = None  # Ajout pour worker thread
        self._loading_overlay = None

    def show_loading(self):
        print("[GEN_TASK] show_loading: création et affichage de l'overlay de loading")
        # S'il existe déjà un overlay, le supprimer proprement
        if self._loading_overlay:
            print("[GEN_TASK] show_loading: overlay déjà existant, suppression")
            self._loading_overlay.hide()
            self._loading_overlay.deleteLater()
            self._loading_overlay.setParent(None)
            QApplication.processEvents()
            self._loading_overlay = None
        if self.parent():
            self._loading_overlay = OverlayLoading(self.parent())
            print(f"[GEN_TASK] show_loading: OverlayLoading instance créée {self._loading_overlay} parent={self.parent()}")
            self._loading_overlay.show()
            print("[GEN_TASK] show_loading: OverlayLoading affiché")
            self._loading_overlay.raise_()
        else:
            print("[GEN_TASK] show_loading: pas de parent pour OverlayLoading")

    def hide_loading(self):
        print("[GEN_TASK] hide_loading: tentative de cacher l'overlay de loading")
        if self._loading_overlay:
            print(f"[GEN_TASK] hide_loading: overlay instance = {self._loading_overlay}")
            if hasattr(self._loading_overlay, "stop_animation"):
                print("[GEN_TASK] hide_loading: appel stop_animation() sur OverlayLoading")
                self._loading_overlay.stop_animation()
            else:
                print("[GEN_TASK] hide_loading: pas de stop_animation() sur OverlayLoading")
            self._loading_overlay.hide()
            print("[GEN_TASK] hide_loading: OverlayLoading caché (hide() appelé)")
            self._loading_overlay.setVisible(False)  # Force la disparition
            self._loading_overlay.deleteLater()
            print("[GEN_TASK] hide_loading: OverlayLoading deleteLater() appelé")
            self._loading_overlay.setParent(None)
            print("[GEN_TASK] hide_loading: OverlayLoading setParent(None) appelé")
            QApplication.processEvents()
            print("[GEN_TASK] hide_loading: QApplication.processEvents() appelé")
            self._loading_overlay = None
        else:
            print("[GEN_TASK] hide_loading: aucun overlay à cacher")

    def clean(self):
        """Nettoyage complet du thread et des ressources."""
        print("[GEN_TASK] clean called")
        self.stop()
        if self._thread:
            print(f"[GEN_TASK] clean: thread isRunning={self._thread.isRunning()}, currentThread={QThread.currentThread()}, self._thread={self._thread}")
            if QThread.currentThread() != self._thread:
                if self._thread.isRunning():
                    print("[GEN_TASK] clean: quitting thread")
                    self._thread.quit()
                    self._thread.wait()
                    print("[GEN_TASK] clean: thread stopped")
                self._thread.deleteLater()
                self._thread = None
            else:
                print("[GEN_TASK] clean: called from inside the thread, defer deletion")
                QTimer.singleShot(0, self._delete_thread_safe)
        else:
            print("[GEN_TASK] clean: no thread to clean")

    def _delete_thread_safe(self):
        """Arrête et supprime le thread depuis le thread principal."""
        if self._thread:
            print("[GEN_TASK] _delete_thread_safe: quitting thread")
            if QThread.currentThread() != self._thread:
                self._thread.quit()
                self._thread.wait()
                print("[GEN_TASK] _delete_thread_safe: thread stopped")
                self._thread.deleteLater()
                self._thread = None
            else:
                print("[GEN_TASK] _delete_thread_safe: in thread, defer deleteLater to finished signal")
                def cleanup():
                    print("[GEN_TASK] _delete_thread_safe: finished signal received, deleting thread")
                    self._thread.deleteLater()
                    self._thread = None
                self._thread.finished.connect(cleanup)
                self._thread.quit()

    def start(self):
        """Démarre la génération d'image dans un thread et affiche l'overlay."""
        print("[GEN_TASK] start called")
        if self._thread and self._thread.isRunning():
            print("[GEN_TASK] start: thread already running")
            return
        self.show_loading()  # Affiche l'overlay AVANT de démarrer le thread
        print("[GEN_TASK] start: création du QThread et du worker")
        self._thread = QThread()
        # Worker interne pour la génération
        class ImageGenerationWorker(QObject):
            finished = Signal(object)
            def __init__(self, api, style, input_image):
                super().__init__()
                self.api = api
                self.style = style
                self.input_image = input_image
                self._running = True
            def stop(self):
                self._running = False
            def run(self):
                from PySide6.QtCore import QThread
                print(f"[GEN_TASK] run lancé dans thread: {QThread.currentThread()}")
                try:
                    print("[GEN_TASK] Task: set style")
                    self.api.set_style(self.style)
                    if not self._running:
                        print("[GEN_TASK] Task interrompue avant génération")
                        self.finished.emit(None)
                        return
                    print("[GEN_TASK] Task: save input image")
                    arr = ImageUtils.qimage_to_cv(self.input_image)
                    os.makedirs("../ComfyUI/input", exist_ok=True)
                    cv2.imwrite("../ComfyUI/input/input.png", arr)
                    print("[GEN_TASK] Task: launch generation")
                    self.api.generate_image()
                    if not self._running:
                        print("[GEN_TASK] Task interrompue après génération")
                        self.finished.emit(None)
                        return
                    print("[GEN_TASK] Task: extract generated image")
                    output_dir = os.path.abspath("../ComfyUI/output")
                    files = glob.glob(os.path.join(output_dir, "*.png"))
                    if not files:
                        print("[ERROR] Aucun fichier PNG trouvé dans le dossier output")
                        self.finished.emit(None)
                        return
                    latest = max(files, key=os.path.getmtime)
                    print(f"[DEBUG] Task: latest output file: {latest}")
                    img = cv2.imread(latest)
                    if img is None:
                        print("[ERROR] Impossible de lire l'image générée")
                        self.finished.emit(None)
                        return
                    qimg = ImageUtils.cv_to_qimage(img)
                    # Nettoyage
                    input_path = os.path.abspath("../ComfyUI/input/input.png")
                    if os.path.exists(input_path):
                        os.remove(input_path)
                        print(f"[DEBUG] Task: input supprimé: {input_path}")
                    if os.path.exists(latest):
                        os.remove(latest)
                        print(f"[DEBUG] Task: output supprimé: {latest}")
                    self.finished.emit(qimg)
                except Exception as e:
                    print(f"[GEN_TASK][ERROR] Erreur dans ImageGenerationTask: {e}")
                    self.finished.emit(None)

        self._worker = ImageGenerationWorker(self.api, self.style, self.input_image)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._on_thread_finished_hide_overlay)
        self._thread.finished.connect(self._thread.deleteLater)
        print("[GEN_TASK] start: démarrage du thread")
        self._thread.start()
        print("[GEN_TASK] start: thread started")

    def _on_worker_finished(self, result):
        self.finished.emit(result)
        self._worker.deleteLater()
        self._worker = None

    def _on_thread_finished_hide_overlay(self):
        print("[GEN_TASK] _on_thread_finished_hide_overlay: thread terminé, on cache l'overlay")
        self.hide_loading()

    def finish(self, *args, **kwargs):
        """Termine proprement la génération (wrapper pour callback/cleanup)."""
        print("[GEN_TASK] finish called")
        self.clean()

    def stop(self):
        print("[GEN_TASK] stop called")
        self._running = False
