# constante.py

# =========================
# === Constantes TECHNIQUES ===
# =========================

# --- Palette de couleurs classiques et personnalisées ---
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
    # Couleurs personnalisées
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

try:
    from config_local import CAMERA_ID
except ImportError:
    CAMERA_ID = 0  # Valeur par défaut si pas de config locale

TEMP_IMAGE = "temp.jpg"

LABEL_WIDTH_RATIO = 0.8   # % largeur écran pour l'affichage principal
LABEL_HEIGHT_RATIO = 0.8  # % hauteur écran pour l'affichage principal
GRID_WIDTH = 7            # Largeur par défaut de toutes les grilles

# --- Styles disponibles ---
dico_styles = {
    "anime": "anime style illustration, vibrant colors, dynamic poses",
    "photo": "photograph, high quality",
    "comic": "comic style illustration, stylized, vibrant colors",
    "oil paint": "oil painting, classic art style, rich textures, brush strokes",
}

# =========================
# === Constantes ESTHÉTIQUES ===
# =========================

# --- Fenêtre principale ---
WINDOW_TITLE = "PhotoBooth"
WINDOW_BG_COLOR = COLORS["orange"]
WINDOW_STYLE = f"background-color: {WINDOW_BG_COLOR};"

# --- Police globale ---
APP_FONT_FAMILY = "Arial"   
APP_FONT_SIZE = 14

# --- Titre principal (label tout en haut) ---
TITLE_LABEL_TEXT = WINDOW_TITLE
TITLE_LABEL_FONT_SIZE = 32
TITLE_LABEL_FONT_FAMILY = "Arial"
TITLE_LABEL_BOLD = True
TITLE_LABEL_ITALIC = False
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
    # f"text-shadow: {TITLE_LABEL_BORDER_WIDTH}px {TITLE_LABEL_BORDER_WIDTH}px 0 {TITLE_LABEL_BORDER_COLOR};"  # <-- À supprimer ou commenter
    f"border-bottom: {TITLE_LABEL_BORDER_WIDTH}px {TITLE_LABEL_BORDER_STYLE} {TITLE_LABEL_BORDER_COLOR};"
)

# --- Cadre des affichages (label central) ---
DISPLAY_BORDER_COLOR = COLORS["black"]
DISPLAY_BORDER_RADIUS = 20  # px
DISPLAY_BACKGROUND_COLOR = COLORS["white"]
DISPLAY_TEXT_COLOR = COLORS["orange"]
DISPLAY_TEXT_SIZE = 18

DISPLAY_LABEL_STYLE = (
    f"background: {DISPLAY_BACKGROUND_COLOR};"
    f"border: 2px solid {DISPLAY_BORDER_COLOR};"
    f"border-radius: {DISPLAY_BORDER_RADIUS}px;"
    f"color: {DISPLAY_TEXT_COLOR};"
    f"font-size: {DISPLAY_TEXT_SIZE}px;"
)

# --- Boutons ---
BUTTON_BG_COLOR = COLORS["softyellow"]
BUTTON_BG_HOVER = COLORS["yellow"]
BUTTON_BG_PRESSED = COLORS["hardorangee"]
BUTTON_TEXT_COLOR = COLORS["white"]
BUTTON_TEXT_SIZE = 14

BUTTON_STYLE = (
    f"QPushButton {{"
    f"background-color: {BUTTON_BG_COLOR};"
    f"color: {BUTTON_TEXT_COLOR};"
    f"font-size: {BUTTON_TEXT_SIZE}px;"
    f"border-radius: 10px;"
    f"}}"
    f"QPushButton:hover {{"
    f"background-color: {BUTTON_BG_HOVER};"
    f"}}"
    f"QPushButton:pressed {{"
    f"background-color: {BUTTON_BG_PRESSED};"
    f"}}"
)

# --- Logos ---
LOGO_SIZE = 64  # Taille (largeur/hauteur) des logos en pixels

