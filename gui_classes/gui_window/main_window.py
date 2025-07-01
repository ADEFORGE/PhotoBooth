DEBUG_MainWindow = False

from typing import Optional, Callable

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPainter, QColor, QImage
from PySide6.QtWidgets import QApplication, QLabel

from gui_classes.gui_window.base_window import BaseWindow
from gui_classes.gui_object.constante import TOOLTIP_STYLE, TOOLTIP_DURATION_MS, dico_styles
from gui_classes.gui_manager.thread_manager import CountdownThread, ImageGenerationThread
from gui_classes.gui_manager.standby_manager import StandbyManager
from gui_classes.gui_manager.background_manager import BackgroundManager
from gui_classes.gui_object.overlay import OverlayRules, OverlayQrcode
from gui_classes.gui_object.toolbox import QRCodeUtils
from gui_classes.gui_manager.language_manager import language_manager


class MainWindow(BaseWindow):
    def __init__(self, parent: Optional[object] = None) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering __init__: args={{'parent':{parent}}}")
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self.setAutoFillBackground(False)
        self.showFullScreen()
        self._default_background_color = QColor(0, 0, 0)
        self.countdown_overlay_manager = CountdownThread(self, 3)
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
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting __init__: return=None")

    def update_language(self) -> None:
        self._texts = language_manager.get_texts('main_window') or {}

    def on_enter(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering on_enter: args={{}}")
        if hasattr(self, 'background_manager'):
            self.background_manager.on_enter()
        self.set_state_default()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting on_enter: return=None")

    def on_leave(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering on_leave: args={{}}")
        if hasattr(self, 'background_manager'):
            self.background_manager.on_leave()
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
            print(f"[DEBUG][MainWindow] Exiting on_leave: return=None")

    def cleanup(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering cleanup: args={{}}")
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
            print(f"[DEBUG][MainWindow] Exiting cleanup: return=None")

    def set_generation_style(self, checked: bool, style_name: str, generate_image: bool = False) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering set_generation_style: args={{'checked':{checked},'style_name':{style_name},'generate_image':{generate_image}}}")
        if self._generation_in_progress:
            if DEBUG_MainWindow:
                print(f"[DEBUG][MainWindow] Exiting set_generation_style: return=None")
            return
        if checked:
            self.selected_style = style_name
        else:
            self.selected_style = None
        if generate_image:
            if self.original_photo and self.selected_style:
                self.start(self.selected_style, self.original_photo)
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting set_generation_style: return=None")

    def take_selfie(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering take_selfie: args={{}}")
        if not getattr(self, 'selected_style', None):
            if hasattr(self, 'btns'):
                popup_msg = self._texts.get("popup", "Select a style first")
                self.show_message(self.btns.style1_btns, popup_msg, TOOLTIP_DURATION_MS)
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
            print(f"[DEBUG][MainWindow] Exiting take_selfie: return=None")

    def selfie_countdown(self, on_finished: Optional[Callable[[], None]] = None) -> None:
        self.countdown_overlay_manager.start_countdown(on_finished=on_finished)

    def selfie(self, callback: Optional[Callable[[], None]] = None) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering selfie: args={{'callback':{callback}}}")
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
            print(f"[DEBUG][MainWindow] Exiting selfie: return=None")

    def generation(self, style_name: str, input_image: QImage, callback: Optional[Callable[[], None]] = None) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering generation: args={{'style_name':{style_name},'input_image':<QImage>,'callback':{callback}}}")
        if self._generation_task:
            self.cleanup()
        self._generation_task = ImageGenerationThread(style=style_name, input_image=input_image, parent=self)
        if callback:
            self._generation_task.finished.connect(callback)
        self._generation_task.start()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting generation: return=None")

    def show_generation(self, qimg: QImage) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering show_generation: args={{'qimg':<QImage>}}")
        self._generation_task = None
        self._generation_in_progress = False
        self.generated_image = qimg if qimg and not qimg.isNull() else None
        self.update_frame()
        self.set_state_validation()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting show_generation: return=None")

    def _on_accept_close(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering _on_accept_close: args={{}}")
        sender = self.sender()
        if sender and sender.objectName() == 'accept':
            self.set_state_wait()
            def on_rules_validated():
                def on_qrcode_close():
                    self.set_state_default()
                data = "https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX"
                pil_img = QRCodeUtils.generate_qrcode(data)
                qimg = QRCodeUtils.pil_to_qimage(pil_img)
                overlay_qr = OverlayQrcode(
                    parent=self.window(),
                    qimage=qimg,
                    on_close=on_qrcode_close
                )
                overlay_qr.show_overlay()
            def on_rules_refused():
                self.set_state_default()
            overlay = OverlayRules(
                parent=self.window(),
                on_validate=on_rules_validated,
                on_close=on_rules_refused
            )
            overlay.show_overlay()
        else:
            self.set_state_default()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting _on_accept_close: return=None")

    def reset_generation_state(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering reset_generation_state: args={{}}")
        self._generation_in_progress = False
        self._generation_task = None
        self.generated_image = None
        self.original_photo = None
        self.selected_style = None
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting reset_generation_state: return=None")

    def set_state_default(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering set_state_default: args={{}}")
        self.reset_generation_state()
        self.clear_display()
        # Prépare la liste des boutons style2 comme liste de paires (name, text_key)
        style2 = [
            (name, f"style.{name}") for name in dico_styles.keys()
        ]
        self.setup_buttons(
            style1_names=["take_selfie"],
            style2_names=style2,
            slot_style1=self.take_selfie,
            slot_style2=lambda checked, btn=None: self.set_generation_style(checked, btn.style_name if btn else None, generate_image=False)
        )
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.raise_()
        if hasattr(self, 'btns'):
            self.btns.raise_()
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.show()
                btn.setEnabled(True)
        self.bg_label.lower()
        if hasattr(self, 'background_manager'):
            self.background_manager.set_live()
            self.background_manager.update_background()
        if self.standby_manager:
            self.standby_manager.put_standby(True)
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting set_state_default: return=None")

    def set_state_validation(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering set_state_validation: args={{}}")
        self.setup_buttons_style_1(['accept', 'close'], slot_style1=self._on_accept_close)
        if hasattr(self, 'btns'):
            self.btns.raise_()
            for btn in self.btns.style1_btns:
                btn.show()
                btn.setEnabled(True)
            self.btns.set_disabled_bw_style2()
        self.update_frame()
        if self.standby_manager:
            self.standby_manager.put_standby(False)
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting set_state_validation: return=None")

    def set_state_wait(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering set_state_wait: args={{}}")
        if hasattr(self, 'btns'):
            self.btns.set_disabled_bw_style2()
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.hide()
        self.update_frame()
        if self.standby_manager:
            self.standby_manager.put_standby(False)
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting set_state_wait: return=None")

    def update_frame(self) -> None:
        if self.generated_image and not isinstance(self.generated_image, str):
            self.background_manager.set_generated(self.generated_image)
        elif self.original_photo:
            self.background_manager.capture()
        else:
            self.background_manager.clear()
        self.background_manager.update_background()
        self.update()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting update_frame: return=None")

    def user_activity(self) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering user_activity: args={{}}")
        if self.standby_manager:
            self.standby_manager.put_standby(True)
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting user_activity: return=None")

    def resizeEvent(self, event: QEvent) -> None:
        super().resizeEvent(event)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
            self.overlay_widget.raise_()
        if hasattr(self, 'btns') and self.btns is not None:
            self.btns.raise_()
        self.bg_label.lower()

    def closeEvent(self, event: QEvent) -> None:
        if hasattr(self, 'background_manager'):
            self.background_manager.close()
        super().closeEvent(event)

    def paintEvent(self, event: QEvent) -> None:
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering paintEvent: args={{'event':{event}}}")
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._default_background_color)
        painter.end()
        if hasattr(super(), 'paintEvent'):
            super().paintEvent(event)
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting paintEvent: return=None")

    def preset(self):
        """Appelle le preset du background_manager si présent."""
        if hasattr(self, 'background_manager'):
            self.background_manager.preset()
