#!/usr/bin/env python3
import base64
import subprocess
import threading
from pathlib import Path
import re
import random
import string
import qrcode
from flask import Flask, request, send_file, jsonify
from PIL import Image, UnidentifiedImageError

# Durée avant extinction du hotspot (en secondes)
HOTSPOT_TIMEOUT_SEC = 300  # 5 minutes

# --- On pointe vers le template vierge (jamais modifié) ---
SPLASH_TEMPLATE_PATH = Path('/etc/nodogsplash/htdocs/splash.tmpl')
ORIGINAL_SPLASH_HTML = SPLASH_TEMPLATE_PATH.read_text()

app = Flask(__name__)

class HotspotShareImage:
    def __init__(self, image_path: str,
                 qr_dir: Path = None,
                 interface: str = 'wlan0',
                 gateway_ip: str = '192.168.5.1',
                 hidden: bool = True):
        self.hostapd_conf = Path('/etc/hostapd/hostapd.conf')
        self.image_dst_dir = Path('/etc/nodogsplash/htdocs')
        self.splash_template = ORIGINAL_SPLASH_HTML
        self.image_src = Path(image_path)
        self.ssid = None
        self.password = None
        self.image = None
        self.qr_dir = Path(qr_dir) if qr_dir else Path(__file__).parent
        self.qr_path = self.qr_dir / 'wifi_qr.png'
        self.interface = interface
        self.gateway_ip = gateway_ip
        self.hidden = hidden

    def generate_random_credentials(self, ssid_length=8, pass_length=12):
        self.ssid = 'HSI_' + ''.join(random.choices(
            string.ascii_uppercase + string.digits,
            k=ssid_length
        ))
        self.password = ''.join(random.choices(
            string.ascii_letters + string.digits,
            k=pass_length
        ))

    def get_credentials(self):
        return self.ssid, self.password

    def update_hostapd_conf(self):
        lines = self.hostapd_conf.read_text().splitlines()
        with self.hostapd_conf.open('w') as f:
            written_ignore = False
            for line in lines:
                if line.startswith('ssid='):
                    f.write(f'ssid={self.ssid}\n')
                elif line.startswith('wpa_passphrase='):
                    f.write(f'wpa_passphrase={self.password}\n')
                elif line.startswith('ignore_broadcast_ssid='):
                    val = '1' if self.hidden else '0'
                    f.write(f'ignore_broadcast_ssid={val}\n')
                    written_ignore = True
                else:
                    f.write(line + '\n')
            if not written_ignore:
                val = '1' if self.hidden else '0'
                f.write(f'ignore_broadcast_ssid={val}\n')

    def copy_image(self):
        dst = self.image_dst_dir / self.image_src.name
        subprocess.run(['cp', str(self.image_src), str(dst)], check=True)
        self.image = dst.name

    def update_splash_html(self):
        content = self.splash_template
        # meta-refresh pour afficher l'image
        content = re.sub(
            r'<meta http-equiv="refresh" content="[0-9]+;url=[^"]+"',
            f'<meta http-equiv="refresh" content="0;url=/{self.image}"',
            content
        )
        # lien de téléchargement
        content = re.sub(
            r'href="/[^"]+"\s+download',
            f'href="/{self.image}" download',
            content
        )
        # injection image partagée et script auto-download
        img_tag = f'<div><img src="/{self.image}" alt="Image partagée"></div>'
        dl_script = f"""
<script>
window.addEventListener('load', function() {{
  var link = document.createElement('a');
  link.href = '/{self.image}';
  link.download = '{self.image}';
  document.body.appendChild(link);
  link.click();
}});
</script>
"""
        content = content.replace(
            '</body>',
            f'{img_tag}\n{dl_script}\n</body>'
        )
        (self.image_dst_dir / 'splash.html').write_text(content)

    def generate_qrcode(self):
        self.qr_dir.mkdir(parents=True, exist_ok=True)
        hidden_flag = 'true' if self.hidden else 'false'
        qr_data = f"WIFI:T:WPA;S:{self.ssid};P:{self.password};H:{hidden_flag};;"
        img = qrcode.make(qr_data)
        img.save(self.qr_path)

    def configure_network(self):
        # IP statique
        subprocess.run(['ip', 'addr', 'flush', 'dev', self.interface], check=True)
        subprocess.run(['ip', 'addr', 'add', f'{self.gateway_ip}/24', 'dev', self.interface], check=True)
        subprocess.run(['ip', 'link', 'set', 'dev', self.interface, 'up'], check=True)
        # forwarding
        subprocess.run(['sysctl', '-w', 'net.ipv4.ip_forward=1'], check=True)
        # NAT rules
        subprocess.run(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', 'eth0', '-j', 'MASQUERADE'], check=True)
        subprocess.run(['iptables', '-A', 'FORWARD', '-i', 'eth0', '-o', self.interface,
                        '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'], check=True)
        subprocess.run(['iptables', '-A', 'FORWARD', '-i', self.interface, '-o', 'eth0', '-j', 'ACCEPT'], check=True)

    def restart_services(self):
        try:
            self.configure_network()
            for svc in ['hostapd', 'dnsmasq', 'nodogsplash']:
                subprocess.run(['systemctl', 'restart', svc], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Erreur lors de redémarrage: {e}")

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


def shutdown_hotspot(image_name: str):
    for svc in ['nodogsplash', 'dnsmasq', 'hostapd']:
        subprocess.run(['systemctl', 'stop', svc], check=False)
    try:
        (Path('/etc/nodogsplash/htdocs') / image_name).unlink()
    except Exception:
        pass

@app.route('/share', methods=['POST'])
def share():
    error_img = Path(__file__).parent / 'error.png'
    if 'image' not in request.files:
        return send_file(str(error_img), mimetype='image/png')

    tmp_path = Path('/tmp/uploaded_image.png')
    tmp_path.unlink(missing_ok=True)
    request.files['image'].save(str(tmp_path))

    try:
        Image.open(tmp_path).verify()
    except (UnidentifiedImageError, Exception):
        return send_file(str(error_img), mimetype='image/png')

    h = HotspotShareImage(str(tmp_path), qr_dir=Path('/tmp'))
    h.run()
    ssid, pwd = h.get_credentials()
    threading.Timer(HOTSPOT_TIMEOUT_SEC, shutdown_hotspot, args=[h.image]).start()

    qr_bytes = (Path('/tmp') / 'wifi_qr.png').read_bytes()
    qr_b64 = base64.b64encode(qr_bytes).decode()

    return jsonify({'ssid': ssid, 'password': pwd, 'qr_code_base64': qr_b64})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
