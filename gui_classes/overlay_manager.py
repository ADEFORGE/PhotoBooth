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

class CountdownThread(QObject):
    overlay_finished = Signal()

    class Thread(QThread):
        tick = Signal(int)
        finished = Signal()
        def __init__(self, start):
            super().__init__()
            self._start = start
            self._running = True
            self._finished_emitted = False
        def run(self):
            count = self._start
            while self._running and count >= 0:
                self.tick.emit(count)
                time.sleep(1)
                count -= 1
            if self._running and not self._finished_emitted:
                self._finished_emitted = True
                self.finished.emit()
        def stop(self):
            self._running = False

    def __init__(self, parent=None, count=None):
        super().__init__(parent)
        self._parent = parent
        self._count = count
        self._thread = None
        self._overlay = None
        self._user_callback = None

    def start_countdown(self, count=None, on_finished=None):
        if self._thread is not None:
            return
        if count is not None:
            self._count = count
        self._user_callback = on_finished
        self._overlay = OverlayCountdown(self._parent, start=self._count)
        if hasattr(self._overlay, '_is_alive') and not self._overlay._is_alive:
            print(f"[PROTECT] OverlayCountdown déjà détruit, start annulé")
            return
        self._overlay.show_overlay()
        self._thread = self.Thread(self._count)
        self._thread.tick.connect(self._on_tick)
        self._thread.finished.connect(self._on_finish)
        self._thread.start()

    def _on_tick(self, count):
        if self._overlay and getattr(self._overlay, '_is_alive', True):
            if hasattr(self._overlay, 'show_number'):
                self._overlay.show_number(count)
            else:
                print(f"[PROTECT] _on_tick: overlay n'a pas show_number")
        else:
            print(f"[PROTECT] _on_tick ignoré, overlay non vivant")

    def _on_finish(self):
        if self._overlay:
            if getattr(self._overlay, '_is_alive', True):
                self._overlay.clean_overlay()
            else:
                print(f"[PROTECT] _on_finish: overlay déjà détruit")
            self._overlay = None
        if self._thread:
            self._thread.stop()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
            self.overlay_finished.emit()
        if self._user_callback:
            print(f"[DEBUG] Appel du callback utilisateur (id={id(self._user_callback)})")
            self._user_callback()
            self._user_callback = None

    def stop_countdown(self):
        if self._thread:
            self._thread.stop()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
        if self._overlay:
            if getattr(self._overlay, '_is_alive', True):
                self._overlay.clean_overlay()
            else:
                print(f"[PROTECT] stop: overlay déjà détruit")
            self._overlay = None

    def clear_overlay(self, reason=None):
        print(f"[GEN_TASK] clear_overlay: appelé pour countdown")
        if self._overlay:
            print(f"[GEN_TASK] clear_overlay: appel clean_overlay sur {self._overlay}")
            try:
                # Bloque tous les signaux
                self._overlay.blockSignals(True)
                # Déconnecte les signaux éventuels (timers, etc.)
                if hasattr(self._overlay, '_anim_timer') and hasattr(self._overlay._anim_timer, 'stop'):
                    print(f"[GEN_TASK] clear_overlay: arrêt du timer d'animation")
                    self._overlay._anim_timer.stop()
                    self._overlay._anim_timer.timeout.disconnect()
                # Ajoute ici d'autres déconnexions spécifiques si besoin
            except Exception as e:
                print(f"[GEN_TASK] clear_overlay: Exception lors du blocage/déconnexion des signaux: {e}")
            self._overlay.clean_overlay()
            self._overlay = None
        else:
            print(f"[GEN_TASK] clear_overlay: aucun overlay à nettoyer pour countdown")

class ImageGenerationThread(QObject):
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
        # Supprimer tous les overlays de loading existants (sécurité)
        for widget in QApplication.allWidgets():
            if widget.__class__.__name__ == "OverlayLoading" and widget is not self._loading_overlay:
                if hasattr(widget, '_is_alive') and not widget._is_alive:
                    print(f"[PROTECT] show_loading: overlay orphelin déjà détruit {widget}")
                    continue
                print(f"[GEN_TASK] show_loading: suppression overlay orphelin {widget}")
                try:
                    widget.hide()
                    widget.deleteLater()
                    widget.setParent(None)
                except Exception as e:
                    print(f"[GEN_TASK] show_loading: erreur suppression overlay orphelin: {e}")
        QApplication.processEvents()
        # S'il existe déjà un overlay, le supprimer proprement
        if self._loading_overlay:
            if hasattr(self._loading_overlay, '_is_alive') and not self._loading_overlay._is_alive:
                print(f"[PROTECT] show_loading: overlay déjà détruit {self._loading_overlay}")
            else:
                print(f"[GEN_TASK] show_loading: overlay déjà existant, suppression {self._loading_overlay}")
                self._loading_overlay.hide()
                self._loading_overlay.deleteLater()
                self._loading_overlay.setParent(None)
                QApplication.processEvents()
            self._loading_overlay = None
        if self.parent():
            self._loading_overlay = OverlayLoading(self.parent())
            print(f"[GEN_TASK] show_loading: OverlayLoading instance créée {self._loading_overlay} parent={self.parent()}")
            self._loading_overlay.show()
            print(f"[GEN_TASK] show_loading: OverlayLoading affiché {self._loading_overlay}")
            self._loading_overlay.raise_()
        else:
            print("[GEN_TASK] show_loading: pas de parent pour OverlayLoading")

    def hide_loading(self):
        print("[GEN_TASK] hide_loading: tentative de cacher l'overlay de loading")
        if self._loading_overlay:
            if hasattr(self._loading_overlay, '_is_alive') and not self._loading_overlay._is_alive:
                print(f"[PROTECT] hide_loading: overlay déjà détruit {self._loading_overlay}")
                self._loading_overlay = None
                return
            print(f"[GEN_TASK] hide_loading: overlay instance = {self._loading_overlay}")
            # Ajout : déconnexion de tous les signaux, arrêt animation, suppression parent/layout
            try:
                if hasattr(self._loading_overlay, "stop_animation"):
                    print(f"[GEN_TASK] hide_loading: appel stop_animation() sur {self._loading_overlay}")
                    self._loading_overlay.stop_animation()
                else:
                    print(f"[GEN_TASK] hide_loading: pas de stop_animation() sur {self._loading_overlay}")
                # Déconnecte tous les signaux éventuels
                self._loading_overlay.blockSignals(True)
                # Supprime du layout parent si présent
                parent = self._loading_overlay.parent()
                if parent and hasattr(parent, "layout") and parent.layout():
                    print(f"[GEN_TASK] hide_loading: suppression du layout parent")
                    parent.layout().removeWidget(self._loading_overlay)
            except Exception as e:
                print(f"[GEN_TASK] hide_loading: Exception during cleanup: {e}")
            self._loading_overlay.hide()
            print(f"[GEN_TASK] hide_loading: hide() appelé sur {self._loading_overlay}")
            self._loading_overlay.setVisible(False)
            print(f"[GEN_TASK] hide_loading: setVisible(False) appelé sur {self._loading_overlay}")
            self._loading_overlay.deleteLater()
            print(f"[GEN_TASK] hide_loading: deleteLater() appelé sur {self._loading_overlay}")
            self._loading_overlay.setParent(None)
            print(f"[GEN_TASK] hide_loading: setParent(None) appelé sur {self._loading_overlay}")
            QApplication.processEvents()
            print(f"[GEN_TASK] hide_loading: QApplication.processEvents() appelé après suppression overlay")
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
        print("[GEN_TASK] start called")
        if self._thread and self._thread.isRunning():
            print("[GEN_TASK] start: thread already running")
            return
            
        self.show_loading()
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
        
        # Modification de l'ordre des connexions
        self._worker.finished.connect(self._on_worker_finished)
        self._thread.started.connect(self._worker.run)
        # On ne connecte plus directement à thread.quit
        
        print("[GEN_TASK] start: démarrage du thread")
        self._thread.start()
        print("[GEN_TASK] start: thread started")

    def _on_worker_finished(self, result):
        print("[GEN_TASK] _on_worker_finished: called")
        self.finished.emit(result)
        # Gérer l'arrêt du thread ici
        if self._thread:
            if self._thread.isRunning():
                print("[GEN_TASK] _on_worker_finished: stopping thread")
                self._thread.quit()
                self._thread.wait()
            print("[GEN_TASK] _on_worker_finished: deleting thread")
            self._thread.deleteLater()
            self._thread = None
        # Nettoyer le worker
        if self._worker:
            print(f"[GEN_TASK] _on_worker_finished: cleanup worker {self._worker}")
            self._worker.deleteLater()
            self._worker = None
        # Cacher l'overlay maintenant que tout est nettoyé
        self.hide_loading()

    def _on_thread_finished_hide_overlay(self):
        # Cette méthode ne fait plus rien maintenant
        pass

    def stop(self):
        print("[GEN_TASK] stop called")
        self._running = False
        if self._thread:
            if self._thread.isRunning():
                print("[GEN_TASK] stop: cleaning up thread")
                self._thread.quit()
                self._thread.wait()
            print("[GEN_TASK] stop: deleting thread")
            self._thread.deleteLater()
            self._thread = None
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        self.hide_loading()
