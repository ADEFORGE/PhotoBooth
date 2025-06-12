from PySide6.QtCore import Qt, QTimer, QThread, Signal, QObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from gui_classes.overlay import OverlayLoading
from gui_classes.gui_base_widget import PhotoBoothBaseWidget
import cv2
import time
from constante import GRID_SIZE

class CameraCaptureThread(QThread):
    frame_ready = Signal(QImage)
    def __init__(self, camera_id=GRID_SIZE, parent=None):
        super().__init__(parent)
        self.camera_id = camera_id
        self._running = True  # Initialisation à True dès le début
        self.cap = None
        print("[CAMERA] Thread créé")

    def run(self):
        print("[CAMERA] Thread démarré, recherche caméra...")
        # Fallback: essaie plusieurs index si la caméra ne s'ouvre pas
        tried = []
        for idx in [self.camera_id, 0, 1, 2, 3]:
            if idx in tried:
                continue
            tried.append(idx)
            print(f"[CAMERA] Essai index {idx}...")
            self.cap = cv2.VideoCapture(idx)
            if self.cap.isOpened():
                print(f"[CAMERA] Caméra trouvée sur index {idx}")
                break
            else:
                self.cap.release()
                self.cap = None

        if not self.cap or not self.cap.isOpened():
            print("[CAMERA] Aucune caméra trouvée")
            # Affiche une image de remplacement si aucune caméra
            from PySide6.QtGui import QPixmap
            import os
            img_path = os.path.join(os.path.dirname(__file__), '../gui_template/nocam.png')
            if os.path.exists(img_path):
                qimg = QPixmap(img_path).toImage()
                self.frame_ready.emit(qimg)
            return

        print("[CAMERA] Démarrage boucle capture")
        while self._running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("[CAMERA] Frame invalide")
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.frame_ready.emit(qimg)
            QThread.msleep(33)  # ~30 FPS, plus précis que time.sleep()

        print("[CAMERA] Fin de la boucle capture")
        if self.cap:
            self.cap.release()
            self.cap = None

    def stop(self):
        print("[CAMERA] Arrêt demandé")
        self._running = False
        self.wait()

class CameraManager:
    _instance = None
    _thread = None
    _viewers = set()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._thread is None:
            print("[CAMERA] Création d'un nouveau thread caméra")
            self._thread = CameraCaptureThread()
            self._thread.start()

    def connect_viewer(self, viewer):
        """Connecte un viewer au thread caméra."""
        print(f"[CAMERA] Connexion viewer {viewer}")
        if self._thread and viewer:
            try:
                # Déconnecter d'abord si déjà connecté
                self.disconnect_viewer(viewer)
                # Connecter le nouveau signal
                self._thread.frame_ready.connect(viewer._on_frame_ready)
                self._viewers.add(viewer)
                print("[CAMERA] Viewer connecté avec succès")
            except Exception as e:
                print(f"[ERROR] Échec de la connexion du viewer: {e}")

    def disconnect_viewer(self, viewer):
        """Déconnecte un viewer du thread caméra."""
        print(f"[CAMERA] Déconnexion viewer {viewer}")
        if self._thread and viewer:
            try:
                # Vérifier si le viewer est connecté avant de déconnecter
                if viewer in self._viewers:
                    self._thread.frame_ready.disconnect(viewer._on_frame_ready)
                    self._viewers.discard(viewer)
                    print("[CAMERA] Viewer déconnecté avec succès")
            except TypeError:
                print("[WARNING] Le viewer était déjà déconnecté")
            except Exception as e:
                print(f"[WARNING] Erreur lors de la déconnexion du viewer: {e}")
                
    def cleanup(self):
        """Nettoie le gestionnaire de caméra et arrête le thread."""
        print("[CAMERA] Nettoyage du gestionnaire de caméra")
        # Déconnecte tous les viewers
        for viewer in list(self._viewers):
            self.disconnect_viewer(viewer)
        self._viewers.clear()

        # Arrête et nettoie le thread
        if self._thread:
            self._thread.stop()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None

    def __del__(self):
        """Assure le nettoyage à la suppression."""
        self.cleanup()

class CameraViewer(PhotoBoothBaseWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._camera_manager = CameraManager.get_instance()
        self._capture_connected = False
        self._last_frame = None
        self.selected_style = None
        self.loading_overlay = None
        self.generated_image = None
        self._thread = None
        self._worker = None
        self._generation_in_progress = False
        self.original_photo = None

    def start_camera(self):
        self._camera_manager.connect_viewer(self)
        self._capture_connected = True

    def stop_camera(self):
        self._capture_connected = False
        self._camera_manager.disconnect_viewer(self)

    def _on_frame_ready(self, qimg):
        """Gestion des frames de la caméra avec vérification du type."""
        if isinstance(qimg, str):
            print(f"[ERROR] Reçu une chaîne au lieu d'une QImage: {qimg}")
            return
        try:
            if not isinstance(qimg, QImage):
                print(f"[ERROR] Type d'image invalide: {type(qimg)}")
                return
            if qimg.isNull():
                print("[WARNING] Image nulle reçue")
                return
            self._last_frame = qimg
            if self._capture_connected:
                # Utilise le BackgroundManager pour la caméra
                self.background_manager.set_camera_pixmap(QPixmap.fromImage(qimg))
                self.update()
        except Exception as e:
            print(f"[ERROR] Erreur lors du traitement de l'image: {e}")
            
    def show_loading(self):
        if not self.loading_overlay:
            self.loading_overlay = OverlayLoading(self)
            self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.show()
        self.loading_overlay.raise_()

    def hide_loading(self):
        if self.loading_overlay:
            self.loading_overlay.hide()

    def capture_photo(self, style_name=None):
        """Capture une photo avec vérification et lance la génération si style."""
        if self._last_frame is None:
            print("[ERROR] Pas de frame disponible pour la capture")
            return
        try:
            qimg = QImage(self._last_frame)
            if qimg.isNull():
                print("[ERROR] Échec de la copie de l'image")
                return
            self.original_photo = qimg
            self.background_manager.set_captured_image(qimg)
            if style_name:
                # Utilise run_generation si disponible
                if hasattr(self, 'image_generation_manager'):
                    self.image_generation_manager.run_generation(style_name, qimg, callback_name="on_image_generated_callback")
                else:
                    print("[ERROR] image_generation_manager non trouvé sur ce widget")
            else:
                self.generated_image = qimg
                self.update_frame()
        except Exception as e:
            print(f"[ERROR] Erreur lors de la capture: {e}")
            self._generation_in_progress = False

    def on_image_generated_callback(self, qimg):
        print("[DEBUG] Callback on_image_generated_callback appelé (CameraViewer)")
        self._generation_in_progress = False
        self.stop_camera()
        if qimg and not qimg.isNull():
            print("[DEBUG] Image générée valide (callback CameraViewer)")
            self.generated_image = qimg
        else:
            print("[DEBUG] Pas d'image générée (callback CameraViewer)")
            self.generated_image = None
        self.update_frame()

    def cleanup(self):
        """Clean up camera resources properly"""
        print("[CAMERA] Starting cleanup")
        # Stop camera first
        self._capture_connected = False
        self._camera_manager.disconnect_viewer(self)
        
        # Clear frame buffer
        self._last_frame = None
        self.original_photo = None
        self.generated_image = None
        
        # Clean up any running threads
        if hasattr(self, '_countdown_thread') and self._countdown_thread:
            if self._countdown_thread.isRunning():
                self._countdown_thread.stop()
                self._countdown_thread.wait()
            self._countdown_thread = None
            
        if hasattr(self, '_countdown_overlay') and self._countdown_overlay:
            self._countdown_overlay.clean_overlay()
            self._countdown_overlay = None
            
        # Call parent cleanup
        super().cleanup()
        print("[CAMERA] Cleanup complete")

    def showEvent(self, event):
        super().showEvent(event)
        if self.generated_image is not None:
            self.update_frame()
