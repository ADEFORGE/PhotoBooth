from gui_classes.overlay import OverlayCountdown, OverlayLoading
from PySide6.QtCore import QObject, QThread, Signal
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
        overlay = self.overlays.get(name)
        if overlay:
            print(f"[DEBUG] clear_overlay: appel clean_overlay sur {overlay}")
            overlay.hide()
            overlay.clean_overlay()
            overlay.setParent(None)
            overlay.deleteLater()
            QApplication.processEvents()
            self.overlays[name] = None
        else:
            print(f"[DEBUG] clear_overlay: aucun overlay à nettoyer pour {name}")
        # Correction : ne pas mettre self._thread = None pour 'loading' ici, sinon le thread de génération ne démarre jamais
        if name == "loading":
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

    def stop(self):
        self._running = False

    def run(self):
        from PySide6.QtCore import QThread
        print(f"[DEBUG] ImageGenerationTask.run lancé dans thread: {QThread.currentThread()}")
        try:
            print("[DEBUG] Task: set style")
            self.api.set_style(self.style)
            if not self._running:
                print("[DEBUG] Task interrompue avant génération")
                return
            print("[DEBUG] Task: save input image")
            arr = ImageUtils.qimage_to_cv(self.input_image)
            os.makedirs("../ComfyUI/input", exist_ok=True)
            cv2.imwrite("../ComfyUI/input/input.png", arr)
            print("[DEBUG] Task: launch generation")
            self.api.generate_image()
            if not self._running:
                print("[DEBUG] Task interrompue après génération")
                return
            print("[DEBUG] Task: extract generated image")
            qimg = self._extract_generated_image()
            if not self._running:
                print("[DEBUG] Task interrompue après extraction")
                return
            print("[DEBUG] Task: emit finished")
            self.finished.emit(qimg)
        except Exception as e:
            print(f"[ERROR] Erreur dans ImageGenerationTask: {e}")
            self.finished.emit(None)

    def _extract_generated_image(self):
        try:
            output_dir = os.path.abspath("../ComfyUI/output")
            files = glob.glob(os.path.join(output_dir, "*.png"))
            if not files:
                print("[ERROR] Aucun fichier PNG trouvé dans le dossier output")
                return None
            latest = max(files, key=os.path.getmtime)
            print(f"[DEBUG] Task: latest output file: {latest}")
            img = cv2.imread(latest)
            if img is None:
                print("[ERROR] Impossible de lire l'image générée")
                return None
            qimg = ImageUtils.cv_to_qimage(img)
            # Nettoyage
            input_path = os.path.abspath("../ComfyUI/input/input.png")
            if os.path.exists(input_path):
                os.remove(input_path)
                print(f"[DEBUG] Task: input supprimé: {input_path}")
            if os.path.exists(latest):
                os.remove(latest)
                print(f"[DEBUG] Task: output supprimé: {latest}")
            return qimg
        except Exception as e:
            print(f"[ERROR] Erreur extraction image générée: {e}")
            return None
