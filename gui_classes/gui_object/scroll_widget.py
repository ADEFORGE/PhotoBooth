import os
import random
from math import ceil
from functools import lru_cache
from collections import deque
from typing import List, Optional, Callable
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QTransform, QPainter, QGuiApplication
from math import cos, radians
from math import atan2, degrees
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget, QVBoxLayout, QLabel
)
from PIL import Image
from screeninfo import get_monitors

import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constante import DEBUG, DEBUG_FULL
DEBUG_ImageLoader = DEBUG
DEBUG_Column = DEBUG
DEBUG_Column_FULL = DEBUG_FULL
DEBUG_ScrollTab = DEBUG
DEBUG_ScrollTab_FULL = DEBUG_FULL
DEBUG_InfiniteScrollView = DEBUG
DEBUG_InfiniteScrollView_FULL = DEBUG_FULL
DEBUG_InfiniteScrollWidget = DEBUG
DEBUG_InfiniteScrollWidget_FULL = DEBUG_FULL
DEBUG_ScrollOverlay = DEBUG
DEBUG_ScrollOverlay_FULL = DEBUG_FULL



def get_monitor_for_widget(widget: QWidget) -> object:
    """
    Return the monitor object that contains the center of the given widget.
    """
    if DEBUG_ImageLoader:
        logger.info(f"[DEBUG][ImageLoader] Entering get_monitor_for_widget: args={{'widget':{widget}}}")
    pos = widget.mapToGlobal(widget.rect().center())
    x, y = pos.x(), pos.y()
    for m in get_monitors():
        if m.x <= x < m.x + m.width and m.y <= y < m.y + m.height:
            return m
    if DEBUG_ImageLoader:
        logger.info(f"[DEBUG][ImageLoader] Exiting get_monitor_for_widget: return={get_monitors()[0]}")
    return get_monitors()[0]

class ImageLoader:
    @staticmethod
    def load_paths(folder_path: str) -> list[str]:
        """
        Load and return a list of image file paths from the specified folder.
        """
        if DEBUG_ImageLoader:
            logger.info(f"[DEBUG][ImageLoader] Entering load_paths: args={{'folder_path':{folder_path}}}")
        if not os.path.isdir(folder_path):
            raise RuntimeError(f"Dossier introuvable: {folder_path}")
        paths = [
            os.path.join(folder_path, f)
            for f in sorted(os.listdir(folder_path))
            if os.path.splitext(f.lower())[1] in {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        ]
        if DEBUG_ImageLoader:
            logger.info(f"[DEBUG][ImageLoader] Exiting load_paths: return={paths}")
        return paths

    @staticmethod
    def resize_images_in_folder(folder_path: str, width: int = 340) -> None:
        """
        Resize all images in the specified folder to the given width, maintaining aspect ratio
        and replacing the original files.
        """
        if DEBUG_ImageLoader:
            logger.info(f"[DEBUG][ImageLoader] Entering resize_images_in_folder: args={{'folder_path':{folder_path}, 'width':{width}}}")
        for f in sorted(os.listdir(folder_path)):
            ext = os.path.splitext(f.lower())[1]
            if ext in {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}:
                img_path = os.path.join(folder_path, f)
                try:
                    with Image.open(img_path) as im:
                        w, h = im.size
                        if w == width:
                            continue  
                        ratio = h / w
                        new_h = int(width * ratio)
                        im = im.resize((width, new_h), Image.LANCZOS)
                        im.save(img_path)
                except Exception as e:
                    logger.error(f"[ImageLoader] Erreur lors du redimensionnement de {img_path}: {e}")
        if DEBUG_ImageLoader:
            logger.info(f"[DEBUG][ImageLoader] Exiting resize_images_in_folder: return=None")

@lru_cache(maxsize=256)
def get_scaled_pixmap(path: str, width: int, height: int) -> QPixmap:
    if DEBUG_ImageLoader:
        logger.error(f"[DEBUG][ImageLoader] Entering get_scaled_pixmap: args={{'path':{path}, 'width':{width}, 'height':{height}}}")
    pix = QPixmap(path)
    if pix.isNull():
        raise RuntimeError(f"Impossible de charger l'image: {path}")
    scaled = pix.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    if DEBUG_ImageLoader:
        logger.error(f"[DEBUG][ImageLoader] Exiting get_scaled_pixmap: return={scaled}")
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
        """
        Initialize a Column with image paths, position, size, row count, direction, scene, and gradient option.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering __init__: args={{'image_paths':{image_paths}, 'x':{x}, 'img_w':{img_w}, 'img_h':{img_h}, 'num_rows':{num_rows}, 'direction':{direction}, 'scene':{scene}, 'gradient_only':{gradient_only}}}")
        self.image_paths = image_paths
        self.x, self.img_w, self.img_h = x, img_w, img_h
        self.num_rows, self.direction = num_rows, direction
        self.scene = scene
        self.total_height = img_h * num_rows

        self._all_changed_once = False
        self._changed_count = 0
        self._changed_total = num_rows
        self.gradient_only = gradient_only

        self._pixmap_cache = {
            path: get_scaled_pixmap(path, img_w, img_h)
            for path in set(image_paths + ["gui_template/gradient/gradient_3.png"])
        }

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

        temp_items.sort(key=lambda it: it.y())
        self.items = deque(temp_items)

        self._min_y = self.items[0].y()
        self._max_y = self.items[-1].y()

        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting __init__: return=None")

    def _create_item(self, path: str, y: float) -> QGraphicsPixmapItem:
        """
        Create a QGraphicsPixmapItem at the given path and y position.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering _create_item: args={{'path':{path}, 'y':{y}}}")
        pixmap = self._pixmap_cache[path]
        item = QGraphicsPixmapItem(pixmap)
        item.setPos(self.x, y)
        self.scene.addItem(item)
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting _create_item: return={item}")
        return item

    def _add_top(self, image_path: Optional[str] = None) -> None:
        """
        Add a new item to the top of the column, optionally with a specific image path.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering _add_top: args={{'image_path':{image_path}}}")
        if not self.items:
            return
        y = min(item.y() for item in self.items) - self.img_h
        choice = image_path if image_path is not None else random.choice(self.image_paths)
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering _add_top: args={{'image_path':{image_path}}}")
        self.items.append(self._create_item(choice, y))
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting _add_top: return=None")

    def _add_bottom(self, image_path: Optional[str] = None) -> None:
        """
        Add a new item to the bottom of the column, optionally with a specific image path.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering _add_bottom: args={{'image_path':{image_path}}}")
        y = max((item.y() for item in self.items), default=-self.img_h) + self.img_h
        choice = image_path if image_path is not None else random.choice(self.image_paths)
        self.items.append(self._create_item(choice, y))
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting _add_bottom: return=None")

    def remove_top(self) -> None:
        """
        Remove the top item from the column.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering remove_top: args={{}}")
        if not self.items:
            return
        top = min(self.items, key=lambda it: it.y())
        self.scene.removeItem(top)
        self.items.remove(top)
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting remove_top: return=None")

    def remove_bottom(self) -> None:
        """
        Remove the bottom item from the column.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering remove_bottom: args={{}}")
        if not self.items:
            return
        bot = max(self.items, key=lambda it: it.y())
        self.scene.removeItem(bot)
        self.items.remove(bot)
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting remove_bottom: return=None")

    def get_count(self) -> int:
        """
        Return the number of items in the column.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering get_count: args={{}}")
        count = len(self.items)
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting get_count: return={count}")
        return count

    def clear(self) -> None:
        """
        Remove all items from the column.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Entering clear: args={{}}")
        for item in list(self.items):
            self.scene.removeItem(item)
        self.items.clear()
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting clear: return=None")

    def get_endstart(self) -> bool:
        """
        Return True if all items have changed at least once, otherwise False.
        """
        if DEBUG_Column:
            logger.info(f"[DEBUG][Column] Exiting get_endstart: return={self._all_changed_once}")
        return self._all_changed_once

    def scroll(self, step: float = 1.0, infinite: bool = True) -> bool:
        """
        Scroll the column by a given step, optionally in infinite mode. Returns True if all items have changed
        """
        if DEBUG_Column_FULL:
            logger.info(f"[DEBUG][Column] Entering scroll: args={{'step':{step}, 'infinite':{infinite}}}")
        for it in self.items:
            it.setY(it.y() + step * self.direction)

        changed = 0

        if infinite:
            if self.direction < 0:
                out_count = sum(1 for it in self.items if it.y() + self.img_h < 0)
                for _ in range(out_count):
                    it = min(self.items, key=lambda i: i.y())
                    max_y = max(i.y() for i in self.items)
                    new_y = max_y + self.img_h
                    it.setY(new_y)
                    choice = random.choice(self.image_paths)
                    it.setPixmap(self._pixmap_cache[choice])
                    changed += 1

            else:
                out_count = sum(1 for it in self.items if it.y() > self.total_height)
                for _ in range(out_count):
                    it = max(self.items, key=lambda i: i.y())
                    min_y = min(i.y() for i in self.items)
                    new_y = min_y - self.img_h
                    it.setY(new_y)
                    choice = random.choice(self.image_paths)
                    it.setPixmap(self._pixmap_cache[choice])
                    changed += 1

        else:
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

        if infinite and not self._all_changed_once:
            self._changed_count += changed
            if self._changed_count >= self._changed_total:
                self._all_changed_once = True
                if DEBUG_Column_FULL:
                    logger.info(f"[DEBUG][Column] Exiting scroll: return=True (all changed once)")
                return True

        if DEBUG_Column_FULL:
            logger.info(f"[DEBUG][Column] Exiting scroll: return=False")
        return False

class ScrollTab:
    def __init__(
        self,
        image_paths: List[str],
        view_w: int,
        view_h: int,
        margin_x: float = 1.1,
        margin_y: float = 1.1,
        angle: float = 0.0,
        gradient_only: bool = False
    ) -> None:
        """
        Initialize a ScrollTab with image paths, view dimensions, margins, angle, and gradient option.
        """
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Entering __init__: args={{'image_paths':{image_paths}, 'view_w':{view_w}, 'view_h':{view_h}, 'margin_x':{margin_x}, 'margin_y':{margin_y}, 'angle':{angle}, 'gradient_only':{gradient_only}}}")
        pix = QPixmap(image_paths[0])
        iw, ih = pix.width(), pix.height()
        diag = (view_w ** 2 + view_h ** 2) ** 0.5

        self.screen_width = view_w
        self.screen_height = view_h
        self.max_angle = degrees(atan2(self.screen_width, self.screen_height))
        if 0<=angle<=self.max_angle:
            phi = cos(radians(angle))
        elif angle < 0:
            phi = cos(radians(0))
        else:
            phi = cos(radians(self.max_angle))
        if phi == 0 :
            phi = 1

        view_width = self.screen_width / phi
        view_height = self.screen_height / phi

        self.num_cols = max(1, int(ceil((view_width / iw) * margin_x)))
        self.num_rows = max(1, int(ceil((view_height / ih) * margin_y))) +1       

        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] view_w={self.screen_width}, view_h={self.screen_height}, view_width={view_width}, view_height={view_height}, image_width={iw}, num_cols={self.num_cols}")

        self.image_paths = image_paths
        self.columns: List[Column] = []
        self.gradient_only = gradient_only

        self._col_params = [
            (i * iw, iw, ih, self.num_rows, -1 if i % 2 == 0 else 1)
            for i in range(self.num_cols)
        ]
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Exiting __init__: return=None")

    def create_columns(self, scene: QGraphicsScene) -> None:
        """
        Create columns for the scroll tab using the given QGraphicsScene.
        """
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Entering create_columns: args={{}}")
        self.columns.clear()
        for params in self._col_params:
            self.columns.append(Column(self.image_paths, *params, scene, gradient_only=self.gradient_only))
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Exiting create_columns: return=None")

    def get_remaining_images(self) -> int:
        """
        Return the total number of images remaining in all columns.
        """
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Entering get_remaining_images: args={{}}")
        count = sum(col.get_count() for col in self.columns)
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Exiting get_remaining_images: return={count}")
        return count

    def get_endstart(self) -> bool:
        """
        Return True if any column has had all its items changed at least once.
        """
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Entering get_endstart: args={{}}")
        for col in self.columns:
            if col.get_endstart():
                if DEBUG_ScrollTab:
                    logger.info(f"[DEBUG][ScrollTab] Exiting get_endstart: return=True")
                return True
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Exiting get_endstart: return=False")
        return False

    def clear(self) -> None:
        """
        Clear all columns and remove their items from the scene.
        """
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Entering clear: args={{}}")
        for col in self.columns:
            col.clear()
        self.columns.clear()
        if DEBUG_ScrollTab:
            logger.info(f"[DEBUG][ScrollTab] Exiting clear: return=None")

class InfiniteScrollView(QGraphicsView):
    def __init__(
        self,
        folder_path: str,
        scroll_speed: float = 1.0,
        fps: int = 60,
        margin_x: float = 2.5,
        margin_y: float = 2.5,
        angle: float = 0,
        parent=None
    ) -> None:
        """
        Initialize the InfiniteScrollView with image folder, scroll speed, fps, margins, angle, and parent widget.
        """

        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering __init__: args={{...}}")

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
        
        ImageLoader.resize_images_in_folder(folder_path, width=340)
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
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting __init__: return=None")

    def drawBackground(self, painter: QPainter, rect) -> None:
        """
        Draw a transparent background for the view.
        """
        if DEBUG_InfiniteScrollView_FULL:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering drawBackground: args={{'painter':{painter}, 'rect':{rect}}}")
        painter.fillRect(rect, Qt.transparent)
        if DEBUG_InfiniteScrollView_FULL:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting drawBackground: return=None")

    def get_physical_screen_resolution(self) -> tuple:
        """
        Return the physical screen resolution as a (width, height) tuple.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering get_physical_screen_resolution: args={{}}")
        monitor = get_monitor_for_widget(self)
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting get_physical_screen_resolution: return=({monitor.width}, {monitor.height})")
        return monitor.width, monitor.height
        
       

    def reset(self, gradient_only: bool = True) -> None:
        """
        Reset the scroll view, optionally using only gradient images.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering reset: args={{'gradient_only':{gradient_only}}}")
        vw, vh = self.get_physical_screen_resolution()
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Résolution physique détectée (screeninfo, widget): {vw}x{vh}")
        self.scroll_tab = ScrollTab(self.image_paths, vw, vh, self.margin_x, self.margin_y, self.angle, gradient_only=gradient_only)
        self.scroll_tab.create_columns(self._scene)
        self.center_view()
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting reset: return=None")

    def start(self, restart: bool = False) -> None:
        """
        Start the scroll animation, optionally restarting with gradients.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering start: args={{'restart':{restart}}}")
        if self.scroll_tab is None:
            self.reset(gradient_only=restart)
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting start: return=None")

    def update_frame(self) -> None:
        """
        Update the current animation frame.
        """
        if DEBUG_InfiniteScrollView_FULL:        
            logger.info(f"[DEBUG][InfiniteScrollView] Entering update_frame: args={{}}")
        if self._stopping:
            self._on_stop_frame()
        elif self._starting:
            self._on_start_frame()
        else:
            self._on_frame()
        if DEBUG_InfiniteScrollView_FULL:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting update_frame: return=None")

    def _on_frame(self) -> None:
        """
        Perform a single animation frame update.
        """
        if DEBUG_InfiniteScrollView_FULL:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering _on_frame: args={{}}")
        if not self.scroll_tab:
            if DEBUG_InfiniteScrollView_FULL:
                logger.info(f"[DEBUG][InfiniteScrollView] Exiting _on_frame: return=None (no scroll_tab)")
            return
        for col in self.scroll_tab.columns:
            col.scroll(self.speed, infinite=True)
        if DEBUG_InfiniteScrollView_FULL:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting _on_frame: return=None")

    def _begin_stop_animation(self, stop_speed: float = 6.0, on_finished: Optional[Callable] = None) -> None:
        """
        Begin the stop animation with a given speed and optional callback.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering _begin_stop_animation: args={{'stop_speed':{stop_speed}, 'on_finished':{on_finished}}}")
        self._stopping = True
        self._stop_speed = float(stop_speed)
        self._stop_callback = on_finished
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting _begin_stop_animation: return=None")

    def _begin_start_animation(self, start_speed: float = 6.0, on_finished: Optional[Callable] = None) -> None:
        """
        Begin the start animation with a given speed and optional callback.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering _begin_start_animation: args={{'start_speed':{start_speed}, 'on_finished':{on_finished}}}")
        self._starting = True
        self._start_speed = float(start_speed)
        self._start_callback = on_finished
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting _begin_start_animation: return=None")

    def _on_stop_frame(self) -> None:
        """
        Handle a frame update during the stop animation.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering _on_stop_frame: args={{}}")

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
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting _on_stop_frame: return=None")

    def _on_start_frame(self) -> None:
        """
        Handle a frame update during the start animation.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering _on_start_frame: args={{}}")
        for col in self.scroll_tab.columns:
            col.scroll(self._start_speed, infinite=True)
            if  self.scroll_tab.get_endstart() and self._starting:
                self._starting = False
                if self._start_callback:
                    self._start_callback()
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting _on_start_frame: return=None")

    def stop(self) -> None:
        """
        Stop the scroll animation immediately.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering stop: args={{}}")
        if self.scroll_tab:
            for col in self.scroll_tab.columns:
                col.scroll(self.speed, infinite=False)
        self._stopping = False
        self._stop_speed = None
        self._stop_callback = None
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting stop: return=None")

    def clear(self) -> None:
        """
        Clear the scroll view and reset its state.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering clear: args={{}}")
        if self.scroll_tab:
            self.scroll_tab.clear()
            self.scroll_tab = None
        self._scene.clear()
        self._stopping = False
        self._stop_speed = None
        self._stop_callback = None
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting clear: return=None")

    def zoom_in(self, factor: float = 1.2) -> None:
        """
        Zoom in the view by the given factor.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering zoom_in: args={{'factor':{factor}}}")
        self.scale(factor, factor)
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting zoom_in: return=None")

    def zoom_out(self, factor: float = 1.2) -> None:
        """
        Zoom out the view by the given factor.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering zoom_out: args={{'factor':{factor}}}")
        self.scale(1 / factor, 1 / factor)
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting zoom_out: return=None")

    def center_view(self) -> None:
        """
        Center the view on the scene.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering center_view: args={{}}")
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        rect = self._scene.sceneRect()
        self.centerOn(rect.center())
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting center_view: return=None")

    def set_angle(self, angle: float) -> None:
        """
        Set the rotation angle of the view.
        """
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Entering set_angle: args={{'angle':{angle}}}")
        self.angle = angle
        self.resetTransform()
        self.setTransform(QTransform().rotate(angle))
        self.center_view()
        if DEBUG_InfiniteScrollView:
            logger.info(f"[DEBUG][InfiniteScrollView] Exiting set_angle: return=None")

class InfiniteScrollWidget(QWidget):
    def __init__(
        self,
        folder_path: str,
        scroll_speed: float = 1.0,
        fps: int = 60,
        margin_x: float = 2.5,
        margin_y: float = 2.5,
        angle: float = 0,
        parent=None
    ) -> None:
        """
        Initialize the InfiniteScrollWidget with image folder, scroll speed, fps, margins, angle, and parent widget.
        """

        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering __init__: args={{...}}")
        super().__init__(parent)
        self._view = InfiniteScrollView(folder_path, scroll_speed, fps, margin_x, margin_y, angle)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)
        self._is_running = False
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting __init__: return=None")

    def update_frame(self) -> None:
        """
        Update the current animation frame in the underlying view.
        """
        if DEBUG_InfiniteScrollWidget_FULL:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering update_frame: args={{}}")
        self._view.update_frame()
        if DEBUG_InfiniteScrollWidget_FULL:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting update_frame: return=None")

    def start(self, restart: bool = False) -> None:
        """
        Start the scroll animation, optionally restarting with gradients.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering start: args={{'restart': {restart}}}")
        if not self._is_running:
            self._view.start(restart=restart)
            self._is_running = True
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting start: return=None")

    def stop(self) -> None:
        """
        Stop the scroll animation immediately.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering stop: args={{}}")
        if self._is_running:
            self._view.stop()
            self._is_running = False
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting stop: return=None")

    def begin_stop(self, stop_speed: int = 1, on_finished: Optional[Callable] = None) -> None:
        """
        Begin the stop animation with a given speed and optional callback.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering begin_stop: args={{'stop_speed': {stop_speed}, 'on_finished': {on_finished}}}")
        if self._is_running:
            self._view._begin_stop_animation(stop_speed, on_finished)
            self._is_running = False
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting begin_stop: return=None")

    def begin_start(self, start_speed: int = 1, on_finished: Optional[Callable] = None) -> None:
        """
        Begin the start animation with a given speed and optional callback.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering begin_start: args={{'start_speed': {start_speed}, 'on_finished': {on_finished}}}")
        if self._is_running:
            self._view._begin_start_animation(start_speed, on_finished)
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting begin_start: return=None")

    def setAngle(self, angle: float) -> None:
        """
        Set the rotation angle of the view.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering setAngle: args={{'angle':{angle}}}")
        self._view.set_angle(angle)
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting setAngle: return=None")

    def zoomIn(self, factor: float = 1.2) -> None:
        """
        Zoom in the view by the given factor.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering zoomIn: args={{'factor':{factor}}}")
        self._view.zoom_in(factor)
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting zoomIn: return=None")

    def zoomOut(self, factor: float = 1.2) -> None:
        """
        Zoom out the view by the given factor.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering zoomOut: args={{'factor':{factor}}}")
        self._view.zoom_out(factor)
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting zoomOut: return=None")

    def clear(self) -> None:
        """
        Clear the scroll view and reset its state.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering clear: args={{}}")
        self._view.clear()
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting clear: return=None")

    def isRunning(self) -> bool:
        """
        Return True if the scroll animation is currently running, otherwise False.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering isRunning: args={{}}")
        state = self._is_running
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting isRunning: return={state}")
        return state

    def setSpeed(self, speed: float) -> None:
        """
        Set the scroll speed of the view.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering setSpeed: args={{'speed':{speed}}}")
        self._view.speed = float(speed)
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting setSpeed: return=None")

    def sizeHint(self):
        """
        Return the recommended size for the widget.
        """
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Entering sizeHint: args={{}}")
        screen = QGuiApplication.primaryScreen()
        size = screen.size()
        if DEBUG_InfiniteScrollWidget:
            logger.info(f"[DEBUG][InfiniteScrollWidget] Exiting sizeHint: return={size}")
        return size

class ScrollOverlay(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the ScrollOverlay widget with an optional parent.
        """

        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering __init__: args={{'parent': parent}}")
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
            scroll_speed=0.2,
            fps=20,
            margin_x=1.05,
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
            logger.info(f"[DEBUG][ScrollOverlay] Exiting __init__: return=None")

    def resizeEvent(self, event) -> None:
        """
        Handle the resize event and update the overlay and gradient accordingly.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay_FULL:
            logger.info(f"[DEBUG][ScrollOverlay] Entering resizeEvent: args={{'event': event}}")
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        super().resizeEvent(event)
        self._resize_gradient()
        if DEBUG_ScrollOverlay_FULL:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting resizeEvent: return=None")
        self.update_frame()

    def _set_gradient_pixmap(self, path: str = "gui_template/gradient/gradient_0.png") -> None:
        """
        Set the gradient pixmap for the overlay using the specified image path.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering _set_gradient_pixmap: args={{'path':{path}}}")
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.gradient_label.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            self.gradient_label.setGeometry(0, 0, self.width(), self.height())
            self.gradient_label.raise_()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting _set_gradient_pixmap: return=None")
        self.update_frame()

    def _resize_gradient(self) -> None:
        """
        Resize the gradient pixmap to fit the overlay dimensions.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering _resize_gradient: args={{}}")
        pixmap = self.gradient_label.pixmap()
        if pixmap:
            self.gradient_label.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))
            self.gradient_label.setGeometry(0, 0, self.width(), self.height())
            self.gradient_label.raise_()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting _resize_gradient: return=None")
        self.update_frame()

    def raise_overlay(self, on_raised: Optional[Callable] = None) -> None:
        """
        Raise the overlay widget and call the optional callback when done.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering raise_overlay: args={{'on_raised':{on_raised}}}")
        self.raise_()
        if on_raised:
            on_raised()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting raise_overlay: return=None")
        self.update_frame()

    def lower_overlay(self, on_lowered: Optional[Callable] = None) -> None:
        """
        Lower the overlay widget and call the optional callback when done.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering lower_overlay: args={{'on_lowered':{on_lowered}}}")
        self.lower()
        if on_lowered:
            on_lowered()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting lower_overlay: return=None")
        self.update_frame()

    def start_scroll_animation(self, stop_speed: int = 30, on_finished: Optional[Callable] = None) -> None:
        """
        Start the scroll animation with a given stop speed and optional callback.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering start_scroll_animation: args={{'stop_speed':{stop_speed}, 'on_finished':{on_finished}}}")
        if self.scroll_widget:
            self.scroll_widget.begin_stop(stop_speed=stop_speed, on_finished=on_finished)
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting start_scroll_animation: return=None")
        self.update_frame()

    def restart_scroll_animation(self, start_speed: int = 30, on_finished: Optional[Callable] = None) -> None:
        """
        Restart the scroll animation with a given start speed and optional callback.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering restart_scroll_animation: args={{'start_speed': start_speed, 'on_finished': on_finished}}")
        if self.scroll_widget:
            self.lower_overlay(on_lowered=lambda: [
                self.show_overlay(on_shown=lambda: self.scroll_widget.begin_start(start_speed=start_speed, on_finished=on_finished), restart=True)
            ])
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting restart_scroll_animation: return=None")
        self.update_frame()

    def clean_scroll(self, on_cleaned: Optional[Callable] = None) -> None:
        """
        Clear the scroll widget and call the optional callback when done.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering clean_scroll: args={{'on_cleaned':{on_cleaned}}}")
        if self.scroll_widget:
            self.scroll_widget.clear()
        if on_cleaned:
            on_cleaned()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting clean_scroll: return=None")
        self.update_frame()

    def clear_overlay(self, on_cleared: Optional[Callable] = None) -> None:
        """
        Clear and delete the overlay, calling the optional callback when done.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering clear_overlay: args={{'on_cleared':{on_cleared}}}")
        self.hide()
        self.deleteLater()
        self.scroll_widget = None
        if on_cleared:
            on_cleared()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting clear_overlay: return=None")
        self.update_frame()

    def hide_overlay(self, on_hidden: Optional[Callable] = None) -> None:
        """
        Hide the overlay and call the optional callback when done.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering hide_overlay: args={{'on_hidden':{on_hidden}}}")
        if self.isVisible():
            self.hide()
        if on_hidden:
            on_hidden()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting hide_overlay: return=None")
        self.update_frame()

    def show_overlay(self, on_shown: Optional[Callable] = None, restart: bool = False) -> None:
        """
        Show the overlay, optionally restarting the scroll animation, and call the optional callback when done.
        """
        self.update_frame()
        if DEBUG_ScrollOverlay:
            logger.info(f"[DEBUG][ScrollOverlay] Entering show_overlay: args={{'on_shown': {on_shown}, 'restart': {restart}}}")
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
            logger.info(f"[DEBUG][ScrollOverlay] Exiting show_overlay: return=None")
        self.update_frame()

    def update_frame(self) -> None:
        """
        Update the current animation frame of the overlay and its
        """
        if DEBUG_ScrollOverlay_FULL:
            logger.info(f"[DEBUG][ScrollOverlay] Entering update_frame: args={{}}")
        if self.scroll_widget:
            self.scroll_widget.update_frame()
        if DEBUG_ScrollOverlay_FULL:
            logger.info(f"[DEBUG][ScrollOverlay] Exiting update_frame: return=None")
