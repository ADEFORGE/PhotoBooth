import sys
from PySide6.QtCore import Qt, QThread, Signal, QObject, QMutex, QMutexLocker, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QTransform
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QComboBox

from gui_classes.gui_manager.thread_manager import CameraCaptureThread

DEBUG_BackgroundManager = False

class BackgroundManager(QObject):
    """
    Manages live camera feed, captures, and generated images, rendering them onto a QLabel.
    """

    def __init__(self, label: QLabel, resolution_level: int = 2, rotation: int = 0, parent=None) -> None:
        """
        Inputs:
            label (QLabel): Widget to render the background.
            resolution_level (int): Camera resolution preset index.
            rotation (int): Rotation angle (0, 90, 180, 270).
            parent: Optional parent QObject.
        Outputs:
            None
        """
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering __init__: args={{label:{label}, resolution_level:{resolution_level}, rotation:{rotation}}}")
        super().__init__(parent)
        self.label = label
        self._mutex = QMutex()
        self.rotation = rotation
        self.label.lower()
        self.thread = CameraCaptureThread()
        self.thread.set_resolution_level(resolution_level)
        self.thread.frame_ready.connect(self._on_frame_ready)
        self.thread.start()
        self.last_camera = None
        self.captured = None
        self.generated = None
        self.current = 'live'
        self._show_gradient = False  # Par défaut, gradient désactivé
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting __init__: return=None")

    def set_rotation(self, angle: int) -> None:
        """
        Inputs:
            angle (int): Rotation angle in degrees (0, 90, 180, 270).
        Outputs:
            None
        """
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering set_rotation: args={{angle:{angle}}}")
        if angle in (0, 90, 180, 270):
            with QMutexLocker(self._mutex):
                self.rotation = angle
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting set_rotation: return=None")

    def _on_frame_ready(self, qimg: QImage) -> None:
        """
        Inputs:
            qimg (QImage): New frame from camera.
        Outputs:
            None
        """
        # if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering _on_frame_ready: args={{qimg:{qimg}}}")
        pix = QPixmap.fromImage(qimg)
        with QMutexLocker(self._mutex):
            self.last_camera = pix
        # if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting _on_frame_ready: return=None")

    def set_live(self) -> None:
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering set_live: args=")
        with QMutexLocker(self._mutex):
            self.current = 'live'
        # Affiche immédiatement le flux live avec gradient
        self.render_pixmap(self.get_pixmap())
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting set_live: return=None")

    def capture(self) -> None:
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering capture: args=")
        with QMutexLocker(self._mutex):
            if self.last_camera:
                self.captured = QPixmap(self.last_camera)
            self.current = 'captured'
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting capture: return=None")

    def set_generated(self, qimage: QImage) -> None:
        """
        Inputs:
            qimage (QImage): Image to display as generated background.
        Outputs:
            None
        """
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering set_generated: args={{qimage:{qimage}}}")
        with QMutexLocker(self._mutex):
            self.generated = QPixmap.fromImage(qimage)
            self.current = 'generated'
        # Affiche immédiatement l'image générée avec gradient
        self.render_pixmap(self.get_pixmap())
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting set_generated: return=None")

    def on_generate(self) -> None:
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering on_generate: args=")
        w, h = 640, 480
        img = QImage(w, h, QImage.Format_RGB888)
        img.fill(Qt.red)
        self.set_generated(img)
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting on_generate: return=None")

    def clear(self) -> None:
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering clear: args=")
        with QMutexLocker(self._mutex):
            self.captured = None
            self.generated = None
            self.current = 'live'
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting clear: return=None")

    def get_pixmap(self) -> QPixmap:
        """
        Inputs:
            None
        Outputs:
            QPixmap: Appropriate pixmap based on current mode.
        """
        # if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering get_pixmap: args=")
        with QMutexLocker(self._mutex):
            if self.current == 'generated' and self.generated:
                result = self.generated
            elif self.current == 'captured' and self.captured:
                result = self.captured
            else:
                result = self.last_camera
        # if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting get_pixmap: return={result}")
        return result

    def background_gradient(self, flag: bool) -> None:
        """
        Active ou désactive dynamiquement l'application du gradient sur le fond.
        Inputs:
            flag (bool): True pour activer, False pour désactiver le gradient.
        Outputs:
            None
        """
        self._show_gradient = bool(flag)
        # Rafraîchit l'affichage immédiatement
        self.update_background()

    def render_pixmap(self, pix: QPixmap) -> None:
        """
        Inputs:
            pix (QPixmap): Pixmap to render onto label.
        Outputs:
            None
        """
        # if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering render_pixmap: args={{pix:{pix}}}")
        if pix is None:
            # Si aucun pixmap n'est disponible, on efface le label
            self.label.clear()
            return
        self.label.lower()
        if self.rotation != 0:
            pix = pix.transformed(QTransform().rotate(self.rotation), Qt.SmoothTransformation)
        lw, lh = self.label.width(), self.label.height()
        ow, oh = pix.width(), pix.height()
        factor = lh / oh
        nw = int(ow * factor)
        scaled = pix.scaled(nw, lh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        if nw < lw:
            result = QPixmap(lw, lh)
            result.fill(Qt.black)
            p = QPainter(result)
            x = (lw - nw) // 2
            p.drawPixmap(x, 0, scaled)
            p.end()
        else:
            x = (nw - lw) // 2
            result = scaled.copy(x, 0, lw, lh)
        import os
        gradient_path = os.path.join(os.path.dirname(__file__), "..", "..", "gui_template", "gradient", "gradient_1.png")
        grad_path_abs = os.path.abspath(gradient_path)
        if self._show_gradient:
            if not os.path.exists(grad_path_abs):
                print(f"[BackgroundManager] Gradient file not found: {grad_path_abs}")
            grad = QPixmap(grad_path_abs)
            if grad.isNull():
                print(f"[BackgroundManager] Gradient QPixmap is null: {grad_path_abs}")
            if not grad.isNull():
                gs = grad.scaled(lw, lh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                p2 = QPainter(result)
                p2.setOpacity(1.0)
                p2.drawPixmap(0, 0, gs)
                p2.end()
        self.label.setPixmap(result)
        # if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting render_pixmap: return=None")

    def update_background(self) -> None:
        """
        Inputs:
            None
        Outputs:
            None
        """
        # if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering update_background: args=")
        pix = self.get_pixmap()
        if pix:
            self.render_pixmap(pix)
        # if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting update_background: return=None")

    def close(self) -> None:
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Entering close: args=")
        self.thread.stop()
        self.thread.wait()
        if DEBUG_BackgroundManager: print(f"[DEBUG][BackgroundManager] Exiting close: return=None")

    def get_background_image(self) -> QPixmap:
        """
        Retourne le QPixmap actuellement affiché (live, captured ou generated).
        """
        return self.get_pixmap()
    
    def is_work(self, flag: bool) -> None:
        """
        Active le gradient et ajuste la résolution selon le mode de travail.
        Si flag=True : gradient ON, résolution MAX.
        Si flag=False : gradient OFF, résolution MIN.
        """        
        if flag:
            # Résolution maximale (ex: index 0)
            self.background_gradient(False)
            # if hasattr(self.thread, 'set_resolution_level'):
            #     self.thread.set_resolution_level(3)
            print("[BackgroundManager] is_work(True) : mode TRAVAIL (gradient ON, résolution MAX)", file=sys.stderr)
        else:
            # Résolution minimale (ex: index le plus élevé)
            self.background_gradient(False)
            # if hasattr(self.thread, 'set_resolution_level') and hasattr(self.thread, 'get_max_resolution_index'):
            #     self.thread.set_resolution_level(0)
            print("[BackgroundManager] is_work(False) : mode REPOS (gradient ON, résolution MIN)", file=sys.stderr)