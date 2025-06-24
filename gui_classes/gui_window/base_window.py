DEBUG_PhotoBoothBaseWidget = True

from PySide6.QtWidgets import (
    QWidget, QLabel, QGridLayout, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
)
from PySide6.QtGui import QPixmap, QIcon, QPainter
from PySide6.QtCore import Qt, QSize
from gui_classes.gui_object.overlay import (
    OverlayLoading, OverlayRules, OverlayInfo, OverlayQrcode, OverlayLang, UI_TEXTS
)
from gui_classes.gui_object.toolbox import normalize_btn_name, QRCodeUtils
from gui_classes.gui_object.constante import (
    GRID_WIDTH, GRID_VERTICAL_SPACING, GRID_HORIZONTAL_SPACING,
    GRID_LAYOUT_MARGINS, GRID_LAYOUT_SPACING, GRID_ROW_STRETCHES,
    ICON_BUTTON_STYLE, LOGO_SIZE, INFO_BUTTON_SIZE
)
from gui_classes.gui_object.btn import Btns

class BaseWindow(QWidget):
    """
    Inputs:
        parent: QWidget or None
    Outputs:
        None
    """
    def __init__(self, parent=None):
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering __init__: args={{'parent': {parent}}}")
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
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting __init__: return=None")

    def resizeEvent(self, event):
        """
        Inputs:
            event: QResizeEvent
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering resizeEvent: args={{'event': {event}}}")
        self.update()
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())
        self.overlay_widget.setVisible(True)
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
        super().resizeEvent(event)
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting resizeEvent: return=None")

    def paintEvent(self, event):
        """
        Inputs:
            event: QPaintEvent
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering paintEvent: args={{'event': {event}}}")
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting paintEvent: return=None")

    def clear_display(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering clear_display: args={{}}")
        print("[DEBUG][BASEWIDGET] clear_display called")
        print(f"[DEBUG][BASEWIDGET] clear_display: parent={self.parent()}, isVisible={self.isVisible()}, geometry={self.geometry()}")
        self.update()
        print("[DEBUG][BASEWIDGET] clear_display finished")
        print(f"[DEBUG][BASEWIDGET] clear_display: parent={self.parent()}, isVisible={self.isVisible()}, geometry={self.geometry()}")
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting clear_display: return=None")

    def clear_buttons(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering clear_buttons: args={{}}")
        print("[DEBUG][BASEWIDGET] clear_buttons called")
        if hasattr(self, 'btns') and self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                if btn is not None:
                    btn.hide()
                    btn.setParent(None)
                    btn.deleteLater()
        for i in reversed(range(2, self.overlay_layout.rowCount())):
            for j in range(self.overlay_layout.columnCount()):
                item = self.overlay_layout.itemAtPosition(i, j)
                if item:
                    widget = item.widget()
                    if widget:
                        widget.hide()
                        widget.setParent(None)
                        widget.deleteLater()
                    self.overlay_layout.removeItem(item)
        print("[DEBUG][BASEWIDGET] clear_buttons finished")
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting clear_buttons: return=None")

    def get_grid_width(self):
        """
        Inputs:
            None
        Outputs:
            int
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering get_grid_width: args={{}}")
        result = GRID_WIDTH
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting get_grid_width: return={result}")
        return result

    def setup_logo(self):
        """
        Inputs:
            None
        Outputs:
            QWidget
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering setup_logo: args={{}}")
        logo_layout = QVBoxLayout()
        logo1 = QLabel()
        logo2 = QLabel()
        for logo, path in [(logo1, "gui_template/logo1.png"), (logo2, "gui_template/logo2.png")]:
            pix = QPixmap(path)
            logo.setPixmap(pix.scaled(LOGO_SIZE, LOGO_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo.setAttribute(Qt.WA_TranslucentBackground)
            logo.setStyleSheet("background: rgba(0,0,0,0);")
            logo_layout.addWidget(logo)
        logo_widget = QWidget()
        logo_widget.setLayout(logo_layout)
        logo_widget.setAttribute(Qt.WA_TranslucentBackground)
        logo_widget.setStyleSheet("background: rgba(0,0,0,0);")
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setup_logo: return={logo_widget}")
        return logo_widget

    def setup_interaction_btn(self):
        """
        Inputs:
            None
        Outputs:
            QWidget
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering setup_interaction_btn: args={{}}")
        lang_btn = QPushButton()
        lang_btn.setStyleSheet(ICON_BUTTON_STYLE)
        lang_icon = QPixmap("gui_template/language.png")
        lang_btn.setIcon(QIcon(lang_icon))
        lang_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        lang_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        lang_btn.raise_()
        self._lang_btn = lang_btn
        rules_btn = QPushButton()
        rules_btn.setStyleSheet(ICON_BUTTON_STYLE)
        rules_btn.setFixedSize(INFO_BUTTON_SIZE + 16, INFO_BUTTON_SIZE + 16)
        rules_icon = QPixmap("gui_template/rule_ico.png")
        rules_btn.setIcon(QIcon(rules_icon))
        rules_btn.setIconSize(QSize(INFO_BUTTON_SIZE, INFO_BUTTON_SIZE))
        rules_btn.raise_()
        self._rules_btn = rules_btn
        btn_layout = QVBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        btn_layout.addWidget(lang_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        btn_layout.addWidget(rules_btn, alignment=Qt.AlignRight | Qt.AlignTop)
        btn_layout.addStretch(1)
        btn_widget = QWidget()
        btn_widget.setLayout(btn_layout)
        btn_widget.setAttribute(Qt.WA_TranslucentBackground)
        btn_widget.setStyleSheet("background: rgba(0,0,0,0);")
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setup_interaction_btn: return={btn_widget}")
        return btn_widget

    def setupcontainer(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering setupcontainer: args={{}}")
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(10)
        top_bar.addWidget(self.setup_logo(), alignment=Qt.AlignLeft | Qt.AlignTop)
        top_bar.addStretch(1)
        top_bar.addWidget(self.setup_interaction_btn(), alignment=Qt.AlignRight | Qt.AlignTop)
        container = QWidget()
        container.setLayout(top_bar)
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background: rgba(0,0,0,0);")
        self.overlay_layout.addWidget(container, 0, 0, 1, GRID_WIDTH)
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setupcontainer: return=None")

    def setup_row_stretches(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering setup_row_stretches: args={{}}")
        for row, stretch in GRID_ROW_STRETCHES.items():
            if row == 'title':
                continue
            row_index = {"title": 0, "display": 1, "buttons": 2}[row]
            self.overlay_layout.setRowStretch(row_index, stretch)
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setup_row_stretches: return=None")

    def show_loading(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering show_loading: args={{}}")
        overlay = self._ensure_overlay()
        overlay.resize(self.size())
        overlay.show()
        overlay.raise_()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting show_loading: return=None")

    def hide_loading(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering hide_loading: args={{}}")
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.hide()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting hide_loading: return=None")

    def _ensure_overlay(self):
        """
        Inputs:
            None
        Outputs:
            OverlayLoading
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering _ensure_overlay: args={{}}")
        if not hasattr(self, 'loading_overlay') or self.loading_overlay is None:
            self.loading_overlay = OverlayLoading(self)
            self.loading_overlay.resize(self.size())
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting _ensure_overlay: return={self.loading_overlay}")
        return self.loading_overlay

    def on_toggle(self, checked: bool, style_name: str, generate_image: bool = False):
        """
        Inputs:
            checked: bool
            style_name: str
            generate_image: bool (default False)
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering on_toggle: args={{'checked': {checked}, 'style_name': {style_name}, 'generate_image': {generate_image}}}")
        if self._generation_in_progress:
            if DEBUG_PhotoBoothBaseWidget:
                print(f"[DEBUG][PhotoBoothBaseWidget] Exiting on_toggle: return=None")
            return
        if checked:
            self.selected_style = style_name
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting on_toggle: return=None")

    def setup_buttons(self, style1_names, style2_names, slot_style1=None, slot_style2=None):
        """
        Inputs:
            style1_names: list
            style2_names: list
            slot_style1: callable or None
            slot_style2: callable or None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering setup_buttons: args={{'style1_names': {style1_names}, 'style2_names': {style2_names}, 'slot_style1': {slot_style1}, 'slot_style2': {slot_style2}}}")
        print("[WIDGET] Setting up buttons")
        self.clear_buttons()
        if hasattr(self, 'btns') and self.btns:
            self.btns.cleanup()
            self.btns = None
       
        self.btns = Btns(self, [], [], None, None)
        self.btns.setup_buttons(
            style1_names, 
            style2_names, 
            slot_style1, 
            slot_style2, 
            layout=self.overlay_layout, 
            start_row=3
        )
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
                btn.show()
        self.raise_()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setup_buttons: return=None")

    def setup_buttons_style_1(self, style1_names, slot_style1=None):
        """
        Inputs:
            style1_names: list
            slot_style1: callable or None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering setup_buttons_style_1: args={{'style1_names': {style1_names}, 'slot_style1': {slot_style1}}}")
        if self.btns:
            self.btns.setup_buttons_style_1(style1_names, slot_style1, layout=self.overlay_layout, start_row=3)
            self.overlay_widget.raise_()
            self.raise_()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setup_buttons_style_1: return=None")

    def setup_buttons_style_2(self, style2_names, slot_style2=None):
        """
        Inputs:
            style2_names: list
            slot_style2: callable or None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering setup_buttons_style_2: args={{'style2_names': {style2_names}, 'slot_style2': {slot_style2}}}")
        if self.btns:
            self.btns.setup_buttons_style_2(style2_names, slot_style2, layout=self.overlay_layout, start_row=4)
            self.overlay_widget.raise_()
            self.raise_()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting setup_buttons_style_2: return=None")

    def showEvent(self, event):
        """
        Inputs:
            event: QShowEvent
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering showEvent: args={{'event': {event}}}")
        super().showEvent(event)
        self.overlay_widget.raise_()
        if self.btns:
            for btn in self.btns.style1_btns + self.btns.style2_btns:
                btn.raise_()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting showEvent: return=None")

    def cleanup(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering cleanup: args={{}}")
        print("[DEBUG][BASEWIDGET] cleanup called")
        if hasattr(self, "btns") and self.btns:
            self.btns.cleanup()
            self.btns = None
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.hide()
            self.loading_overlay.setParent(None)
            self.loading_overlay.deleteLater()
            self.loading_overlay = None
        self.clear_display()
        self._generation_in_progress = False
        print("[DEBUG][BASEWIDGET] cleanup finished")
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting cleanup: return=None")

    def show_info_dialog(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering show_info_dialog: args={{}}")
        overlay = OverlayInfo(self)
        overlay.show_overlay()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting show_info_dialog: return=None")

    def show_rules_dialog(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering show_rules_dialog: args={{}}")

        app = QApplication.instance()
        parent = app.activeWindow() if app else self
        def show_qrcode_overlay():
            if getattr(self, 'generated_image', None) is not None:
                data = "https://youtu.be/xvFZjo5PgG0?si=pp6hBg7rL4zineRX"
                pil_img = QRCodeUtils.generate_qrcode(data)
                qimg = QRCodeUtils.pil_to_qimage(pil_img)
                overlay_qr = OverlayQrcode(
                    parent=parent,
                    qimage=qimg,
                    on_close=None
                )
                overlay_qr.show_overlay()
        overlay = OverlayRules(
            parent=parent,
            on_validate=show_qrcode_overlay,
            on_close=None
        )
        overlay.show_overlay()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting show_rules_dialog: return=None")

    def show_lang_dialog(self):
        """
        Inputs:
            None
        Outputs:
            None
        """
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Entering show_lang_dialog: args={{}}")
        overlay = OverlayLang(self)
        overlay.show_overlay()
        if DEBUG_PhotoBoothBaseWidget:
            print(f"[DEBUG][PhotoBoothBaseWidget] Exiting show_lang_dialog: return=None")

