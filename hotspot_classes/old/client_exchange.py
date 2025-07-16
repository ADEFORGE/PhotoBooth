#!/usr/bin/env python3
import requests
import json
from PIL import Image
import time

# --- CONFIGURATION ---
URL       = "http://192.168.10.2:5000/exchange"
IMAGE_IN  = "in_image.png"    # nom de ton image, quelle que soit la taille
IMAGE_OUT = "out.png"         # nom du fichier de sortie

# Préparer les infos (on y inclut la taille de l'image)
img = Image.open(IMAGE_IN)
dimensions = img.size       # (largeur, hauteur) en pixels

info = {
    "machine": "pc_windows" if __import__('platform').system().startswith("Win") else "pc_linux",
    "timestamp": time.time(),
    "dimensions": dimensions
}

# 1. Préparer la requête
with open(IMAGE_IN, "rb") as f:
    files = {"image": (IMAGE_IN, f, "image/png")}
    data  = {"info": json.dumps(info)}

    # 2. Envoyer l'image + infos
    resp = requests.post(URL, files=files, data=data)
    resp.raise_for_status()

# 3. Sauvegarder l'image retournée
with open(IMAGE_OUT, "wb") as f:
    f.write(resp.content)

# 4. Lire et afficher les infos renvoyées par le serveur
retour = resp.headers.get("X-Info", "{}")
result = json.loads(retour)
print("Infos retournées :", result)
print(f"Dimensions origine : {dimensions}, dimensions traitée : {result.get('dimensions')}")

