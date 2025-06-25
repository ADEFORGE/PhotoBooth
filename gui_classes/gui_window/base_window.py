from typing import Optional, Callable, List
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon, QPainter, QResizeEvent, QPaintEvent, QShowEvent
from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QPushButton,
    QHBoxLayout, QVBoxLayout, QApplication
)
from gui_classes.gui_object.overlay import (
    OverlayLoading, OverlayRules, OverlayInfo, OverlayQrcode, OverlayLang
)
from gui_classes.gui_object.toolbox import normalize_btn_name, QRCodeUtils
from gui_classes.gui_object.constante import (
    GRID_WIDTH, GRID_VERTICAL_SPACING, GRID_HORIZONTAL_SPACING,
    GRID_LAYOUT_MARGINS, GRID_LAYOUT_SPACING, GRID_ROW_STRETCHES,
    ICON_BUTTON_STYLE, LOGO_SIZE, INFO_BUTTON_SIZE
)
from gui_classes.gui_object.btn import Btns

DEBUG_BaseWindow: bool = False

class BaseWindow(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering __init__: args={{'parent': {parent}}}")
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent;")
        self._generation_in_progress = False
        self.loading_overlay = None
        self.selected_style = None
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
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting __init__: return=None")

    def resizeEvent(self, event: QResizeEvent) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering resizeEvent: args={{'event': {event}}}")
        self.update()
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
        self.overlay_widget.setVisible(True)
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
        super().resizeEvent(event)
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting resizeEvent: return=None")

    def paintEvent(self, event: QPaintEvent) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering paintEvent: args={{'event': {event}}}")
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting paintEvent: return=None")

    def clear_display(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering clear_display: args={{}}")
        self.update()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting clear_display: return=None")

    def clear_buttons(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering clear_buttons: args={{}}")
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
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
            print(f"[DEBUG][BaseWindow] Exiting clear_buttons: return=None")

    def get_grid_width(self) -> int:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering get_grid_width: args={{}}")
        result = GRID_WIDTH
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting get_grid_width: return={result}")
        return result

    def setup_logo(self) -> QWidget:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering setup_logo: args={{}}")
        layout = QVBoxLayout()
        for path in ("gui_template/base_window/logo1.png", "gui_template/base_window/logo2.png"):
            lbl = QLabel()
            pix = QPixmap(path)
            lbl.setPixmap(pix.scaled(LOGO_SIZE, LOGO_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            lbl.setAttribute(Qt.WA_TranslucentBackground)
            lbl.setStyleSheet("background: rgba(0,0,0,0);")
            layout.addWidget(lbl)
        widget = QWidget()
        widget.setLayout(layout)
        widget.setAttribute(Qt.WA_TranslucentBackground)
        widget.setStyleSheet("background: rgba(0,0,0,0);")
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting setup_logo: return={widget}")
        return widget

    def setup_interaction_btn(self) -> QWidget:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering setup_interaction_btn: args={{}}")
        lang_btn = QPushButton()
        lang_btn.setStyleSheet(ICON_BUTTON_STYLE)
        lang_btn.setIcon(QIcon(QPixmap("gui_template/base_window/language.png")))
        lang_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        lang_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        lang_btn.raise_()
        self._lang_btn = lang_btn

        rules_btn = QPushButton()
        rules_btn.setStyleSheet(ICON_BUTTON_STYLE)
        rules_btn.setIcon(QIcon(QPixmap("gui_template/base_window/rule_ico.png")))
        rules_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        rules_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
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
            print(f"[DEBUG][BaseWindow] Exiting setup_interaction_btn: return={widget}")
        return widget

    def setupcontainer(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering setupcontainer: args={{}}")
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.setup_logo(), alignment=Qt.AlignLeft | Qt.AlignTop)
        layout.addStretch(1)
        layout.addWidget(self.setup_interaction_btn(), alignment=Qt.AlignRight | Qt.AlignTop)
        container = QWidget()
        container.setLayout(layout)
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background: rgba(0,0,0,0);")
        self.overlay_layout.addWidget(container, 0, 0, 1, GRID_WIDTH)
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting setupcontainer: return=None")

    def setup_row_stretches(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering setup_row_stretches: args={{}}")
        for row, stretch in GRID_ROW_STRETCHES.items():
            if row == "title":
                continue
            idx = {"title": 0, "display": 1, "buttons": 2}[row]
            self.overlay_layout.setRowStretch(idx, stretch)
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting setup_row_stretches: return=None")

    def show_loading(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering show_loading: args={{}}")
        overlay = self._ensure_overlay()
        overlay.resize(self.size())
        overlay.show()
        overlay.raise_()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting show_loading: return=None")

    def hide_loading(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering hide_loading: args={{}}")
        if self.loading_overlay:
            self.loading_overlay.hide()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting hide_loading: return=None")

    def _ensure_overlay(self) -> OverlayLoading:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering _ensure_overlay: args={{}}")
        if not self.loading_overlay:
            self.loading_overlay = OverlayLoading(self)
            self.loading_overlay.resize(self.size())
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting _ensure_overlay: return={self.loading_overlay}")
        return self.loading_overlay

    def on_toggle(self, checked: bool, style_name: str, generate_image: bool = False) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering on_toggle: args={{'checked': {checked}, 'style_name': {style_name}, 'generate_image': {generate_image}}}")
        if self._generation_in_progress:
            if DEBUG_BaseWindow:
                print(f"[DEBUG][BaseWindow] Exiting on_toggle: return=None")
            return
        if checked:
            self.selected_style = style_name
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting on_toggle: return=None")

    def setup_buttons(
        self,
        style1_names: List[str],
        style2_names: List[str],
        slot_style1: Optional[Callable[..., None]] = None,
        slot_style2: Optional[Callable[..., None]] = None
    ) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering setup_buttons: args={{'style1_names': {style1_names}, 'style2_names': {style2_names}, 'slot_style1': {slot_style1}, 'slot_style2': {slot_style2}}}")
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
        for btn in self.btns.style1_btns + self.btns.style2_btns:
            btn.raise_()
            btn.show()
        self.raise_()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting setup_buttons: return=None")

    def setup_buttons_style_1(
        self,
        style1_names: List[str],
        slot_style1: Optional[Callable[..., None]] = None
    ) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering setup_buttons_style_1: args={{'style1_names': {style1_names}, 'slot_style1': {slot_style1}}}")
        if self.btns:
            self.btns.setup_buttons_style_1(
                style1_names, slot_style1,
                layout=self.overlay_layout, start_row=3
            )
            self.overlay_widget.raise_()
            self.raise_()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting setup_buttons_style_1: return=None")

    def setup_buttons_style_2(
        self,
        style2_names: List[str],
        slot_style2: Optional[Callable[..., None]] = None
    ) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering setup_buttons_style_2: args={{'style2_names': {style2_names}, 'slot_style2': {slot_style2}}}")
        if self.btns:
            self.btns.setup_buttons_style_2(
                style2_names, slot_style2,
                layout=self.overlay_layout, start_row=4
            )
            self.overlay_widget.raise_()
            self.raise_()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting setup_buttons_style_2: return=None")

    def showEvent(self, event: QShowEvent) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering showEvent: args={{'event': {event}}}")
        super().showEvent(event)
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting showEvent: return=None")

    def cleanup(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering cleanup: args={{}}")
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
            print(f"[DEBUG][BaseWindow] Exiting cleanup: return=None")

    def show_info_dialog(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering show_info_dialog: args={{}}")
        OverlayInfo(self).show_overlay()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting show_info_dialog: return=None")

    def show_rules_dialog(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering show_rules_dialog: args={{}}")
        app = QApplication.instance()
        parent = app.activeWindow() if app else self
        def show_qrcode_overlay() -> None:
            if self.generated_image is not None:
                data = "https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX"
                pil_img = QRCodeUtils.generate_qrcode(data)
                qimg = QRCodeUtils.pil_to_qimage(pil_img)
                OverlayQrcode(parent=parent, qimage=qimg, on_close=None).show_overlay()
        OverlayRules(parent=parent, on_validate=show_qrcode_overlay, on_close=None).show_overlay()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting show_rules_dialog: return=None")

    def show_lang_dialog(self) -> None:
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Entering show_lang_dialog: args={{}}")
        OverlayLang(self).show_overlay()
        if DEBUG_BaseWindow:
            print(f"[DEBUG][BaseWindow] Exiting show_lang_dialog: return=None")
