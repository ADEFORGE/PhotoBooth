# === ComfyUI API/Workflow constants ===
WS_URL = "ws://127.0.0.1:8188/ws"
HTTP_BASE_URL = "http://127.0.0.1:8188"

# Paths
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
COMFY_OUTPUT_FOLDER = os.path.abspath(
    os.path.join(BASE_DIR, "../../../ComfyUI/output")
)
INPUT_IMAGE_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "../../../ComfyUI/input/input.png")
)
COMFY_WORKFLOW_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "../../workflows")
)

ShareByHotspot = False  # Mettre à False pour désactiver le workflow Hotspot/QR
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
    from config_local import CAMERA_ID # type: ignore
except ImportError:
    CAMERA_ID = 0  # Valeur par défaut si pas de config locale

TEMP_IMAGE = "temp.jpg"

LABEL_WIDTH_RATIO = 0.8   # % largeur écran pour l'affichage principal
LABEL_HEIGHT_RATIO = 0.9  # % hauteur écran pour l'affichage principal
GRID_WIDTH = 7            # Largeur par défaut de toutes les grilles

# --- Styles disponibles ---
dico_styles = {
    "clay":  "Transform this person into a claymation character. Give them a handcrafted look with soft, rounded features, visible fingerprints or texture in the clay, and slightly exaggerated expressions. Use stop-motion lighting and a warm, tactile feel. Background should look like a miniature set made of clay or craft materials.",
    "comic": "Turn this person into a bold comic book style character. Use clean black ink outlines, vibrant cel-shading, and dramatic contrast. Emphasize comic-style features like expressive eyes, stylized hair, and sharp facial structure. Keep the background minimal or graphic, like in classic comic panels",
    "oil paint": "Render the subject as a classical Renaissance oil painting. Preserve their exact identity, age, and gender, and depict them with high-contrast lighting emerging from a deep, shadowed background. Use smooth, yet expressive brushwork with rich pigment layering, especially in illuminated areas. The composition should be formal, dignified, and naturalistic, with refined anatomy and soft, golden light reminiscent of masters like Rembrandt, Caravaggio, or Leonardo da Vinci. Surround the figure with minimal, period-authentic detail or drapery, avoiding modern or fantastical elements. Textures should reflect aged canvas and layered oil paint, with subtle impasto highlights. Skin tones should be warm and realistic, set against velvety dark shadows. (renaissance painting: 1.1), (clair-obscur: 1.1), (oil painting: 1.1), (visible brushstrokes: 1.5), (pigment texture: 1.1), (impasto highlights: 1.5), (deep shadows: 1.1), (dramatic lighting: 1.1), (canvas texture: 1.1), (moody atmosphere: 1.1), (rich pigments: 1.5), (golden tones: 1.1)",
    "statue" : "Make it into a marble statue while preserving their original identity, age, and gender exactly. Sculpt them in smooth, white marble with realistic but modest features. Avoid any exaggeration or changes to body shape or facial structure. The statue should resemble classical art with respectful, child-appropriate detail. Use soft lighting and natural stone texture, with no added accessories or fantasy elements. Make sure the whole statue is white without colors. Make the eyes white, no black details. Lapis blue stones mosaics, gold metal engravings, green jade stones, obsidian glass tiles. (White eyes: 1.1), (White hair: 1.1), (clothes: 1.1), (white marble statue: 1.1)",
    #"stone" : "Transform this person into a stone statue, maintaining their original identity, age, and gender exactly. Sculpt them in rough, gray stone with realistic but modest features. Avoid any exaggeration or changes to body shape or facial structure. The statue should resemble classical art with respectful, child-appropriate detail. Use soft lighting and natural stone texture, with no added accessories or fantasy elements.",
    #"cyberpunk": "Transform this person into a futuristic cyberpunk character. Use neon colors, high-tech accessories, and a gritty urban aesthetic. Emphasize glowing elements like circuit patterns, holographic displays, and cybernetic enhancements. The background should be a dark, neon-lit cityscape with rain or fog for atmosphere.",
    #"retro": "Turn this person into a retro character from the 80s or 90s. Use bright, bold colors, geometric patterns, and nostalgic accessories like cassette tapes or vintage electronics. Emphasize a playful, vibrant style with exaggerated features. The background should reflect the era with neon lights, old-school technology, and a fun, upbeat atmosphere.",
    "steampunk": "Turn this person into a steampunk character with Victorian-era fashion and mechanical elements. Use brass, copper, and leather textures, with goggles, gears, and clockwork details. Emphasize a retro-futuristic look with intricate machinery and steam-powered accessories. The background should be an industrial setting with pipes, cogs, and vintage machinery.",
    #"fantasy": "Transform this person into a fantasy character with magical elements. Use vibrant colors, ethereal lighting, and whimsical accessories. Emphasize fantasy features like pointed ears, flowing hair, and mystical attire. The background should be a magical landscape with enchanted forests, castles, or mythical creatures.",
    #"history": "Transform this person into a historical figure from a specific era. Use period-appropriate clothing, hairstyles, and accessories. Emphasize the cultural and historical context of the time, whether it's ancient Rome, medieval Europe, or the Renaissance. The background should reflect the architecture and environment of that era, with attention to detail in the setting.",
    "minecraft": "Transform this person into a stylized Minecraft character, ensuring their original facial features, hairstyle, body type, and gender expression are clearly recognizable within the cubic, pixelated aesthetic of the Minecraft universe. Use blocky geometry to recreate the person's appearance, translating realistic details into simplified forms while retaining defining characteristics such as skin tone, hair color, hairstyle, facial structure, and clothing style. The Minecraft character should look as if it truly represents the individual, as though they were authentically rendered inside the game. Clothing should reflect the person’s usual outfit or fashion sense, reimagined with the classic 8-bit textures and limited color palettes typical of Minecraft skins. Accessories or unique style elements—such as glasses, jewelry, or hats—should be adapted in a pixel-friendly manner while still clearly referencing the real-world look. Maintain proportional accuracy according to Minecraft’s character format (e.g., square head, rectangular limbs), but ensure the transformed version still feels personal and identifiable. Place the character in a richly detailed Minecraft environment that complements their style or personality—this could be a lush forest biome, a cozy village, a castle setting, or any classic overworld scene. The background should include iconic blocky elements such as pixelated grass, trees, clouds, and structures made of wood, stone, or brick. Lighting should be bright and vivid, reflecting the cheerful tone of Minecraft’s visual style.",
    #"horror": "Transform this person into a horror character. Use dark colors, eerie lighting, and unsettling details. Emphasize horror elements like ghostly features, creepy accessories, and a menacing atmosphere. The background should be a dark, foreboding setting with elements like fog, shadows, and haunted structures.",
    #"cartoon": "Transform this person into a cartoon character. Use bright, bold colors, exaggerated features, and playful expressions. Emphasize cartoon-style elements like large eyes, simplified shapes, and whimsical accessories. The background should be colorful and fun, like a scene from a children's animated show.",
    "pixel art": "Transform this person into a pixel art character. Use a limited color palette, blocky shapes, and pixelated details. Emphasize the retro video game aesthetic with large, square pixels and simplified features. The background should be a pixelated landscape, like a classic 8-bit game scene.",
    #"watercolor": "Transform this person into a watercolor painting. Use soft, blended colors, and delicate brush strokes to create a dreamy, ethereal effect. Emphasize fluid shapes and a gentle color palette. The background should be a soft wash of color, like a blurred landscape or abstract design.",
    #"charcoal": "Transform this person into a charcoal drawing. Use bold, dark lines and soft shading to create a dramatic, textured effect. Emphasize the contrast between light and shadow, with a focus on the person's facial features and expressions. The background should be a simple, muted tone to highlight the charcoal texture.",
    #"sketch": "Transform this person into a pencil sketch. Use fine lines, shading, and cross-hatching to create a detailed, realistic effect. Emphasize the person's features with careful attention to detail, while keeping the overall look light and airy. The background should be a simple, untextured paper-like surface to enhance the sketch effect.",
    #"anime": "Transform this person into an anime character. Use vibrant colors, exaggerated facial features, and stylized hair. Emphasize large, expressive eyes, and a dynamic pose. The background should be a colorful, fantastical setting typical of anime, with elements like cherry blossoms, futuristic cityscapes, or magical landscapes.",
    #"ww2": "Make this person into a third reich general, ensuring their original identity, age, and gender are preserved. Use period-appropriate military attire, insignia, and a stern expression. The background should reflect a historical setting, with elements like military vehicles, flags, or a war-torn landscape.",
    "vintage": "Transform this person into a vintage character from the 1920s-1950s. Use sepia tones, classic hairstyles, and period-appropriate clothing. Emphasize a nostalgic, timeless look with soft lighting and a vintage aesthetic. The background should reflect the era with elements like old cars, vintage posters, or classic architecture.",
    #"roblox": "Transform this person into a Roblox character, ensuring their original facial features, hairstyle, body type, and gender expression are clearly recognizable within the blocky, pixelated aesthetic of the Roblox universe. Use simple shapes and bright colors to recreate the person's appearance, translating realistic details into a more cartoonish style while retaining defining characteristics such as skin tone, hair color, hairstyle, facial structure, and clothing style. The Roblox character should look as if it truly represents the individual, as though they were authentically rendered inside the game. Clothing should reflect the person’s usual outfit or fashion sense, reimagined with the classic Roblox textures and limited color palettes typical of Roblox avatars. Accessories or unique style elements—such as glasses, jewelry, or hats—should be adapted in a blocky manner while still clearly referencing the real-world look. Maintain proportional accuracy according to Roblox’s character format (e.g., blocky limbs, oversized head), but ensure the transformed version still feels personal and identifiable. Place the character in a richly detailed Roblox environment that complements their style or personality—this could be a vibrant cityscape, a cozy home, or any classic Roblox setting. The background should include iconic blocky elements such as pixelated grass, trees, clouds, and structures made of wood, stone, or brick. Lighting should be bright and vivid, reflecting the cheerful tone of Roblox’s visual style.",
    "disney": "Transform this person into a Disney-style character, ensuring their original facial features, hairstyle, body type, and gender expression are clearly recognizable within the whimsical, animated aesthetic of Disney films. Use soft lines and vibrant colors to recreate the person's appearance, translating realistic details into a more cartoonish style while retaining defining characteristics such as skin tone, hair color, hairstyle, facial structure, and clothing style. The Disney character should look as if it truly represents the individual, as though they were authentically rendered inside a Disney movie. Clothing should reflect the person’s usual outfit or fashion sense, reimagined with the classic Disney textures and limited color palettes typical of Disney characters. Accessories or unique style elements—such as glasses, jewelry, or hats—should be adapted in a playful manner while still clearly referencing the real-world look. Maintain proportional accuracy according to Disney’s character format (e.g., exaggerated features, large eyes), but ensure the transformed version still feels personal and identifiable. Place the character in a richly detailed Disney environment that complements their style or personality—this could be a magical kingdom, a bustling city, or any classic Disney setting. The background should include iconic elements such as lush landscapes, whimsical architecture, and enchanting details. Lighting should be bright and cheerful, reflecting the optimistic tone of Disney’s visual style."
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

# --- Style pour les boutons génériques (autres que styles et first_buttons) ---
GENERIC_BUTTON_STYLE = FIRST_BUTTON_STYLE  # ou personnalise si besoin

# --- Message affiché en haut de l'overlay de validation ---
VALIDATION_OVERLAY_MESSAGE = "Merci de lire et accepter les règles avant de continuer."  # Personnalisez ici

# --- Styles personnalisables pour les boutons ---
# BTN_STYLE_ONE supprimé, n'est plus utilisé
BTN_STYLE_TWO_FONT_SIZE_PERCENT = 14  # Pourcentage de la taille du bouton (ex: 28 pour 28%)
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

# --- Tooltip duration for take photo button (in milliseconds) ---
TOOLTIP_DURATION_MS = 3000  # Default: 3 seconds

# --- Tooltip Style (infobulle) ---
TOOLTIP_STYLE = (
    "QToolTip {"
    "background-color: rgba(255,255,255,0.65);"  # Blanc plus transparent
    "color: #111;"  # Texte noir
    "border: 2.5px solid #fff;"  # Bordure blanche opaque
    "border-radius: 12px;"  # Coins arrondis plus petits
    "font-size: 18px;"  # Taille réduite
    "padding: 6px 12px;"  # Padding réduit
    "font-family: Arial, sans-serif;"
    "font-weight: bold;"
    "}"
)

# --- Countdown Overlay ---
COUNTDOWN_START = 2  # Valeur de départ du compteur (modifiable)
COUNTDOWN_FONT_STYLE = "font-size: 120px; font-weight: bold; color: #fff; font-family: Arial, sans-serif; background: transparent;"

# DEBUG constant for controlling debug prints
DEBUG = True
DEBUG_FULL = False

# Tooltip configuration
TOOLTIP_DURATION_MS = 3000  # Duration in milliseconds
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

# --- Timer for auto-sleep/restore to welcome screen ---
SLEEP_TIMER_SECONDS = 20  # Default inactivity timeout in seconds (can be changed)

# --- Taille des boutons et logos (en % de la hauteur de l'écran) ---
HUD_SIZE_RATIO = 0.08  # 8% de la hauteur de l'écran par défaut

# --- Affichage des logos dans le HUD ---
SHOW_LOGOS = True  # Mettre à False pour masquer les logos dans le HUD

