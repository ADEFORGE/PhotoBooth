from gui_classes.overlay import OverlayCountdown, OverlayLoading
from gui_classes.toolbox import ImageUtils
from PySide6.QtCore import QObject, QThread, Signal, QTimer
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from comfy_classes.comfy_class_API import ImageGeneratorAPIWrapper
import os
import glob
import cv2
import time

DEBUG_CountdownThread = False
DEBUG_Thread = False
DEBUG_ImageGenerationThread = False
DEBUG_ImageGenerationWorker = False
DEBUG_CameraCaptureThread = True

class CountdownThread(QObject):
    overlay_finished = Signal()

    class Thread(QThread):
        tick = Signal(int)
        finished = Signal()

        # Inputs: start (int)
        # Outputs: emits tick and finished signals
        def __init__(self, start):
            if DEBUG_Thread: print(f"[DEBUG][Thread] Entering __init__: args={(start,)}")
            super().__init__()
            self._start = start
            self._running = True
            self._finished_emitted = False
            if DEBUG_Thread: print(f"[DEBUG][Thread] Exiting __init__: return=None")

        # Inputs: none
        # Outputs: emits tick(count) every second, emits finished at end
        def run(self):
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

        # Inputs: none
        # Outputs: stops the loop
        def stop(self):
            if DEBUG_Thread: print(f"[DEBUG][Thread] Entering stop: args=()")
            self._running = False
            if DEBUG_Thread: print(f"[DEBUG][Thread] Exiting stop: return=None")

    # Inputs: parent (QObject), count (int)
    # Outputs: initializes countdown
    def __init__(self, parent=None, count=None):
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering __init__: args={(parent, count)}")
        super().__init__(parent)
        self._parent = parent
        self._count = count
        self._thread = None
        self._overlay = None
        self._user_callback = None
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting __init__: return=None")

    # Inputs: count (int), on_finished (callable)
    # Outputs: starts countdown thread and overlay
    def start_countdown(self, count=None, on_finished=None):
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering start_countdown: args={(count, on_finished)}")
        if self._thread is not None:
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

    # Inputs: count (int)
    # Outputs: updates overlay number
    def _on_tick(self, count):
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering _on_tick: args={(count,)}")
        if self._overlay and getattr(self._overlay, '_is_alive', True):
            self._overlay.show_number(count) if hasattr(self._overlay, 'show_number') else None
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting _on_tick: return=None")

    # Inputs: none
    # Outputs: cleans overlay and thread, emits overlay_finished, calls user callback
    def _on_finish(self):
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

    # Inputs: none
    # Outputs: stops and deletes thread and overlay
    def stop_countdown(self):
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

    # Inputs: reason (any)
    # Outputs: forcibly clears overlay
    def clear_overlay(self, reason=None):
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Entering clear_overlay: args={(reason,)}")
        if self._overlay:
            try:
                self._overlay.blockSignals(True)
                if hasattr(self._overlay, '_anim_timer'):
                    self._overlay._anim_timer.stop()
                    self._overlay._anim_timer.timeout.disconnect()
            except:
                pass
            self._overlay.clean_overlay()
        self._overlay = None
        if DEBUG_CountdownThread: print(f"[DEBUG][CountdownThread] Exiting clear_overlay: return=None")

class ImageGenerationThread(QObject):
    finished = Signal(object)

    # Inputs: style (any), input_image (QImage), parent (QObject)
    # Outputs: initializes API wrapper and state
    def __init__(self, style, input_image, parent=None):
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering __init__: args={(style, input_image, parent)}")
        super().__init__(parent)
        self.api = ImageGeneratorAPIWrapper()
        self.input_image = input_image
        self.style = style
        self._running = True
        self._thread = None
        self._worker = None
        self._loading_overlay = None
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting __init__: return=None")

    # Inputs: none
    # Outputs: shows loading overlay
    def show_loading(self):
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

    # Inputs: none
    # Outputs: hides and deletes loading overlay
    def hide_loading(self):
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering hide_loading: args=()")
        if self._loading_overlay:
            try:
                if hasattr(self._loading_overlay, "stop_animation"):
                    self._loading_overlay.stop_animation()
                self._loading_overlay.blockSignals(True)
                parent = self._loading_overlay.parent()
                if parent and hasattr(parent, "layout") and parent.layout():
                    parent.layout().removeWidget(self._loading_overlay)
            except:
                pass
            self._loading_overlay.hide()
            self._loading_overlay.setVisible(False)
            self._loading_overlay.deleteLater()
            self._loading_overlay.setParent(None)
            QApplication.processEvents()
            self._loading_overlay = None
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting hide_loading: return=None")

    # Inputs: none
    # Outputs: cleans thread resources
    def clean(self):
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

    # Inputs: none
    # Outputs: deletes thread safely in main thread
    def _delete_thread_safe(self):
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering _delete_thread_safe: args=()")
        if self._thread and QThread.currentThread() != self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting _delete_thread_safe: return=None")

    # Inputs: none
    # Outputs: starts image generation in background thread
    def start(self):
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering start: args=()")
        if self._thread and self._thread.isRunning():
            if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting start: return=None")
            return

        self.show_loading()
        self._thread = QThread()

        class ImageGenerationWorker(QObject):
            finished = Signal(object)

            # Inputs: api, style, input_image
            # Outputs: emits QImage or None
            def __init__(self, api, style, input_image):
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Entering __init__: args={(api, style, input_image)}")
                super().__init__()
                self.api = api
                self.style = style
                self.input_image = input_image
                self._running = True
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting __init__: return=None")

            # Inputs: none
            # Outputs: emits generated QImage or None
            def run(self):
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
                        self.finished.emit(None)
                        if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")
                        return
                    latest = max(files, key=os.path.getmtime)
                    img = cv2.imread(latest)
                    if img is None:
                        self.finished.emit(None)
                        if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")
                        return
                    qimg = ImageUtils.cv_to_qimage(img)
                    inp = os.path.abspath("../ComfyUI/input/input.png")
                    if os.path.exists(inp):
                        os.remove(inp)
                    if os.path.exists(latest):
                        os.remove(latest)
                    self.finished.emit(qimg)
                except:
                    self.finished.emit(None)
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")

            # Inputs: none
            # Outputs: flags stop
            def stop(self):
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Entering stop: args=()")
                self._running = False
                if DEBUG_ImageGenerationWorker: print(f"[DEBUG][ImageGenerationWorker] Exiting stop: return=None")

        self._worker = ImageGenerationWorker(self.api, self.style, self.input_image)
        self._worker.moveToThread(self._thread)
        self._worker.finished.connect(self._on_worker_finished)
        self._thread.started.connect(self._worker.run)
        self._thread.start()
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting start: return=None")

    # Inputs: result (QImage or None)
    # Outputs: emits finished, cleans thread and worker, hides overlay
    def _on_worker_finished(self, result):
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering _on_worker_finished: args={(result,)}")
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

    # Inputs: none
    # Outputs: no operation
    def _on_thread_finished_hide_overlay(self):
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Entering _on_thread_finished_hide_overlay: args=()")
        if DEBUG_ImageGenerationThread: print(f"[DEBUG][ImageGenerationThread] Exiting _on_thread_finished_hide_overlay: return=None")

    # Inputs: none
    # Outputs: stops worker and thread, hides overlay
    def stop(self):
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

    def __init__(self, camera_id: int = 0, parent=None):
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering __init__: args={{camera_id:{camera_id}, parent:{parent}}}")
        super().__init__(parent)
        self.camera_id = camera_id
        self._running = True
        self.cap = None
        self.current_res = 0
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting __init__: return=None")

    def set_resolution_level(self, level: int) -> None:
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering set_resolution_level: args={{level:{level}}}")
        if level in self.RESOLUTIONS:
            self.current_res = level
            if self.cap and self.cap.isOpened():
                w, h = self.RESOLUTIONS[level]
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting set_resolution_level: return=None")

    def run(self) -> None:
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering run: args={{}}")
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            print(f"[Camera] Impossible d'ouvrir la caméra id={self.camera_id}")
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
            self.msleep(33)
        self.cap.release()
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting run: return=None")

    def stop(self) -> None:
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Entering stop: args={{}}")
        self._running = False
        self.wait()
        if DEBUG_CameraCaptureThread: print(f"[DEBUG][CameraCaptureThread] Exiting stop: return=None")
