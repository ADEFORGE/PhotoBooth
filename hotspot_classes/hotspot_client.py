import sys
import json
import base64
import requests
from pathlib import Path
from PIL import Image
import os
from PySide6.QtGui import QImage

import logging
logger = logging.getLogger(__name__)

try :
    from gui_classes.gui_object.constant import DEBUG, DEBUG_FULL
    DEBUG_HotspotClient: bool = DEBUG
    DEBUG_HotspotClient_FULL: bool = DEBUG_FULL
    
except ImportError:
    DEBUG_HotspotClient: bool = True
    DEBUG_HotspotClient_FULL: bool = True


class HotspotClient:
    """
    Robust client to send an image to the Raspberry Pi and retrieve the hotspot QR code.
    In case of error, returns an error image.
    """
    def __init__(self, url: str, timeout: float = 10.0) -> None:
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Initializing with URL: {url}, timeout: {timeout}")
        self.url = url
        self.timeout = timeout
        self.image_path: Path = None
        self.resp_data: dict = {}
        self.qr_bytes: bytes = b""
        self.credentials: tuple = (None, None)
        self.error_image = Path(__file__).parent.parent / 'gui_template' / 'other' / 'error.png'
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Error image path: {self.error_image}")

    def set_image(self, path: str) -> None:
        """
        Sets the path of the image to be sent.
        """
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Setting image path: {path}")
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        self.image_path = p
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Image path set to: {self.image_path}")

    def set_qimage(self, qimg: QImage) -> None:
        """
        Sets the image to be sent from a QImage (PySide6), saved in gui_template/tm.
        """
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Setting QImage for sending.")

        temp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'gui_template', 'tm')
        temp_dir = os.path.abspath(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        temp_img_path = os.path.join(temp_dir, "hotspotclient_qimage.png")
        if not qimg.save(temp_img_path):
            raise RuntimeError("Unable to save QImage as PNG.")
        self.set_image(temp_img_path)
        self._temp_img_path = temp_img_path
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] QImage saved to temporary path: {self._temp_img_path}")

    def cleanup_temp_image(self) -> None:
        """
        Deletes the temporary file created by set_qimage, if present.
        """
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Cleaning up temporary image: {self._temp_img_path if hasattr(self, '_temp_img_path') else 'None'}")
        if hasattr(self, '_temp_img_path') and self._temp_img_path:
            try:
                os.remove(self._temp_img_path)
            except Exception:
                pass
            self._temp_img_path = None
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Temporary image cleaned up.")

    def run(self) -> None:
        """
        Sends the image to the server, retrieves the data and the QR code. Handles timeout and fallback.
        """
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Starting run with image path: {self.image_path}")
        if self.image_path is None:
            raise RuntimeError("No image defined. Call set_image() before run().")
        try:
            with self.image_path.open("rb") as f:
                files = {"image": (self.image_path.name, f, "image/png")}
                resp = requests.post(self.url, files=files, timeout=self.timeout, verify=False)
                resp.raise_for_status()
            self.resp_data = resp.json()
            ssid = self.resp_data.get("ssid")
            pwd = self.resp_data.get("password")
            qr_b64 = self.resp_data.get("qr_code_base64", "")
            self.credentials = (ssid, pwd)

            try:
                self.qr_bytes = base64.b64decode(qr_b64)

                Image.open(Path("temp.png"))._close() if False else None
            except Exception:
                raise ValueError("Invalid QR code data")
        except Exception as e:
            logger.info(f"[DEBUG][HotspotClient] Error during exchange with the server: {e}")

            if self.error_image.exists():
                self.qr_bytes = self.error_image.read_bytes()
            else:
                self.qr_bytes = b""
            self.credentials = (None, None)
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Run completed. Credentials: {self.credentials}, QR bytes length: {len(self.qr_bytes)}")

    def reset(self) -> None:
        """
        Resets the hotspot but uses the error image as the broadcasted image.
        """
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Resetting hotspot client, using error image: {self.error_image}")
        if not self.error_image.exists():
            raise FileNotFoundError(f"Error image not found: {self.error_image}")
        self.set_image(str(self.error_image))
        self.run()
        if DEBUG_HotspotClient: 
            logger.info(f"[DEBUG][HotspotClient] Reset completed. Credentials: {self.credentials}, QR bytes length: {len(self.qr_bytes)}")

    def save_qr(self, out_path: str) -> Path:
        """
        Saves the QR code or the error image to a file.
        """
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Saving QR code to {out_path}")
        p = Path(out_path)
        if not self.qr_bytes:
            raise RuntimeError("No QR data to save.")
        p.write_bytes(self.qr_bytes)
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] QR code saved successfully to {p}")
        return p

    def save_info(self, out_path: str) -> Path:
        """
        Saves the complete response received from the server to a JSON file.
        """
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Saving info to {out_path}")
        p = Path(out_path)
        p.write_text(
            json.dumps(self.resp_data, indent=2, ensure_ascii=False)
        )
        if DEBUG_HotspotClient:
            logger.info(f"[DEBUG][HotspotClient] Info saved successfully to {p}")
        return p

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <image_path>")
        sys.exit(1)
    img = sys.argv[1]
    client = HotspotClient(url="https://192.168.10.2:5000/share")
    client.set_image(img)
    client.run()
    try:
        qr_file = client.save_qr("wifi_qr.png")
        print(f"QR code saved to {qr_file}")
    except Exception as e:
        print(f"Unable to save QR code: {e}")
    try:
        info_file = client.save_info("hotspot_info.json")
        ssid, pwd = client.credentials
        if ssid:
            print(f"Hotspot SSID: {ssid}\nPassword: {pwd}")
        else:
            print("No credentials received.")
        print(f"Info saved to {info_file}")
    except Exception as e:
        print(f"Unable to save info: {e}")
