#!/usr/bin/env python3
import base64
import json
import subprocess
from pathlib import Path
import re
import random
import string
import qrcode
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

class HotspotShareImage:
    def __init__(self, image_path: str, qr_dir: Path = None):
        self.hostapd_conf = Path('/etc/hostapd/hostapd.conf')
        self.splash_html = Path('/etc/nodogsplash/htdocs/splash.html')
        self.image_dst_dir = Path('/etc/nodogsplash/htdocs')
        self.image_src = Path(image_path)
        self.ssid = None
        self.password = None
        self.image = None
        self.qr_dir = Path(qr_dir) if qr_dir else Path(__file__).parent
        self.qr_path = self.qr_dir / 'wifi_qr.png'

    def generate_random_credentials(self, ssid_length=8, pass_length=12):
        self.ssid = 'HSI_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=ssid_length))
        self.password = ''.join(random.choices(string.ascii_letters + string.digits, k=pass_length))

    def get_credentials(self):
        return self.ssid, self.password

    def update_hostapd_conf(self):
        # Lire les lignes existantes
        lines = self.hostapd_conf.read_text().splitlines()
        with self.hostapd_conf.open('w') as f:
            has_ignore = False
            for line in lines:
                if line.startswith('ssid='):
                    f.write(f'ssid={self.ssid}\n')
                elif line.startswith('wpa_passphrase='):
                    f.write(f'wpa_passphrase={self.password}\n')
                elif line.startswith('ignore_broadcast_ssid='):
                    f.write('ignore_broadcast_ssid=1\n')
                    has_ignore = True
                else:
                    f.write(line + '\n')
            # Ajouter ignore_broadcast_ssid si absent
            if not has_ignore:
                f.write('ignore_broadcast_ssid=1\n')

    def copy_image(self):
        dst = self.image_dst_dir / self.image_src.name
        subprocess.run(['cp', str(self.image_src), str(dst)], check=True)
        self.image = dst.name

    def update_splash_html(self):
        content = self.splash_html.read_text()
        content = re.sub(r'<meta http-equiv="refresh" content="[0-9]+;url=[^\"]+"',
                         f'<meta http-equiv="refresh" content="0;url=/{self.image}"', content)
        content = re.sub(r'href="/[^"]+"\s+download', f'href="/{self.image}" download', content)
        qr_tag = f'<div><img src="/wifi_qr.png" alt="Wi-Fi QR Code"></div>'
        content = content.replace('</body>', f'  {qr_tag}\n</body>')
        self.splash_html.write_text(content)

    def generate_qrcode(self):
        self.qr_dir.mkdir(parents=True, exist_ok=True)
        qr_data = f"WIFI:T:WPA;S:{self.ssid};P:{self.password};H:true;;"
        img = qrcode.make(qr_data)
        img.save(self.qr_path)

    def restart_services(self):
        subprocess.run(['systemctl', 'restart', 'hostapd'], check=True)
        subprocess.run(['systemctl', 'restart', 'dnsmasq'], check=True)
        subprocess.run(['systemctl', 'restart', 'nodogsplash'], check=True)

    def run(self, use_random=True, ssid=None, password=None):
        if use_random:
            self.generate_random_credentials()
        else:
            self.ssid = ssid
            self.password = password

        self.update_hostapd_conf()
        self.copy_image()
        self.generate_qrcode()
        self.update_splash_html()
        self.restart_services()

@app.post("/share")
def share():
    if 'image' not in request.files:
        abort(400, "Image manquante")
    img_file = request.files['image']
    tmp_path = Path('/tmp/uploaded_image.png')
    try:
        tmp_path.unlink()
    except Exception:
        pass
    img_file.save(str(tmp_path))

    h = HotspotShareImage(str(tmp_path), qr_dir=Path('/tmp'))
    h.run()

    qr_bytes = (Path('/tmp') / 'wifi_qr.png').read_bytes()
    qr_b64 = base64.b64encode(qr_bytes).decode()
    ssid, pwd = h.get_credentials()
    return jsonify({
        "ssid": ssid,
        "password": pwd,
        "qr_code_base64": qr_b64
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
