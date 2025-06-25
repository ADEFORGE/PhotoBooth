from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QButtonGroup
from PySide6.QtGui import QIcon, QPixmap, QImage, QGuiApplication
from PySide6.QtCore import QSize, Qt, QEvent
from gui_classes.gui_object.constante import BTN_STYLE_TWO, BTN_STYLE_TWO_FONT_SIZE_PERCENT
import os
from PIL import Image
import io

DEBUG_Btn = False
DEBUG_BtnStyleOne = False
DEBUG_BtnStyleTwo = False
DEBUG_Btns = False
DEBUG__compute_dynamic_size = False

Changed_names = []

def _compute_dynamic_size(original_size: QSize) -> QSize:
    if DEBUG__compute_dynamic_size:
        print(f"[DEBUG][__compute_dynamic_size] Entering _compute_dynamic_size: args={(original_size,)}")
    screen = QGuiApplication.primaryScreen()
    geom = screen.availableGeometry()
    target = int(min(geom.width(), geom.height()) * 0.07)
    result = QSize(target, target)
    if DEBUG__compute_dynamic_size:
        print(f"[DEBUG][__compute_dynamic_size] Exiting _compute_dynamic_size: return={result}")
    return result

class Btn(QPushButton):
    def __init__(self, name: str, parent: QWidget = None) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering __init__: args={(name, parent)}")
        super().__init__(parent)
        self.name = name
        self._connected_slots = []
        self.setObjectName(name)
        self._icon_path = None
        self._setup_standby_manager_events()
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting __init__: return=None")

    def _setup_standby_manager_events(self) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering _setup_standby_manager_events: args=()")
        p = self.parent()
        self._standby_manager = None
        while p:
            if getattr(p, "standby_manager", None):
                self._standby_manager = p.standby_manager
                break
            p = p.parent() if hasattr(p, "parent") else None
        if self._standby_manager:
            self.installEventFilter(self)
            self.clicked.connect(self._on_btn_clicked_reset_stop_timer)
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting _setup_standby_manager_events: return=None")

    def eventFilter(self, obj, ev) -> bool:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering eventFilter: args={(obj, ev)}")
        if obj is self and self._standby_manager:
            if ev.type() == QEvent.Enter:
                self._standby_manager.reset_standby_timer()
            elif ev.type() == QEvent.MouseButtonPress:
                self._standby_manager.reset_standby_timer()
                self._standby_manager.stop_standby_timer()
        result = super().eventFilter(obj, ev)
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting eventFilter: return={result}")
        return result

    def _on_btn_clicked_reset_stop_timer(self) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering _on_btn_clicked_reset_stop_timer: args=()")
        if self._standby_manager:
            self._standby_manager.reset_standby_timer()
            self._standby_manager.stop_standby_timer()
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting _on_btn_clicked_reset_stop_timer: return=None")

    def initialize(self, style: str = None, icon_path: str = None, size: QSize = None, checkable: bool = False) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering initialize: args={(style, icon_path, size, checkable)}")
        if style:
            self.setStyleSheet(style)
        if size:
            dyn_size = _compute_dynamic_size(size)
            side = max(dyn_size.width(), dyn_size.height())
            square = QSize(side, side)
            self.setMinimumSize(square)
            self.setMaximumSize(square)
        self.setCheckable(checkable)
        if icon_path and os.path.exists(icon_path):
            self._icon_path = icon_path
            self.setIcon(QIcon(self._icon_path))
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting initialize: return=None")

    def resizeEvent(self, event) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering resizeEvent: args={(event,)}")
        side = min(self.width(), self.height())
        self.resize(side, side)
        if self._icon_path:
            pad = 0.75
            icon_side = int(side * pad)
            self.setIconSize(QSize(icon_side, icon_side))
        super().resizeEvent(event)
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting resizeEvent: return=None")

    def place(self, layout, row: int, col: int, alignment=Qt.AlignCenter) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering place: args={(layout, row, col, alignment)}")
        layout.addWidget(self, row, col, alignment=alignment)
        self.setVisible(True)
        self.raise_()
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting place: return=None")

    def connect_slot(self, slot, signal: str = "clicked") -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering connect_slot: args={(slot, signal)}")
        if hasattr(self, signal):
            getattr(self, signal).connect(slot)
            self._connected_slots.append((signal, slot))
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting connect_slot: return=None")

    def connect_by_name(self, obj, method_name: str, signal: str = "clicked") -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering connect_by_name: args={(obj, method_name, signal)}")
        if hasattr(obj, method_name):
            self.connect_slot(getattr(obj, method_name), signal)
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting connect_by_name: return=None")

    def cleanup(self) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering cleanup: args=()")
        for sig, sl in self._connected_slots:
            try:
                getattr(self, sig).disconnect(sl)
            except:
                pass
        self._connected_slots.clear()
        self.setParent(None)
        self.deleteLater()
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting cleanup: return=None")

    def set_disabled_bw(self) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering set_disabled_bw: args=()")
        self.setEnabled(False)
        self.blockSignals(True)
        self.setCheckable(False)
        self.setChecked(False)
        self.setFocusPolicy(Qt.NoFocus)

        def to_bw(path: str):
            if os.path.exists(path):
                with Image.open(path) as img:
                    buf = io.BytesIO()
                    img.convert("L").save(buf, "PNG")
                    return QPixmap.fromImage(QImage.fromData(buf.getvalue()))
            return None

        if isinstance(self, BtnStyleOne):
            p = f"gui_template/btn_icons/{self.name}.png"
            pix = to_bw(p)
            if pix:
                self.setIcon(QIcon(pix))
        elif isinstance(self, BtnStyleTwo):
            p = f"gui_template/btn_textures copy/{self.name}.png"
            pix = to_bw(p)
            if pix:
                tmp = f"/tmp/bw_{self.name}.png"
                pix.save(tmp)
                style = f"""
                    QPushButton {{
                        border:2px solid black; border-radius:5px;
                        background-image:url({tmp}); background-position:center;
                        background-repeat:no-repeat; color:black;
                    }}
                    QPushButton:disabled {{
                        border:2px solid black; border-radius:5px;
                        background-image:url({tmp}); background-position:center;
                        background-repeat:no-repeat; color:black;
                    }}
                """
                self.setStyleSheet(style)
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting set_disabled_bw: return=None")

    def set_enabled_color(self) -> None:
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Entering set_enabled_color: args=()")
        self.setEnabled(True)
        p = f"gui_template/btn_icons/{self.name}.png"
        if os.path.exists(p):
            self.setIcon(QIcon(p))
        self.setStyleSheet(self.styleSheet().replace(";opacity:0.5;", ""))
        if DEBUG_Btn:
            print(f"[DEBUG][Btn] Exiting set_enabled_color: return=None")


class BtnStyleOne(Btn):
    def __init__(self, name: str, parent: QWidget = None) -> None:
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Entering __init__: args={(name, parent)}")
        super().__init__(name, parent)
        base = f"gui_template/btn_icons/{name}"
        self._icon_path_passive = f"{base}_passive.png"
        self._icon_path_pressed = f"{base}_pressed.png"
        dyn = _compute_dynamic_size(QSize(80, 80))
        side = max(dyn.width(), dyn.height(), 120)
        self._btn_side = side
        self._icon_pad = 1.0
        self.setStyleSheet("QPushButton { background: transparent; border: none; }")
        self._set_passive_icon()
        square = QSize(side, side)
        self.setMinimumSize(square)
        self.setMaximumSize(square)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(True)
        self.raise_()
        self.pressed.connect(self._set_pressed_icon)
        self.released.connect(self._set_passive_icon)
        self.toggled.connect(self._on_toggled)
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Exiting __init__: return=None")

    def _set_pressed_icon(self) -> None:
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Entering _set_pressed_icon: args=()")
        if os.path.exists(self._icon_path_pressed):
            pix = QPixmap(self._icon_path_pressed)
            if not pix.isNull():
                size = int(self._btn_side * self._icon_pad)
                icon = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setIcon(QIcon(icon))
                self.setIconSize(QSize(size, size))
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Exiting _set_pressed_icon: return=None")

    def _set_passive_icon(self) -> None:
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Entering _set_passive_icon: args=()")
        if os.path.exists(self._icon_path_passive):
            pix = QPixmap(self._icon_path_passive)
            if not pix.isNull():
                size = int(self._btn_side * self._icon_pad)
                icon = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setIcon(QIcon(icon))
                self.setIconSize(QSize(size, size))
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Exiting _set_passive_icon: return=None")

    def _on_toggled(self, checked: bool) -> None:
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Entering _on_toggled: args={(checked,)}")
        if checked:
            self._set_pressed_icon()
        else:
            self._set_passive_icon()
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Exiting _on_toggled: return=None")

    def resizeEvent(self, event) -> None:
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Entering resizeEvent: args={(event,)}")
        side = min(self.width(), self.height())
        self._btn_side = side
        if self.isDown() or self.isChecked():
            self._set_pressed_icon()
        else:
            self._set_passive_icon()
        super().resizeEvent(event)
        if DEBUG_BtnStyleOne:
            print(f"[DEBUG][BtnStyleOne] Exiting resizeEvent: return=None")


class BtnStyleTwo(Btn):
    def __init__(self, name: str, parent: QWidget = None) -> None:
        if DEBUG_BtnStyleTwo:
            print(f"[DEBUG][BtnStyleTwo] Entering __init__: args={(name, parent)}")
        super().__init__(name, parent)
        texture_path = f"gui_template/btn_textures copy/{name}.png"
        style = BTN_STYLE_TWO.format(texture=texture_path)
        dyn = _compute_dynamic_size(QSize(80, 80))
        side = max(dyn.width(), dyn.height(), 120)
        square = QSize(side, side)
        self.setText(name)
        self.initialize(style=style, icon_path=None, size=square, checkable=True)
        self.setMinimumSize(square)
        self.setMaximumSize(square)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(True)
        self.raise_()
        font = self.font()
        font.setFamily("Arial")
        font.setPointSize(int(side * BTN_STYLE_TWO_FONT_SIZE_PERCENT / 100))
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet(self.styleSheet() + "\ncolor: white;")
        if DEBUG_BtnStyleTwo:
            print(f"[DEBUG][BtnStyleTwo] Exiting __init__: return=None")


class Btns:
    def __init__(self, parent: QWidget, style1_names: list, style2_names: list, slot_style1=None, slot_style2=None) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering __init__: args={(parent, style1_names, style2_names, slot_style1, slot_style2)}")
        self.parent = parent
        overlay = getattr(parent, "overlay_widget", parent)
        self.style1_btns = []
        self.style2_btns = []
        self.button_group = QButtonGroup(overlay)
        self.button_group.setExclusive(True)
        self.setup_buttons(style1_names, style2_names, slot_style1, slot_style2)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting __init__: return=None")

    def lower_(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering lower_: args=()")
        for btn in self.style1_btns + self.style2_btns:
            btn.setVisible(False)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting lower_: return=None")

    def setup_buttons(self, style1_names: list, style2_names: list, slot_style1=None, slot_style2=None, layout=None, start_row: int = 3) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering setup_buttons: args={(style1_names, style2_names, slot_style1, slot_style2, layout, start_row)}")
        self.lower_()
        self.clear_style1_btns()
        self.clear_style2_btns()
        for name in style1_names:
            self.add_style1_btn(name, slot_style1)
        for name in style2_names:
            self.add_style2_btn(name, slot_style2)
        if layout:
            self.place_all(layout, start_row)
        self.raise_()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting setup_buttons: return=None")

    def setup_buttons_style_1(self, style1_names: list, slot_style1=None, layout=None, start_row: int = 3) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering setup_buttons_style_1: args={(style1_names, slot_style1, layout, start_row)}")
        self.lower_()
        self.clear_style1_btns()
        for name in style1_names:
            self.add_style1_btn(name, slot_style1)
        if layout:
            self.place_style1(layout, start_row)
        self.raise_()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting setup_buttons_style_1: return=None")

    def setup_buttons_style_2(self, style2_names: list, slot_style2=None, layout=None, start_row: int = 4) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering setup_buttons_style_2: args={(style2_names, slot_style2, layout, start_row)}")
        self.lower_()
        self.clear_style2_btns()
        for name in style2_names:
            self.add_style2_btn(name, slot_style2)
        if layout:
            self.place_style2(layout, start_row)
        self.raise_()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting setup_buttons_style_2: return=None")

    def add_style1_btn(self, name: str, slot_style1=None):
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering add_style1_btn: args={(name, slot_style1)}")
        overlay = getattr(self.parent, "overlay_widget", self.parent)
        btn = BtnStyleOne(name, parent=overlay)
        if isinstance(slot_style1, str):
            btn.connect_by_name(self.parent, slot_style1)
        elif callable(slot_style1):
            btn.clicked.connect(slot_style1)
        self.style1_btns.append(btn)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting add_style1_btn: return={btn}")
        return btn

    def add_style2_btn(self, name: str, slot_style2=None):
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering add_style2_btn: args={(name, slot_style2)}")
        overlay = getattr(self.parent, "overlay_widget", self.parent)
        btn = BtnStyleTwo(name, parent=overlay)
        if isinstance(slot_style2, str):
            btn.connect_by_name(self.parent, slot_style2)
        elif callable(slot_style2):
            btn.clicked.connect(lambda checked, b=btn: slot_style2(checked, b))
        self.button_group.addButton(btn)
        self.style2_btns.append(btn)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting add_style2_btn: return={btn}")
        return btn

    def remove_style1_btn(self, name: str) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering remove_style1_btn: args={(name,)}")
        for btn in self.style1_btns:
            if btn.name == name:
                btn.cleanup()
                self.style1_btns.remove(btn)
                break
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting remove_style1_btn: return=None")

    def remove_style2_btn(self, name: str) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering remove_style2_btn: args={(name,)}")
        for btn in self.style2_btns:
            if btn.name == name:
                btn.cleanup()
                self.button_group.removeButton(btn)
                self.style2_btns.remove(btn)
                break
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting remove_style2_btn: return=None")

    def clear_style1_btns(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering clear_style1_btns: args=()")
        for btn in self.style1_btns:
            btn.cleanup()
        self.style1_btns.clear()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting clear_style1_btns: return=None")

    def clear_style2_btns(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering clear_style2_btns: args=()")
        for btn in self.style2_btns:
            btn.cleanup()
            self.button_group.removeButton(btn)
        self.style2_btns.clear()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting clear_style2_btns: return=None")

    def place_style1(self, layout, start_row: int = 3) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering place_style1: args={(layout, start_row)}")
        col_max = layout.columnCount() if hasattr(layout, "columnCount") else 7
        n = len(self.style1_btns)
        if n:
            if n % 2 == 0:
                left = (col_max - n - 1) // 2
                for i, btn in enumerate(self.style1_btns):
                    col = left + i if i < n // 2 else left + i + 1
                    btn.place(layout, start_row, col)
            else:
                col1 = (col_max - n) // 2
                for i, btn in enumerate(self.style1_btns):
                    btn.place(layout, start_row, col1 + i)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting place_style1: return=None")

    def place_style2(self, layout, start_row: int = 4) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering place_style2: args={(layout, start_row)}")
        col_max = layout.columnCount() if hasattr(layout, "columnCount") else 7
        n = len(self.style2_btns)
        if n:
            if n % 2 == 0:
                left = (col_max - n - 1) // 2
                for i, btn in enumerate(self.style2_btns):
                    col = left + i if i < n // 2 else left + i + 1
                    btn.place(layout, start_row, col)
            else:
                col2 = (col_max - n) // 2
                for i, btn in enumerate(self.style2_btns):
                    btn.place(layout, start_row, col2 + i)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting place_style2: return=None")

    def place_all(self, layout, start_row: int = 3) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering place_all: args={(layout, start_row)}")
        self.place_style1(layout, start_row)
        self.place_style2(layout, start_row + 1)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting place_all: return=None")

    def set_style1_btns(self, names: list, slot_style1=None, layout=None, start_row: int = 3) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_style1_btns: args={(names, slot_style1, layout, start_row)}")
        self.clear_style1_btns()
        for name in names:
            self.add_style1_btn(name, slot_style1)
        if layout:
            self.place_style1(layout, start_row)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_style1_btns: return=None")

    def set_style2_btns(self, names: list, slot_style2=None, layout=None, start_row: int = 4) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_style2_btns: args={(names, slot_style2, layout, start_row)}")
        self.clear_style2_btns()
        for name in names:
            self.add_style2_btn(name, slot_style2)
        if layout:
            self.place_style2(layout, start_row)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_style2_btns: return=None")

    def set_all_btns(self, style1_names: list, style2_names: list, slot_style1=None, slot_style2=None, layout=None, start_row: int = 3) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_all_btns: args={(style1_names, style2_names, slot_style1, slot_style2, layout, start_row)}")
        self.set_style1_btns(style1_names, slot_style1, layout, start_row)
        self.set_style2_btns(style2_names, slot_style2, layout, start_row + 1)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_all_btns: return=None")

    def set_all_disabled_bw(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_all_disabled_bw: args=()")
        for btn in self.style1_btns + self.style2_btns:
            btn.set_disabled_bw()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_all_disabled_bw: return=None")

    def set_all_enabled_color(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_all_enabled_color: args=()")
        for btn in self.style1_btns + self.style2_btns:
            btn.set_enabled_color()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_all_enabled_color: return=None")

    def set_disabled_bw_style1(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_disabled_bw_style1: args=()")
        for btn in self.style1_btns:
            btn.set_disabled_bw()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_disabled_bw_style1: return=None")

    def set_disabled_bw_style2(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_disabled_bw_style2: args=()")
        for btn in self.style2_btns:
            btn.set_disabled_bw()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_disabled_bw_style2: return=None")

    def set_enabled_color_style1(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_enabled_color_style1: args=()")
        for btn in self.style1_btns:
            btn.set_enabled_color()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_enabled_color_style1: return=None")

    def set_enabled_color_style2(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering set_enabled_color_style2: args=()")
        for btn in self.style2_btns:
            btn.set_enabled_color()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting set_enabled_color_style2: return=None")

    def cleanup(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering cleanup: args=()")
        for btn in self.style1_btns + self.style2_btns:
            btn.cleanup()
        self.style1_btns.clear()
        self.style2_btns.clear()
        self.button_group.setParent(None)
        self.button_group.deleteLater()
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting cleanup: return=None")

    def raise_(self) -> None:
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Entering raise_: args=()")
        for btn in self.style1_btns + self.style2_btns:
            btn.raise_()
            btn.setVisible(True)
        if DEBUG_Btns:
            print(f"[DEBUG][Btns] Exiting raise_: return=None")
