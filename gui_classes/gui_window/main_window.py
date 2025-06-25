DEBUG_PhotoBooth = True

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from gui_classes.gui_window.base_window import BaseWindow
from gui_classes.gui_object.constante import DEBUG, TOOLTIP_STYLE, TOOLTIP_DURATION_MS, dico_styles
from gui_classes.gui_manager.thread_manager import CountdownThread, ImageGenerationThread
from gui_classes.gui_manager.standby_manager import StandbyManager
from gui_classes.gui_manager.background_manager import BackgroundManager
from gui_classes.gui_object.overlay import OverlayRules, OverlayQrcode
from gui_classes.gui_object.toolbox import QRCodeUtils
from PySide6.QtWidgets import QToolTip, QApplication
import re

class MainWindow(BaseWindow):
    def __init__(self, parent=None):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering __init__: args={{'parent':{parent}}}")
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
        self.background_manager = BackgroundManager(self)
        self.generated_image = None
        self.original_photo = None
        if DEBUG:
            print("[INIT] Generation task and flags initialized")
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting __init__: return=None")

    def on_enter(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering on_enter: args={{}}")
        self.generated_image = None
        self.original_photo = None
        self.selected_style = None
        self.set_state_default()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting on_enter: return=None")

    def on_leave(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering on_leave: args={{}}")
        self.clean()
        self.hide_loading()
        if hasattr(self, '_countdown_overlay') and self._countdown_overlay:
            try:
                if getattr(self._countdown_overlay, '_is_alive', True):
                    self._countdown_overlay.clean_overlay()
                else:
                    pass
            except Exception as e:
                pass
            self._countdown_overlay = None
        self.countdown_overlay_manager.clear_overlay("countdown")
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting on_leave: return=None")

    def clean(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering clean: args={{}}")
        self._generation_in_progress = False
        if self._generation_task:
            if hasattr(self._generation_task, 'finished'):
                try:
                    self._generation_task.finished.disconnect()
                except Exception:
                    pass
            self._generation_task.clean()
            self._generation_task = None
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting clean: return=None")

    def cleanup(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering cleanup: args={{}}")
        if hasattr(self, 'clean'):
            self.clean()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting cleanup: return=None")

    def start(self, style_name, input_image):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering start: args={{'style_name':{style_name},'input_image':<QImage>}}")
        if self._generation_task:
            self.clean()
        self._generation_task = ImageGenerationThread(style=style_name, input_image=input_image, parent=self)
        self._generation_task.finished.connect(self._on_image_generated_callback)
        self._generation_task.start()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting start: return=None")

    def finish(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering finish: args={{}}")
        if self._generation_task:
            self._generation_task.finish()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting finish: return=None")

    def _on_style_toggle(self, checked, style_name):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering _on_style_toggle: args={{'checked':{checked},'style_name':{style_name}}}")
        self.selected_style = style_name if checked else None
        super().on_toggle(checked, style_name, generate_image=False)
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting _on_style_toggle: return=None")

    def _on_take_selfie(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering _on_take_selfie: args={{}}")
        if not getattr(self, 'selected_style', None):
            take_selfie_btn = None
            if hasattr(self, 'btns'):
                for btn in self.btns.style1_btns:
                    if btn.objectName() == "take_selfie":
                        take_selfie_btn = btn
                        break
            if take_selfie_btn:
                app = QApplication.instance()
                if app is not None:
                    old_style = app.styleSheet() or ""
                    new_style = re.sub(r"QToolTip\s*\{[^}]*\}", "", old_style)
                    app.setStyleSheet(new_style + "\n" + TOOLTIP_STYLE)
                global_pos = take_selfie_btn.mapToGlobal(take_selfie_btn.rect().center())
                QToolTip.showText(global_pos, "Select a style first", take_selfie_btn, take_selfie_btn.rect(), TOOLTIP_DURATION_MS)
            if DEBUG_PhotoBooth:
                print(f"[DEBUG][PhotoBooth] Exiting _on_take_selfie: return=None")
            return
        self.countdown_overlay_manager.start_countdown(on_finished=self._after_countdown_finish)
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting _on_take_selfie: return=None")

    def _after_countdown_finish(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering _after_countdown_finish: args={{}}")
        self.clean()
        # Note: _last_frame logic removed, must be handled elsewhere if needed
        if getattr(self, 'selected_style', None) and not self._generation_in_progress and self.original_photo:
            self.start(self.selected_style, self.original_photo)
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting _after_countdown_finish: return=None")

    def _on_image_generated_callback(self, qimg):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering _on_image_generated_callback: args={{'qimg':<QImage>}}")
        self._generation_task = None
        self._generation_in_progress = False
        if qimg and not qimg.isNull():
            self.generated_image = qimg
        else:
            self.generated_image = None
        self.update_frame()
        self.set_state_validation()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting _on_image_generated_callback: return=None")

    def _on_accept_close(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering _on_accept_close: args={{}}")
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
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting _on_accept_close: return=None")

    def reset_generation_state(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering reset_generation_state: args={{}}")
        self._generation_in_progress = False
        self._generation_task = None
        self.generated_image = None
        self.original_photo = None
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting reset_generation_state: return=None")

    def reset_to_default_state(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering reset_to_default_state: args={{}}")
        self.set_state_default()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting reset_to_default_state: return=None")

    def set_state_default(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering set_state_default: args={{}}")
        self.reset_generation_state()
        self.selected_style = None
        self.clear_display()
        self.setup_buttons(
            style1_names=["take_selfie"],
            style2_names=list(dico_styles.keys()),
            slot_style1=self._on_take_selfie,
            slot_style2=lambda checked, btn=None: self._on_style_toggle(checked, btn.text() if btn else None)
        )
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.raise_()
        if hasattr(self, 'btns'):
            self.btns.raise_()
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.show()
                btn.setEnabled(True)
        if self.standby_manager:
            self.standby_manager.set_timer_from_constante()
            self.standby_manager.start_standby_timer()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting set_state_default: return=None")

    def set_state_validation(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering set_state_validation: args={{}}")
        self.setup_buttons_style_1(['accept', 'close'], slot_style1=self._on_accept_close)
        if hasattr(self, 'btns'):
            self.btns.raise_()
            for btn in self.btns.style1_btns:
                btn.show()
                btn.setEnabled(True)
            self.btns.set_disabled_bw_style2()
        self.update_frame()
        if self.standby_manager:
            self.standby_manager.stop_standby_timer()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting set_state_validation: return=None")

    def set_state_wait(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering set_state_wait: args={{}}")
        if hasattr(self, 'btns'):
            self.btns.set_disabled_bw_style2()
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.hide()
        self.update_frame()
        if self.standby_manager:
            self.standby_manager.stop_standby_timer()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting set_state_wait: return=None")

    def update_frame(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering update_frame: args={{}}")
        if self.generated_image and not isinstance(self.generated_image, str):
            self.background_manager.set_generated_image(self.generated_image)
        elif self.original_photo:
            self.background_manager.set_captured_image(self.original_photo)
        else:
            self.background_manager.clear_all()
        self.update()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting update_frame: return=None")

    def user_activity(self):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering user_activity: args={{}}")
        if self.standby_manager:
            self.standby_manager.set_timer_from_constante()
            self.standby_manager.start_standby_timer()
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting user_activity: return=None")

    def paintEvent(self, event):
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Entering paintEvent: args={{'event':{event}}}")
        painter = QPainter(self)
        painter.fillRect(self.rect(), self._default_background_color)
        painter.end()
        if hasattr(super(), 'paintEvent'):
            super().paintEvent(event)
        if DEBUG_PhotoBooth:
            print(f"[DEBUG][PhotoBooth] Exiting paintEvent: return=None")

