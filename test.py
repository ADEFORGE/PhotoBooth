import sys
import os
import random
from math import ceil

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPixmap, QTransform, QPainter, QGuiApplication
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem


class Image:
    """Représente une image avec pixmap préchargé"""
    VALID_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}

    def __init__(self, path, width, height):
        self.path = path
        self.pixmap = QPixmap(path).scaled(width, height,
                                           Qt.IgnoreAspectRatio,
                                           Qt.SmoothTransformation)


class Column:
    """Colonne d'images avec scrolling infini"""
    def __init__(self, paths, x, img_w, img_h, count, direction, scene):
        self.paths = paths
        self.x = x
        self.w = img_w
        self.h = img_h
        self.count = count
        self.direction = direction  # -1 pour monter, 1 pour descendre
        self.scene = scene
        self.total_h = img_h * count
        self.items = []
        self._populate_initial()

    def _populate_initial(self):
        offset = random.randint(0, self.count - 1)
        for i in range(self.count):
            path = random.choice(self.paths)
            img = Image(path, self.w, self.h)
            item = QGraphicsPixmapItem(img.pixmap)
            idx = i + (-offset if self.direction < 0 else offset)
            y = (idx * self.h) % self.total_h
            item.setPos(self.x, y)
            self.scene.addItem(item)
            self.items.append(item)

    def move_up(self, step=1):
        for item in self.items:
            item.moveBy(0, -step)

    def move_down(self, step=1):
        for item in self.items:
            item.moveBy(0, step)

    def remove_top(self):
        # Supprime et retire l'item le plus en haut
        top = min(self.items, key=lambda it: it.y())
        self.scene.removeItem(top)
        self.items.remove(top)

    def remove_bottom(self):
        # Supprime et retire l'item le plus en bas
        bottom = max(self.items, key=lambda it: it.y())
        self.scene.removeItem(bottom)
        self.items.remove(bottom)

    def add_bottom(self):
        # Ajoute une image en bas
        path = random.choice(self.paths)
        img = Image(path, self.w, self.h)
        item = QGraphicsPixmapItem(img.pixmap)
        bottom_y = max(it.y() for it in self.items)
        item.setPos(self.x, bottom_y + self.h)
        self.scene.addItem(item)
        self.items.append(item)

    def add_top(self):
        # Ajoute une image en haut
        path = random.choice(self.paths)
        img = Image(path, self.w, self.h)
        item = QGraphicsPixmapItem(img.pixmap)
        top_y = min(it.y() for it in self.items)
        item.setPos(self.x, top_y - self.h)
        self.scene.addItem(item)
        self.items.append(item)

    def infinite_scroll_up(self, step=1):
        """Fait défiler vers le haut: déplace, ajoute en bas, retire en haut"""
        self.move_up(step)
        # si un item dépasse en haut
        top = min(self.items, key=lambda it: it.y())
        if top.y() + self.h < 0:
            self.remove_top()
            self.add_bottom()

    def infinite_scroll_up_no_add(self, step=1):
        """Fait défiler vers le haut sans ajout: déplace et retire en haut"""
        self.move_up(step)
        top = min(self.items, key=lambda it: it.y())
        if top.y() + self.h < 0:
            self.remove_top()

    def infinite_scroll_down(self, step=1):
        """Fait défiler vers le bas: déplace, ajoute en haut, retire en bas"""
        self.move_down(step)
        bottom = max(self.items, key=lambda it: it.y())
        if bottom.y() > self.total_h:
            self.remove_bottom()
            self.add_top()

    def infinite_scroll_down_no_add(self, step=1):
        """Fait défiler vers le bas sans ajout: déplace et retire en bas"""
        self.move_down(step)
        bottom = max(self.items, key=lambda it: it.y())
        if bottom.y() > self.total_h:
            self.remove_bottom()


class ScrollTab:
    """Gestionnaire de colonnes"""
    def __init__(self, paths, view_w, view_h, margin_x, margin_y):
        pix = QPixmap(paths[0])
        iw, ih = pix.width(), pix.height()
        self.nb_cols = max(1, int(ceil((view_w / iw) * margin_x)))
        self.nb_rows = max(1, int(ceil((view_h / ih) * margin_y))) + 2
        self.paths = paths
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.columns = []

    def create_columns(self, scene):
        for i in range(self.nb_cols):
            x = i * QPixmap(self.paths[0]).width()
            direction = -1 if i % 2 == 0 else 1
            col = Column(self.paths, x,
                         QPixmap(self.paths[0]).width(),
                         QPixmap(self.paths[0]).height(),
                         self.nb_rows, direction, scene)
            self.columns.append(col)


class InfiniteScrollView(QGraphicsView):
    """Vue principale pour le scroll infini"""
    def __init__(self, folder_path, scroll_speed=1, fps=60,
                 margin_x=2.5, margin_y=2.5, angle=0, parent=None):
        super().__init__(parent)
        self.folder = folder_path
        self.speed = scroll_speed
        self.fps = fps
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.angle = angle
        self._setup_view()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scrolltab = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_frame)

    def _setup_view(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setRenderHint(QPainter.Antialiasing)

    def reset(self):
        """Réinitialise la scène et les colonnes"""
        self.timer.stop()
        self.scene.clear()
        screen = QGuiApplication.primaryScreen()
        vw, vh = screen.size().width(), screen.size().height()
        paths = ImageLoader.load_paths(self.folder)
        self.scrolltab = ScrollTab(paths, vw, vh, self.margin_x, self.margin_y)
        self.scrolltab.create_columns(self.scene)
        self.scene.setSceneRect(self.scene.itemsBoundingRect())

    def start(self):
        """Démarre l'animation"""
        if not self.scrolltab:
            self.reset()
        # Appliquer rotation
        if self.angle:
            t = QTransform()
            rect = self.scene.sceneRect()
            cx, cy = rect.center().x(), rect.center().y()
            t.translate(cx, cy)
            t.rotate(self.angle)
            t.translate(-cx, -cy)
            self.setTransform(t)
        inv, _ = self.transform().inverted()
        bbox = self.transform().mapRect(self.scene.sceneRect())
        scene_center = inv.map(bbox.center())
        self.centerOn(scene_center)
        interval = max(1, int(1000 / self.fps))
        self.timer.start(interval)

    def _on_frame(self):
        for col in self.scrolltab.columns:
            if col.direction < 0:
                col.infinite_scroll_up(self.speed)
            else:
                col.infinite_scroll_down(self.speed)

    def end(self):
        """Arrête et nettoie en conservant la scène vide"""
        self.timer.stop()
        self.scene.clear()
        self.scrolltab = None

    def clear(self):
        """Nettoie absolument tout"""
        self.timer.stop()
        self.scene.clear()
        self.scrolltab = None

    def get_dim_scene(self):
        rect = self.scene.sceneRect()
        transformed = self.transform().mapRect(rect)
        return transformed.width(), transformed.height()

    def get_coord_view(self):
        vr = self.mapToScene(self.viewport().rect()).boundingRect()
        return (vr.x(), vr.y(), vr.width(), vr.height())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(here, './images')
    view = InfiniteScrollView(folder, scroll_speed=1, fps=60,
                               margin_x=1, margin_y=1, angle=0)
    view.setWindowTitle("Infinite Scroll")
    view.showFullScreen()
    view.start()
    QTimer.singleShot(2000, view.end)
    sys.exit(app.exec())
