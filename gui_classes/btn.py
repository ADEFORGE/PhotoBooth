from PySide6.QtWidgets import QPushButton, QButtonGroup, QWidget
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize, Qt
import os

from constante import BTN_STYLE_ONE, BTN_STYLE_TWO

class Btn(QPushButton):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self._connected_slots = []
        self.setObjectName(name)

    def initialize(self, style=None, icon_path=None, size=None, checkable=False):
        if style:
            self.setStyleSheet(style)
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.setIcon(icon)
            if size:
                self.setIconSize(size)
        if size:
            self.setMinimumSize(size)
            self.setMaximumSize(size)
        self.setCheckable(checkable)

    def place(self, layout, row, col, alignment=Qt.AlignCenter):
        layout.addWidget(self, row, col, alignment=alignment)
        self.setVisible(True)
        self.raise_()

    def connect_slot(self, slot, signal="clicked"):
        if hasattr(self, signal):
            getattr(self, signal).connect(slot)
            self._connected_slots.append((signal, slot))

    def connect_by_name(self, obj, method_name, signal="clicked"):
        if hasattr(obj, method_name):
            slot = getattr(obj, method_name)
            self.connect_slot(slot, signal)

    def cleanup(self):
        for signal, slot in self._connected_slots:
            try:
                getattr(self, signal).disconnect(slot)
            except Exception:
                pass
        self._connected_slots.clear()
        if self.parent():
            self.setParent(None)
        self.deleteLater()

class BtnStyleOne(Btn):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        icon_path = f"gui_template/btn_icons/{name}.png"
        size = QSize(80, 80)
        self.initialize(
            style=BTN_STYLE_ONE,
            icon_path=icon_path,
            size=size,
            checkable=False
        )
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(True)
        self.raise_()

class BtnStyleTwo(Btn):
    def __init__(self, name, parent=None):
        super().__init__(name, parent)
        texture_path = f"gui_template/btn_textures copy/{name}.png"
        style = BTN_STYLE_TWO.format(texture=texture_path)
        self.setText(name)
        self.adjustSize()
        width = max(self.sizeHint().width() + 32, 120)
        size = QSize(width, 56)
        self.initialize(
            style=style,
            icon_path=None,
            size=size,
            checkable=True
        )
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setVisible(True)
        self.raise_()

class Btns:
    def __init__(self, parent: QWidget, style1_names, style2_names, slot_style1=None, slot_style2=None):
        self.parent = parent
        overlay = getattr(parent, "overlay_widget", parent)
        self.style1_btns = []
        self.style2_btns = []
        self.button_group = QButtonGroup(overlay)
        self.button_group.setExclusive(True)
        for name in style1_names:
            btn = BtnStyleOne(name, parent=overlay)
            # Correction : pour slot_style1 (accept/close), connecte le slot SANS argument
            if slot_style1 and isinstance(slot_style1, str):
                btn.connect_by_name(parent, slot_style1)
            elif callable(slot_style1):
                btn.clicked.connect(slot_style1)
            self.style1_btns.append(btn)
        for name in style2_names:
            btn = BtnStyleTwo(name, parent=overlay)
            if slot_style2 and isinstance(slot_style2, str):
                btn.connect_by_name(parent, slot_style2)
            elif callable(slot_style2):
                btn.clicked.connect(lambda checked, b=btn: slot_style2(checked, b))
            self.button_group.addButton(btn)
            self.style2_btns.append(btn)

    def place(self, layout, start_row=3):
        col_max = layout.columnCount() if hasattr(layout, "columnCount") else 7
        n1 = len(self.style1_btns)
        if n1 > 0:
            # Si pair, on saute la colonne centrale
            if n1 % 2 == 0:
                mid = col_max // 2
                left = (col_max - n1 - 1) // 2
                for i, btn in enumerate(self.style1_btns):
                    col = left + i if i < n1 // 2 else left + i + 1
                    btn.place(layout, start_row, col)
            else:
                col1 = (col_max - n1) // 2
                for i, btn in enumerate(self.style1_btns):
                    btn.place(layout, start_row, col1 + i)
        n2 = len(self.style2_btns)
        if n2 > 0:
            # Si pair, on saute la colonne centrale
            if n2 % 2 == 0:
                mid = col_max // 2
                left = (col_max - n2 - 1) // 2
                for i, btn in enumerate(self.style2_btns):
                    col = left + i if i < n2 // 2 else left + i + 1
                    btn.place(layout, start_row + 1, col)
            else:
                col2 = (col_max - n2) // 2
                for i, btn in enumerate(self.style2_btns):
                    btn.place(layout, start_row + 1, col2 + i)

    def cleanup(self):
        for btn in self.style1_btns + self.style2_btns:
            btn.cleanup()
        self.style1_btns.clear()
        self.style2_btns.clear()
        self.button_group.setParent(None)
        self.button_group.deleteLater()

    def raise_(self):
        for btn in self.style1_btns + self.style2_btns:
            btn.raise_()
            btn.setVisible(True)
