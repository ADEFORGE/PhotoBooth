from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QHBoxLayout,
    QPushButton, QSizePolicy, QApplication, QGraphicsBlurEffect,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize, QEvent, QThread, Signal, QObject, QTimer
from PySide6.QtGui import (
    QMovie, QPixmap, QIcon, QImage, QPainter, QColor,
    QPen, QPainterPath
)
from gui_classes.gui_object.constante import TITLE_LABEL_STYLE, GRID_WIDTH, COUNTDOWN_FONT_STYLE
from gui_classes.gui_object.btn import Btns
from gui_classes.gui_object.toolbox import normalize_btn_name, LoadingBar
from gui_classes.gui_manager.language_manager import language_manager

DEBUG_Overlay = False
DEBUG_OverlayGray = False
DEBUG_OverlayWhite = False
DEBUG_OverlayLoading = False
DEBUG_OverlayRules = False
DEBUG_OverlayQrcode = False
DEBUG_OverlayInfo = False
DEBUG_OverlayCountdown = False
DEBUG_OverlayLang = False

CHANGED_NAMES = {}

class Overlay(QWidget):
    def __init__(self, parent: QWidget = None, center_on_screen: bool = True) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering __init__: args={(parent, center_on_screen)}")
        super().__init__(parent)
        self._is_visible = False
        self._is_alive = True
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setVisible(False)
        self.GRID_WIDTH = GRID_WIDTH
        self._center_on_screen = center_on_screen
        self._centered_once = False
        self._disabled_widgets = set()
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.setAttribute(Qt.WA_TranslucentBackground)
            self.overlay_widget.setStyleSheet("background: transparent; border-radius: 18px;")
        self.setStyleSheet("background: transparent;")
        self._register_to_parent_window()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting __init__: return=None")

    def _register_to_parent_window(self):
        """Recherche la première fenêtre parente héritant de BaseWindow et s'y enregistre."""
        try:
            from gui_classes.gui_window.base_window import BaseWindow
        except ImportError:
            return
        parent = self.parentWidget()
        while parent is not None:
            if isinstance(parent, BaseWindow):
                print(f"[DEBUG][Overlay] Registering to parent window: {parent}")
                if hasattr(parent, "register_overlay"):
                    parent.register_overlay(self)
                break
            parent = parent.parentWidget() if hasattr(parent, 'parentWidget') else None

    def setVisible(self, visible: bool) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering setVisible: args={(visible,)}")
        if not self._is_alive:
            return
        super().setVisible(visible)
        self._is_visible = visible
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting setVisible: return=None")

    def center_overlay(self) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering center_overlay: args=()")
        # Robust multi-monitor centering: center on the screen containing the parent or window
        screen = None
        # Try to get the screen from the parent widget or window
        parent = self.parentWidget() or self.window() or None
        if parent is not None and hasattr(parent, 'screen'):
            screen = parent.screen()
        if screen is None and hasattr(self, 'screen'):
            screen = self.screen()
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            w, h = self.width(), self.height()
            x = geometry.x() + (geometry.width() - w) // 2
            y = geometry.y() + (geometry.height() - h) // 2
            self.move(x, y)
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting center_overlay: return=None")

    def showEvent(self, event: QEvent) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering showEvent: args={(event,)}")
        super().showEvent(event)
        self._is_visible = True
        if self._center_on_screen and not self._centered_once:
            self.center_overlay()
            self._centered_once = True
        self._disable_all_buttons_except_overlay()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting showEvent: return=None")

    def hideEvent(self, event: QEvent) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering hideEvent: args={(event,)}")
        super().hideEvent(event)
        self._is_visible = False
        self._reenable_all_buttons()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting hideEvent: return=None")

    def get_overlay_bg_color(self) -> QColor:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering get_overlay_bg_color: args=()")
        result = QColor(0, 0, 0, 0)
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting get_overlay_bg_color: return={result}")
        return result

    def paintEvent(self, event: QEvent) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering paintEvent: args={(event,)}")
        painter = QPainter(self)
        if not painter.isActive():
            if DEBUG_Overlay:
                print("[DEBUG][Overlay] QPainter not active, skipping paintEvent.")
            return
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        radius = 18
        path.addRoundedRect(self.rect(), radius, radius)
        painter.fillPath(path, self.get_overlay_bg_color())
        painter.end()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting paintEvent: return=None")

    def setup_buttons(
        self,
        style1_names: list[str],
        style2_names: list[str],
        slot_style1: callable = None,
        slot_style2: callable = None,
        start_row: int = 3
    ) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering setup_buttons: args={(style1_names, style2_names, slot_style1, slot_style2, start_row)}")
        if hasattr(self, 'btns') and self.btns:
            self.btns.cleanup()
        self.btns = Btns(self, [], [], None, None)
        self.btns.setup_buttons(style1_names, style2_names, slot_style1, slot_style2, layout=self.overlay_layout, start_row=start_row)
        self.overlay_widget.raise_()
        self.raise_()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting setup_buttons: return=None")

    def setup_buttons_style_1(
        self,
        style1_names: list[str],
        slot_style1: callable = None,
        start_row: int = 3
    ) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering setup_buttons_style_1: args={(style1_names, slot_style1, start_row)}")
        if hasattr(self, 'btns') and self.btns:
            self.btns.setup_buttons_style_1(style1_names, slot_style1, layout=self.overlay_layout, start_row=start_row)
            self.overlay_widget.raise_()
            self.raise_()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting setup_buttons_style_1: return=None")

    def setup_buttons_style_2(
        self,
        style2_names: list[str],
        slot_style2: callable = None,
        start_row: int = 4
    ) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering setup_buttons_style_2: args={(style2_names, slot_style2, start_row)}")
        if hasattr(self, 'btns') and self.btns:
            self.btns.setup_buttons_style_2(style2_names, slot_style2, layout=self.overlay_layout, start_row=start_row)
            self.overlay_widget.raise_()
            self.raise_()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting setup_buttons_style_2: return=None")

    def show_overlay(self) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering show_overlay: args=()")
        if not self._is_alive or self._is_visible:
            return
        self.setVisible(True)
        self.raise_()
        self._disable_all_buttons_except_overlay()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting show_overlay: return=None")

    def hide_overlay(self) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering hide_overlay: args=()")
        if not self._is_alive or not self._is_visible:
            return
        self.setVisible(False)
        self._centered_once = False
        self._reenable_all_buttons()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting hide_overlay: return=None")

    def clean_overlay(self) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering clean_overlay: args=()")
        if not self._is_alive:
            return
        try:
            self.hide_overlay()
            self._centered_once = False
            self._reenable_all_buttons()
            if hasattr(self, 'overlay_widget'):
                self.overlay_widget.hide()
                self.overlay_widget.setParent(None)
                self.overlay_widget.deleteLater()
            self._disabled_widgets.clear()
            self._is_alive = False
            self.deleteLater()
            QApplication.processEvents()
        except Exception:
            pass
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting clean_overlay: return=None")

    def __del__(self) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering __del__: args=()")
        self._is_alive = False
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting __del__: return=None")

    def _disable_all_buttons_except_overlay(self) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering _disable_all_buttons_except_overlay: args=()")
        app = QApplication.instance()
        self._disabled_widgets.clear()
        if not app:
            return
        try:
            for widget in app.allWidgets():
                if isinstance(widget, QPushButton) and not self.isAncestorOf(widget) and widget.isEnabled():
                    widget.setEnabled(False)
                    self._disabled_widgets.add(widget)
            if hasattr(self, 'btns'):
                for btn in self.btns.style1_btns + self.btns.style2_btns:
                    btn.setEnabled(True)
                    btn.raise_()
        except Exception:
            pass
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting _disable_all_buttons_except_overlay: return=None")

    def _reenable_all_buttons(self) -> None:
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Entering _reenable_all_buttons: args=()")
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if isinstance(widget, QPushButton):
                    widget.setEnabled(True)
        self._disabled_widgets.clear()
        if DEBUG_Overlay: print(f"[DEBUG][Overlay] Exiting _reenable_all_buttons: return=None")

class OverlayGray(Overlay):
    def __init__(self, parent: QWidget = None, center_on_screen: bool = True) -> None:
        if DEBUG_OverlayGray: print(f"[DEBUG][OverlayGray] Entering __init__: args={(parent, center_on_screen)}")
        super().__init__(parent, center_on_screen)
        self.setStyleSheet("background: transparent;")
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px;")
        if DEBUG_OverlayGray: print(f"[DEBUG][OverlayGray] Exiting __init__: return=None")

    def get_overlay_bg_color(self) -> QColor:
        if DEBUG_OverlayGray: print(f"[DEBUG][OverlayGray] Entering get_overlay_bg_color: args=()")
        result = QColor(24, 24, 24, 210)
        if DEBUG_OverlayGray: print(f"[DEBUG][OverlayGray] Exiting get_overlay_bg_color: return={result}")
        return result

class OverlayWhite(Overlay):
    def __init__(self, parent: QWidget = None, center_on_screen: bool = True) -> None:
        if DEBUG_OverlayWhite: print(f"[DEBUG][OverlayWhite] Entering __init__: args={(parent, center_on_screen)}")
        super().__init__(parent, center_on_screen)
        self.setStyleSheet("background: transparent;")
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,0.85); border-radius: 18px;")
        if DEBUG_OverlayWhite: print(f"[DEBUG][OverlayWhite] Exiting __init__: return=None")

    def get_overlay_bg_color(self) -> QColor:
        if DEBUG_OverlayWhite: print(f"[DEBUG][OverlayWhite] Entering get_overlay_bg_color: args=()")
        alpha = int(255 * 0.85)
        result = QColor(255, 255, 255, alpha)
        if DEBUG_OverlayWhite: print(f"[DEBUG][OverlayWhite] Exiting get_overlay_bg_color: return={result}")
        return result

class OverlayLoading(OverlayWhite):
    def __init__(
        self,
        parent: QWidget = None,
        width_percent: float = 0.6,
        height_percent: float = 0.05,
        border_thickness: int = 8,
        duration: int = 45
    ) -> None:
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Entering __init__: args={(parent, width_percent, height_percent, border_thickness, duration)}")
        super().__init__(parent, center_on_screen=False)
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(255,255,255,0.3);")
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay_widget.setGeometry(self.rect())
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        self.loading_bar = LoadingBar(width_percent, height_percent, border_thickness, parent=self)
        self.loading_bar.setDuration(duration)
        self.overlay_layout.addWidget(self.loading_bar, 0, 0, alignment=Qt.AlignCenter)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.overlay_widget)
        self.setFocusPolicy(Qt.NoFocus)
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Exiting __init__: return=None")

    def resizeEvent(self, event: QEvent) -> None:
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Entering resizeEvent: args={(event,)}")
        screen = self.screen()
        if screen:
            self.setGeometry(screen.geometry())
            self.overlay_widget.setGeometry(self.rect())
        super().resizeEvent(event)
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Exiting resizeEvent: return=None")

    def showEvent(self, event: QEvent) -> None:
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Entering showEvent: args={(event,)}")
        if hasattr(self, 'loading_bar'):
            self.loading_bar.progress.setValue(0)
            self.loading_bar.timer.stop()
        super().showEvent(event)
        if hasattr(self, 'loading_bar'):
            self.loading_bar.start()
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Exiting showEvent: return=None")

    def hideEvent(self, event: QEvent) -> None:
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Entering hideEvent: args={(event,)}")
        if hasattr(self, 'loading_bar'):
            self.loading_bar.timer.stop()
            self.loading_bar.progress.setValue(0)
        super().hideEvent(event)
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Exiting hideEvent: return=None")

    def clean_overlay(self) -> None:
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Entering clean_overlay: args=()")
        if hasattr(self, 'loading_bar'):
            self.loading_bar.timer.stop()
            self.loading_bar.deleteLater()
        super().clean_overlay()
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Exiting clean_overlay: return=None")

    def stop_animation(self) -> None:
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Entering stop_animation: args=()")
        if hasattr(self, 'loading_bar'):
            self.loading_bar.timer.stop()
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Exiting stop_animation: return=None")

    def hide_overlay(self) -> None:
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Entering hide_overlay: args=()")
        if hasattr(self, 'loading_bar'):
            self.loading_bar.timer.stop()
        super().hide_overlay()
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Exiting hide_overlay: return=None")

    def __del__(self) -> None:
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Entering __del__: args=()")
        if hasattr(self, 'loading_bar'):
            self.loading_bar.timer.stop()
        super().__del__()
        if DEBUG_OverlayLoading: print(f"[DEBUG][OverlayLoading] Exiting __del__: return=None")

class OverlayRules(OverlayWhite):
    def __init__(self, parent: QWidget = None, on_validate: callable = None, on_close: callable = None) -> None:
        if DEBUG_OverlayRules: print(f"[DEBUG][OverlayRules] Entering __init__: args={(parent, on_validate, on_close)}")
        super().__init__(parent)
        self.setFixedSize(700, 540)
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(40, 32, 40, 32)
        self.overlay_layout.setSpacing(24)
        for i, stretch in enumerate([0,2,1,0]):
            self.overlay_layout.setRowStretch(i, stretch)
        row = 0
        self._on_validate = on_validate
        self._on_close = on_close
        self.title_label = QLabel("", self.overlay_widget)
        self.title_label.setStyleSheet("color: black; font-size: 24px; font-weight: bold; background: transparent;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.title_label, row, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        self.msg_label = QLabel("", self.overlay_widget)
        self.msg_label.setStyleSheet("color: black; font-size: 20px; background: transparent;")
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.msg_label, row, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        self.btns = Btns(self, [], [], None, None)
        self.setup_buttons(
            style1_names=["accept", "close"],
            style2_names=[],
            slot_style1=self._on_accept_close,
            slot_style2=None,
            start_row=row
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)
        language_manager.subscribe(self.update_language)
        self.update_language()
        if DEBUG_OverlayRules: print(f"[DEBUG][OverlayRules] Exiting __init__: return=None")

    def update_language(self) -> None:
        if DEBUG_OverlayRules: print(f"[DEBUG][OverlayRules] Entering update_language: args=()")
        rules_texts = language_manager.get_texts("OverlayRules")
        self.title_label.setText(rules_texts.get("title", ""))
        self.msg_label.setText(rules_texts.get("message", ""))
        if DEBUG_OverlayRules: print(f"[DEBUG][OverlayRules] Exiting update_language: return=None")

    def _on_accept_close(self) -> None:
        if DEBUG_OverlayRules: print(f"[DEBUG][OverlayRules] Entering _on_accept_close: args=()")
        sender = self.sender()
        if sender and sender.objectName() == 'accept':
            if self._on_validate:
                self._on_validate()
            self.hide_overlay()
        elif sender and sender.objectName() == 'close':
            if self._on_close:
                self._on_close()
            self.hide_overlay()
        if DEBUG_OverlayRules: print(f"[DEBUG][OverlayRules] Exiting _on_accept_close: return=None")

    def closeEvent(self, event: QEvent) -> None:
        if DEBUG_OverlayRules: print(f"[DEBUG][OverlayRules] Entering closeEvent: args={(event,)}")
        language_manager.unsubscribe(self.update_language)
        super().closeEvent(event)
        if DEBUG_OverlayRules: print(f"[DEBUG][OverlayRules] Exiting closeEvent: return=None")

class OverlayQrcode(OverlayWhite):
    def __init__(self, parent: QWidget = None, qimage: QImage = None, on_close: callable = None) -> None:
        if DEBUG_OverlayQrcode: print(f"[DEBUG][OverlayQrcode] Entering __init__: args={(parent, qimage, on_close)}")
        super().__init__(parent)
        self.setFixedSize(700, 540)
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(40, 32, 40, 32)
        self.overlay_layout.setSpacing(24)
        for i, stretch in enumerate([0,2,1,0]):
            self.overlay_layout.setRowStretch(i, stretch)
        row = 0
        self.title_label = QLabel("", self.overlay_widget)
        self.title_label.setStyleSheet(TITLE_LABEL_STYLE + "color: black; border-bottom: none; text-decoration: none; background: transparent;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.title_label, row, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        self.qr_label = QLabel(self.overlay_widget)
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumSize(220, 220)
        self.qr_label.setMaximumSize(260, 260)
        self.qr_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if qimage and not qimage.isNull():
            pix = QPixmap.fromImage(qimage)
            scaled_pix = pix.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.qr_label.setPixmap(scaled_pix)
        self.overlay_layout.addWidget(self.qr_label, row, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        self.msg_label = QLabel("", self.overlay_widget)
        self.msg_label.setStyleSheet("color: black; font-size: 18px; background: transparent;")
        self.msg_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.msg_label, row, 0, 1, GRID_WIDTH, alignment=Qt.AlignCenter)
        row += 1
        self.btns = Btns(self, [], [], None, None)
        self._on_close = on_close
        self.setup_buttons(
            style1_names=["close"],
            style2_names=[],
            slot_style1=self._on_close_btn,
            slot_style2=None,
            start_row=row
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)
        language_manager.subscribe(self.update_language)
        self.update_language()
        if DEBUG_OverlayQrcode: print(f"[DEBUG][OverlayQrcode] Exiting __init__: return=None")

    def update_language(self) -> None:
        if DEBUG_OverlayQrcode: print(f"[DEBUG][OverlayQrcode] Entering update_language: args=()")
        qr_texts = language_manager.get_texts("OverlayQrcode")
        self.title_label.setText(qr_texts.get("title", ""))
        self.msg_label.setText(qr_texts.get("message", ""))
        if DEBUG_OverlayQrcode: print(f"[DEBUG][OverlayQrcode] Exiting update_language: return=None")

    def _on_close_btn(self) -> None:
        if DEBUG_OverlayQrcode: print(f"[DEBUG][OverlayQrcode] Entering _on_close_btn: args=()")
        if self._on_close:
            self._on_close()
        self.hide_overlay()
        if DEBUG_OverlayQrcode: print(f"[DEBUG][OverlayQrcode] Exiting _on_close_btn: return=None")

    def closeEvent(self, event: QEvent) -> None:
        if DEBUG_OverlayQrcode: print(f"[DEBUG][OverlayQrcode] Entering closeEvent: args={(event,)}")
        language_manager.unsubscribe(self.update_language)
        super().closeEvent(event)
        if DEBUG_OverlayQrcode: print(f"[DEBUG][OverlayQrcode] Exiting closeEvent: return=None")

class OverlayInfo(OverlayGray):
    def __init__(self, parent: QWidget = None) -> None:
        if DEBUG_OverlayInfo: print(f"[DEBUG][OverlayInfo] Entering __init__: args={(parent,)}")
        super().__init__(parent)
        self.setWindowTitle("Information")
        self.setFixedSize(600, 400)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        center_col = self.GRID_WIDTH // 2
        bg = QLabel(self.overlay_widget)
        bg.setGeometry(0, 0, 600, 400)
        bg.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(18)
        bg.setGraphicsEffect(blur)
        bg.lower()
        self.image_paths = [
            "gui_template/info1.png",
            "gui_template/info2.png",
            "gui_template/info3.png"
        ]
        self.current_index = 0
        self.image_label = QLabel(self.overlay_widget)
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.update_image()
        self.overlay_layout.addWidget(self.image_label, 0, 0, 1, self.GRID_WIDTH, alignment=Qt.AlignCenter)
        self.btns = Btns(self, [], [], None, None)
        btn_previous = self.btns.add_style1_btn('previous', self._on_info_btn)
        btn_close = self.btns.add_style1_btn('close', self._on_info_btn)
        btn_next = self.btns.add_style1_btn('next', self._on_info_btn)
        self.btns.place_style1(self.overlay_layout, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)
        if DEBUG_OverlayInfo: print(f"[DEBUG][OverlayInfo] Exiting __init__: return=None")

    def _on_info_btn(self) -> None:
        if DEBUG_OverlayInfo: print(f"[DEBUG][OverlayInfo] Entering _on_info_btn: args=()")
        sender = self.sender()
        if sender and sender.objectName() == 'previous' and self.current_index > 0:
            self.current_index -= 1
            self.update_image()
            self.update_buttons_state()
        elif sender and sender.objectName() == 'next' and self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.update_image()
            self.update_buttons_state()
        elif sender and sender.objectName() == 'close':
            self.hide_overlay()
            self.deleteLater()
        if DEBUG_OverlayInfo: print(f"[DEBUG][OverlayInfo] Exiting _on_info_btn: return=None")

    def update_image(self) -> None:
        if DEBUG_OverlayInfo: print(f"[DEBUG][OverlayInfo] Entering update_image: args=()")
        current_path = self.image_paths[self.current_index]
        pixmap = QPixmap(current_path)
        if not pixmap.isNull():
            self.image_label.setPixmap(pixmap.scaled(
                500, 300,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        if DEBUG_OverlayInfo: print(f"[DEBUG][OverlayInfo] Exiting update_image: return=None")

    def update_buttons_state(self) -> None:
        if DEBUG_OverlayInfo: print(f"[DEBUG][OverlayInfo] Entering update_buttons_state: args=()")
        if DEBUG_OverlayInfo: print(f"[DEBUG][OverlayInfo] Exiting update_buttons_state: return=None")

class OverlayCountdown(Overlay):
    def __init__(self, parent: QWidget = None, start: int = None) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering __init__: args={(parent, start)}")
        super().__init__(parent)
        self.setWindowTitle("Countdown")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,0);")
        self.overlay_layout = QVBoxLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        self.label = QLabel("", self.overlay_widget)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(COUNTDOWN_FONT_STYLE)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        shadow = QGraphicsDropShadowEffect(self.label)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor("white"))
        shadow.setOffset(0, 0)
        self.label.setGraphicsEffect(shadow)
        self.overlay_layout.addWidget(self.label, alignment=Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)
        self._anim_timer = QTimer(self)
        self._anim_timer.setSingleShot(True)
        self._anim_timer.timeout.connect(self._hide_number)
        self.showFullScreen()
        screen = QApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            self.setGeometry(geometry)
            self.overlay_widget.setGeometry(self.rect())
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting __init__: return=None")

    def center_overlay(self) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering center_overlay: args=()")
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting center_overlay: return=None")

    def resizeEvent(self, event: QEvent) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering resizeEvent: args={(event,)}")
        self.overlay_widget.setGeometry(self.rect())
        super().resizeEvent(event)
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting resizeEvent: return=None")

    def show_overlay(self) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering show_overlay: args=()")
        super().show_overlay()
        self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,0);")
        self.label.setVisible(False)
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting show_overlay: return=None")

    def show_number(self, value: int) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering show_number: args={(value,)}")
        self.label.setText(str(value))
        opacity = 0.65 if value > 0 else 1.0
        self.overlay_widget.setStyleSheet(f"background-color: rgba(255,255,255,{int(opacity*255)});")
        self.label.setVisible(True)
        self._anim_timer.start(500)
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting show_number: return=None")

    def _hide_number(self) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering _hide_number: args=()")
        if self.label.text() != "0":
            self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,0);")
        self.label.setVisible(False)
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting _hide_number: return=None")

    def set_full_white(self) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering set_full_white: args=()")
        self.overlay_widget.setStyleSheet("background-color: rgba(255,255,255,1);")
        self.label.setVisible(False)
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting set_full_white: return=None")

    def clean_overlay(self) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering clean_overlay: args=()")
        self._anim_timer.stop()
        super().clean_overlay()
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting clean_overlay: return=None")

    def hide_overlay(self) -> None:
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Entering hide_overlay: args=()")
        self._anim_timer.stop()
        super().hide_overlay()
        if DEBUG_OverlayCountdown: print(f"[DEBUG][OverlayCountdown] Exiting hide_overlay: return=None")

class OverlayLang(OverlayGray):
    def __init__(self, parent: QWidget = None) -> None:
        if DEBUG_OverlayLang: print(f"[DEBUG][OverlayLang] Entering __init__: args={(parent,)}")
        super().__init__(parent)
        self.setWindowTitle("Choix de la langue")
        self.setFixedSize(600, 220)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.overlay_widget = QWidget(self)
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)
        bg = QLabel(self.overlay_widget)
        bg.setGeometry(0, 0, 600, 220)
        bg.setStyleSheet("background-color: rgba(24,24,24,0.82); border-radius: 18px;")
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(18)
        bg.setGraphicsEffect(blur)
        bg.lower()
        self.btns = Btns(self, [], [], None, None)
        btn_uk = self.btns.add_style1_btn('uk', lambda: self._on_lang_btn('uk'))
        btn_norway = self.btns.add_style1_btn('norway', lambda: self._on_lang_btn('norway'))
        btn_sami = self.btns.add_style1_btn('sami', lambda: self._on_lang_btn('sami'))
        for i in range(GRID_WIDTH):
            self.overlay_layout.setColumnMinimumWidth(i, 1)
        self.btns.place_style1(self.overlay_layout, 0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.overlay_widget)
        self.setLayout(layout)
        if DEBUG_OverlayLang: print(f"[DEBUG][OverlayLang] Exiting __init__: return=None")

    def _on_lang_btn(self, lang_code: str) -> None:
        if DEBUG_OverlayLang: print(f"[DEBUG][OverlayLang] Entering _on_lang_btn: args={(lang_code,)}")
        language_manager.load_language(lang_code)
        self.hide_overlay()
        if DEBUG_OverlayLang: print(f"[DEBUG][OverlayLang] Exiting _on_lang_btn: return=None")
