# constante.py

dico_styles = {
    "anime": "anime style illustration, vibrant colors, dynamic poses",
    "photo": "photograph, high quality",
    "comic": "comic style illustration, stylized, vibrant colors",
    "oil paint": "oil painting, classic art style, rich textures, brush strokes",
}

# autres constantes (par ex. chemins fichiers temporaires)
TEMP_IMAGE = "temp.jpg"

LABEL_WIDTH_RATIO = 0.8   # 50% de la largeur de l'écran
LABEL_HEIGHT_RATIO = 0.8  # 50% de la hauteur de l'écran

GRID_WIDTH = 7  # Largeur par défaut de toutes les grilles

# Police globale
APP_FONT_FAMILY = "Arial"
APP_FONT_SIZE = 14

# Cadre des affichages (label central)
DISPLAY_BORDER_COLOR = "#888"
DISPLAY_BORDER_RADIUS = 20  # px
DISPLAY_BACKGROUND_COLOR = "#222"
DISPLAY_TEXT_COLOR = "#fff"
DISPLAY_TEXT_SIZE = 18

# Boutons
BUTTON_BG_COLOR = "#444"
BUTTON_BG_HOVER = "#666"
BUTTON_BG_PRESSED = "#222"
BUTTON_TEXT_COLOR = "#fff"
BUTTON_TEXT_SIZE = 14

# Fenêtre principale
WINDOW_BG_COLOR = "#111"

# Exemple de styleSheet pour QLabel d'affichage central
DISPLAY_LABEL_STYLE = (
    f"background: {DISPLAY_BACKGROUND_COLOR};"
    f"border: 2px solid {DISPLAY_BORDER_COLOR};"
    f"border-radius: {DISPLAY_BORDER_RADIUS}px;"
    f"color: {DISPLAY_TEXT_COLOR};"
    f"font-size: {DISPLAY_TEXT_SIZE}px;"
)

# Exemple de styleSheet pour QPushButton
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

# Exemple de styleSheet pour la fenêtre principale
WINDOW_STYLE = f"background: {WINDOW_BG_COLOR};"

