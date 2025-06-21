import sys
import os
import random
from math import ceil
from functools import lru_cache

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform, QPainter, QGuiApplication
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform, QPainter, QGuiApplication
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene

# Debug switch
DEBUG_SCROLL = False

class ImageLoader:
    """Charge et filtre les images d'un dossier"""
    VALID_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}

    @staticmethod
    def load_paths(folder_path):
        if DEBUG_SCROLL: print(f"[LOAD_PATHS] Dossier: {folder_path}")
        if not os.path.isdir(folder_path):
            raise RuntimeError(f"Dossier introuvable: {folder_path}")
        paths = [
            os.path.join(folder_path, f)
            for f in sorted(os.listdir(folder_path))
            if os.path.splitext(f.lower())[1] in ImageLoader.VALID_EXTS
        ]
        if DEBUG_SCROLL: print(f"[LOAD_PATHS] {len(paths)} images trouvées")
        return paths

@lru_cache(maxsize=256)
def get_scaled_pixmap(path, width, height):
    """Cache et retourne un QPixmap redimensionné"""
    pix = QPixmap(path)
    if pix.isNull():
        raise RuntimeError(f"Impossible de charger l'image: {path}")
    scaled = pix.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    if DEBUG_SCROLL: print(f"[CACHE] Pixmap mise en cache: {path} ({width}x{height})")
    return scaled

class Column:
    """Colonne d'images avec défilement infini"""
    def __init__(self, image_paths, x, img_w, img_h, num_rows, direction, scene):
        if DEBUG_SCROLL: print(f"[COLUMN INIT] x={x}, rows={num_rows}, dir={direction}")
        self.image_paths = image_paths
        self.x, self.img_w, self.img_h = x, img_w, img_h
        self.num_rows, self.direction = num_rows, direction
        self.scene = scene
        self.items = []
        self.total_height = img_h * num_rows
        # Précharger initial items
        for _ in range(num_rows):
            self._add_bottom()

    def _create_item(self, path, y):
        if DEBUG_SCROLL: print(f"[CREATE_ITEM] {path} at y={y}")
        pixmap = get_scaled_pixmap(path, self.img_w, self.img_h)
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(self.x, y)
        self.scene.addItem(item)
        return item

    def _add_top(self):
        if not self.items:
            return
        y = min(item.y() for item in self.items) - self.img_h
        choice = random.choice(self.image_paths)
        if DEBUG_SCROLL: print(f"[ADD_TOP] {choice} at y={y}")
        self.items.append(self._create_item(choice, y))

    def _add_bottom(self):
        y = max((item.y() for item in self.items), default=-self.img_h) + self.img_h
        choice = random.choice(self.image_paths)
        if DEBUG_SCROLL: print(f"[ADD_BOTTOM] {choice} at y={y}")
        self.items.append(self._create_item(choice, y))

    def remove_top(self):
        if not self.items:
            return
        top = min(self.items, key=lambda it: it.y())
        if DEBUG_SCROLL: print(f"[REMOVE_TOP] at y={top.y()}")
        self.scene.removeItem(top)
        self.items.remove(top)

    def remove_bottom(self):
        if not self.items:
            return
        bot = max(self.items, key=lambda it: it.y())
        if DEBUG_SCROLL: print(f"[REMOVE_BOTTOM] at y={bot.y()}")
        self.scene.removeItem(bot)
        self.items.remove(bot)

    def get_count(self):
        return len(self.items)

    def clear(self):
        if DEBUG_SCROLL: print(f"[COLUMN CLEAR] Removing {len(self.items)} items")
        for item in list(self.items):
            self.scene.removeItem(item)
        self.items.clear()

    def scroll(self, step=1, infinite=True):
        if not self.items:
            if DEBUG_SCROLL: print("[SCROLL] No items to scroll")
            return
        # Défilement unifié
        for it in list(self.items):
            new_y = it.y() + step * self.direction
            it.setY(new_y)
        if infinite:
            if self.direction < 0:
                if self.items and min(it.y() for it in self.items) + self.img_h < 0:
                    self.remove_top(); self._add_bottom()
            else:
                if self.items and max(it.y() for it in self.items) > self.total_height:
                    self.remove_bottom(); self._add_top()
        else:
            if self.direction < 0:
                if self.items and min(it.y() for it in self.items) + self.img_h < 0:
                    self.remove_top()
            else:
                if self.items and max(it.y() for it in self.items) > self.total_height:
                    self.remove_bottom()

class ScrollTab:
    """Gère plusieurs colonnes de scroll"""
    def __init__(self, image_paths, view_w, view_h, margin_x=2.5, margin_y=2.5):
        if DEBUG_SCROLL: print(f"[SCROLLTAB INIT] view=({view_w}x{view_h}), margins=({margin_x},{margin_y})")
        pix = QPixmap(image_paths[0])
        iw, ih = pix.width(), pix.height()
        diag = (view_w ** 2 + view_h ** 2) ** 0.5
        self.num_cols = max(1, int(ceil((diag / iw) * margin_x)))
        self.num_rows = max(1, int(ceil((view_h / ih) * margin_y))) + 2
        self.image_paths = image_paths
        self.columns = []
        self._col_params = [
            (i*iw, iw, ih, self.num_rows, -1 if i % 2 == 0 else 1)
            for i in range(self.num_cols)
        ]
        if DEBUG_SCROLL: print(f"[SCROLLTAB] cols={self.num_cols}, rows={self.num_rows}")

    def create_columns(self, scene):
        if DEBUG_SCROLL: print(f"[CREATE_COLUMNS] Creating columns")
        self.columns.clear()
        for params in self._col_params:
            self.columns.append(Column(self.image_paths, *params, scene))

    def get_remaining_images(self):
        return sum(col.get_count() for col in self.columns)

    def clear(self):
        if DEBUG_SCROLL: print("[SCROLLTAB CLEAR] Clearing all columns")
        for col in self.columns:
            col.clear()
        self.columns.clear()

class InfiniteScrollView(QGraphicsView):
    """Vue principale pour le scroll infini"""
    def __init__(self, folder_path, scroll_speed=1, fps=60,
                 margin_x=2.5, margin_y=2.5, angle=0, parent=None):
        super().__init__(parent)
        if DEBUG_SCROLL: print("[VIEW INIT]")
        # config view
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        # scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        # params
        self.image_paths = ImageLoader.load_paths(folder_path)
        self.speed, self.fps = scroll_speed, fps
        self.margin_x, self.margin_y = margin_x, margin_y
        self.angle = angle
        # timers
        self.timer = QTimer(self); self.timer.timeout.connect(self._on_frame)
        self.stop_timer = QTimer(self); self.stop_timer.timeout.connect(self._on_stop_frame)
        self.scroll_tab = None
        self.set_angle(angle)

    def reset(self):
        if DEBUG_SCROLL: print("[RESET] Reinitialisation du scroll")
        self.timer.stop(); self.stop_timer.stop()
        self.clear()
        screen = QGuiApplication.primaryScreen()
        vw, vh = screen.size().width(), screen.size().height()
        self.scroll_tab = ScrollTab(self.image_paths, vw, vh, self.margin_x, self.margin_y)
        self.scroll_tab.create_columns(self._scene)
        self.center_view()

    def start(self):
        if DEBUG_SCROLL: print("[START] Début du scroll infini")
        if self.scroll_tab is None: self.reset()
        self.timer.start(max(1, int(1000 / self.fps)))

    def _begin_stop_animation(self, stop_speed=1):
        if DEBUG_SCROLL: print("[BEGIN_STOP] Arrêt programmé")
        self.timer.stop()
        self.stop_speed = stop_speed
        self.stop_timer.start(max(1, int(1000 / self.fps)))

    def _on_frame(self):
        if not self.scroll_tab:
            return
        for col in self.scroll_tab.columns:
            col.scroll(self.speed, infinite=True)

    def _on_stop_frame(self):
        if not self.scroll_tab:
            self.stop_timer.stop()
            return
        for col in self.scroll_tab.columns:
            col.scroll(self.stop_speed, infinite=False)
        if self.get_remaining_images() == 0:
            if DEBUG_SCROLL: print("[STOP_FRAME] Plus d'images restantes")
            self.stop_timer.stop()
            self.clear()

    def stop(self):
        if DEBUG_SCROLL: print("[STOP] Arrêt immédiat")
        self.timer.stop(); self.stop_timer.stop()
        if self.scroll_tab:
            for col in self.scroll_tab.columns:
                col.scroll(self.speed, infinite=False)

    def get_remaining_images(self):
        """Retourne le nombre total d'images restantes"""
        count = self.scroll_tab.get_remaining_images() if self.scroll_tab else 0
        if DEBUG_SCROLL: print(f"[GET_REMAINING] {count} images restantes")
        return count

    def clear(self):
        if DEBUG_SCROLL: print("[STOP] Arrêt immédiat")
        self.timer.stop(); self.stop_timer.stop()
        if self.scroll_tab:
            for col in self.scroll_tab.columns:
                col.scroll(self.speed, infinite=False)

    def clear(self):
        if DEBUG_SCROLL: print("[CLEAR] Nettoyage complet")
        self.timer.stop(); self.stop_timer.stop()
        if self.scroll_tab:
            self.scroll_tab.clear(); self.scroll_tab = None
        self._scene.clear()

    def zoom_in(self, factor=1.2):
        if DEBUG_SCROLL: print(f"[ZOOM_IN] factor={factor}")
        self.scale(factor, factor)

    def zoom_out(self, factor=1.2):
        if DEBUG_SCROLL: print(f"[ZOOM_OUT] factor={factor}")
        self.scale(1/factor, 1/factor)

    def center_view(self):
        if DEBUG_SCROLL: print("[CENTER_VIEW]")
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        rect = self._scene.sceneRect()
        self.centerOn(rect.center())

    def set_angle(self, angle):
        if DEBUG_SCROLL: print(f"[SET_ANGLE] {angle}")
        self.angle = angle
        self.resetTransform()
        self.setTransform(QTransform().rotate(angle))
        self.center_view()

class InfiniteScrollWidget(QWidget):
    """
    Wrapper widget that encapsulates an infinite scrolling image view,
    exposing a QLabel-like API similar to QMovie.
    """
    def __init__(self, folder_path, scroll_speed=1, fps=60,
                 margin_x=2.5, margin_y=2.5, angle=0, parent=None):
        super().__init__(parent)
        # Set up internal graphics view
        self._view = InfiniteScrollView(folder_path, scroll_speed,
                                        fps, margin_x, margin_y, angle)
        # Layout to contain the view
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)
        self.setLayout(layout)
        # Playback state
        self._is_running = False

    def start(self):
        """Start the scrolling animation."""
        if not self._is_running:
            self._view.start()
            self._is_running = True

    def stop(self):
        """Immediately stop the scrolling animation."""
        if self._is_running:
            self._view.stop()
            self._is_running = False

    def begin_stop(self, stop_speed=1):
        """Stop the animation gradually with a given speed."""
        if self._is_running:
            self._view._begin_stop_animation(stop_speed)
            self._is_running = False

    def setAngle(self, angle):
        """Rotate the entire view by the given angle."""
        self._view.set_angle(angle)

    def zoomIn(self, factor=1.2):
        """Zoom in by the factor."""
        self._view.zoom_in(factor)

    def zoomOut(self, factor=1.2):
        """Zoom out by the factor."""
        self._view.zoom_out(factor)

    def clear(self):
        """Clear all items and reset the view."""
        self._view.clear()

    def isRunning(self):
        """Return True if the animation is active."""
        return self._is_running

    def setSpeed(self, speed):
        """Dynamically adjust scroll speed."""
        self._view.speed = speed

    def sizeHint(self):
        """Provide a sensible default size."""
        screen = QGuiApplication.primaryScreen()
        return screen.size()




    # Example usage:
    # widget = InfiniteScrollWidget('/path/to/images', scroll_speed=2, fps=60, angle=15)
    # widget.show()  # can be added to any layout or window
    # widget.start()

# from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout


# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         central = QWidget()
#         self.setCentralWidget(central)

#         # Création d'une grille
#         grid = QGridLayout(central)
#         central.setLayout(grid)

#         # Instanciation du widget de scroll infini
#         scroll_widget = InfiniteScrollWidget(
#             './gui_template/sleep_picture',
#             scroll_speed=2,
#             fps=60,
#             margin_x=1,
#             margin_y=1,
#             angle=15
#         )

#         # On l'ajoute comme un QLabel dans la grille :
#         grid.addWidget(scroll_widget, 0, 0)   # ligne 0, colonne 0
#         # Vous pouvez aussi le mettre ailleurs :
#         # grid.addWidget(scroll_widget, 1, 2)  # ligne 1, colonne 2

#         scroll_widget.start()

# if __name__ == '__main__':
#     app = QApplication([])
#     win = MainWindow()
#     win.show()
#     app.exec()
