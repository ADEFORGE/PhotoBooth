from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QButtonGroup
from PySide6.QtGui import QIcon, QPixmap, QImage, QGuiApplication
from PySide6.QtCore import QSize, Qt, QEvent
from gui_classes.gui_object.constante import BTN_STYLE_TWO, BTN_STYLE_TWO_FONT_SIZE_PERCENT, GRID_WIDTH
from gui_classes.gui_manager.language_manager import language_manager
import os
from PIL import Image
import io, re

import logging
logger = logging.getLogger(__name__)

from gui_classes.gui_object.constante import DEBUG, DEBUG_FULL

DEBUG_Btn = DEBUG
DEBUG_Btn_FULL = DEBUG_FULL
DEBUG_BtnStyleOne = DEBUG
DEBUG_BtnStyleOne_FULL = DEBUG_FULL
DEBUG_BtnStyleTwo = DEBUG
DEBUG_BtnStyleTwo_FULL = DEBUG_FULL
DEBUG_Btns = DEBUG
DEBUG_Btns_FULL = DEBUG_FULL
DEBUG_compute_dynamic_size = DEBUG


def _compute_dynamic_size(original_size: QSize) -> QSize:
    if DEBUG_compute_dynamic_size:
        logger.info(f"[DEBUG][_compute_dynamic_size] Entering _compute_dynamic_size: args={(original_size,)}")
    screen = QGuiApplication.primaryScreen()
    geom = screen.availableGeometry()
    target = int(min(geom.width(), geom.height()) * 0.07)
    result = QSize(target, target)
    if DEBUG_compute_dynamic_size:
        logger.info(f"[DEBUG][_compute_dynamic_size] Exiting _compute_dynamic_size: return={result}")
    return result

class Btn(QPushButton):
    def __init__(self, name: str, parent: QWidget = None) -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering __init__: args={(name, parent)}")
        super().__init__(parent)
        self._name = name
        self._connected_slots = []
        self.setObjectName(name)
        self._icon_path = None
        self._setup_standby_manager_events()
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting __init__: return=None")
    
    def get_name(self) -> str:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering get_name: args=()")
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting get_name: return={self._name}")
        return self._name

    def _setup_standby_manager_events(self) -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering _setup_standby_manager_events: args=()")
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
            logger.info(f"[DEBUG][Btn] Exiting _setup_standby_manager_events: return=None")

    def eventFilter(self, obj, ev) -> bool:
        if DEBUG_Btn_FULL:
            logger.info(f"[DEBUG][Btn] Entering eventFilter: args={(obj, ev)}")
        if obj is self and self._standby_manager:
            if ev.type() == QEvent.Enter:
                self._standby_manager.reset_standby_timer()
            elif ev.type() == QEvent.MouseButtonPress:
                self._standby_manager.reset_standby_timer()
                self._standby_manager.stop_standby_timer()
        result = super().eventFilter(obj, ev)
        if DEBUG_Btn_FULL:
            logger.info(f"[DEBUG][Btn] Exiting eventFilter: return={result}")
        return result

    def _on_btn_clicked_reset_stop_timer(self) -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering _on_btn_clicked_reset_stop_timer: args=()")
        if self._standby_manager:
            self._standby_manager.reset_standby_timer()
            self._standby_manager.stop_standby_timer()
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting _on_btn_clicked_reset_stop_timer: return=None")

    def initialize(self, style: str = None, icon_path: str = None, size: QSize = None, checkable: bool = False) -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering initialize: args={(style, icon_path, size, checkable)}")
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
            logger.info(f"[DEBUG][Btn] Exiting initialize: return=None")

    def resizeEvent(self, event) -> None:
        if DEBUG_Btn_FULL:
            logger.info(f"[DEBUG][Btn] Entering resizeEvent: args={(event,)}")
        side = min(self.width(), self.height())
        self.resize(side, side)
        if self._icon_path:
            pad = 0.75
            icon_side = int(side * pad)
            self.setIconSize(QSize(icon_side, icon_side))
        super().resizeEvent(event)
        if DEBUG_Btn_FULL:
            logger.info(f"[DEBUG][Btn] Exiting resizeEvent: return=None")

    def place(self, layout, row: int, col: int, alignment=Qt.AlignCenter) -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering place: args={(layout, row, col, alignment)}")
        layout.addWidget(self, row, col, alignment=alignment)
        self.setVisible(True)
        self.raise_()
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting place: return=None")

    def _connect_slot(self, slot, signal: str = "clicked") -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering _connect_slot: args={(slot, signal)}")
        if hasattr(self, signal):
            getattr(self, signal).connect(slot)
            self._connected_slots.append((signal, slot))
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting _connect_slot: return=None")

    def connect_by_name(self, obj, method_name: str, signal: str = "clicked") -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering connect_by_name: args={(obj, method_name, signal)}")
        if hasattr(obj, method_name):
            self._connect_slot(getattr(obj, method_name), signal)
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting connect_by_name: return=None")

    def cleanup(self) -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering cleanup: args=()")
        for sig, sl in self._connected_slots:
            try:
                getattr(self, sig).disconnect(sl)
            except:
                pass
        self._connected_slots.clear()
        self.setParent(None)
        self.deleteLater()
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting cleanup: return=None")

    def set_disabled_bw(self) -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering set_disabled_bw: args=()")
        self.setEnabled(False)
        self.blockSignals(True)
        self.setCheckable(False)
        self.setChecked(False)
        self.setFocusPolicy(Qt.NoFocus)

        def to_bw(src_path: str, dest_path: str):
            if not os.path.exists(dest_path):
                if os.path.exists(src_path):
                    with Image.open(src_path) as img:
                        img.convert("L").save(dest_path, "PNG", icc_profile=None)
            return QPixmap(dest_path) if os.path.exists(dest_path) else None

        if isinstance(self, BtnStyleOne):
            p = f"gui_template/btn_icons/{self._name}.png"
            pix = QPixmap(p)
            if not pix.isNull():
                self.setIcon(QIcon(pix))
        elif isinstance(self, BtnStyleTwo):
            src = f"gui_template/btn_textures/{self._name}.png"
            dest = f"gui_template/btn_textures/bw_{self._name}.png"
            if not os.path.exists(src):
                src = "gui_template/btn_textures/default.png"
                dest = "gui_template/btn_textures/bw_default.png"
            pix = to_bw(src, dest)
            if pix and not pix.isNull():
                style = f"""
                    QPushButton {{
                        border:2px solid black; border-radius:5px;
                        background-image:url('{dest}'); background-position:center;
                        background-repeat:no-repeat; color:black;
                    }}
                    QPushButton:disabled {{
                        border:2px solid black; border-radius:5px;
                        background-image:url('{dest}'); background-position:center;
                        background-repeat:no-repeat; color:black;
                    }}
                """
                self.setStyleSheet(style)
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting set_disabled_bw: return=None")

    def set_enabled_color(self) -> None:
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Entering set_enabled_color: args=()")
        self.setEnabled(True)
        p = f"gui_template/btn_icons/{self._name}.png"
        if os.path.exists(p):
            self.setIcon(QIcon(p))
        self.setStyleSheet(self.styleSheet().replace(";opacity:0.5;", ""))
        if DEBUG_Btn:
            logger.info(f"[DEBUG][Btn] Exiting set_enabled_color: return=None")

class BtnStyleOne(Btn):
    def __init__(self, name: str, parent: QWidget = None) -> None:
        if DEBUG_BtnStyleOne:
            logger.info(f"[DEBUG][BtnStyleOne] Entering __init__: args={(name, parent)}")
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
            logger.info(f"[DEBUG][BtnStyleOne] Exiting __init__: return=None")

    def _set_pressed_icon(self) -> None:
        if DEBUG_BtnStyleOne:
            logger.info(f"[DEBUG][BtnStyleOne] Entering _set_pressed_icon: args=()")
        if os.path.exists(self._icon_path_pressed):
            pix = QPixmap(self._icon_path_pressed)
            if not pix.isNull():
                size = int(self._btn_side * self._icon_pad)
                icon = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setIcon(QIcon(icon))
                self.setIconSize(QSize(size, size))
        if DEBUG_BtnStyleOne:
            logger.info(f"[DEBUG][BtnStyleOne] Exiting _set_pressed_icon: return=None")

    def _set_passive_icon(self) -> None:
        if DEBUG_BtnStyleOne:
            logger.info(f"[DEBUG][BtnStyleOne] Entering _set_passive_icon: args=()")
        if os.path.exists(self._icon_path_passive):
            pix = QPixmap(self._icon_path_passive)
            if not pix.isNull():
                size = int(self._btn_side * self._icon_pad)
                icon = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setIcon(QIcon(icon))
                self.setIconSize(QSize(size, size))
        if DEBUG_BtnStyleOne:
            logger.info(f"[DEBUG][BtnStyleOne] Exiting _set_passive_icon: return=None")

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
        if DEBUG_BtnStyleOne_FULL:
            logger.info(f"[DEBUG][BtnStyleOne] Entering resizeEvent: args={(event,)}")
        side = min(self.width(), self.height())
        self._btn_side = side
        if self.isDown() or self.isChecked():
            self._set_pressed_icon()
        else:
            self._set_passive_icon()
        super().resizeEvent(event)
        if DEBUG_BtnStyleOne_FULL:
            logger.info(f"[DEBUG][BtnStyleOne] Exiting resizeEvent: return=None")

class BtnStyleTwo(Btn):
    def __init__(self, name: str, text_key: str, parent: QWidget = None) -> None:
        if DEBUG_BtnStyleTwo:
            logger.info(f"[DEBUG][BtnStyleTwo] Entering __init__: args={(name, text_key, parent)}")
        super().__init__(name, parent)
        self._text_key = text_key
        self._style_name = name 
        language_manager.subscribe(self._refresh_text)
        texture_path = f"gui_template/btn_textures/{name}.png"
        if not os.path.exists(texture_path):
            texture_path = "gui_template/btn_textures/default.png"
        style = BTN_STYLE_TWO.format(texture=texture_path)
        dyn = _compute_dynamic_size(QSize(80, 80))
        side = max(dyn.width(), dyn.height(), 120)
        square = QSize(side, side)
        self.setText("") 
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
        self._refresh_text()
        if DEBUG_BtnStyleTwo:
            logger.info(f"[DEBUG][BtnStyleTwo] Exiting __init__: return=None")

    def _refresh_text(self) -> None:
        if DEBUG_BtnStyleTwo:
            logger.info(f"[DEBUG][BtnStyleTwo] Entering _refresh_text: args=()")
        value = language_manager.get_texts(self._text_key)
        if isinstance(value, dict):
            text = value.get(self._name, self._name)
        else:
            text = value or self._name
        self.setText(text)
        if DEBUG_BtnStyleTwo:
            logger.info(f"[DEBUG][BtnStyleTwo] Exiting _refresh_text: return=None")

    def cleanup(self) -> None:
        if DEBUG_BtnStyleTwo:
            logger.info(f"[DEBUG][BtnStyleTwo] Entering cleanup: args=()")
        language_manager.unsubscribe(self._refresh_text)
        super().cleanup()
        if DEBUG_BtnStyleTwo:
            logger.info(f"[DEBUG][BtnStyleTwo] Exiting cleanup: return=None")

class Btns:
    def __init__(self, parent: QWidget, style1_names: list, style2_names: list, slot_style1=None, slot_style2=None) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering __init__: args={(parent, style1_names, style2_names, slot_style1, slot_style2)}")
        self._parent = parent
        overlay = getattr(parent, "overlay_widget", parent)
        self._style1_btns = []
        self._style2_btns = []
        self._button_group = QButtonGroup(overlay)
        self._button_group.setExclusive(True)
        self.setup_buttons(style1_names, style2_names, slot_style1, slot_style2)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting __init__: return=None")

    def get_style1_btns(self) -> list:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering get_style1_btns: args=()")
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting get_style1_btns: return={self._style1_btns}")
        return self._style1_btns

    def get_style2_btns(self) -> list:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering get_style2_btns: args=()")
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting get_style2_btns: return={self._style2_btns}")
        return self._style2_btns

    def get_every_btns(self) -> list:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering get_every_btns: args=()")
        all_btns = self._style1_btns + self._style2_btns
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting get_every_btns: return={all_btns}")
        return all_btns

    def lower_(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering lower_: args=()")
        for btn in self._style1_btns + self._style2_btns:
            btn.setVisible(False)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting lower_: return=None")

    def setup_buttons(self, style1_names: list, style2_names: list, slot_style1=None, slot_style2=None, layout=None, start_row: int = 3) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering setup_buttons: args={(style1_names, style2_names, slot_style1, slot_style2, layout, start_row)}")
        self.lower_()
        self.clear_style1_btns()
        self.clear_style2_btns()
        for name in style1_names:
            self.add_style1_btn(name, slot_style1)
        # style2_names est maintenant [(name, text_key), ...]
        for name, text_key in style2_names:
            self.add_style2_btn(name, text_key, slot_style2)
        if layout:
            self.place_all(layout, start_row)
        self.raise_()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting setup_buttons: return=None")

    def setup_buttons_style_1(self, style1_names: list, slot_style1=None, layout=None, start_row: int = 3) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering setup_buttons_style_1: args={(style1_names, slot_style1, layout, start_row)}")
        self.lower_()
        self.clear_style1_btns()
        for name in style1_names:
            self.add_style1_btn(name, slot_style1)
        if layout:
            self.place_style1(layout, start_row)
        self.raise_()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting setup_buttons_style_1: return=None")

    def setup_buttons_style_2(self, style2_names: list, slot_style2=None, layout=None, start_row: int = 4) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering setup_buttons_style_2: args={(style2_names, slot_style2, layout, start_row)}")
        self.lower_()
        self.clear_style2_btns()
        for name in style2_names:
            self.add_style2_btn(name, slot_style2)
        if layout:
            self.place_style2(layout, start_row)
        self.raise_()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting setup_buttons_style_2: return=None")


    def _is_valid_btn_name(self, name: str) -> bool:
        # Accept alphanumeric, underscores, and spaces, length 1-32
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering _is_valid_btn_name: args={(name,)}")
        is_valid = bool(re.match(r'^[A-Za-z0-9_ ]{1,32}$', name))
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting _is_valid_btn_name: return={is_valid}")
        return is_valid

    def add_style1_btn(self, name: str, slot_style1=None):
        if not self._is_valid_btn_name(name):
            raise ValueError(f"Invalid button name: {name}. Must be alphanumeric or underscore, 1-32 characters.")
        else:
            if DEBUG_Btns:
                logger.info(f"[DEBUG][Btns] Entering add_style1_btn: args={(name, slot_style1)}")
            overlay = getattr(self._parent, "overlay_widget", self._parent)
            btn = BtnStyleOne(name, parent=overlay)
            if isinstance(slot_style1, str):
                btn.connect_by_name(self._parent, slot_style1)
            elif callable(slot_style1):
                btn.clicked.connect(slot_style1)
            self._style1_btns.append(btn)
            if DEBUG_Btns:
                logger.info(f"[DEBUG][Btns] Exiting add_style1_btn: return={btn}")
            return btn

    def add_style2_btn(self, name: str, text_key: str, slot_style2=None):
        if not self._is_valid_btn_name(name):
            raise ValueError(f"Invalid button name: {name}. Must be alphanumeric or underscore, 1-32 characters.")
        else:
            if DEBUG_Btns:
                logger.info(f"[DEBUG][Btns] Entering add_style2_btn: args={(name, text_key, slot_style2)}")
            overlay = getattr(self._parent, "overlay_widget", self._parent)
            btn = BtnStyleTwo(name, text_key, parent=overlay)
            if isinstance(slot_style2, str):
                btn.connect_by_name(self._parent, slot_style2)
            elif callable(slot_style2):
                btn.clicked.connect(lambda checked, b=btn: slot_style2(checked, b))
            self._button_group.addButton(btn)
            self._style2_btns.append(btn)
            if DEBUG_Btns:
                logger.info(f"[DEBUG][Btns] Exiting add_style2_btn: return={btn}")
            return btn

    def remove_style1_btn(self, name: str) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering remove_style1_btn: args={(name,)}")
        for btn in self._style1_btns:
            if btn.name == name:
                btn.cleanup()
                self._style1_btns.remove(btn)
                break
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting remove_style1_btn: return=None")

    def remove_style2_btn(self, name: str) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering remove_style2_btn: args={(name,)}")
        for btn in self._style2_btns:
            if btn.name == name:
                btn.cleanup()
                self._button_group.removeButton(btn)
                self._style2_btns.remove(btn)
                break
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting remove_style2_btn: return=None")

    def clear_style1_btns(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering clear_style1_btns: args=()")
        for btn in self._style1_btns:
            btn.cleanup()
        self._style1_btns.clear()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting clear_style1_btns: return=None")

    def clear_style2_btns(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering clear_style2_btns: args=()")
        for btn in self._style2_btns:
            btn.cleanup()
            self._button_group.removeButton(btn)
        self._style2_btns.clear()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting clear_style2_btns: return=None")

    def place_style1(self, layout, start_row: int = 3) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering place_style1: args={(layout, start_row)}")
        col_max = layout.columnCount() if hasattr(layout, "columnCount") else 7
        n = len(self._style1_btns)
        if n:
            if n % 2 == 0:
                left = (col_max - n - 1) // 2
                for i, btn in enumerate(self._style1_btns):
                    col = left + i if i < n // 2 else left + i + 1
                    btn.place(layout, start_row, col)
            else:
                col1 = (col_max - n) // 2
                for i, btn in enumerate(self._style1_btns):
                    btn.place(layout, start_row, col1 + i)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting place_style1: return=None")

    def place_style2(self, layout, start_row: int = 4) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering place_style2: args={(layout, start_row)}")
        col_max = (GRID_WIDTH)
        nb_btn = len(self._style2_btns)
        
        if nb_btn:        
            end_row = start_row + nb_btn // col_max
            if nb_btn % col_max != 0:
                end_row += 1
            for row in range(start_row, end_row):    
               nb_btn_in_row = min(col_max, nb_btn)               
               nb_btn -= nb_btn_in_row               
               i_start_btn_will_be_placed = (row - start_row) * col_max
               i_end_btn_will_be_placed = i_start_btn_will_be_placed + nb_btn_in_row  
               if nb_btn_in_row % 2 == 0:
                   left = (col_max - nb_btn_in_row - 1) // 2
                   for i, btn in enumerate(self._style2_btns[i_start_btn_will_be_placed:i_end_btn_will_be_placed]):
                       col = left + i if i < nb_btn_in_row // 2 else left + i + 1
                       btn.place(layout, row, col)
               else:
                    col2 = (col_max - nb_btn_in_row) // 2
                    for i, btn in enumerate(self._style2_btns[i_start_btn_will_be_placed:i_end_btn_will_be_placed]):
                        btn.place(layout, row, col2 + i)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting place_style2: return=None")

    def place_all(self, layout, start_row: int = 3) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering place_all: args={(layout, start_row)}")
        self.place_style1(layout, start_row)
        self.place_style2(layout, start_row + 1)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting place_all: return=None")

    def set_style1_btns(self, names: list, slot_style1=None, layout=None, start_row: int = 3) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_style1_btns: args={(names, slot_style1, layout, start_row)}")
        self.clear_style1_btns()
        for name in names:
            self.add_style1_btn(name, slot_style1)
        if layout:
            self.place_style1(layout, start_row)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_style1_btns: return=None")

    def set_style2_btns(self, names: list, slot_style2=None, layout=None, start_row: int = 4) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_style2_btns: args={(names, slot_style2, layout, start_row)}")
        self.clear_style2_btns()
        for name in names:
            self.add_style2_btn(name, slot_style2)
        if layout:
            self.place_style2(layout, start_row)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_style2_btns: return=None")

    def set_all_btns(self, style1_names: list, style2_names: list, slot_style1=None, slot_style2=None, layout=None, start_row: int = 3) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_all_btns: args={(style1_names, style2_names, slot_style1, slot_style2, layout, start_row)}")
        self.set_style1_btns(style1_names, slot_style1, layout, start_row)
        self.set_style2_btns(style2_names, slot_style2, layout, start_row + 1)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_all_btns: return=None")

    def set_all_disabled_bw(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_all_disabled_bw: args=()")
        for btn in self._style1_btns + self._style2_btns:
            btn.set_disabled_bw()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_all_disabled_bw: return=None")

    def set_all_enabled_color(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_all_enabled_color: args=()")
        for btn in self._style1_btns + self._style2_btns:
            btn.set_enabled_color()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_all_enabled_color: return=None")

    def set_disabled_bw_style1(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_disabled_bw_style1: args=()")
        for btn in self._style1_btns:
            btn.set_disabled_bw()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_disabled_bw_style1: return=None")

    def set_disabled_bw_style2(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_disabled_bw_style2: args=()")
        for btn in self._style2_btns:
            btn.set_disabled_bw()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_disabled_bw_style2: return=None")

    def set_enabled_color_style1(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_enabled_color_style1: args=()")
        for btn in self._style1_btns:
            btn.set_enabled_color()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_enabled_color_style1: return=None")

    def set_enabled_color_style2(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering set_enabled_color_style2: args=()")
        for btn in self._style2_btns:
            btn.set_enabled_color()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting set_enabled_color_style2: return=None")

    def cleanup(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering cleanup: args=()")
        for btn in self._style1_btns + self._style2_btns:
            btn.cleanup()
        self._style1_btns.clear()
        self._style2_btns.clear()
        self._button_group.setParent(None)
        self._button_group.deleteLater()
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting cleanup: return=None")

    def raise_(self) -> None:
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Entering raise_: args=()")
        for btn in self._style1_btns + self._style2_btns:
            btn.raise_()
            btn.setVisible(True)
        if DEBUG_Btns:
            logger.info(f"[DEBUG][Btns] Exiting raise_: return=None")
