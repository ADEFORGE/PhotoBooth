from gui_classes.overlay import OverlayCountdown, OverlayLoading
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication  # <-- Ajoutez cette ligne
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

class ImageGenerationWorker(QObject):
    finished = Signal(object)  # QImage ou None

    def __init__(self, api, extract_generated_image_func):
        super().__init__()
        self.api = api
        self.extract_generated_image_func = extract_generated_image_func

    def run(self):
        import sys
        from PySide6.QtCore import QThread
        print(f"[DEBUG] ImageGenerationWorker.run lancé dans thread: {QThread.currentThread()}")
        try:
            print("[DEBUG] Thread de génération lancé")
            self.api.generate_image()
            print("[DEBUG] Génération terminée, extraction de l'image générée")
            qimg = self.extract_generated_image_func()
            print(f"[DEBUG] Emission du signal finished depuis worker")
            self.finished.emit(qimg)
        except Exception as e:
            print(f"[ERROR] Erreur dans le thread de génération: {e}")
            sys.stdout.flush()
            print("[DEBUG] Emission du signal finished (erreur) depuis worker")
            self.finished.emit(None)

class ImageGenerationManager(QObject):
    generationFinished = Signal(object)  # QImage ou None
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.overlays = {}
        self._thread = None
        self._user_on_finished = None
        self.input_image = None  # QImage
        self.output_image = None  # QImage
        self.style = list(dico_styles.keys())[0] if dico_styles else None
        self.has_generated = False
        self.api = ImageGeneratorAPIWrapper()
        print(f"[DEBUG] ImageGenerationManager initialisé avec style par défaut: {self.style}")

    def set_input_image(self, qimage):
        print("[DEBUG] set_input_image appelé")
        self.input_image = qimage
        self.output_image = qimage.copy() if qimage else None
        self.has_generated = False
        print(f"[DEBUG] Image input définie, output copiée, has_generated={self.has_generated}")

    def set_style(self, style_name):
        print(f"[DEBUG] set_style appelé avec: {style_name}")
        try:
            self.api.set_style(style_name)
            self.style = style_name
            print(f"[DEBUG] Style défini: {self.style}")
        except Exception as e:
            print(f"[ERROR] Impossible de définir le style: {e}")

    def save_input_image_to_comfyui(self) -> bool:
        print("[DEBUG] save_input_image_to_comfyui appelé")
        try:
            if self.input_image is None:
                print("[ERROR] Pas d'image input à sauvegarder")
                return False
            arr = ImageUtils.qimage_to_cv(self.input_image)
            os.makedirs("../ComfyUI/input", exist_ok=True)
            cv2.imwrite("../ComfyUI/input/input.png", arr)
            print("[DEBUG] Image input sauvegardée dans ../ComfyUI/input/input.png")
            return True
        except Exception as e:
            print(f"[ERROR] Erreur lors de la sauvegarde de l'image input: {e}")
            return False

    def start_generation(self, on_finished=None):
        print("[DEBUG] start_generation appelé") 
        if not self.save_input_image_to_comfyui():
            print("[ERROR] Impossible de sauvegarder l'image input, annulation génération")
            if on_finished:
                on_finished(None)
            return

        # Nettoyage du thread précédent si existant
        if self._thread is not None and self._thread.isRunning():
            print("[DEBUG] Arrêt forcé du thread précédent")
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            
        if hasattr(self, "_worker") and self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

        # Afficher l'overlay AVANT de créer le thread
        self.show_overlay()
        
        # Créer et démarrer le nouveau thread
        self._thread = QThread()
        self._worker = ImageGenerationWorker(self.api, self.extract_generated_image)
        self._worker.moveToThread(self._thread)
        
        # Connecter les signaux dans le bon ordre  
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        
        # Stocker le callback
        self._user_on_finished = on_finished
        
        print(f"[DEBUG] Démarrage du thread de génération")
        self._thread.start()

    def _on_worker_finished(self, qimg):
        print("[DEBUG] _on_worker_finished (thread GUI)")
        self.output_image = qimg
        self.has_generated = qimg is not None and not qimg.isNull()
        # Appeler le callback utilisateur si défini
        if self._user_on_finished:
            try:
                print("[DEBUG] Appel du callback utilisateur depuis _on_worker_finished")
                self._user_on_finished(qimg)
            except Exception as e:
                print(f"[ERROR] Exception dans le callback utilisateur: {e}")
        self.hide_overlay()
        # Arrêter proprement le thread
        if self._thread is not None:
            print(f"[DEBUG] Arrêt du thread: {self._thread}, isRunning={self._thread.isRunning()}")
            self._thread.quit()
            self._thread.wait()
            print("[DEBUG] Thread mis à None")
            self._thread = None
        else:
            print("[DEBUG] Pas de thread à arrêter")
        self._user_on_finished = None
        self._worker = None

    def show_overlay(self):
        """Affiche l'overlay de chargement."""
        print("[DEBUG] Affichage overlay de chargement")
        # S'assurer qu'il n'y a qu'un seul overlay
        self.clear_overlay("loading")
        overlay = OverlayLoading(self.parent)
        overlay.show_overlay()
        self.overlays["loading"] = overlay
        overlay.raise_()

    def hide_overlay(self):
        """Cache l'overlay de chargement."""
        print("[DEBUG] Masquage overlay de chargement")  
        if "loading" in self.overlays and self.overlays["loading"]:
            self.overlays["loading"].hide()
            self.clear_overlay("loading")

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
        self._thread = None
        self._worker = None
        self._user_on_finished = None

    def setup_signals(self):
        """Connecte les signaux nécessaires pour le fonctionnement du manager."""
        print("[DEBUG] Configuration des signaux")
        # Connecter les signaux ici si nécessaire

    def convert_image(self, image: QImage):
        """Convertit une image au format requis par le worker."""
        print("[DEBUG] Conversion de l'image")
        # Logique de conversion ici

    def extract_results(self, result):
        """Extrait et traite les résultats du worker."""
        print("[DEBUG] Extraction des résultats")
        # Logique d'extraction ici

    def debug_info(self):
        """Affiche des informations de débogage sur l'état actuel du manager."""
        print("[DEBUG] Informations de débogage:")
        print(f"  Thread en cours: {self._thread.isRunning() if self._thread else 'Aucun'}")
        print(f"  Worker: {self._worker}")
        print(f"  Overlays: {self.overlays.keys()}")
        print(f"  User on finished: {self._user_on_finished}")

    def run_generation(self, style, image, callback_name=None):
        """Initialise et lance la génération d'image, puis appelle le callback nommé à la fin."""
        print(f"[DEBUG] run_generation appelé avec style={style}, callback={callback_name}")
        self.setup(image, style=style)
        def finished_callback(qimg):
            print(f"[DEBUG] finished_callback appelé pour {callback_name}")
            if callback_name and hasattr(self.parent, callback_name):
                getattr(self.parent, callback_name)(qimg)
            else:
                print(f"[WARNING] Callback {callback_name} non trouvé sur {self.parent}")
        self.start(on_finished=finished_callback)

    def _call_callback(self, callback_name, qimg):
        print(f"[DEBUG] _call_callback: {callback_name}")
        if callback_name and hasattr(self.parent, callback_name):
            getattr(self.parent, callback_name)(qimg)
        else:
            print(f"[WARNING] Callback {callback_name} non trouvé sur {self.parent}")

    # Ajoutez la méthode setup (manquante)
    def setup(self, qimage, style=None):
        print("[DEBUG] setup appelé")
        self.set_input_image(qimage)
        if style:
            self.set_style(style)
        print(f"[DEBUG] Setup terminé avec style={self.style}")

    # Ajoutez la méthode start (manquante)
    def start(self, on_finished=None):
        print("[DEBUG] start appelé")
        self.start_generation(on_finished=on_finished)

    # Ajoutez la méthode extract_generated_image (manquante)
    def extract_generated_image(self) -> QImage:
        print("[DEBUG] extract_generated_image appelé")
        try:
            latest_file = self._find_latest_output_file()
            if not latest_file:
                print("[ERROR] Aucun fichier de sortie trouvé")
                return None
            qimg = self._load_output_image(latest_file)
            self._cleanup_input_output_files(latest_file)
            print("[DEBUG] Image générée extraite et nettoyée")
            return qimg
        except Exception as e:
            print(f"[ERROR] Erreur lors de l'extraction de l'image générée: {e}")
            return None

    def _find_latest_output_file(self):
        print("[DEBUG] Recherche du fichier de sortie le plus récent")
        try:
            output_dir = os.path.abspath("../ComfyUI/output")
            files = glob.glob(os.path.join(output_dir, "*.png"))
            if not files:
                print("[ERROR] Aucun fichier PNG trouvé dans le dossier output")
                return None
            latest = max(files, key=os.path.getmtime)
            print(f"[DEBUG] Fichier le plus récent: {latest}")
            return latest
        except Exception as e:
            print(f"[ERROR] Erreur lors de la recherche du fichier de sortie: {e}")
            return None

    def _load_output_image(self, filepath):
        print(f"[DEBUG] Chargement de l'image générée depuis {filepath}")
        try:
            img = cv2.imread(filepath)
            if img is None:
                print("[ERROR] Impossible de lire l'image générée")
                return None
            qimg = ImageUtils.cv_to_qimage(img)
            print("[DEBUG] Image générée chargée en QImage")
            return qimg
        except Exception as e:
            print(f"[ERROR] Erreur lors du chargement de l'image générée: {e}")
            return None

    def _cleanup_input_output_files(self, output_file):
        print("[DEBUG] Nettoyage des fichiers input/output")
        try:
            input_path = os.path.abspath("../ComfyUI/input/input.png")
            if os.path.exists(input_path):
                os.remove(input_path)
                print(f"[DEBUG] Fichier input supprimé: {input_path}")
            if output_file and os.path.exists(output_file):
                os.remove(output_file)
                print(f"[DEBUG] Fichier output supprimé: {output_file}")
        except Exception as e:
            print(f"[ERROR] Erreur lors du nettoyage des fichiers: {e}")
