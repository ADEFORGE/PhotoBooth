# === ComfyUI API/Workflow constants ===
########################################
#   Constant Aesthetic
########################################
SHOW_LOGOS = False  # ML group and Tvibit logos display
GRID_WIDTH = 5

BTN_STYLE_ONE_ROW = 4
BTN_STYLE_TWO_ROW = 5

HUD_SIZE_RATIO = 0.08 

COLORS = {
    "white": "#FFFFFF",
    "black": "#000000",
    "red": "#FF0000",
    "green": "#00FF00",
    "blue": "#0000FF",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "gray": "#888888",
    "darkgray": "#222222",
    "lightgray": "#CCCCCC",
    "orange": "#FFA500",
    "primary": "#1abc9c",
    "secondary": "#2ecc71",
    "accent": "#e67e22",
    "danger": "#e74c3c",
    "info": "#3498db",
    "warning": "#f1c40f",
    "success": "#27ae60",
    "background": "#23272e", 
    "panel": "#363b48",
    "highlight": "#9b59b6",
    "softblue": "#5dade2",
    "softgreen": "#58d68d",
    "softred": "#ec7063",
    "softyellow": "#eecc46",
    "hardorangee" : "#f7811a",
}

LABEL_WIDTH_RATIO = 0.8   
LABEL_HEIGHT_RATIO = 0.9  

WINDOW_TITLE = "PhotoBooth"
WINDOW_BG_COLOR = "transparent"  # transparent instead of a color
WINDOW_STYLE = """
    QWidget {
        background-color: transparent;
    }
    QLabel {
        background: transparent;
    }
    QPushButton {
        background-color: %s;
    }
""" % (COLORS["darkgray"])

APP_FONT_FAMILY = "Arial"   
APP_FONT_SIZE = 14

TITLE_LABEL_TEXT = WINDOW_TITLE
TITLE_LABEL_FONT_SIZE = 40
TITLE_LABEL_FONT_FAMILY = "Arial"
TITLE_LABEL_BOLD = True
TITLE_LABEL_ITALIC = True
TITLE_LABEL_COLOR = COLORS["white"]
TITLE_LABEL_BORDER_COLOR = COLORS["black"]
TITLE_LABEL_BORDER_WIDTH = 5  # px
TITLE_LABEL_BORDER_STYLE = "dashed"  # solid, dashed, etc.

TITLE_LABEL_STYLE = (
    f"color: {TITLE_LABEL_COLOR};"
    f"font-size: {TITLE_LABEL_FONT_SIZE}px;"
    f"font-family: {TITLE_LABEL_FONT_FAMILY};"
    f"{'font-weight: bold;' if TITLE_LABEL_BOLD else ''}"
    f"{'font-style: italic;' if TITLE_LABEL_ITALIC else ''}"
    f"text-align: center;"
    # f"text-shadow: {TITLE_LABEL_BORDER_WIDTH}px {TITLE_LABEL_BORDER_WIDTH}px 0 {TITLE_LABEL_BORDER_COLOR};" 
    f"border-bottom: {TITLE_LABEL_BORDER_WIDTH}px {TITLE_LABEL_BORDER_STYLE} {TITLE_LABEL_BORDER_COLOR};"
)

DISPLAY_BORDER_COLOR = COLORS["black"]
DISPLAY_BORDER_WIDTH = 4  # px  # Ajout de cette ligne
DISPLAY_BORDER_RADIUS = 20  # px
DISPLAY_BACKGROUND_COLOR = COLORS["white"]
DISPLAY_TEXT_COLOR = COLORS["orange"]
DISPLAY_TEXT_SIZE = 18

DISPLAY_LABEL_STYLE = (
    f"background: {DISPLAY_BACKGROUND_COLOR};"
    f"border: {DISPLAY_BORDER_WIDTH}px solid {DISPLAY_BORDER_COLOR};"  # Modification ici
    f"border-radius: {DISPLAY_BORDER_RADIUS}px;"
    f"color: {DISPLAY_TEXT_COLOR};"
    f"font-size: {DISPLAY_TEXT_SIZE}px;"
)

BUTTON_BG_COLOR = COLORS["softyellow"]
BUTTON_BG_HOVER = COLORS["yellow"]
BUTTON_BG_PRESSED = COLORS["hardorangee"]
BUTTON_TEXT_COLOR = COLORS["white"]
BUTTON_TEXT_SIZE = 16
BUTTON_BORDER_COLOR = COLORS["black"] 
BUTTON_BORDER_WIDTH = 2 
BUTTON_BORDER_RADIUS = 10 

BUTTON_STYLE = (
    f"QPushButton {{"
    f"background-color: {BUTTON_BG_COLOR};"
    f"color: {BUTTON_TEXT_COLOR};"
    f"font-size: {BUTTON_TEXT_SIZE}px;"
    f"border: {BUTTON_BORDER_WIDTH}px solid {BUTTON_BORDER_COLOR};"
    f"border-radius: {BUTTON_BORDER_RADIUS}px;"
    f"font-weight: bold;"
    f"}}"
    f"QPushButton:hover {{"
    f"background-color: {BUTTON_BG_HOVER};"
    f"}}"
    f"QPushButton:pressed {{"
    f"background-color: {BUTTON_BG_PRESSED};"
    f"}}"
    f"QPushButton:checked {{"
    f"background-color: {COLORS['hardorangee']};"
    f"border: {BUTTON_BORDER_WIDTH}px solid {COLORS['black']};"
    f"}}"
)

SPECIAL_BUTTON_NAMES = [
    "Apply Style",
    "Save",
    "Print",
    "Back to Camera"
]

SPECIAL_BUTTON_STYLE = (
    f"QPushButton {{"
    f"background-color: {COLORS['red']};" 
    f"color: {COLORS['white']};"
    f"font-size: {BUTTON_TEXT_SIZE}px;"
    f"border: {BUTTON_BORDER_WIDTH}px solid {COLORS['black']};"
    f"border-radius: {BUTTON_BORDER_RADIUS}px;"
    f"font-weight: bold;"
    f"}}"
    f"QPushButton:hover {{"
    f"background-color: {COLORS['gray']};"  
    f"}}"
    f"QPushButton:pressed {{"
    f"background-color: {COLORS['black']};"  
    f"}}"
    f"QPushButton:checked {{"
    f"background-color: {COLORS['primary']};"
    f"border: {BUTTON_BORDER_WIDTH}px solid {COLORS['white']};"
    f"}}"
)

LOGO_SIZE = 64  

GRID_MARGIN_TOP = 20
GRID_MARGIN_BOTTOM = 40
GRID_MARGIN_LEFT = 20
GRID_MARGIN_RIGHT = 20
GRID_VERTICAL_SPACING = 20
GRID_HORIZONTAL_SPACING = 10

GRID_LAYOUT_MARGINS = (10, 10, 10, 10)  
GRID_LAYOUT_SPACING = 5

GRID_ROW_STRETCHES = {
    "title": 1,     # Row 0
    "display": 10,  # Row 1
    "buttons": 2    # Row 2
}

DISPLAY_SIZE_RATIO = (0.7, 0.6)  

INFO_BUTTON_SIZE = 32  # px
INFO_BUTTON_STYLE = (
    f"QPushButton {{"
    f"background-color: transparent;"
    f"border: none;"
    f"width: {INFO_BUTTON_SIZE}px;"
    f"height: {INFO_BUTTON_SIZE}px;"
    f"}}"
    f"QPushButton:hover {{"
    f"background-color: rgba(255, 255, 255, 0.1);"
    f"}}"
    f"QPushButton:pressed {{"
    f"background-color: rgba(0, 0, 0, 0.1);"
    f"}}"
)

DIALOG_BOX_STYLE = (
    "QDialog {"
    "background-color: rgba(24, 24, 24, 0.82);" 
    "border-radius: 18px;"
    "}"
    "QLabel {"
    "background: transparent;"
    "color: white;"
    "font-size: 18px;"
    "}"
    "QTextEdit {"
    "background: transparent;"
    "color: white;"
    "font-size: 16px;"
    "border: none;"
    "}"
    "QPushButton {"
    "background-color: #444;"
    "color: white;"
    "font-size: 16px;"
    "border-radius: 10px;"
    "padding: 8px 24px;"
    "margin-top: 12px;"
    "}"
    "QPushButton:hover {"
    "background-color: #666;"
    "}"
    "QPushButton:pressed {"
    "background-color: #222;"
    "}"
)

TOOLTIP_STYLE = """
QToolTip {
    background-color: #2a2a2a;
    color: white;
    border: 1px solid white;
    border-radius: 4px;
    padding: 4px;
    font-size: 12px;
}
"""

COUNTDOWN_FONT_STYLE = "font-size: 120px; font-weight: bold; color: #fff; font-family: Arial, sans-serif; background: transparent;"

COLOR_LOADING_BAR = "rgba(0, 0, 0, 255)"

OVERLAY_TITLE_STYLE = ("color: black; font-size: 40px; font-weight: bold; background: transparent;")
OVERLAY_MSG_STYLE = ("color: black; font-size: 30px; background: transparent;")

OVERLAY_LOADING_TITLE_STYLE = (TITLE_LABEL_STYLE + "color: rgba(0, 0, 0, 255); border-bottom: none; text-decoration: none; background: transparent;")
OVERLAY_LOADING_MSG_STYLE = (
    "color: rgba(0, 0, 0, 255); "
    "font-size: 24px; "
    "background: transparent; "
    "line-height: 2.2;"
)

MAIN_WINDOW_MSG_STYLE = (   """
            background: rgba(80, 80, 80, 0.6);
            color: rgba(255, 255, 255, 1.0);
            font-size: 35px;
            border-radius: 18px;
            padding: 12px 24px;
        """)


BTN_SIZE = 2 
BTN_STYLE_TWO_SIZE_COEFFICIENT = 1.6
BTN_STYLE_TWO_FONT_SIZE_PERCENT = 12 
BTN_STYLE_TWO_FONT_OUTLINE = 0.15
BTN_STYLE_TWO = (
    "QPushButton {{"
    "background: transparent;"
    "border: none;"
    "background-image: url({texture});"
    "background-position: center;"
    "background-repeat: no-repeat;"
    "color: white;"
    "font-weight: 900;"
    "font-size: 2.2em;"
    "border-radius: 24px;"
    "}}"
    "QPushButton:pressed {{"
    "background-color: rgba(180,180,180,0.5);"
    "border: 10px solid white;"
    "border-radius: 24px;"
    "}}"
    "QPushButton:checked {{"
    "background: transparent;"
    "border: 4px solid white;"
    "border-radius: 24px;"
    "}}"
)

DIALOG_ACTION_BUTTON_STYLE = (
    "QPushButton {"
    "background-color: rgba(180,180,180,0.35);"
    "border: 2px solid #bbb;"
    "border-radius: 24px;"
    "min-width: 48px; min-height: 48px;"
    "max-width: 48px; max-height: 48px;"
    "font-size: 18px;"
    "color: white;"
    "font-weight: bold;"
    "}"
    "QPushButton:hover {"
    "border: 2.5px solid white;"
    "background-color: rgba(200,200,200,0.45);"
    "}"
    "QPushButton:pressed {"
    "background-color: rgba(220,220,220,0.55);"
    "border: 3px solid #eee;"
    "}"
)

ICON_BUTTON_STYLE = (
    "QPushButton {"
    "background-color: rgba(180,180,180,0.35);"
    "border: 2px solid #bbb;"
    "border-radius: 24px;"
    "min-width: 48px; min-height: 48px;"
    "max-width: 48px; max-height: 48px;"
    "}"
    "QPushButton:hover {"
    "border: 2.5px solid white;"
    "}"
    "QPushButton:pressed {"
    "background-color: rgba(220,220,220,0.55);"
    "border: 3px solid #eee;"
    "}"
)

def get_style_button_style(style_name):
    import os
    texture_path = f"gui_template/styles_textures/{style_name}.png"
    checked = (
        "QPushButton:checked {"
        "background-color: #f7811a;"
        "border: 3px solid #fff;"
        "color: #fff;"
        "}"
    )
    if os.path.exists(texture_path):
        return (
            "QPushButton {"
            "border: 2px solid black;"
            "border-radius: 16px;"
            f"background-image: url('{texture_path}');"
            "background-repeat: no-repeat;"
            "background-position: center;"
            # "background-size: cover;" 
            "background-color: black;"
            "color: white;"
            "font-size: 18px;"
            "font-weight: bold;"
            "min-width: 80px; min-height: 80px;"
            "max-width: 120px; max-height: 120px;"
            "}"
            "QPushButton:hover {"
            "border: 2px solid gray;"
            "}"
            "QPushButton:pressed {"
            "border: 4px solid white;"
            "}"
            + checked
        )
    else:
        return (
            "QPushButton {"
            "border: 2px solid black;"
            "border-radius: 16px;"
            "background-color: black;"
            "color: white;"
            "font-size: 18px;"
            "font-weight: bold;"
            "min-width: 80px; min-height: 80px;"
            "max-width: 120px; max-height: 120px;"
            "}"
            "QPushButton:hover {"
            "border: 2px solid gray;"
            "}"
            "QPushButton:pressed {"
            "border: 4px solid white;"
            "}"
            + checked
        )

FIRST_BUTTON_STYLE = (
    "QPushButton {"
    "background-color: rgba(180,180,180,0.5);"
    "border: 2px solid #888;"
    "border-radius: 24px;"
    "min-width: 48px; min-height: 48px;"
    "max-width: 48px; max-height: 48px;"
    "font-size: 30px;"
    "color: white;"
    "font-weight: bold;"
    "}"
    "QPushButton:hover {"
    "border: 2.5px solid white;"
    "}"
    "QPushButton:pressed {"
    "border: 3px solid black;"
    "}"
)

GENERIC_BUTTON_STYLE = FIRST_BUTTON_STYLE 
############################################
# Technical Constant
############################################


EASY_KID_ACCESS = True

SLEEP_TIMER_SECONDS = 20 
SLEEP_TIMER_SECONDS_QRCODE_OVERLAY = 90

TOOLTIP_DURATION_MS = 3000 

DEBUG = False
DEBUG_FULL = False

WS_URL = "ws://127.0.0.1:8188/ws"
HTTP_BASE_URL = "http://127.0.0.1:8188"
HOTSPOT_URL = "https://192.168.10.2:5000/share"

import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
COMFY_OUTPUT_FOLDER = os.path.abspath(
    os.path.join(BASE_DIR, "../ComfyUI/output")
)
INPUT_IMAGE_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "../ComfyUI/input/input.png")
)
COMFY_WORKFLOW_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "workflows")
)

ShareByHotspot = False  

#try:
#    from config_local import CAMERA_ID # type: ignore
#except ImportError:
CAMERA_ID = 0
CAMERA_ROTATE_ANGLE = 270    # Default camera rotation angle (0, 90, 180, 270)

TEMP_IMAGE = "temp.jpg"

VALIDATION_OVERLAY_MESSAGE = "" 


COUNTDOWN_START = 2  
