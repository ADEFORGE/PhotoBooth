import sys
import os
import random
from math import ceil
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGraphicsItem,
)
from PySide6.QtGui import QPixmap, QPainter, QTransform, QGuiApplication
from PySide6.QtCore import Qt, QTimer


class InfiniteScrollView(QGraphicsView):
    def __init__(self, folder_path, scroll_speed=1, tilt_angle=30, parent=None, fps=60, on_frame=None):
        print("[SCROLE][DEBUG] __init__ start")
        super().__init__(parent)
        self.folder_path = folder_path
        self.scroll_speed = scroll_speed
        self.tilt_angle = tilt_angle
        self.fps = fps
        self.on_frame = on_frame  # callback to call after each frame (for background update)

        self.image_paths = self._load_image_paths(self.folder_path)
        if not self.image_paths:
            raise RuntimeError(f"Aucune image trouvée dans le dossier : {self.folder_path}")

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(Qt.black)

        self.columns = []
        self._populated = False  # NE PAS appeler _populate_scene ici

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_frame)
        self.set_fps(self.fps)
        self.timer.start()
        print(f"[SCROLE][DEBUG] __init__ end, timer isActive={self.timer.isActive()}")

    def set_fps(self, fps):
        self.fps = fps
        interval = max(1, int(1000 / fps))
        self.timer.setInterval(interval)

    def _on_frame(self):
        self._scroll_step()
        if self.on_frame:
            self.on_frame(self)

    def showEvent(self, event):
        print(f"[SCROLE][DEBUG] showEvent: isVisible={self.isVisible()} geometry={self.geometry()} scene={self.scene} populated={self._populated}")
        super().showEvent(event)

    def hideEvent(self, event):
        print(f"[SCROLE][DEBUG] hideEvent: isVisible={self.isVisible()} scene={self.scene}")
        super().hideEvent(event)

    def paintEvent(self, event):
        print(f"[SCROLE][DEBUG] paintEvent: isVisible={self.isVisible()} scene={self.scene} populated={self._populated}")
        super().paintEvent(event)

    def resizeEvent(self, event):
        print(f"[SCROLE][DEBUG] resizeEvent: size={self.size()} populated={self._populated}")
        super().resizeEvent(event)
        # Toujours repopuler la scène si la taille a changé (même si déjà peuplée)
        if self.viewport().width() > 0 and self.viewport().height() > 0:
            print(f"[SCROLE][DEBUG] resizeEvent: force _populate_scene (avant clear)")
            if self.scene is not None:
                self.scene.clear()
            self.columns.clear()
            self._populated = False
            self._populate_scene()
            self._populated = True

    def _load_image_paths(self, folder_path):
        valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
        files = sorted(os.listdir(folder_path))
        return [
            os.path.join(folder_path, f)
            for f in files
            if os.path.splitext(f.lower())[1] in valid_exts
        ]

    def _populate_scene(self):
        print(f"[SCROLE][DEBUG] _populate_scene: called, scene={self.scene} populated={self._populated}")
        if self.scene is None:
            print("[SCROLE][DEBUG] _populate_scene: scene is None, recreating scene")
            self.scene = QGraphicsScene(self)
            self.setScene(self.scene)
        screen = QGuiApplication.screenAt(self.mapToGlobal(self.rect().center()))
        screen_size = screen.size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()

        sample_pixmap = QPixmap(self.image_paths[0])
        orig_w = sample_pixmap.width()
        orig_h = sample_pixmap.height()

        raw_cols = (screen_width / orig_w) * 2.5
        int_cols = max(1, int(raw_cols))
        column_count = int_cols if abs(raw_cols - int_cols) < 1e-6 else int_cols + 1

        factor = 1
        scaled_w = orig_w * factor
        scaled_h = orig_h * factor

        visible_count = ceil(screen_height / scaled_h) + 2
        total_items = max(visible_count * 3, 10)
        total_h = scaled_h * total_items

        scene_w = column_count * scaled_w
        scene_h = total_h
        self.scene.setSceneRect(0, 0, scene_w, scene_h)

        original_count = len(self.image_paths)

        for col in range(column_count):
            base_x = col * scaled_w
            direction = -1 if (col % 2 == 0) else 1
            offset_steps = random.randint(0, total_items - 1)
            column_items = []

            for idx in range(total_items):
                img_path = self.image_paths[idx % original_count]
                pixmap = QPixmap(img_path).scaled(
                    int(scaled_w), int(scaled_h), Qt.IgnoreAspectRatio, Qt.SmoothTransformation
                )
                item = QGraphicsPixmapItem(pixmap)

                raw_index = idx + offset_steps if direction < 0 else idx - offset_steps
                y = (raw_index * scaled_h) % total_h

                item.setPos(base_x, y)
                self.scene.addItem(item)
                column_items.append(item)

            self.columns.append({
                "items": column_items,
                "item_h": scaled_h,
                "total_h": total_h,
                "direction": direction,
            })

        # 🎯 Centrage personnalisé : centre scène - moitié largeur colonnes
        scene_center = self.scene.sceneRect().center()

        offset_x = 0#(scaled_w * column_count) / 3
        custom_center_x = scene_center.x() - offset_x
        custom_center_y = scene_center.y()

        self.centerOn(custom_center_x, custom_center_y)

        # Appliquer l’inclinaison
        transform = QTransform()
        transform.rotate(self.tilt_angle)
        self.setTransform(transform)
        print(f"[SCROLE][DEBUG] _populate_scene: scene populated, item count={len(self.scene.items())} columns={len(self.columns)}")

    def _scroll_step(self):
        for col_data in self.columns:
            items = col_data["items"]
            h = col_data["item_h"]
            total_h = col_data["total_h"]
            direction = col_data["direction"]

            for item in items:
                new_y = item.y() + direction * self.scroll_speed
                if direction < 0 and (new_y + h) < 0:
                    new_y += total_h
                elif direction > 0 and new_y > total_h:
                    new_y -= total_h
                item.setY(new_y)

    def wheelEvent(self, event):
        event.ignore()

    def stop(self):
        print("[SCROLE][DEBUG] stop() called")
        if hasattr(self, 'timer') and self.timer.isActive():
            print("[SCROLE][DEBUG] Stopping scroll timer")
            self.timer.stop()
        else:
            print("[SCROLE][DEBUG] Timer already stopped or missing")
        if hasattr(self, 'timer'):
            print(f"[SCROLE][DEBUG] Timer object: {self.timer}")
        # Clean up graphics items and scene
        if hasattr(self, 'scene') and self.scene is not None:
            print("[SCROLE][DEBUG] Cleaning up graphics scene")
            for item in self.scene.items():
                self.scene.removeItem(item)
            self.columns.clear()
            self.scene.clear()
            self.scene.deleteLater()
            self.scene = None
        else:
            print("[SCROLE][DEBUG] No scene to clean")
        self._populated = False
        print(f"[SCROLE][DEBUG] stop() end: scene={self.scene} populated={self._populated}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Utilise le dossier sleep_picture par défaut
    images_folder = os.path.join(script_dir, "../gui_template/sleep_picture")

    window = InfiniteScrollView(
        folder_path=images_folder,
        scroll_speed=1,
        tilt_angle=30
    )
    window.setWindowTitle("Écran de veille – Centrage personnalisé")
    window.showFullScreen()

    sys.exit(app.exec())
