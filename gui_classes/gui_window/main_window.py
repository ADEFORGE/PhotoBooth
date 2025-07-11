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
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting __init__: return=None")

    def update_language(self) -> None:
        self.update_frame()
        self._texts = language_manager.get_texts('main_window') or {}
        self.update_frame()

    def on_enter(self) -> None:
        self.update_frame()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering on_enter: args={{}}")
        if hasattr(self, 'background_manager'):
            self.background_manager.on_enter()
        self.set_state_default()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting on_enter: return=None")
        self.update_frame()

    def on_leave(self) -> None:
        self.update_frame()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering on_leave: args={{}}")
        if hasattr(self, 'background_manager'):
            self.background_manager.on_leave()
        # Appel du on_leave de la classe parente pour nettoyage overlays
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
            print(f"[DEBUG][MainWindow] Exiting on_leave: return=None")
        self.update_frame()

    def cleanup(self) -> None:
        self.update_frame()
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
        self.update_frame()

    def set_generation_style(self, checked: bool, style_name: str, generate_image: bool = False) -> None:
        self.update_frame()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering set_generation_style: args={{'checked':{checked},'style_name':{style_name},'generate_image':{generate_image}}}")
        if self._generation_in_progress:
            if DEBUG_MainWindow:
                print(f"[DEBUG][MainWindow] Exiting set_generation_style: return=None")
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
            print(f"[DEBUG][MainWindow] Exiting set_generation_style: return=None")
        self.update_frame()

    def take_selfie(self) -> None:
        self.update_frame()
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
        self.update_frame()

    def selfie_countdown(self, on_finished: Optional[Callable[[], None]] = None) -> None:
        self.update_frame()
        self.countdown_overlay_manager.start_countdown(on_finished=on_finished)
        self.update_frame()

    def selfie(self, callback: Optional[Callable[[], None]] = None) -> None:
        self.update_frame()
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
        self.update_frame()

    def generation(self, style_name: str, input_image: QImage, callback: Optional[Callable[[], None]] = None) -> None:
        self.update_frame()
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
        self.update_frame()

    def show_generation(self, qimg: QImage) -> None:
        self.update_frame()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering show_generation: args={{'qimg':<QImage>}}")
        self._generation_task = None
        self._generation_in_progress = False
        self.generated_image = qimg if qimg and not qimg.isNull() else None
        self.update_frame()
        self.set_state_validation()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting show_generation: return=None")
        self.update_frame()

    def show_qrcode_overlay(self, image_to_send):
        print(f"[MainWindow] show_qrcode_overlay called with image_to_send={type(image_to_send)}")
        # URL du hotspot, à adapter selon la config réseau
        hotspot_url = "http://192.168.10.2:5000/share"
        overlay_qr = OverlayQrcode(
            self,
            on_close=self.set_state_default,
            hotspot_url=hotspot_url,
            image_to_send=image_to_send
        )
        overlay_qr.show_overlay()

    def show_rules_overlay(self, qimg):
        """
        Initialise et affiche l'overlay des règles.
        En validation, affiche l'overlay QR code. En fermeture, reset l'état.
        """
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


    def _on_accept_close(self) -> None:
        self.update_frame()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering _on_accept_close: args={{}}")
        sender = self.sender()
        if sender and sender.objectName() == 'accept':
            self.set_state_wait()
            # Vérifier qu'une image a bien été générée
            if not hasattr(self, 'generated_image') or self.generated_image is None:
                print("Aucune image générée disponible.")
                self.set_state_default()
                return
            qimg = self.generated_image
            self.show_rules_overlay(qimg)
        else:
            self.set_state_default()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting _on_accept_close: return=None")
        self.update_frame()

    def reset_generation_state(self) -> None:
        self.update_frame()
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Entering reset_generation_state: args={{}}")
        self._generation_in_progress = False
        self._generation_task = None
        self.generated_image = None
        self.original_photo = None
        self.selected_style = None
        if DEBUG_MainWindow:
            print(f"[DEBUG][MainWindow] Exiting reset_generation_state: return=None")
        self.update_frame()

    def set_state_default(self) -> None:
        self.update_frame()
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
        self.update_frame()

    def set_state_validation(self) -> None:
        self.update_frame()
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
        self.update_frame()

    def set_state_wait(self) -> None:
        self.update_frame()
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
        self.update_frame()

    def update_frame(self) -> None:
        # Sécurité : update uniquement si les objets existent
        if hasattr(self, 'background_manager') and self.background_manager:
            if hasattr(self, 'generated_image') and self.generated_image and not isinstance(self.generated_image, str):
                self.background_manager.set_generated(self.generated_image)
            elif hasattr(self, 'original_photo') and self.original_photo:
                self.background_manager.capture()
            self.background_manager.update_background()
        if hasattr(self, 'update') and callable(self.update):
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
        if not painter.isActive():
            if DEBUG_MainWindow:
                print("[DEBUG][MainWindow] QPainter not active, skipping paintEvent.")
            return
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
