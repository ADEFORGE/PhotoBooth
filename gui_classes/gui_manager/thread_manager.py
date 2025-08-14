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
from hotspot_classes.hotspot_client import HotspotClient

import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constant import DEBUG, DEBUG_FULL
DEBUG_CountdownThread = DEBUG
DEBUG_CountdownThread_FULL = DEBUG_FULL

DEBUG_ImageGenerationThread = DEBUG
DEBUG_ImageGenerationThread_FULL = DEBUG_FULL

DEBUG_CameraCaptureThread = DEBUG
DEBUG_CameraCaptureThread_FULL = DEBUG_FULL

DEBUG_ThreadShareImage = DEBUG
DEBUG_ThreadShareImage_FULL = DEBUG_FULL

class CountdownThread(QObject):
    overlay_finished = Signal()

    class Thread(QThread):
        tick = Signal(int)
        finished = Signal()

        def __init__(self, start: int) -> None:
            """
            Initialize the countdown thread with a starting count.
            """
            if DEBUG_CountdownThread: 
                logger.info(f"[DEBUG][Thread] Entering __init__: args={{(start,)}}")
            super().__init__()
            self._start = start
            self._running = True
            self._finished_emitted = False
            if DEBUG_CountdownThread: 
                logger.info(f"[DEBUG][Thread] Exiting __init__: return=None")

        def run(self) -> None:
            """
            Run the countdown, emitting tick and finished signals.
            """
            if DEBUG_CountdownThread: 
                logger.info(f"[DEBUG][Thread] Entering run: args=()")
            count = self._start
            while self._running and count >= 0:
                self.tick.emit(count)
                time.sleep(1)
                count -= 1
            if self._running and not self._finished_emitted:
                self._finished_emitted = True
                self.finished.emit()
            if DEBUG_CountdownThread: 
                logger.info(f"[DEBUG][Thread] Exiting run: return=None")

        def stop(self) -> None:
            """
            Stop the countdown loop.
            """
            if DEBUG_CountdownThread: 
                logger.info(f"[DEBUG][Thread] Entering stop: args=()")
            self._running = False
            if DEBUG_CountdownThread: 
                logger.info(f"[DEBUG][Thread] Exiting stop: return=None")

    def __init__(self, parent: QObject = None, count: int = 0) -> None:
        """
        Initialize the CountdownThread with an optional parent and starting count.
        """
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Entering __init__: args={{(parent, count)}}")
        super().__init__(parent)
        self._parent = parent
        self._count = count
        self._thread = None
        self._overlay = None
        self._user_callback = None
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Exiting __init__: return=None")

    def start_countdown(self, count: int = None, on_finished: callable = None) -> None:
        """
        Start the countdown with an optional count and callback for when finished.
        """
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Entering start_countdown: args={{(count, on_finished)}}")
        if self._thread:
            if DEBUG_CountdownThread: 
                logger.info(f"[DEBUG][CountdownThread] Exiting start_countdown: return=None")
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
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Exiting start_countdown: return=None")

    def _on_tick(self, count: int) -> None:
        """
        Update the overlay with the current countdown number.
        """
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Entering _on_tick: args={{(count,)}}")
        if self._overlay and getattr(self._overlay, '_is_alive', True):
            if hasattr(self._overlay, 'show_number'):
                self._overlay.show_number(count)
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Exiting _on_tick: return=None")

    def _on_finish(self) -> None:
        """
        Handle the end of the countdown, cleanup, and call the callback.
        """
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Entering _on_finish: args=()")
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
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Exiting _on_finish: return=None")

    def stop_countdown(self) -> None:
        """
        Stop the countdown and remove the overlay.
        """
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Entering stop_countdown: args=()")
        if self._thread:
            self._thread.stop()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
        if self._overlay and getattr(self._overlay, '_is_alive', True):
            self._overlay.clean_overlay()
        self._overlay = None
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Exiting stop_countdown: return=None")

    def clear_overlay(self, reason: object = None) -> None:
        """
        Forcefully clear the overlay, optionally providing a reason.
        """
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Entering clear_overlay: args={{(reason,)}}")
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
        if DEBUG_CountdownThread: 
            logger.info(f"[DEBUG][CountdownThread] Exiting clear_overlay: return=None")

class ImageGenerationThread(QObject):
    finished = Signal(object)

    def __init__(self, style: object, input_image: QImage, parent: QObject = None) -> None:
        """
        Initialize the ImageGenerationThread with style, input image, and optional parent.
        """
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Entering __init__: args={{(style, input_image, parent)}}")
        super().__init__(parent)
        self.style = style
        self.input_image = input_image
        self.api = ImageGeneratorAPIWrapper(style=style, qimg=input_image)
        self._running = True
        self._thread = None
        self._worker = None
        self._loading_overlay = None
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Exiting __init__: return=None")

    def show_loading(self) -> None:
        """
        Display the loading overlay and connect the progress signal.
        """
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Entering show_loading: args=()")
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
            
            try:
                self.api.progress_changed.disconnect()
            except Exception:
                pass
            self.api.progress_changed.connect(self._on_progress_changed)
            self._loading_overlay.show()
            self._loading_overlay.raise_()
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Exiting show_loading: return=None")

    def _on_progress_changed(self, percent: float) -> None:
        """
        Update the loading overlay's progress bar with the given percent.
        """
        if DEBUG_ImageGenerationThread:
            logger.info(f"[DEBUG][ImageGenerationThread] Entering _on_progress_changed: args={{(percent,)}}")
        if self._loading_overlay is not None:
            
            self._loading_overlay.set_percent(int(percent))
        if DEBUG_ImageGenerationThread:
            logger.info(f"[DEBUG][ImageGenerationThread] Exiting _on_progress_changed: return=None")

    def hide_loading(self) -> None:
        """
        Hide and delete the loading overlay.
        """
        if DEBUG_ImageGenerationThread:
            logger.info(f"[DEBUG][ImageGenerationThread] Entering hide_loading: args=()")
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
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Exiting hide_loading: return=None")

    def cleanup(self) -> None:
        """
        Stop and delete the thread and worker, cleaning up resources.
        """
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Entering cleanup: args=()")
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
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Exiting cleanup: return=None")

    def _delete_thread_safe(self) -> None:
        """
        Delete the thread safely in the main thread.
        """
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Entering _delete_thread_safe: args=()")
        if self._thread and QThread.currentThread() != self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread.deleteLater()
            self._thread = None
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Exiting _delete_thread_safe: return=None")

    def start(self) -> None:
        """
        Start the background image generation and show the loading overlay.
        """
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Entering start: args=()")
        if self._thread and self._thread.isRunning():
            if DEBUG_ImageGenerationThread: 
                logger.info(f"[DEBUG][ImageGenerationThread] Exiting start: return=None")
            return
        self.show_loading()
        self._thread = QThread()
        if DEBUG_ImageGenerationThread: 
            logger.info(f"[DEBUG][ImageGenerationThread] Starting worker thread")

        class ImageGenerationWorker(QObject):
            finished = Signal(object)

            def __init__(self, api: ImageGeneratorAPIWrapper, style: any, input_image: QImage):
                """
                Inputs:
                    api (ImageGeneratorAPIWrapper), style (any), input_image (QImage)
                Outputs: initializes worker
                """
                if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationWorker] Entering __init__: args={{(api, style, input_image)}}")
                super().__init__()
                self.api = api
                self.style = style
                self.input_image = input_image
                self._running = True
                if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationWorker] Exiting __init__: return=None")

            def run(self) -> None:
                """
                Inputs: none
                Outputs: emits generated QImage or None
                """
                if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationWorker] Entering run: args=()")
                try:
                    self.api.set_style(self.style)
                    if not self._running:
                        self.finished.emit(None)
                        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")
                        return
                    self.api.set_img(self.input_image)
                    self.api.generate_image()
                    if not self._running:
                        self.finished.emit(None)
                        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")
                        return
                    
                    qimg = self.api.wait_for_and_load_image(timeout=15.0)
                    if qimg is None or qimg.isNull():
                        if DEBUG_ImageGenerationThread:
                            logger.info(f"[DEBUG][ImageGenerationWorker] Failed to load generated image, falling back to input image.")
                        self.finished.emit(self.input_image)
                    else:
                        if DEBUG_ImageGenerationThread:
                            logger.info(f"[DEBUG][ImageGenerationWorker] Successfully loaded generated image.")
                        self.finished.emit(qimg)
                        
                    self.api.delete_input_and_output_images()
                except Exception as e:
                    if DEBUG_ImageGenerationThread:
                        logger.info(f"[DEBUG][ImageGenerationWorker] Exception: {e}")
                    self.finished.emit(self.input_image)
                if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationWorker] Exiting run: return=None")

            def stop(self) -> None:
                """
                Inputs: none
                Outputs: flags stop
                """
                if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationWorker] Entering stop: args=()")
                self._running = False
                if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationWorker] Exiting stop: return=None")

        self._worker = ImageGenerationWorker(self.api, self.style, self.input_image)
        self._worker.moveToThread(self._thread)
        self._worker.finished.connect(self._on_worker_finished)
        self._thread.started.connect(self._worker.run)
        self._thread.start()
        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationThread] Exiting start: return=None")

    def _on_worker_finished(self, result: QImage) -> None:
        """
        Handle the completion of the worker, emit finished, clean resources, and hide loading.
        """
        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationThread] Entering _on_worker_finished: args={{(result,)}}")
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
        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationThread] Exiting _on_worker_finished: return=None")

    def _on_thread_finished_hide_overlay(self) -> None:
        """
        Placeholder method for thread finished event, does nothing.
        """
        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationThread] Entering _on_thread_finished_hide_overlay: args=()")
        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationThread] Exiting _on_thread_finished_hide_overlay: return=None")

    def stop(self) -> None:
        """
        Stop the worker and thread, and hide the loading overlay.
        """
        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationThread] Entering stop: args=()")
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
        if DEBUG_ImageGenerationThread: logger.info(f"[DEBUG][ImageGenerationThread] Exiting stop: return=None")

class CameraCaptureThread(QThread):
    frame_ready = Signal(QImage)
    RESOLUTIONS = {0: (640, 480), 1: (1280, 720), 2: (1920, 1080), 3: (2560, 1440)}

    def __init__(self, camera_id: int = 0, parent: QObject = None) -> None:
        """
        Initialize the camera capture thread with a camera ID and optional parent.
        """
        if DEBUG_CameraCaptureThread: 
            logger.info(f"[DEBUG][CameraCaptureThread] Entering __init__: args={{(camera_id, parent)}}")
        super().__init__(parent)
        self.camera_id = camera_id
        self._running = True
        self.cap = None
        self.current_res = 0
        
        self.set_resolution_level(0)
        if DEBUG_CameraCaptureThread: 
            logger.info(f"[DEBUG][CameraCaptureThread] Exiting __init__: return=None")

    def set_capture_interval(self, interval_ms: int) -> None:
        """
        Dynamically change the capture interval in milliseconds.
        """

        if DEBUG_CameraCaptureThread:
            logger.info(f"[DEBUG][CameraCaptureThread] Entering set_capture_interval: args={{'interval_ms':{interval_ms}}}")
        self.capture_interval_ms = max(1, int(interval_ms))
        if DEBUG_CameraCaptureThread:
            logger.info(f"[DEBUG][CameraCaptureThread] Exiting set_capture_interval: interval now {self.capture_interval_ms} ms")


    def set_resolution_level(self, level: int) -> None:
        """
        Set the camera resolution level and adjust capture interval accordingly.
        """
        if DEBUG_CameraCaptureThread: 
            logger.info(f"[DEBUG][CameraCaptureThread] Entering set_resolution_level: args={{(level,)}}")
        if level == 0:
            self.set_capture_interval(50) 
            if DEBUG_CameraCaptureThread:
                logger.info(f"[DEBUG][CameraCaptureThread] set_resolution_level: niveau 0, intervalle capture 50ms (20 fps)")
        else:
            self.set_capture_interval(13) 
            if DEBUG_CameraCaptureThread:
                logger.info(f"[DEBUG][CameraCaptureThread] set_resolution_level: niveau {level}, intervalle capture 13ms (~75 fps)")
        if DEBUG_CameraCaptureThread: 
            logger.info(f"[DEBUG][CameraCaptureThread] Entering set_resolution_level: args={{(level,)}}")
        if level in self.RESOLUTIONS:
            self.current_res = level
            if self.cap and self.cap.isOpened():
                w, h = self.RESOLUTIONS[level]
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        if DEBUG_CameraCaptureThread: 
            logger.info(f"[DEBUG][CameraCaptureThread] Exiting set_resolution_level: return=None")

    def run(self) -> None:
        """
        Start the camera capture loop and emit frames until stopped.
        """
        if DEBUG_CameraCaptureThread: 
            logger.info(f"[DEBUG][CameraCaptureThread] Entering run: args=()")
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            logger.info(f"[Camera] Cannot open camera id={self.camera_id}")
            if DEBUG_CameraCaptureThread: 
                logger.info(f"[DEBUG][CameraCaptureThread] Exiting run: return=None")
            return
        self.set_resolution_level(self.current_res)
        if DEBUG_CameraCaptureThread:
            logger.info(f"[DEBUG][CameraCaptureThread] Camera opened with resolution {self.RESOLUTIONS[self.current_res]} at id={self.camera_id}")
        
        if not hasattr(self, 'capture_interval_ms'):
            self.capture_interval_ms = 10
        while self._running:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
                self.frame_ready.emit(qimg)
            self.msleep(self.capture_interval_ms)
        self.cap.release()
        if DEBUG_CameraCaptureThread:
            logger.info(f"[DEBUG][CameraCaptureThread] Exiting run: return=None")

    def stop(self) -> None:
        """
        Stop the camera capture and wait for the thread to finish.
        """
        if DEBUG_CameraCaptureThread:
            logger.info(f"[DEBUG][CameraCaptureThread] Entering stop: args=()")
        self._running = False
        self.wait()
        if DEBUG_CameraCaptureThread:
            logger.info(f"[DEBUG][CameraCaptureThread] Exiting stop: return=None")

class ThreadShareImage(QThread):
    """
    Thread to send an image to the Raspberry Pi via HotspotClient without blocking the UI.
    Usage:
        thread = ThreadShareImage(url, image_path_or_qimage)
        thread.finished.connect(slot)
        thread.start()
    Result: thread.qr_bytes, thread.credentials, thread.error (None if OK)
    """

    def __init__(self, url: str, image: object = None, timeout: float = 10.0, parent: object = None) -> None:
        """
        Initialize the ThreadShareImage with a URL, image (path or QImage), timeout, and optional parent.
        """
        if DEBUG_ThreadShareImage:
            logger.info(f"[DEBUG][ThreadShareImage] Entering __init__: args={{(url, image, timeout, parent)}}")
        super().__init__(parent)
        self.url = url
        self.image = image  
        self.timeout = timeout
        self.qr_bytes = b""
        self.credentials = (None, None)
        self.error = None
        if DEBUG_ThreadShareImage:
            logger.info(f"[DEBUG][ThreadShareImage] Exiting __init__: return=None")

    def run(self) -> None:
        """
        Execute the image sharing process in a separate thread.
        """
        if DEBUG_ThreadShareImage:
            logger.info(f"[DEBUG][ThreadShareImage] Entering run: args=()")
            logger.info(f"[DEBUG][ThreadShareImage] run called for url={self.url}, image={type(self.image)}")
        try:
            client = HotspotClient(self.url, timeout=self.timeout)
            
            if hasattr(self.image, 'save') and callable(self.image.save):
                if DEBUG_ThreadShareImage:
                    logger.info(f"[DEBUG][ThreadShareImage] Detected QImage, using set_qimage.")
                client.set_qimage(self.image)
            else:
                if DEBUG_ThreadShareImage:
                    logger.info(f"[DEBUG][ThreadShareImage] Detected path, using set_image.")
                client.set_image(str(self.image))
            client.run()
            self.qr_bytes = client.qr_bytes
            self.credentials = client.credentials
            self.error = None
            client.cleanup_temp_image()
            if DEBUG_ThreadShareImage:
                logger.info(f"[DEBUG][ThreadShareImage] run finished successfully.")
        except Exception as e:
            if DEBUG_ThreadShareImage:
                logger.info(f"[DEBUG][ThreadShareImage] Exception: {e}")
            self.qr_bytes = b""
            self.credentials = (None, None)
            self.error = e
        if DEBUG_ThreadShareImage:
            logger.info(f"[DEBUG][ThreadShareImage] Exiting run: return=None")

    def cleanup(self) -> None:
        """
        Clean up resources, stop the thread, and reset the HotspotClient if needed.
        """
        if DEBUG_ThreadShareImage:
            logger.info(f"[DEBUG][ThreadShareImage] Entering cleanup: args=()")

        try:
            if hasattr(self, 'url') and self.url:
                try:
                    client = HotspotClient(self.url, timeout=2.0)
                    if hasattr(client, 'reset') and callable(client.reset):
                        if DEBUG_ThreadShareImage:
                            logger.info(f"[DEBUG][ThreadShareImage] Calling client.reset()")
                        client.reset()
                except Exception as e:
                    if DEBUG_ThreadShareImage:
                        logger.info(f"[DEBUG][ThreadShareImage] Exception during client.reset: {e}")
        except Exception as e:
            if DEBUG_ThreadShareImage:
                logger.info(f"[DEBUG][ThreadShareImage] Exception in cleanup: {e}")

        if self.isRunning():
            try:
                self.requestInterruption()
            except Exception as e:
                if DEBUG_ThreadShareImage:
                    logger.info(f"[DEBUG][ThreadShareImage] Exception during requestInterruption: {e}")
            try:
                self.quit()
                self.wait(2000)
            except Exception as e:
                if DEBUG_ThreadShareImage:
                    logger.info(f"[DEBUG][ThreadShareImage] Exception during quit/wait: {e}")

        try:
            self.deleteLater()
        except Exception as e:
            if DEBUG_ThreadShareImage:
                logger.info(f"[DEBUG][ThreadShareImage] Exception during deleteLater: {e}")