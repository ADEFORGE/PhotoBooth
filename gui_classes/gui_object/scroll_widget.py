DEBUG_ImageLoader = False
DEBUG_Column = False
DEBUG_ScrollTab = False
DEBUG_InfiniteScrollView = False
DEBUG_InfiniteScrollWidget = False
DEBUG_ScrollOverlay = False

import os
import random
from math import ceil
from functools import lru_cache
from collections import deque
from typing import List, Optional, Callable
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform, QPainter, QGuiApplication
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget, QVBoxLayout, QLabel
)

class ImageLoader:
    @staticmethod
    def load_paths(folder_path: str) -> List[str]:
        if DEBUG_ImageLoader:
            print(f"[DEBUG][ImageLoader] Entering load_paths: args={{'folder_path':{folder_path}}}")
        if not os.path.isdir(folder_path):
            raise RuntimeError(f"Dossier introuvable: {folder_path}")
        paths = [
            os.path.join(folder_path, f)
            for f in sorted(os.listdir(folder_path))
            if os.path.splitext(f.lower())[1] in {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        ]
        if DEBUG_ImageLoader:
            print(f"[DEBUG][ImageLoader] Exiting load_paths: return={paths}")
        return paths

@lru_cache(maxsize=256)
def get_scaled_pixmap(path: str, width: int, height: int) -> QPixmap:
    if DEBUG_ImageLoader:
        print(f"[DEBUG][ImageLoader] Entering get_scaled_pixmap: args={{'path':{path}, 'width':{width}, 'height':{height}}}")
    pix = QPixmap(path)
    if pix.isNull():
        raise RuntimeError(f"Impossible de charger l'image: {path}")
    scaled = pix.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    if DEBUG_ImageLoader:
        print(f"[DEBUG][ImageLoader] Exiting get_scaled_pixmap: return={scaled}")
    return scaled

class Column:
    def __init__(
        self,
        image_paths: List[str],
        x: float,
        img_w: int,
        img_h: int,
        num_rows: int,
        direction: int,
        scene: QGraphicsScene,
        gradient_only: bool = False
    ) -> None:
        self.image_paths = image_paths
        self.x, self.img_w, self.img_h = x, img_w, img_h
        self.num_rows, self.direction = num_rows, direction
        self.scene = scene
        self.total_height = img_h * num_rows

        # flags
        self._all_changed_once = False
        self._changed_count = 0
        self._changed_total = num_rows
        self.gradient_only = gradient_only

        # cache des QPixmaps déjà scalés
        self._pixmap_cache = {
            path: get_scaled_pixmap(path, img_w, img_h)
            for path in set(image_paths + ["gui_template/gradient/gradient_3.png"])
        }

        # remplissage initial dans une liste temporaire
        temp_items = []
        if gradient_only:
            for _ in range(num_rows):
                temp_items.append(self._create_item("gui_template/gradient/gradient_3.png",
                                                   len(temp_items) * self.img_h))
        else:
            y = 0
            for _ in range(num_rows):
                choice = random.choice(self.image_paths)
                temp_items.append(self._create_item(choice, y))
                y += self.img_h

        # tri par y puis conversion en deque
        temp_items.sort(key=lambda it: it.y())
        self.items = deque(temp_items)

        # bornes actuelles
        self._min_y = self.items[0].y()
        self._max_y = self.items[-1].y()

    def _create_item(self, path: str, y: float) -> QGraphicsPixmapItem:
        # === MODIF : on prend la pixmap depuis le cache au lieu de la rescaler à chaque fois ===
        pixmap = self._pixmap_cache[path]
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(self.x, y)
        self.scene.addItem(item)
        return item

    def _add_top(self, image_path: Optional[str] = None) -> None:
        if not self.items:
            return
        y = min(item.y() for item in self.items) - self.img_h
        choice = image_path if image_path is not None else random.choice(self.image_paths)
        if DEBUG_Column:
            print(f"[DEBUG][Column] Entering _add_top: args={{'image_path':{image_path}}}")
        self.items.append(self._create_item(choice, y))
        if DEBUG_Column:
            print(f"[DEBUG][Column] Exiting _add_top: return=None")

    def _add_bottom(self, image_path: Optional[str] = None) -> None:
        if DEBUG_Column:
            print(f"[DEBUG][Column] Entering _add_bottom: args={{'image_path':{image_path}}}")
        y = max((item.y() for item in self.items), default=-self.img_h) + self.img_h
        choice = image_path if image_path is not None else random.choice(self.image_paths)
        self.items.append(self._create_item(choice, y))
        if DEBUG_Column:
            print(f"[DEBUG][Column] Exiting _add_bottom: return=None")

    def remove_top(self) -> None:
        if DEBUG_Column:
            print(f"[DEBUG][Column] Entering remove_top: args={{}}")
        if not self.items:
            return
        top = min(self.items, key=lambda it: it.y())
        self.scene.removeItem(top)
        self.items.remove(top)
        if DEBUG_Column:
            print(f"[DEBUG][Column] Exiting remove_top: return=None")

    def remove_bottom(self) -> None:
        if DEBUG_Column:
            print(f"[DEBUG][Column] Entering remove_bottom: args={{}}")
        if not self.items:
            return
        bot = max(self.items, key=lambda it: it.y())
        self.scene.removeItem(bot)
        self.items.remove(bot)
        if DEBUG_Column:
            print(f"[DEBUG][Column] Exiting remove_bottom: return=None")

    def get_count(self) -> int:
        if DEBUG_Column:
            print(f"[DEBUG][Column] Entering get_count: args={{}}")
        count = len(self.items)
        if DEBUG_Column:
            print(f"[DEBUG][Column] Exiting get_count: return={count}")
        return count

    def clear(self) -> None:
        if DEBUG_Column:
            print(f"[DEBUG][Column] Entering clear: args={{}}")
        for item in list(self.items):
            self.scene.removeItem(item)
        self.items.clear()
        if DEBUG_Column:
            print(f"[DEBUG][Column] Exiting clear: return=None")

    def get_endstart(self) -> bool:
        if DEBUG_Column:
            print(f"[DEBUG][Column] Exiting get_endstart: return={self._all_changed_once}")
        return self._all_changed_once

    def scroll(self, step: float = 1.0, infinite: bool = True) -> bool:
        """
        - infinite=True : on recalcule le nombre d'items sortis et on les recycle exactement.
        - infinite=False: on supprime simplement les items hors-écran.
        Retourne True dès que (_all_changed_once) vient d’être validé.
        """
        # 1) Déplacer tous les items
        for it in self.items:
            it.setY(it.y() + step * self.direction)

        changed = 0

        if infinite:
            if self.direction < 0:
                # scroll vers le haut : combien ont disparu au-dessus ?
                out_count = sum(1 for it in self.items if it.y() + self.img_h < 0)
                for _ in range(out_count):
                    # choisit l'item le plus haut
                    it = min(self.items, key=lambda i: i.y())
                    # calcule la nouvelle y au bas de la colonne
                    max_y = max(i.y() for i in self.items)
                    new_y = max_y + self.img_h
                    it.setY(new_y)
                    # change la pixmap
                    choice = random.choice(self.image_paths)
                    it.setPixmap(self._pixmap_cache[choice])
                    changed += 1

            else:
                # scroll vers le bas : combien ont disparu en-dessous ?
                out_count = sum(1 for it in self.items if it.y() > self.total_height)
                for _ in range(out_count):
                    # choisit l'item le plus bas
                    it = max(self.items, key=lambda i: i.y())
                    min_y = min(i.y() for i in self.items)
                    new_y = min_y - self.img_h
                    it.setY(new_y)
                    choice = random.choice(self.image_paths)
                    it.setPixmap(self._pixmap_cache[choice])
                    changed += 1

        else:
            # mode arrêt : suppression pure
            if self.direction < 0:
                for it in list(self.items):
                    if it.y() + self.img_h < 0:
                        self.scene.removeItem(it)
                        self.items.remove(it)
            else:
                for it in list(self.items):
                    if it.y() > self.total_height:
                        self.scene.removeItem(it)
                        self.items.remove(it)

        # 2) Flag “tout changé une fois”
        if infinite and not self._all_changed_once:
            self._changed_count += changed
            if self._changed_count >= self._changed_total:
                self._all_changed_once = True
                return True

        return False


class ScrollTab:
    def __init__(
        self,
        image_paths: List[str],
        view_w: int,
        view_h: int,
        margin_x: float = 2.5,
        margin_y: float = 2.5,
        gradient_only: bool = False
    ) -> None:
        pix = QPixmap(image_paths[0])
        iw, ih = pix.width(), pix.height()
        diag = (view_w ** 2 + view_h ** 2) ** 0.5

        # Retour au calcul diagonal pour bien couvrir écran
        self.num_cols = max(1, int(ceil((diag / iw) * margin_x)))
        self.num_rows = max(1, int(ceil((diag / ih) * margin_y))) + 2

        self.image_paths = image_paths
        self.columns: List[Column] = []
        self.gradient_only = gradient_only

        self._col_params = [
            (i * iw, iw, ih, self.num_rows, -1 if i % 2 == 0 else 1)
            for i in range(self.num_cols)
        ]

    def create_columns(self, scene: QGraphicsScene) -> None:
        if DEBUG_ScrollTab:
            print(f"[DEBUG][ScrollTab] Entering create_columns: args={{}}")
        self.columns.clear()
        for params in self._col_params:
            self.columns.append(Column(self.image_paths, *params, scene, gradient_only=self.gradient_only))
        if DEBUG_ScrollTab:
            print(f"[DEBUG][ScrollTab] Exiting create_columns: return=None")

    def get_remaining_images(self) -> int:
        if DEBUG_ScrollTab:
            print(f"[DEBUG][ScrollTab] Entering get_remaining_images: args={{}}")
        count = sum(col.get_count() for col in self.columns)
        if DEBUG_ScrollTab:
            print(f"[DEBUG][ScrollTab] Exiting get_remaining_images: return={count}")
        return count

    def get_endstart(self) -> bool:
        for col in self.columns:
            if col.get_endstart():
                if DEBUG_ScrollTab :
                    print(f"[DEBUG][ScrollTab] Exiting get_endstart: return=True")
                return True
        return False

    def clear(self) -> None:
        if DEBUG_ScrollTab:
            print(f"[DEBUG][ScrollTab] Entering clear: args={{}}")
        for col in self.columns:
            col.clear()
        self.columns.clear()
        if DEBUG_ScrollTab:
            print(f"[DEBUG][ScrollTab] Exiting clear: return=None")

class InfiniteScrollView(QGraphicsView):
    def __init__(self, folder_path: str, scroll_speed: float = 1.0, fps: int = 60,
                 margin_x: float = 2.5, margin_y: float = 2.5, angle: float = 0, parent=None) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering __init__: args={{...}}")
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(Qt.transparent)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self._scene = QGraphicsScene(self)
        self._scene.setBackgroundBrush(Qt.transparent)
        self.setScene(self._scene)
        self.image_paths = ImageLoader.load_paths(folder_path)
        self.speed, self.fps = float(scroll_speed), fps
        self.margin_x, self.margin_y = margin_x, margin_y
        self.angle = angle
        self.scroll_tab: Optional[ScrollTab] = None
        self.set_angle(angle)
        self._stopping = False
        self._stop_speed = None
        self._stop_callback = None
        self._starting = False
        self._start_speed = None
        self._start_callback = None
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting __init__: return=None")

    def drawBackground(self, painter: QPainter, rect) -> None:
        painter.fillRect(rect, Qt.transparent)

    def reset(self, gradient_only: bool = True) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering reset: args={{'gradient_only':{gradient_only}}}")
        screen = QGuiApplication.primaryScreen()
        vw, vh = screen.size().width(), screen.size().height()
        self.scroll_tab = ScrollTab(self.image_paths, vw, vh, self.margin_x, self.margin_y, gradient_only=gradient_only)
        self.scroll_tab.create_columns(self._scene)
        self.center_view()
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting reset: return=None")

    def start(self, restart: bool = False) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering start: args={{'restart':{restart}}}")
        if self.scroll_tab is None:
            self.reset(gradient_only=restart)
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting start: return=None")

    def update_frame(self) -> None:
        if self._stopping:
            self._on_stop_frame()
        elif self._starting:
            self._on_start_frame()
        else:
            self._on_frame()

    def _on_frame(self) -> None:
        if not self.scroll_tab:
            return
        for col in self.scroll_tab.columns:
            col.scroll(self.speed, infinite=True)

    def _begin_stop_animation(self, stop_speed: float = 6.0, on_finished: Optional[Callable] = None) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering _begin_stop_animation: args={{...}}")
        self._stopping = True
        self._stop_speed = float(stop_speed)
        self._stop_callback = on_finished
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting _begin_stop_animation: return=None")

    def _begin_start_animation(self, start_speed: float = 6.0, on_finished: Optional[Callable] = None) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering _begin_start_animation: args={{...}}")
        self._starting = True
        self._start_speed = float(start_speed)
        self._start_callback = on_finished
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting _begin_start_animation: return=None")

    def _on_stop_frame(self) -> None:
        if not self.scroll_tab:
            self._stopping = False
            if self._stop_callback:
                self._stop_callback()
            return
        for col in self.scroll_tab.columns:
            col.scroll(self._stop_speed, infinite=False)
        if self.scroll_tab.get_remaining_images() == 0:
            self._stopping = False
            self._scene.clear()
            if self._stop_callback:
                self._stop_callback()

    def _on_start_frame(self) -> None:
        for col in self.scroll_tab.columns:
            col.scroll(self._start_speed, infinite=True)
            if  self.scroll_tab.get_endstart() and self._starting:
                self._starting = False
                if self._start_callback:
                    self._start_callback()

    def stop(self) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering stop: args={{}}")
        if self.scroll_tab:
            for col in self.scroll_tab.columns:
                col.scroll(self.speed, infinite=False)
        self._stopping = False
        self._stop_speed = None
        self._stop_callback = None
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting stop: return=None")

    def clear(self) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering clear: args={{}}")
        if self.scroll_tab:
            self.scroll_tab.clear()
            self.scroll_tab = None
        self._scene.clear()
        self._stopping = False
        self._stop_speed = None
        self._stop_callback = None
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting clear: return=None")

    def zoom_in(self, factor: float = 1.2) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering zoom_in: args={{'factor':{factor}}}")
        self.scale(factor, factor)
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting zoom_in: return=None")

    def zoom_out(self, factor: float = 1.2) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering zoom_out: args={{'factor':{factor}}}")
        self.scale(1 / factor, 1 / factor)
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting zoom_out: return=None")

    def center_view(self) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering center_view: args={{}}")
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        rect = self._scene.sceneRect()
        self.centerOn(rect.center())
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting center_view: return=None")

    def set_angle(self, angle: float) -> None:
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Entering set_angle: args={{'angle':{angle}}}")
        self.angle = angle
        self.resetTransform()
        self.setTransform(QTransform().rotate(angle))
        self.center_view()
        if DEBUG_InfiniteScrollView:
            print(f"[DEBUG][InfiniteScrollView] Exiting set_angle: return=None")

class InfiniteScrollWidget(QWidget):
    def __init__(self, folder_path: str, scroll_speed: float = 1.0, fps: int = 60,
                 margin_x: float = 2.5, margin_y: float = 2.5, angle: float = 0, parent=None) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering __init__: args={{...}}")
        super().__init__(parent)
        self._view = InfiniteScrollView(folder_path, scroll_speed, fps, margin_x, margin_y, angle)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)
        self._is_running = False
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting __init__: return=None")

    def update_frame(self) -> None:
        self._view.update_frame()

    def start(self, restart: bool = False) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering start: args={{'restart': {restart}}}")
        if not self._is_running:
            self._view.start(restart=restart)
            self._is_running = True
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting start: return=None")

    def stop(self) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering stop: args={{}}")
        if self._is_running:
            self._view.stop()
            self._is_running = False
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting stop: return=None")

    def begin_stop(self, stop_speed: int = 1, on_finished: Optional[Callable] = None) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering begin_stop: args={{...}}")
        if self._is_running:
            self._view._begin_stop_animation(stop_speed, on_finished)
            self._is_running = False
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting begin_stop: return=None")

    def begin_start(self, start_speed: int = 1, on_finished: Optional[Callable] = None) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering begin_start: args={{...}}")
        if self._is_running:
            self._view._begin_start_animation(start_speed, on_finished)
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting begin_start: return=None")

    def setAngle(self, angle: float) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering setAngle: args={{'angle':{angle}}}")
        self._view.set_angle(angle)
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting setAngle: return=None")

    def zoomIn(self, factor: float = 1.2) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering zoomIn: args={{'factor':{factor}}}")
        self._view.zoom_in(factor)
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting zoomIn: return=None")

    def zoomOut(self, factor: float = 1.2) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering zoomOut: args={{'factor':{factor}}}")
        self._view.zoom_out(factor)
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting zoomOut: return=None")

    def clear(self) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering clear: args={{}}")
        self._view.clear()
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting clear: return=None")

    def isRunning(self) -> bool:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering isRunning: args={{}}")
        state = self._is_running
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting isRunning: return={state}")
        return state

    def setSpeed(self, speed: float) -> None:
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering setSpeed: args={{'speed':{speed}}}")
        self._view.speed = float(speed)
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting setSpeed: return=None")

    def sizeHint(self):
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Entering sizeHint: args={{}}")
        screen = QGuiApplication.primaryScreen()
        size = screen.size()
        if DEBUG_InfiniteScrollWidget:
            print(f"[DEBUG][InfiniteScrollWidget] Exiting sizeHint: return={size}")
        return size

class ScrollOverlay(QWidget):
    def __init__(self, parent=None) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering __init__: args={{'parent': parent}}")
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        if parent:
            self.setGeometry(0, 0, parent.width(), parent.height())
        self.hide()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.scroll_widget = InfiniteScrollWidget(
            './gui_template/sleep_picture',
            scroll_speed=0.4,
            fps=20,
            margin_x=1,
            margin_y=1,
            angle=15
        )
        layout.addWidget(self.scroll_widget)
        self.gradient_label = QLabel(self)
        self.gradient_label.setAttribute(Qt.WA_TranslucentBackground)
        self.gradient_label.setStyleSheet("background: transparent;")
        self.gradient_label.setVisible(True)
        self._set_gradient_pixmap()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting __init__: return=None")

    def resizeEvent(self, event) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering resizeEvent: args={{'event': event}}")
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        super().resizeEvent(event)
        self._resize_gradient()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting resizeEvent: return=None")

    def _set_gradient_pixmap(self, path: str = "gui_template/gradient/gradient_0.png") -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering _set_gradient_pixmap: args={{'path':{path}}}")
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.gradient_label.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            self.gradient_label.setGeometry(0, 0, self.width(), self.height())
            self.gradient_label.raise_()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting _set_gradient_pixmap: return=None")

    def _resize_gradient(self) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering _resize_gradient: args={{}}")
        pixmap = self.gradient_label.pixmap()
        if pixmap:
            self.gradient_label.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            self.gradient_label.setGeometry(0, 0, self.width(), self.height())
            self.gradient_label.raise_()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting _resize_gradient: return=None")

    def raise_overlay(self, on_raised: Optional[Callable] = None) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering raise_overlay: args={{'on_raised':{on_raised}}}")
        self.raise_()
        if on_raised:
            on_raised()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting raise_overlay: return=None")

    def lower_overlay(self, on_lowered: Optional[Callable] = None) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering lower_overlay: args={{'on_lowered':{on_lowered}}}")
        self.lower()
        if on_lowered:
            on_lowered()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting lower_overlay: return=None")

    def start_scroll_animation(self, stop_speed: int = 30, on_finished: Optional[Callable] = None) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering start_scroll_animation: args={{'stop_speed':{stop_speed}, 'on_finished':{on_finished}}}")
        if self.scroll_widget:
            self.scroll_widget.begin_stop(stop_speed=stop_speed, on_finished=on_finished)
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting start_scroll_animation: return=None")

    def restart_scroll_animation(self, start_speed: int = 30, on_finished: Optional[Callable] = None) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering restart_scroll_animation: args={{'start_speed': start_speed, 'on_finished': on_finished}}")
        if self.scroll_widget:
            self.lower_overlay(on_lowered=lambda: [
                self.show_overlay(on_shown=lambda: self.scroll_widget.begin_start(start_speed=start_speed, on_finished=on_finished), restart=True)
            ])
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting restart_scroll_animation: return=None")

    def clean_scroll(self, on_cleaned: Optional[Callable] = None) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering clean_scroll: args={{'on_cleaned':{on_cleaned}}}")
        if self.scroll_widget:
            self.scroll_widget.clear()
        if on_cleaned:
            on_cleaned()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting clean_scroll: return=None")

    def clear_overlay(self, on_cleared: Optional[Callable] = None) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering clear_overlay: args={{'on_cleared':{on_cleared}}}")
        self.hide()
        self.deleteLater()
        self.scroll_widget = None
        if on_cleared:
            on_cleared()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting clear_overlay: return=None")

    def hide_overlay(self, on_hidden: Optional[Callable] = None) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering hide_overlay: args={{'on_hidden':{on_hidden}}}")
        if self.isVisible():
            self.hide()
        if on_hidden:
            on_hidden()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting hide_overlay: return=None")

    def show_overlay(self, on_shown: Optional[Callable] = None, restart: bool = False) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering show_overlay: args={{'on_shown': {on_shown}, 'restart': {restart}}}")
        if not self.isVisible():
            self.show()
        running = False
        if hasattr(self.scroll_widget, 'isRunning'):
            running = self.scroll_widget.isRunning()
        if not running and self.scroll_widget:
            self.scroll_widget.start(restart=restart)
        if on_shown:
            on_shown()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting show_overlay: return=None")

    def update_frame(self) -> None:
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Entering update_frame: args={{}}")
        if self.scroll_widget:
            self.scroll_widget.update_frame()
        if DEBUG_ScrollOverlay:
            print(f"[DEBUG][ScrollOverlay] Exiting update_frame: return=None")
