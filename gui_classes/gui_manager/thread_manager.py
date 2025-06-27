DEBUG_CountdownThread = False
DEBUG_Thread = False
DEBUG_ImageGenerationThread = True
DEBUG_ImageGenerationWorker = True
DEBUG_CameraCaptureThread = False

import os
import glob
import time
import cv2
from PySide6.QtCore import Qt, QObject, QThread, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QTransform
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QComboBox
from comfy_classes.comfy_class_API import ImageGeneratorAPIWrapper
from gui_classes.gui_object.overlay import OverlayCountdown, OverlayLoading
from gui_classes.gui_object.toolbox import ImageUtils

class CountdownThread(QObject):
    overlay_finished = Signal()

    class Thread(QThread):
        tick = Signal(int)
        finished = Signal()

        def __init__(self, start: int):
            """
            Inputs:
                start (int)
            Outputs:
                emits tick(int) and finished()
            """
            if DEBUG_Thread: print(f"[DEBUG][Thread] Entering __init__: args={{(start,)}}")
            super().__init__()
            self._start = start
            self._running = True
            self._finished_emitted = False
            if DEBUG_Thread: print(f"[DEBUG][Thread] Exiting __init__: return=None")

        def run(self) -> None:
            """
            Inputs: none
            Outputs: emits tick(count) every second; emits finished() at end
            """
            if DEBUG_Thread: print(f"[DEBUG][Thread] Entering run: args=()")
            count = self._start
            while self._running and count >= 0:
                self.tick.emit(count)
                time.sleep(1)
                count -= 1
            if self._running and not self._finished_emitted:
                self._finished_emitted = True
                self.finished.emit()
            if DEBUG_Thread: print(f"[DEBUG][Thread] Exiting run: return=None")

        def stop(self) -> None:
            """
            Inputs: none
            Outputs: stops the loop
            """
            if DEBUG_Thread: print(f"[DEBUG][Thread] Entering stop: args=()")
            self._running = False
            if DEBUG_Thread: print(f"[DEBUG][Thread] Exiting stop: return=None")

    def __init__(self, parent: QObject = None, count: int = 0):
        """
        Inputs:
            parent (QObject), count (int)
        Outputs:
            initializes countdown thread and overlay
        """
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering __init__: args={{(parent, count)}}")
        super().__init__(parent)
        self._parent = parent
        self._count = count
        self._thread = None
        self._overlay = None
        self._user_callback = None
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting __init__: return=None")

    def start_countdown(self, count: int = None, on_finished: callable = None) -> None:
        """
        Inputs:
            count (int), on_finished (callable)
        Outputs:
            starts countdown, shows overlay
        """
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering start_countdown: args={{(count, on_finished)}}")
        if self._thread:
            if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting start_countdown: return=None")
            return
        if count is not None:
            self._count = count
        self._user_callback = on_finished
        self._overlay = OverlayCountdown(self._parent, start=self._count)
        self._overlay.show_overlay()
        self._thread = self.Thread(self._count)
        self._thread.tick.connect(self._on_tick)
        self._thread.finished.connect(self._on_finish)
        self._thread.start()
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting start_countdown: return=None")

    def _on_tick(self, count: int) -> None:
        """
        Inputs:
            count (int)
        Outputs:
            updates overlay number
        """
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering _on_tick: args={{(count,)}}")
        if self._overlay and getattr(self._overlay, '_is_alive', True):
            if hasattr(self._overlay, 'show_number'):
                self._overlay.show_number(count)
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting _on_tick: return=None")

    def _on_finish(self) -> None:
        """
        Inputs: none
        Outputs:
            cleans up overlay and thread, emits overlay_finished, calls callback
        """
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering _on_finish: args=()")
        if self._overlay and getattr(self._overlay, '_is_alive', True):
            self._overlay.clean_overlay()
        self._overlay = None
        if self._thread:
            self._thread.stop()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
            self.overlay_finished.emit()
        if self._user_callback:
            self._user_callback()
            self._user_callback = None
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting _on_finish: return=None")

    def stop_countdown(self) -> None:
        """
        Inputs: none
        Outputs: stops countdown and removes overlay
        """
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering stop_countdown: args=()")
        if self._thread:
            self._thread.stop()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
        if self._overlay and getattr(self._overlay, '_is_alive', True):
            self._overlay.clean_overlay()
        self._overlay = None
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting stop_countdown: return=None")

    def clear_overlay(self, reason: any = None) -> None:
        """
        Inputs:
            reason (any)
        Outputs: clears overlay forcibly
        """
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering clear_overlay: args={{(reason,)}}")
        if self._overlay:
            try:
                self._overlay.blockSignals(True)
                if hasattr(self._overlay, '_anim_timer'):
                    self._overlay._anim_timer.stop()
                    self._overlay._anim_timer.timeout.disconnect()
            except Exception:
                pass
            self._overlay.clean_overlay()
        self._overlay = None
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting clear_overlay: return=None")

class ImageGenerationThread(QObject):
    finished = Signal(object)

    def __init__(self, style: any, input_image: QImage, parent: QObject = None):
        """
        Inputs:
            style (any), input_image (QImage), parent (QObject)
        Outputs: initializes API wrapper and state
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering __init__: args={{(style, input_image, parent)}}")
        super().__init__(parent)
        self.api = ImageGeneratorAPIWrapper()
        self.input_image = input_image
        self.style = style
        self._running = True
        self._thread = None
        self._worker = None
        self._loading_overlay = None
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting __init__: return=None")

    def show_loading(self) -> None:
        """
        Inputs: none
        Outputs: displays loading overlay
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering show_loading: args=()")
        for widget in QApplication.allWidgets():
            if widget.__class__.__name__ == "OverlayLoading" and widget is not self._loading_overlay:
                widget.hide()
                widget.deleteLater()
                widget.setParent(None)
        QApplication.processEvents()
        if self._loading_overlay:
            self._loading_overlay.hide()
            self._loading_overlay.deleteLater()
            self._loading_overlay.setParent(None)
            QApplication.processEvents()
            self._loading_overlay = None
        if self.parent():
            self._loading_overlay = OverlayLoading(self.parent())
            self._loading_overlay.show()
            self._loading_overlay.raise_()
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting show_loading: return=None")

    def hide_loading(self) -> None:
        """
        Inputs: none
        Outputs: hides and deletes loading overlay
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering hide_loading: args=()")
        if self._loading_overlay:
            try:
                if hasattr(self._loading_overlay, "stop_animation"):
                    self._loading_overlay.stop_animation()
                self._loading_overlay.blockSignals(True)
                parent = self._loading_overlay.parent()
                if parent and hasattr(parent, "layout") and parent.layout():
                    parent.layout().removeWidget(self._loading_overlay)
            except Exception:
                pass
            self._loading_overlay.hide()
            self._loading_overlay.setVisible(False)
            self._loading_overlay.deleteLater()
            self._loading_overlay.setParent(None)
            QApplication.processEvents()
            self._loading_overlay = None
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting hide_loading: return=None")

    def clean(self) -> None:
        """
        Inputs: none
        Outputs: stops and deletes thread and worker
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering clean: args=()")
        self.stop()
        if self._thread:
            if QThread.currentThread() != self._thread:
                if self._thread.isRunning():
                    self._thread.quit()
                    self._thread.wait()
                self._thread.deleteLater()
                self._thread = None
            else:
                QTimer.singleShot(0, self._delete_thread_safe)
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting clean: return=None")

    def _delete_thread_safe(self) -> None:
        """
        Inputs: none
        Outputs: deletes thread safely in main thread
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering _delete_thread_safe: args=()")
        if self._thread and QThread.currentThread() != self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting _delete_thread_safe: return=None")

    def start(self) -> None:
        """
        Inputs: none
        Outputs: starts background generation and shows loading
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering start: args=()")
        if self._thread and self._thread.isRunning():
            if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting start: return=None")
            return
        self.show_loading()
        self._thread = QThread()

        class ImageGenerationWorker(QObject):
            finished = Signal(object)

            def __init__(self, api: ImageGeneratorAPIWrapper, style: any, input_image: QImage):
                """
                Inputs:
                    api (ImageGeneratorAPIWrapper), style (any), input_image (QImage)
                Outputs: initializes worker
                """
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Entering __init__: args={{(api, style, input_image)}}")
                super().__init__()
                self.api = api
                self.style = style
                self.input_image = input_image
                self._running = True
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting __init__: return=None")

            def run(self) -> None:
                """
                Inputs: none
                Outputs: emits generated QImage or None
                """
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Entering run: args=()")
                try:
                    self.api.set_style(self.style)
                    if not self._running:
                        self.finished.emit(None)
                        if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")
                        return
                    arr = ImageUtils.qimage_to_cv(self.input_image)
                    os.makedirs("../ComfyUI/input", exist_ok=True)
                    cv2.imwrite("../ComfyUI/input/input.png", arr)
                    self.api.generate_image()
                    if not self._running:
                        self.finished.emit(None)
                        if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")
                        return
                    output_dir = os.path.abspath("../ComfyUI/output")
                    files = glob.glob(os.path.join(output_dir, "*.png"))
                    if not files:
                        self.finished.emit(self.input_image)
                        if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")
                        return
                    latest = max(files, key=os.path.getmtime)
                    img = cv2.imread(latest)
                    if img is None:
                        self.finished.emit(self.input_image)
                        if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")
                        return
                    qimg = ImageUtils.cv_to_qimage(img)
                    inp = os.path.abspath("../ComfyUI/input/input.png")
                    if os.path.exists(inp): os.remove(inp)
                    if os.path.exists(latest): os.remove(latest)
                    self.finished.emit(qimg)
                except Exception:
                    self.finished.emit(self.input_image)
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")

            def stop(self) -> None:
                """
                Inputs: none
                Outputs: flags stop
                """
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Entering stop: args=()")
                self._running = False
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting stop: return=None")

        self._worker = ImageGenerationWorker(self.api, self.style, self.input_image)
        self._worker.moveToThread(self._thread)
        self._worker.finished.connect(self._on_worker_finished)
        self._thread.started.connect(self._worker.run)
        self._thread.start()
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting start: return=None")

    def _on_worker_finished(self, result: QImage) -> None:
        """
        Inputs:
            result (QImage or None)
        Outputs: emits finished, cleans resources, hides loading
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering _on_worker_finished: args={{(result,)}}")
        self.finished.emit(result)
        if self._thread:
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        self.hide_loading()
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting _on_worker_finished: return=None")

    def _on_thread_finished_hide_overlay(self) -> None:
        """
        Inputs: none
        Outputs: placeholder no-op
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering _on_thread_finished_hide_overlay: args=()")
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting _on_thread_finished_hide_overlay: return=None")

    def stop(self) -> None:
        """
        Inputs: none
        Outputs: stops worker and thread, hides loading
        """
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering stop: args=()")
        self._running = False
        if self._thread:
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        self.hide_loading()
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting stop: return=None")

class CameraCaptureThread(QThread):
    frame_ready = Signal(QImage)
    RESOLUTIONS = {0: (640, 480), 1: (1280, 720), 2: (1920, 1080), 3: (2560, 1440)}

    def __init__(self, camera_id: int = 0, parent: QObject = None):
        """
        Inputs:
            camera_id (int), parent (QObject)
        Outputs: initializes camera capture thread
        """
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering __init__: args={{(camera_id, parent)}}")
        super().__init__(parent)
        self.camera_id = camera_id
        self._running = True
        self.cap = None
        self.current_res = 0
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting __init__: return=None")

    def set_resolution_level(self, level: int) -> None:
        """
        Inputs:
            level (int)
        Outputs: applies new resolution if valid
        """
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering set_resolution_level: args={{(level,)}}")
        if level in self.RESOLUTIONS:
            self.current_res = level
            if self.cap and self.cap.isOpened():
                w, h = self.RESOLUTIONS[level]
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting set_resolution_level: return=None")

    def run(self) -> None:
        """
        Inputs: none
        Outputs: emits frame_ready(QImage) until stopped
        """
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering run: args=()")
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"[Camera] Cannot open camera id={self.camera_id}")
            if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting run: return=None")
            return
        self.set_resolution_level(self.current_res)
        while self._running:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
                self.frame_ready.emit(qimg)
            self.msleep(10)
        self.cap.release()
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting run: return=None")

    def stop(self) -> None:
        """
        Inputs: none
        Outputs: stops capture and waits thread end
        """
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering stop: args=()")
        self._running = False
        self.wait()
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting stop: return=None")
