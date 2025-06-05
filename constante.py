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
LABEL_HEIGHT_RATIO = 0.9  # % hauteur écran pour l'affichage principal
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
WINDOW_BG_COLOR = "transparent"  # transparent au lieu d'une couleur
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

# --- Police globale ---
APP_FONT_FAMILY = "Arial"   
APP_FONT_SIZE = 14

# --- Titre principal (label tout en haut) ---
TITLE_LABEL_TEXT = WINDOW_TITLE
TITLE_LABEL_FONT_SIZE = 32
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
    # f"text-shadow: {TITLE_LABEL_BORDER_WIDTH}px {TITLE_LABEL_BORDER_WIDTH}px 0 {TITLE_LABEL_BORDER_COLOR};"  # <-- À supprimer ou commenter
    f"border-bottom: {TITLE_LABEL_BORDER_WIDTH}px {TITLE_LABEL_BORDER_STYLE} {TITLE_LABEL_BORDER_COLOR};"
)

# --- Cadre des affichages (label central) ---
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

# --- Boutons ---
BUTTON_BG_COLOR = COLORS["softyellow"]
BUTTON_BG_HOVER = COLORS["yellow"]
BUTTON_BG_PRESSED = COLORS["hardorangee"]
BUTTON_TEXT_COLOR = COLORS["white"]
BUTTON_TEXT_SIZE = 16
BUTTON_BORDER_COLOR = COLORS["black"]  # Ajout
BUTTON_BORDER_WIDTH = 2  # px            # Ajout
BUTTON_BORDER_RADIUS = 10  # px         # Déplacé ici pour plus de clarté

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

# --- Boutons spéciaux ---
SPECIAL_BUTTON_NAMES = [
    "Apply Style",
    "Save",
    "Print",
    "Back to Camera"
]

# Style pour les boutons spéciaux (plus foncé)
SPECIAL_BUTTON_STYLE = (
    f"QPushButton {{"
    f"background-color: {COLORS['red']};"  # Fond plus foncé
    f"color: {COLORS['white']};"
    f"font-size: {BUTTON_TEXT_SIZE}px;"
    f"border: {BUTTON_BORDER_WIDTH}px solid {COLORS['black']};"
    f"border-radius: {BUTTON_BORDER_RADIUS}px;"
    f"font-weight: bold;"
    f"}}"
    f"QPushButton:hover {{"
    f"background-color: {COLORS['gray']};"  # Hover plus foncé
    f"}}"
    f"QPushButton:pressed {{"
    f"background-color: {COLORS['black']};"  # Pressed encore plus foncé
    f"}}"
    f"QPushButton:checked {{"
    f"background-color: {COLORS['primary']};"
    f"border: {BUTTON_BORDER_WIDTH}px solid {COLORS['white']};"
    f"}}"
)

# --- Logos ---
LOGO_SIZE = 64  # Taille (largeur/hauteur) des logos en pixels

# --- Layout Spacing & Margins ---
GRID_MARGIN_TOP = 20     # px
GRID_MARGIN_BOTTOM = 40  # px  # Réduit de 400 à 40
GRID_MARGIN_LEFT = 20    # px
GRID_MARGIN_RIGHT = 20   # px
GRID_VERTICAL_SPACING = 20   # px entre les lignes  # Augmenté de 10 à 20
GRID_HORIZONTAL_SPACING = 10 # px entre les colonnes

# --- Grid Layout Configuration ---
GRID_LAYOUT_MARGINS = (10, 10, 10, 10)  # left, top, right, bottom
GRID_LAYOUT_SPACING = 5

# --- Grid Row Configuration ---
GRID_ROW_STRETCHES = {
    "title": 1,     # Row 0
    "display": 10,  # Row 1
    "buttons": 2    # Row 2
}

# --- Display Configuration ---
DISPLAY_SIZE_RATIO = (0.7, 0.6)  # width%, height% of screen

# --- Info Button ---
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

# --- Dialog Box Style (InfoDialog & RulesDialog) ---
DIALOG_BOX_STYLE = (
    "QDialog {"
    "background-color: rgba(24, 24, 24, 0.82);"  # gris très foncé, bien transparent
    "border-radius: 18px;"
    # "backdrop-filter: blur(6px);"  # <-- SUPPRIMÉ car non supporté par Qt
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

# --- Style pour les boutons d'action dans les boîtes de dialogue (InfoDialog & RulesDialog) ---
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

# --- Icon Button Style (pour info/rules boutons ronds transparents) ---
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

# --- Style pour les boutons de style (TOGGLE, AVEC OU SANS TEXTURE) ---
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
            # "background-size: cover;"  # <-- Supprimé car non supporté par Qt
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

# --- Style pour les boutons "first_buttons" (icônes ronds) ---
FIRST_BUTTON_STYLE = (
    "QPushButton {"
    "background-color: rgba(180,180,180,0.5);"
    "border: 2px solid #888;"
    "border-radius: 24px;"
    "min-width: 48px; min-height: 48px;"
    "max-width: 48px; max-height: 48px;"
    "font-size: 22px;"
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

# --- Style pour les boutons génériques (autres que styles et first_buttons) ---
GENERIC_BUTTON_STYLE = FIRST_BUTTON_STYLE  # ou personnalise si besoin

# --- Message affiché en haut de l'overlay de validation ---
VALIDATION_OVERLAY_MESSAGE = "Merci de lire et accepter les règles avant de continuer."  # Personnalisez ici

# --- Styles personnalisables pour les boutons ---
BTN_STYLE_ONE = (
    "QPushButton {"
    "background-color: rgba(255, 128, 0, 0.95);"  # Orange plus visible
    "border: 4px solid white;"                    # Bordure plus épaisse
    "border-radius: 40px;"                        # Plus arrondi
    "min-width: 80px; min-height: 80px;"         # Taille plus grande
    "max-width: 80px; max-height: 80px;"
    "font-size: 24px;"
    "color: white;"
    "font-weight: bold;"
    "}"
    "QPushButton:hover {"
    "background-color: rgba(255, 160, 0, 1.0);"
    "border: 5px solid white;"
    "}"
    "QPushButton:pressed {"
    "background-color: rgba(255, 200, 0, 1.0);"
    "border: 6px solid white;"
    "}"
)

BTN_STYLE_TWO = (
    "QPushButton {{"
    "border: 2px solid black;"
    "border-radius: 8px;"
    "background-image: url('{texture}');"
    "background-repeat: no-repeat;"
    "background-position: center;"
    "background-color: black;"
    "color: white;"
    "font-size: 18px;"
    "font-weight: bold;"
    "}}"
    "QPushButton:checked {{"
    "background-color: #f7811a;"
    "border: 3px solid #fff;"
    "color: #fff;"
    "}}"
    "QPushButton:hover {{"
    "border: 2px solid gray;"
    "}}"
    "QPushButton:pressed {{"
    "border: 4px solid white;"
    "}}"
)

