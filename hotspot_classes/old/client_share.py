#!/usr/bin/env python3
import requests
import json
import base64
from PIL import Image
from pathlib import Path

# --- CONFIGURATION ---
URL       = "http://192.168.10.2:5000/share"
IMAGE_IN  = "in_image.png"   # Image à envoyer
QR_OUT    = "wifi_qr.png"    # QR code à sauver
RESP_JSON = "hotspot_info.json"

# 1. Charger et envoyer l'image
with open(IMAGE_IN, "rb") as f:
    files = {"image": (IMAGE_IN, f, "image/png")}
    resp = requests.post(URL, files=files)
    resp.raise_for_status()

# 2. Récupérer la réponse JSON
data = resp.json()
ssid = data["ssid"]
password = data["password"]
qr_b64 = data["qr_code_base64"]

# 3. Sauvegarder le QR code
qr_bytes = base64.b64decode(qr_b64)
Path(QR_OUT).write_bytes(qr_bytes)

# 4. Sauvegarder les infos
with open(RESP_JSON, "w") as f:
    json.dump({"ssid": ssid, "password": password}, f, indent=2)

print(f"Hotspot SSID   : {ssid}")
print(f"Hotspot mot de passe : {password}")
print(f"QR code sauvé : {QR_OUT}")
print(f"Infos JSON    : {RESP_JSON}")
print("Connecte‑toi au hotspot et ouvre l’URL de splash pour voir l’image.")
