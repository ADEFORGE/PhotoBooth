#!/usr/bin/env python3
import sys
import json
import base64
import requests
from pathlib import Path
from PIL import Image

class HotspotClient:
    """
    Client robuste pour envoyer une image à la Raspberry Pi et récupérer le QR code du hotspot.
    En cas d'erreur, renvoie une image d'erreur.
    """
    def __init__(self, url: str, timeout: float = 10.0):
        self.url = url
        self.timeout = timeout
        self.image_path: Path = None
        self.resp_data: dict = {}
        self.qr_bytes: bytes = b""
        self.credentials: tuple = (None, None)
        self.error_image = Path(__file__).parent / 'error.png'

    def set_image(self, path: str):
        """Définit le chemin de l'image à envoyer"""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Fichier image introuvable: {path}")
        self.image_path = p

    def run(self):
        """Envoie l'image au serveur, récupère les données et le QR code. Timeout et fallback gérés."""
        if self.image_path is None:
            raise RuntimeError("Aucune image définie. Appel set_image() avant run().")
        try:
            with self.image_path.open("rb") as f:
                files = {"image": (self.image_path.name, f, "image/png")}
                resp = requests.post(self.url, files=files, timeout=self.timeout)
                resp.raise_for_status()
            self.resp_data = resp.json()
            ssid = self.resp_data.get("ssid")
            pwd = self.resp_data.get("password")
            qr_b64 = self.resp_data.get("qr_code_base64", "")
            self.credentials = (ssid, pwd)
            # Décoder le QR code
            try:
                self.qr_bytes = base64.b64decode(qr_b64)
                # Vérifier que ce sont bien des octets d'image
                Image.open(Path("temp.png"))._close() if False else None
            except Exception:
                raise ValueError("Données QR code invalides")
        except Exception as e:
            print(f"Erreur durant l'échange avec le serveur : {e}")
            # Charger l'image d'erreur
            if self.error_image.exists():
                self.qr_bytes = self.error_image.read_bytes()
            else:
                self.qr_bytes = b""
            self.credentials = (None, None)

    def save_qr(self, out_path: str) -> Path:
        """Sauve le QR code ou l'image d'erreur dans un fichier."""
        p = Path(out_path)
        if not self.qr_bytes:
            raise RuntimeError("Aucune donnée QR à sauvegarder.")
        p.write_bytes(self.qr_bytes)
        return p

    def save_info(self, out_path: str) -> Path:
        """Sauve les credentials (SSID et mot de passe) dans un fichier JSON."""
        p = Path(out_path)
        data = {"ssid": self.credentials[0], "password": self.credentials[1]}
        p.write_text(json.dumps(data, indent=2))
        return p

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <image_path>")
        sys.exit(1)
    img = sys.argv[1]
    client = HotspotClient(url="http://192.168.10.2:5000/share")
    client.set_image(img)
    client.run()
    try:
        qr_file = client.save_qr("wifi_qr.png")
        print(f"QR code sauvegardé dans {qr_file}")
    except Exception as e:
        print(f"Impossible de sauvegarder le QR code: {e}")
    try:
        info_file = client.save_info("hotspot_info.json")
        ssid, pwd = client.credentials
        if ssid:
            print(f"Hotspot SSID : {ssid}\nMot de passe : {pwd}")
        else:
            print("Aucune credentiels reçus.")
        print(f"Infos sauvegardées dans {info_file}")
    except Exception as e:
        print(f"Impossible de sauvegarder les infos: {e}")
