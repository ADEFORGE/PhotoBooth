import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constante import DEBUG, DEBUG_FULL

DEBUG_MainWindow = DEBUG
DEBUG_MainWindow_FULL = DEBUG_FULL

from typing import Optional, Callable

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPainter, QColor, QImage
from PySide6.QtWidgets import QApplication, QLabel

from gui_classes.gui_window.base_window import BaseWindow
from gui_classes.gui_object.constante import HOTSPOT_URL, TOOLTIP_STYLE, TOOLTIP_DURATION_MS, dico_styles,SLEEP_TIMER_SECONDS_QRCODE_OVERLAY
from gui_classes.gui_manager.thread_manager import CountdownThread, ImageGenerationThread
from gui_classes.gui_manager.standby_manager import StandbyManager
from gui_classes.gui_manager.background_manager import BackgroundManager
from gui_classes.gui_object.overlay import OverlayRules, OverlayQrcode
from gui_classes.gui_object.toolbox import QRCodeUtils
from gui_classes.gui_manager.language_manager import language_manager
from gui_classes.gui_object.constante import ShareByHotspot


class MainWindow(BaseWindow):

    def __init__(self, parent: Optional[object] = None) -> None:
        """
        Initialize the MainWindow with an optional parent object.
        """
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering __init__: args={{'parent':{parent}}}")
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setAutoFillBackground(False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self._default_background_color = QColor(0, 0, 0)
        self.countdown_overlay_manager = CountdownThread(self, 5)
        self._generation_task = None
        self._generation_in_progress = False
        self._countdown_callback_active = False
        self.standby_manager = StandbyManager(parent) if hasattr(parent, 'set_view') else None
        QApplication.instance().installEventFilter(self.standby_manager)
        self.bg_label = QLabel(self)
        self.bg_label.setAlignment(Qt.AlignCenter)
        self.bg_label.setStyleSheet("background: black;")
        self.bg_label.lower()
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.background_manager = BackgroundManager(self.bg_label)
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.raise_()
        self.bg_label.lower()
        self.background_manager.update_background()
        self._texts = {}
        language_manager.subscribe(self.update_language)
        self.update_language()
        self.showFullScreen()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting __init__: return=None")
        

    def update_language(self) -> None:
        """
        Update the UI texts based on the current language settings.
        """
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering update_language: args={{}}")
        self.update_frame()
        self._texts = language_manager.get_texts('main_window') or {}
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting update_language: return=None")

    def on_enter(self) -> None:
        """
        Called when entering the window, updates UI and background.
        """        
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering on_enter: args={{}}")
        self.update_frame()
        if hasattr(self, 'background_manager'):
            self.background_manager.on_enter()
        self.set_state_default()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting on_enter: return=None")
        self.update_frame()

    def on_leave(self) -> None:
        """
        Called when leaving the window, cleans up and resets state.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering on_leave: args={{}}")
        if hasattr(self, 'background_manager'):
            self.background_manager.on_leave()
        super().on_leave()
        self.cleanup()
        self.hide_loading()
        if hasattr(self, '_countdown_overlay') and self._countdown_overlay:
            try:
                if getattr(self._countdown_overlay, '_is_alive', True):
                    self._countdown_overlay.clean_overlay()
            except Exception:
                pass
            self._countdown_overlay = None
        self.countdown_overlay_manager.clear_overlay("countdown")
        self.set_state_default()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting on_leave: return=None")
        self.update_frame()

    def cleanup(self) -> None:
        """
        Clean up resources and disconnect signals for the window.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering cleanup: args={{}}")
        self._generation_in_progress = False
        if self._generation_task:
            if hasattr(self._generation_task, 'finished'):
                try:
                    self._generation_task.finished.disconnect()
                except Exception:
                    pass
            self._generation_task.cleanup()
            self._generation_task = None
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting cleanup: return=None")
        self.update_frame()

    def set_generation_style(self, checked: bool, style_name: str, generate_image: bool = False) -> None:
        """
        Set the selected style for image generation and optionally generate an image.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering set_generation_style: args={{'checked':{checked},'style_name':{style_name},'generate_image':{generate_image}}}")
        if self._generation_in_progress:
            if DEBUG_MainWindow:
                logger.info(f"[DEBUG][MainWindow] Exiting set_generation_style: return=None")
            self.update_frame()
            return
        if checked:
            self.selected_style = style_name
        else:
            self.selected_style = None
        if generate_image:
            if self.original_photo and self.selected_style:
                self.start(self.selected_style, self.original_photo)
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting set_generation_style: return=None")
        self.update_frame()

    def take_selfie(self) -> None:
        """
        Start the selfie process, including countdown and image generation.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering take_selfie: args={{}}")
        if not getattr(self, 'selected_style', None):
            if hasattr(self, 'btns'):
                popup_msg = self._texts.get("popup", "Select a style first")
                self.show_message(self.btns.get_style1_btns(), popup_msg, TOOLTIP_DURATION_MS)
        else:
            if self.standby_manager:
                self.standby_manager.put_standby(False)
            self.selfie_countdown(
                on_finished=lambda: (
                    self.selfie(
                        callback=lambda: (
                            self.generation(
                                self.selected_style,
                                self.original_photo,
                                callback=self.show_generation
                            )
                        )
                    )
                )
            )
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting take_selfie: return=None")
        self.update_frame()

    def selfie_countdown(self, on_finished: Optional[Callable[[], None]] = None) -> None:
        """
        Start the countdown before taking a selfie, with an optional callback.
        """
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering selfie_countdown: args={{'on_finished':{on_finished}}}")
        self.update_frame()
        self.countdown_overlay_manager.start_countdown(on_finished=on_finished)
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting selfie_countdown: return=None")

    def selfie(self, callback: Optional[Callable[[], None]] = None) -> None:
        """
        Capture a selfie and call the callback when done.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering selfie: args={{'callback':{callback}}}")
        self.cleanup()
        if hasattr(self, 'background_manager'):
            self.background_manager.capture()
            pixmap = self.background_manager.get_background_image()
            if pixmap is not None and not pixmap.isNull():
                self.original_photo = pixmap.toImage()
            else:
                self.original_photo = None
        if not self._generation_in_progress and self.original_photo and callback:
            callback()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting selfie: return=None")
        self.update_frame()

    def generation(self, style_name: str, input_image: QImage, callback: Optional[Callable[[], None]] = None) -> None:
        """
        Generate an image using the selected style and input image, with an optional callback.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering generation: args={{'style_name':{style_name},'input_image':<QImage>,'callback':{callback}}}")
        if self._generation_task:
            self.cleanup()
        self._generation_task = ImageGenerationThread(style=style_name, input_image=input_image, parent=self)
        if callback:
            self._generation_task.finished.connect(callback)
        self._generation_task.start()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting generation: return=None")
        self.update_frame()

    def show_generation(self, qimg: QImage) -> None:
        """
        Display the generated image and update the UI to validation state.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering show_generation: args={{'qimg':<QImage>}}")
        self._generation_task = None
        self._generation_in_progress = False
        self.generated_image = qimg if qimg and not qimg.isNull() else None
        self.update_frame()
        self.set_state_validation()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting show_generation: return=None")
        self.update_frame()

    def show_qrcode_overlay(self, image_to_send: object) -> None:
        """
        Show the QR code overlay for sharing the given image.
        """

        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering show_qrcode_overlay: args={{'image_to_send':{type(image_to_send)}}}")
        if self.standby_manager:
            self.standby_manager.put_standby(True)
            self.standby_manager.set_timer(SLEEP_TIMER_SECONDS_QRCODE_OVERLAY)
            self.standby_manager.reset_standby_timer()
            if DEBUG_MainWindow:
                logger.info(f"[DEBUG][MainWindow] Standby timer set to {SLEEP_TIMER_SECONDS_QRCODE_OVERLAY} seconds.")
        hotspot_url = HOTSPOT_URL
        overlay_qr = OverlayQrcode(
            self,
            on_close=self.set_state_default,
            hotspot_url=hotspot_url,
            image_to_send=image_to_send
        )
        overlay_qr.show_overlay()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting show_qrcode_overlay: return=None")

    def show_rules_overlay(self, qimg: QImage) -> None:
        """
        Show the rules overlay and handle validation or refusal.
        """
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering show_rules_overlay: args={{'qimg':<QImage>}}")
        if not ShareByHotspot:
            if DEBUG_MainWindow:
                logger.info("[DEBUG][MainWindow] ShareByHotspot off.")
            self.set_state_default()
            return
        def on_rules_validated():
            self.show_qrcode_overlay(qimg)
        def on_rules_refused():
            self.set_state_default()
        overlay = OverlayRules(
            self,
            on_validate=on_rules_validated,
            on_close=on_rules_refused
        )
        overlay.show_overlay()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting show_rules_overlay: return=None")

    def _on_accept_close(self) -> None:
        """
        Handle accept, close, or regenerate actions from the validation UI.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering _on_accept_close: args={{}}")
        sender = self.sender()
        if sender and sender.objectName() == 'accept':
            self.set_state_wait()
            if not hasattr(self, 'generated_image') or self.generated_image is None:
                logger.info("Aucune image générée disponible.")
                self.set_state_default()
                return
            qimg = self.generated_image
            self.show_rules_overlay(qimg)
        elif sender and sender.objectName() == 'regenerate':
            self.generation(
                self.selected_style,
                self.original_photo,
                callback=self.show_generation
            )
        else:
            self.set_state_default()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting _on_accept_close: return=None")
        self.update_frame()

    def reset_generation_state(self) -> None:
        """
        Reset the state related to image generation.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering reset_generation_state: args={{}}")
        self._generation_in_progress = False
        self._generation_task = None
        self.generated_image = None
        self.original_photo = None
        self.selected_style = None
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting reset_generation_state: return=None")
        self.update_frame()

    def set_state_default(self) -> None:
        """
        Set the UI to the default state, ready for a new selfie.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering set_state_default: args={{}}")
        self.reset_generation_state()
        self.clear_display()
        stylesheet = """
            background: rgba(80, 80, 80, 0.6);
            color: rgba(255, 255, 255, 1.0);
            font-weight: bold;
            font-size: 24px;
            border-radius: 18px;
            padding: 12px 24px;
        """
        self.set_header_text("coucou")
        self.place_header_label()
        self.set_header_style(stylesheet)
        self.show_header_label()

        style2 = [
            (name, f"style.{name}") for name in dico_styles.keys()
        ]
        self.setup_buttons(
            style1_names=["take_selfie"],
            style2_names=style2,
            slot_style1=self.take_selfie,
            slot_style2=lambda checked, btn=None: self.set_generation_style(checked, btn.get_name(), generate_image=False)
        )

        
        
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.raise_()
        if hasattr(self, 'btns'):
            self.btns.raise_()
            for btn in self.btns.get_every_btns():
                btn.show()
                btn.setEnabled(True)
        self.bg_label.lower()
        if hasattr(self, 'background_manager'):
            self.background_manager.set_live()
            self.background_manager.update_background()
        if self.standby_manager:
            self.standby_manager.put_standby(True)
            self.standby_manager.set_timer_from_constante()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting set_state_default: return=None")
        self.update_frame()

    def set_state_validation(self) -> None:
        """
        Set the UI to the validation state after image generation.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering set_state_validation: args={{}}")
        self.hide_header_label()
        self.setup_buttons_style_1(['accept', 'close','regenerate'], slot_style1=self._on_accept_close)
        if hasattr(self, 'btns'):
            self.btns.raise_()
            for btn in self.btns.get_style1_btns():
                btn.show()
                btn.setEnabled(True)
            self.btns.set_disabled_bw_style2()
        self.update_frame()
        if self.standby_manager:
            self.standby_manager.put_standby(False)
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting set_state_validation: return=None")
        self.update_frame()

    def set_state_wait(self) -> None:
        """
        Set the UI to the waiting state, disabling buttons.
        """
        self.update_frame()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering set_state_wait: args={{}}")
        if hasattr(self, 'btns'):
            self.btns.set_disabled_bw_style2()
            for btn in self.btns.get_every_btns():
                btn.hide()
        self.update_frame()
        if self.standby_manager:
            self.standby_manager.put_standby(False)
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting set_state_wait: return=None")
        self.update_frame()

    def update_frame(self) -> None:
        """
        Update the background and UI frame.
        """
        if DEBUG_MainWindow_FULL:
            logger.info(f"[DEBUG][MainWindow] Entering update_frame: args={{}}")
        if hasattr(self, 'background_manager') and self.background_manager:
            if hasattr(self, 'generated_image') and self.generated_image and not isinstance(self.generated_image, str):
                self.background_manager.set_generated(self.generated_image)
            elif hasattr(self, 'original_photo') and self.original_photo:
                self.background_manager.capture()
            self.background_manager.update_background()
        if hasattr(self, 'update') and callable(self.update):
            self.update()
        if DEBUG_MainWindow_FULL:
            logger.info(f"[DEBUG][MainWindow] Exiting update_frame: return=None")

    def user_activity(self) -> None:
        """
        Notify the standby manager of user activity.
        """
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering user_activity: args={{}}")
        if self.standby_manager:
            self.standby_manager.put_standby(True)
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting user_activity: return=None")

    def resizeEvent(self, event: QEvent) -> None:
        """
        Handle window resize events and update geometry of UI elements.
        """
        if DEBUG_MainWindow_FULL:
            logger.info(f"[DEBUG][MainWindow] Entering resizeEvent: args={{'event':{event}}}")
        super().resizeEvent(event)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
            self.overlay_widget.raise_()
        if hasattr(self, 'btns') and self.btns is not None:
            self.btns.raise_()
        self.bg_label.lower()
        if DEBUG_MainWindow_FULL:
            logger.info(f"[DEBUG][MainWindow] Exiting resizeEvent: return=None")

    def closeEvent(self, event: QEvent) -> None:
        """
        Handle the window close event and clean up resources.
        """
        if DEBUG_MainWindow_FULL:
            logger.info(f"[DEBUG][MainWindow] Entering closeEvent: args={{'event':{event}}}")
        if hasattr(self, 'background_manager'):
            self.background_manager.close()
        super().closeEvent(event)
        if DEBUG_MainWindow_FULL:
            logger.info(f"[DEBUG][MainWindow] Exiting closeEvent: return=None")

    def paintEvent(self, event: QEvent) -> None:
        """
        Handle paint events for custom background rendering.
        """
        if DEBUG_MainWindow_FULL:
            logger.info(f"[DEBUG][MainWindow] Entering paintEvent: args={{'event':{event}}}")
        painter = QPainter(self)
        if not painter.isActive():
            if DEBUG_MainWindow_FULL:
                logger.info("[DEBUG][MainWindow] QPainter not active, skipping paintEvent.")
            return
        painter.fillRect(self.rect(), self._default_background_color)
        painter.end()
        if hasattr(super(), 'paintEvent'):
            super().paintEvent(event)
        if DEBUG_MainWindow_FULL:
            logger.info(f"[DEBUG][MainWindow] Exiting paintEvent: return=None")

    def preset(self) -> None:
        """
        Call the preset method on the background manager if present.
        """
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Entering preset: args={{}}")
            logger.info("[DEBUG][MainWindow] Calling preset on background_manager")
        if hasattr(self, 'background_manager'):
            self.background_manager.preset()
        if DEBUG_MainWindow:
            logger.info(f"[DEBUG][MainWindow] Exiting preset: return=None")