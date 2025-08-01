import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constante import DEBUG, DEBUG_FULL

DEBUG_BaseWindow: bool = DEBUG
DEBUG_BaseWindow_FULL: bool = DEBUG_FULL

from typing import Optional, Callable, List
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QPainter, QResizeEvent, QPaintEvent, QShowEvent
from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QPushButton,
    QHBoxLayout, QVBoxLayout, QApplication, QToolTip
)
import re
from gui_classes.gui_object.overlay import (
    OverlayLoading, OverlayRules, OverlayQrcode, OverlayLang
)
from gui_classes.gui_object.toolbox import normalize_btn_name, QRCodeUtils
from gui_classes.gui_object.constante import (
    GRID_WIDTH, GRID_VERTICAL_SPACING, GRID_HORIZONTAL_SPACING,
    GRID_LAYOUT_MARGINS, GRID_LAYOUT_SPACING, GRID_ROW_STRETCHES,
    ICON_BUTTON_STYLE, LOGO_SIZE, INFO_BUTTON_SIZE, HUD_SIZE_RATIO, SHOW_LOGOS
)
from gui_classes.gui_object.btn import Btns




class BaseWindow(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the BaseWindow with an optional parent widget.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering __init__: args={{'parent': {parent}}}")
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self._generation_in_progress = False
        self.loading_overlay = None
        self.generated_image = None
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setObjectName("overlay_widget")
        self.overlay_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.overlay_widget.setStyleSheet("background: transparent;")
        self.overlay_layout = QGridLayout(self.overlay_widget)
        self.overlay_layout.setContentsMargins(*GRID_LAYOUT_MARGINS)
        self.overlay_layout.setSpacing(GRID_LAYOUT_SPACING)
        self.overlay_layout.setVerticalSpacing(GRID_VERTICAL_SPACING)
        self.overlay_layout.setHorizontalSpacing(GRID_HORIZONTAL_SPACING)
        self.overlay_widget.setVisible(True)
        self.overlay_widget.setGeometry(0, 0, 1920, 1080)
        self.overlay_widget.raise_()


                # Add label at the top of the overlay layout
        self.header_label = QLabel("", self.overlay_widget)
        self.place_header_label()
        self.hide_header_label()

        self.setupcontainer()
        self.setup_row_stretches()
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.overlay_widget)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.btns = None
        self._lang_btn.clicked.connect(self.show_lang_dialog)
        self._rules_btn.clicked.connect(self.show_rules_dialog)
        self.overlay_widget.raise_()
        self.raise_()
        self._overlays = [] 
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting __init__: return=None")

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handle window resize events and update overlay geometry.
        """
        if DEBUG_BaseWindow_FULL:
            logger.info(f"[DEBUG][BaseWindow] Entering resizeEvent: args={{'event': {event}}}")
        self.update()
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
        self.overlay_widget.setVisible(True)
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.get_every_btns():
                btn.raise_()
        super().resizeEvent(event)
        if DEBUG_BaseWindow_FULL:
            logger.info(f"[DEBUG][BaseWindow] Exiting resizeEvent: return=None")

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Handle paint events for custom rendering.
        """
        if DEBUG_BaseWindow_FULL:
            logger.info(f"[DEBUG][BaseWindow] Entering paintEvent: args={{'event': {event}}}")
        painter = QPainter(self)
        if not painter.isActive():
            if DEBUG_BaseWindow_FULL:
                logger.info("[DEBUG][BaseWindow] QPainter not active, skipping paintEvent.")
            return
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.end()
        if DEBUG_BaseWindow_FULL:
            logger.info(f"[DEBUG][BaseWindow] Exiting paintEvent: return=None")

    def clear_display(self) -> None:
        """
        Clear and update the display area.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering clear_display: args={{}}")
        self.update()
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting clear_display: return=None")

    def clear_buttons(self) -> None:
        """
        Remove and delete all buttons from the overlay layout.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering clear_buttons: args={{}}")
        if self.btns:
            for btn in self.btns.get_every_btns():
                btn.hide()
                btn.setParent(None)
                btn.deleteLater()
        for i in range(self.overlay_layout.rowCount() - 1, 1, -1):
            for j in range(self.overlay_layout.columnCount()):
                item = self.overlay_layout.itemAtPosition(i, j)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.hide()
                        widget.setParent(None)
                        widget.deleteLater()
                    self.overlay_layout.removeItem(item)
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting clear_buttons: return=None")

    def get_grid_width(self) -> int:
        """
        Return the grid width used for layout.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering get_grid_width: args={{}}")
        result = GRID_WIDTH
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting get_grid_width: return={result}")
        return result

    def setup_logo(self) -> QWidget:
        """
        Set up and return the logo widget for the window.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering setup_logo: args={{}}")
        layout = QVBoxLayout()
        screen = QApplication.primaryScreen()
        screen_height = screen.size().height() if screen else 1080
        logo_size = int(screen_height * HUD_SIZE_RATIO)
        for path in ("gui_template/base_window/logo1.png", "gui_template/base_window/logo2.png"):
            lbl = QLabel()
            pix = QPixmap(path)
            lbl.setPixmap(pix.scaled(logo_size, logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            lbl.setAttribute(Qt.WA_TranslucentBackground)
            lbl.setStyleSheet("background: rgba(0,0,0,0);")
            layout.addWidget(lbl)
        widget = QWidget()
        widget.setLayout(layout)
        widget.setAttribute(Qt.WA_TranslucentBackground)
        widget.setStyleSheet("background: rgba(0,0,0,0);")
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting setup_logo: return={widget}")
        return widget

    def setup_interaction_btn(self) -> QWidget:
        """
        Set up and return the interaction buttons widget.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering setup_interaction_btn: args={{}}")

        from gui_classes.gui_object.btn import _compute_dynamic_size
        btn_size = _compute_dynamic_size(QSize(80, 80)).width()

        btn_style = (
            f"QPushButton {{"
            f"background-color: rgba(180,180,180,0.35);"
            f"border: 2px solid #bbb;"
            f"border-radius: 24px;"
            f"min-width: {btn_size}px; min-height: {btn_size}px;"
            f"max-width: {btn_size}px; max-height: {btn_size}px;"
            f"}}"
            f"QPushButton:hover {{"
            f"border: 2.5px solid white;"
            f"}}"
            f"QPushButton:pressed {{"
            f"background-color: rgba(220,220,220,0.55);"
            f"border: 3px solid #eee;"
            f"}}"
        )
        lang_btn = QPushButton()
        lang_btn.setStyleSheet(btn_style)
        lang_btn.setIcon(QIcon(QPixmap("gui_template/base_window/language.png")))
        lang_btn.setIconSize(QSize(btn_size, btn_size))
        lang_btn.setFixedSize(btn_size, btn_size)
        lang_btn.raise_()
        self._lang_btn = lang_btn

        rules_btn = QPushButton()
        rules_btn.setStyleSheet(btn_style)
        rules_btn.setIcon(QIcon(QPixmap("gui_template/base_window/rule_ico.png")))
        rules_btn.setIconSize(QSize(btn_size, btn_size))
        rules_btn.setFixedSize(btn_size, btn_size)
        rules_btn.raise_()
        self._rules_btn = rules_btn

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(lang_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        layout.addWidget(rules_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        layout.addStretch(1)

        widget = QWidget()
        widget.setLayout(layout)
        widget.setAttribute(Qt.WA_TranslucentBackground)
        widget.setStyleSheet("background: rgba(0,0,0,0);")
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting setup_interaction_btn: return={{widget}}")
        return widget

    def setupcontainer(self) -> None:
        """
        Set up the main container layout for the window.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering setupcontainer: args={{}}")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        if SHOW_LOGOS:
            layout.addWidget(self.setup_logo(), alignment=Qt.AlignLeft | Qt.AlignTop)
        layout.addStretch(1)
        layout.addWidget(self.setup_interaction_btn(), alignment=Qt.AlignRight | Qt.AlignTop)
        container = QWidget()
        container.setLayout(layout)
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background: rgba(0,0,0,0);")
        self.overlay_layout.addWidget(container, 0, 0, 1, GRID_WIDTH)
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting setupcontainer: return=None")

    def setup_row_stretches(self) -> None:
        """
        Configure row stretches for the overlay layout.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering setup_row_stretches: args={{}}")
        for row, stretch in GRID_ROW_STRETCHES.items():
            if row == "title":
                continue
            idx = {"title": 0, "display": 1, "buttons": 2}[row]
            self.overlay_layout.setRowStretch(idx, stretch)
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting setup_row_stretches: return=None")

    def show_loading(self) -> None:
        """
        Show the loading overlay on the window.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering show_loading: args={{}}")
        overlay = self._ensure_overlay()
        overlay.resize(self.size())
        overlay.show()
        overlay.raise_()
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting show_loading: return=None")

    def hide_loading(self) -> None:
        """
        Hide the loading overlay if it is visible.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering hide_loading: args={{}}")
        if self.loading_overlay:
            self.loading_overlay.hide()
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting hide_loading: return=None")

    def _ensure_overlay(self) -> OverlayLoading:
        """
        Ensure the loading overlay exists and return it.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering _ensure_overlay: args={{}}")
        if not self.loading_overlay:
            self.loading_overlay = OverlayLoading(self)
            self.loading_overlay.resize(self.size())
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting _ensure_overlay: return={self.loading_overlay}")
        return self.loading_overlay

    def register_overlay(self, overlay: object) -> None:
        """
        Register a new overlay, closing all active overlays first.
        """
        logger.info(f"[BaseWindow] register_overlay called with overlay={overlay}")

        if overlay not in self._overlays:
            self._overlays.append(overlay)

    def clean_all_overlays(self) -> None:
        """
        Clean up all registered overlays and clear the list.
        """
        logger.info("[BaseWindow] clean_all_overlays called, cleaning overlays.")
        for overlay in list(self._overlays):
            try:
                overlay.clean_overlay()
            except Exception:
                pass
        self._overlays.clear()

    def on_leave(self) -> None:
        """
        Called when changing windows, cleans up overlays.
        """
        logger.info("[BaseWindow] on_leave called, cleaning overlays.")
        self.clean_all_overlays()

    def setup_buttons(
        self,
        style1_names: List[str],
        style2_names: List[str],
        slot_style1: Optional[Callable[..., None]] = None,
        slot_style2: Optional[Callable[..., None]] = None
    ) -> None:
        """
        Set up buttons for both style 1 and style 2 with optional slots.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering setup_buttons: args={{'style1_names': {style1_names}, 'style2_names': {style2_names}, 'slot_style1': {slot_style1}, 'slot_style2': {slot_style2}}}")
        self.clear_buttons()
        if self.btns:
            self.btns.cleanup()
            self.btns = None
        self.btns = Btns(self, [], [], None, None)
        self.btns.setup_buttons(
            style1_names, style2_names, slot_style1, slot_style2,
            layout=self.overlay_layout, start_row=3
        )
        self.overlay_widget.raise_()
        for btn in self.btns.get_every_btns():
            btn.raise_()
            btn.show()
        self.raise_()
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting setup_buttons: return=None")

    def setup_buttons_style_1(
        self,
        style1_names: List[str],
        slot_style1: Optional[Callable[..., None]] = None
    ) -> None:
        """
        Set up only style 1 buttons with an optional slot.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering setup_buttons_style_1: args={{'style1_names': {style1_names}, 'slot_style1': {slot_style1}}}")
        if self.btns:
            self.btns.setup_buttons_style_1(
                style1_names, slot_style1,
                layout=self.overlay_layout, start_row=3
            )
            self.overlay_widget.raise_()
            self.raise_()
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting setup_buttons_style_1: return=None")

    def setup_buttons_style_2(
        self,
        style2_names: List[str],
        slot_style2: Optional[Callable[..., None]] = None
    ) -> None:
        """
        Set up only style 2 buttons with an optional slot.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering setup_buttons_style_2: args={{'style2_names': {style2_names}, 'slot_style2': {slot_style2}}}")
        if self.btns:
            self.btns.setup_buttons_style_2(
                style2_names, slot_style2,
                layout=self.overlay_layout, start_row=4
            )
            self.overlay_widget.raise_()
            self.raise_()
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting setup_buttons_style_2: return=None")

    def showEvent(self, event: QShowEvent) -> None:
        """
        Handle the show event and raise overlays and buttons.
        """
        if DEBUG_BaseWindow_FULL:
            logger.info(f"[DEBUG][BaseWindow] Entering showEvent: args={{'event': {event}}}")
        super().showEvent(event)
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.get_every_btns():
                btn.raise_()
        if DEBUG_BaseWindow_FULL:
            logger.info(f"[DEBUG][BaseWindow] Exiting showEvent: return=None")

    def cleanup(self) -> None:
        """
        Clean up resources, overlays, and buttons for the window.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering cleanup: args={{}}")
        if self.btns:
            self.btns.cleanup()
            self.btns = None
        if self.loading_overlay:
            self.loading_overlay.hide()
            self.loading_overlay.setParent(None)
            self.loading_overlay.deleteLater()
            self.loading_overlay = None
        self.clear_display()
        self._generation_in_progress = False
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting cleanup: return=None")



    def show_rules_dialog(self) -> None:
        """
        Show the rules dialog overlay and display a QR code if validated.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering show_rules_dialog: args={{}}")
        parent = self
        def show_qrcode_overlay() -> None:
            if self.generated_image is not None:
                data = "https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX"
                pil_img = QRCodeUtils.generate_qrcode(data)
                qimg = QRCodeUtils.pil_to_qimage(pil_img)
                OverlayQrcode(self, qimage=qimg, on_close=None).show_overlay()
        OverlayRules(self, on_validate=show_qrcode_overlay, on_close=None).show_overlay()
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting show_rules_dialog: return=None")

    def show_lang_dialog(self) -> None:
        """
        Show the language selection dialog overlay.
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering show_lang_dialog: args={{}}")
        OverlayLang(self).show_overlay()
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting show_lang_dialog: return=None")

    def show_message(self, items: object, message: str, duration: int = 2000) -> None:
        """
        Display a tooltip message centered on the first widget found in items.
        items : liste de widgets (ou boutons)
        message : texte à afficher
        duration : durée d'affichage en ms
        """
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Entering show_message: args={{'items': {items}, 'message': {message}, 'duration': {duration}}}")
        target = None
        for widget in items:
            if widget is not None:
                target = widget
                break
        if target:
            app = QApplication.instance()
            if app is not None:
                old_style = app.styleSheet() or ""
                try:
                    from gui_classes.gui_object.constante import TOOLTIP_STYLE
                except ImportError:
                    TOOLTIP_STYLE = ""
                new_style = re.sub(r"QToolTip\\s*\\{[^}]*\\}", "", old_style)
                app.setStyleSheet(new_style + "\n" + TOOLTIP_STYLE)
            global_pos = target.mapToGlobal(target.rect().center())
            QToolTip.showText(global_pos, message, target, target.rect(), duration)
        if DEBUG_BaseWindow:
            logger.info(f"[DEBUG][BaseWindow] Exiting show_message: return=None")

    def place_header_label(self, row: int = 1, col: int = 0, colspan: int = GRID_WIDTH) -> None:
        """
        Place and align the header label in the overlay layout at the specified position.
        """
        self.header_label.setAlignment(Qt.AlignCenter)
        self.overlay_layout.addWidget(self.header_label, row, col, 1, colspan, alignment=Qt.AlignCenter)

    def show_header_label(self) -> None:
        """
        Show the header label.
        """
        self.header_label.show()

    def hide_header_label(self) -> None:
        """
        Hide the header label.
        """
        self.header_label.hide()

    def set_header_text(self, text: str) -> None:
        """
        Change the text displayed in the header label.
        """
        self.header_label.setText(text)

    def set_header_style(self, style: str) -> None:
        """
        Apply a stylesheet to the header label.
        """