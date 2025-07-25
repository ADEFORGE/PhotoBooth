import base64
import subprocess
import threading
from pathlib import Path
import re
import random
import string
import qrcode
from PIL import Image, UnidentifiedImageError
from flask import Flask, request, send_file, jsonify, send_from_directory, redirect, url_for,Response
import logging
from typing import Optional, Any, List, Dict, Tuple

DEBUG = True

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def log(message: str, level: str = "info") -> None:
    """
    Entry: log(message, level)
    Exit: None
    Logs a message at the specified level if DEBUG is True.
    """
    if DEBUG:
        if level == "info":
            logging.info(message)
        elif level == "warning":
            logging.warning(message)
        elif level == "error":
            logging.error(message)
        elif level == "debug":
            logging.debug(message)
        else:
            logging.info(message)


HOTSPOT_TIMEOUT_SEC = 300
"""
Entry: HOTSPOT_TIMEOUT_SEC
Exit: None
Timeout in seconds before hotspot shutdown.
"""

SPLASH_TEMPLATE_PATH = Path('/etc/nodogsplash/htdocs/splash.tmpl')
"""
Entry: SPLASH_TEMPLATE_PATH
Exit: None
Path to the original splash template file.
"""
ORIGINAL_SPLASH_HTML = SPLASH_TEMPLATE_PATH.read_text()
"""
Entry: ORIGINAL_SPLASH_HTML
Exit: None
Contents of the original splash template file.
"""

app = Flask(__name__)
"""
Entry: app
Exit: None
Flask application instance.
"""

class HotspotShareImage:
    """
    Entry: HotspotShareImage class
    Exit: None
    Manages hotspot sharing, configuration, and QR code generation.
    """
    def __init__(self, image_path: str,
                 qr_dir: Optional[Path] = None,
                 interface: str = 'wlan0',
                 gateway_ip: str = '192.168.5.1',
                 hidden: bool = True) -> None:
        """
        Entry: __init__(self, image_path, qr_dir, interface, gateway_ip, hidden)
        Exit: None
        Initializes the HotspotShareImage instance and its configuration.
        """
        log("[HotspotShareImage.__init__] Enter", level="info")
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
        log("[HotspotShareImage.__init__] Exit", level="info")


    def generate_random_credentials(self, ssid_length: int = 8, pass_length: int = 12) -> None:
        """
        Entry: generate_random_credentials(self, ssid_length, pass_length)
        Exit: None
        Generates random SSID and password for the hotspot.
        """
        log("[generate_random_credentials] Enter", level="info")
        self.ssid = 'PhotoBooth_' + ''.join(random.choices(
            string.ascii_uppercase + string.digits,
            k=ssid_length
        ))
        self.password = ''.join(random.choices(
            string.ascii_letters + string.digits,
            k=pass_length
        ))
        log(f"Generated SSID={self.ssid}, Password=***hidden***", level="info")
        log("[generate_random_credentials] Exit", level="info")

    def get_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Entry: get_credentials(self)
        Exit: tuple
        Returns the current SSID and password as a tuple.
        """
        log("[get_credentials] Enter", level="info")
        creds = (self.ssid, self.password)
        log(f"get_credentials returning credentials: {creds}", level="info")
        log("[get_credentials] Exit", level="info")
        return creds

    def update_hostapd_conf(self) -> None:
        """
        Entry: update_hostapd_conf(self)
        Exit: None
        Updates the hostapd configuration file with new credentials and settings.
        """
        log("[update_hostapd_conf] Enter", level="info")
        lines = self.hostapd_conf.read_text().splitlines()
        log("Read hostapd.conf lines", level="debug")
        with self.hostapd_conf.open('w') as f:
            written_ignore = False
            for line in lines:
                if line.startswith('ssid='):
                    f.write(f'ssid={self.ssid}\n')
                    log(f"Updated ssid line: ssid={self.ssid}", level="info")
                elif line.startswith('wpa_passphrase='):
                    f.write(f'wpa_passphrase={self.password}\n')
                    log(f"Updated wpa_passphrase line", level="info")
                elif line.startswith('ignore_broadcast_ssid='):
                    val = '1' if self.hidden else '0'
                    f.write(f'ignore_broadcast_ssid={val}\n')
                    log(f"Updated ignore_broadcast_ssid line: {val}", level="info")
                    written_ignore = True
                else:
                    f.write(line + '\n')
            if not written_ignore:
                val = '1' if self.hidden else '0'
                f.write(f'ignore_broadcast_ssid={val}\n')
                log(f"Appended ignore_broadcast_ssid line: {val}", level="info")
        log("hostapd config updated", level="info")
        log("[update_hostapd_conf] Exit", level="info")

    def copy_image(self) -> None:
        """
        Entry: copy_image(self)
        Exit: None
        Copies the source image to the destination directory for sharing.
        """
        log("[copy_image] Enter", level="info")
        dst = self.image_dst_dir / self.image_src.name
        try:
            subprocess.run(['cp', str(self.image_src), str(dst)], check=True)
            self.image = dst.name
            log(f"Image copied to {dst}", level="info")
        except Exception as e:
            log(f"Error copying image: {e}", level="error")
            raise
        log("[copy_image] Exit", level="info")

    def update_splash_html(self) -> None:
        """
        Entry: update_splash_html(self)
        Exit: None
        Updates the splash HTML file with the shared image and download link.
        """
        log("[update_splash_html] Enter", level="info")
        content = self.splash_template

        content = re.sub(
            r'<meta http-equiv="refresh" content="[0-9]+;url=[^"]+"',
            f'<meta http-equiv="refresh" content="0;url=/{self.image}"',
            content
        )
        log("Meta refresh updated", level="debug")

        content = re.sub(
            r'href="/[^"]+"\s+download',
            f'href="/{self.image}" download',
            content
        )
        log("Download link updated", level="debug")

        injected_html = f'''
        <div style="text-align:center;margin-top:20px;">
        <img src="/{self.image}" alt="Shared image" style="max-width:100%;height:auto;">
        <p><a href="/{self.image}" download>Download the image</a></p>
        <p>If you are not automatically redirected, <a href="/{self.image}">click here</a>.</p>
        <p style="margin-top:20px; font-size:0.9em; color:#555;">
            Still blocked? Open your browser and manually visit 
            <a href="https://neverssl.com" target="_blank">https://neverssl.com</a>
        </p>
        </div>
        <script>
        window.addEventListener('load', function() {{
          // Crée un lien invisible, définit download et clique dessus
          var link = document.createElement('a');
          link.href = '/{self.image}';
          link.download = '{self.image}';
          document.body.appendChild(link);
          link.click();
        }});
        </script>
        '''

        content = content.replace('</body>', f'{injected_html}\n</body>')
        try:
            (self.image_dst_dir / 'splash.html').write_text(content)
            log("splash.html updated", level="info")
        except Exception as e:
            log(f"Error writing splash.html: {e}", level="error")
            raise
        log("[update_splash_html] Exit", level="info")

    def generate_qrcode(self) -> None:
        """
        Entry: generate_qrcode(self)
        Exit: None
        Generates and saves a QR code for the WiFi credentials.
        """
        log("[generate_qrcode] Enter", level="info")
        self.qr_dir.mkdir(parents=True, exist_ok=True)
        log(f"QR directory ensured: {self.qr_dir}", level="debug")
        hidden_flag = 'true' if self.hidden else 'false'
        qr_data = f"WIFI:T:WPA;S:{self.ssid};P:{self.password};H:{hidden_flag};;"
        img = qrcode.make(qr_data)
        try:
            img.save(str(self.qr_path))
            log(f"QR code generated at {self.qr_path}", level="info")
        except Exception as e:
            log(f"Error saving QR code: {e}", level="error")
            raise
        log("[generate_qrcode] Exit", level="info")

    def configure_network(self) -> None:
        """
        Entry: configure_network(self)
        Exit: None
        Configures the network interface and firewall rules for the hotspot.
        """
        log("[configure_network] Enter", level="info")
        try:
            subprocess.run(['ip', 'addr', 'flush', 'dev', self.interface], check=True)
            log(f"Flushed IP addresses on {self.interface}", level="debug")
            subprocess.run(['ip', 'addr', 'add', f'{self.gateway_ip}/24', 'dev', self.interface], check=True)
            log(f"Added IP {self.gateway_ip}/24 to {self.interface}", level="debug")
            subprocess.run(['ip', 'link', 'set', 'dev', self.interface, 'up'], check=True)
            log(f"Set {self.interface} up", level="debug")
            subprocess.run(['sysctl', '-w', 'net.ipv4.ip_forward=1'], check=True)
            log("Enabled IP forwarding", level="debug")
            subprocess.run(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', 'eth0', '-j', 'MASQUERADE'], check=True)
            log("Set up NAT masquerading", level="debug")
            subprocess.run(['iptables', '-A', 'FORWARD', '-i', 'eth0', '-o', self.interface,
                            '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'], check=True)
            log("Set up FORWARD rule for established connections", level="debug")
            subprocess.run(['iptables', '-A', 'FORWARD', '-i', self.interface, '-o', 'eth0', '-j', 'ACCEPT'], check=True)
            log("Set up FORWARD rule for outgoing connections", level="debug")
            log("Network configured", level="info")
        except Exception as e:
            log(f"Error configuring network: {e}", level="error")
            raise
        log("[configure_network] Exit", level="info")

    def restart_services(self) -> None:
        """
        Entry: restart_services(self)
        Exit: None
        Restarts required services for the hotspot to function.
        """
        log("[restart_services] Enter", level="info")
        try:
            self.configure_network()
            for svc in ['hostapd', 'dnsmasq']:
                try:
                    subprocess.run(['systemctl', 'restart', svc], check=True)
                    log(f"Restarted service: {svc}", level="info")
                except Exception as e:
                    log(f"Error restarting service {svc}: {e}", level="error")
                    raise
            try:
                subprocess.run(['systemctl', 'restart', 'nodogsplash'], check=True)
                log("Restarted service: nodogsplash", level="info")
            except Exception as e:
                log(f"Error restarting nodogsplash: {e}", level="error")
                raise
            log("Services restarted", level="info")
        except Exception as e:
            log(f"Error in restart_services: {e}", level="error")
            raise RuntimeError(f"Erreur lors de redémarrage: {e}")
        log("[restart_services] Exit", level="info")

    def run(self, use_random: bool = True, ssid: Optional[str] = None, password: Optional[str] = None) -> None:
        """
        Entry: run(self, use_random, ssid, password)
        Exit: None
        Runs the full hotspot setup and sharing workflow.
        """
        log("[run] Enter", level="info")
        try:
            if use_random:
                self.generate_random_credentials()
            else:
                self.ssid = ssid
                self.password = password
            log("Credentials set", level="debug")
            self.update_hostapd_conf()
            self.copy_image()
            self.generate_qrcode()
            self.update_splash_html()
            self.restart_services()
            log("run completed", level="info")
        except Exception as e:
            log(f"Error in run: {e}", level="error")
            raise
        log("[run] Exit", level="info")


def shutdown_hotspot(image_name: str) -> None:
    """
    Entry: shutdown_hotspot(image_name)
    Exit: None
    Stops hotspot services and removes the shared image file.
    """
    log(f"[shutdown_hotspot] Enter for {image_name}", level="info")
    for svc in ['nodogsplash', 'dnsmasq', 'hostapd']:
        try:
            subprocess.run(['systemctl', 'stop', svc], check=False)
            log(f"Stopped service: {svc}", level="info")
        except Exception as e:
            log(f"Error stopping service {svc}: {e}", level="error")
    try:
        (Path('/etc/nodogsplash/htdocs') / image_name).unlink()
        log(f"Unlinked image {image_name}", level="info")
    except Exception as e:
        log(f"Error unlinking image {image_name}: {e}", level="error")
    log(f"[shutdown_hotspot] Exit for {image_name}", level="info")

def attach_app_log_to_response(response: Dict[str, Any], log_path: str = 'app.log') -> None:
    """
    Entry: attach_app_log_to_response(response, log_path)
    Exit: None
    Reads the log file and attaches its contents to the response dictionary.
    """
    log(f"[attach_app_log_to_response] Enter for {log_path}", level="info")
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        log(f"Read log file {log_path}", level="debug")
    except Exception as e:
        lines = [f"Unable to read log file '{log_path}': {e}"]
        log(f"Error reading log file {log_path}: {e}", level="error")
    response['app_log_file'] = lines
    log(f"[attach_app_log_to_response] Exit for {log_path}", level="info")
    
    

@app.route('/share', methods=['POST'])
def share() -> Response:
    """
    Entry: share()
    Exit: Response
    Flask endpoint to share an image via hotspot and return credentials and logs.
    """
    log("[/share] Enter endpoint", level="info")
    error_img = Path(__file__).parent / 'error.png'
    if 'image' not in request.files:
        log("[/share] No image in request.files", level="warning")
        log("[/share] Exit endpoint (no image)", level="info")
        return send_file(str(error_img), mimetype='image/png')

    tmp_path = Path('/tmp/uploaded_image.png')
    tmp_path.unlink(missing_ok=True)
    request.files['image'].save(str(tmp_path))
    log("Image uploaded to /tmp/uploaded_image.png", level="info")

    try:
        Image.open(tmp_path).verify()
        log("Uploaded file verified as image", level="info")
    except (UnidentifiedImageError, Exception) as e:
        log(f"[/share] Uploaded file is not a valid image: {e}", level="error")
        log("[/share] Exit endpoint (invalid image)", level="info")
        return send_file(str(error_img), mimetype='image/png')

    h = HotspotShareImage(str(tmp_path), qr_dir=Path('/tmp'))
    h.run()
    ssid, pwd = h.get_credentials()
    threading.Timer(HOTSPOT_TIMEOUT_SEC, shutdown_hotspot, args=[h.image]).start()
    log("Hotspot started and timer set for shutdown", level="info")

    qr_bytes = (Path('/tmp') / 'wifi_qr.png').read_bytes()
    qr_b64 = base64.b64encode(qr_bytes).decode()

    response = {
        'ssid': ssid,
        'password': pwd,
        'qr_code_base64': qr_b64,
    }

    if DEBUG:
        journal = {}
        services = ['hostapd', 'dnsmasq', 'nodogsplash', 'flask_rpi.service']
        for svc in services:
            try:
                out = subprocess.check_output([
                    'journalctl', '-u', svc, '-n', '30', '--no-pager', '--since', '2 minutes ago'
                ], text=True)
                journal[svc] = out.splitlines()
                log(f"Systemd logs retrieved for {svc}", level="debug")
            except subprocess.CalledProcessError as e:
                journal[svc] = ['Error retrieving logs']
                log(f"Error retrieving systemd logs for {svc}: {e}", level="error")
        response['journal'] = journal
        log("[/share] Added systemd logs to response", level="info")
        log("[/share] Exit endpoint (success)", level="info")

    attach_app_log_to_response(response)
    log(f"Response: {response}", level="debug")
    return jsonify(response)

SPLASH_DIR = '/etc/nodogsplash/htdocs'
"""
Entry: SPLASH_DIR
Exit: None
Directory containing the splash.html file generated by HotspotShareImage.
"""

@app.before_request
def force_splash() -> Optional[Response]:
    """
    Entry: force_splash()
    Exit: Response or None
    Flask before-request hook to redirect to splash.html except for allowed routes.
    """
    log("[force_splash] Enter", level="info")
    if request.path.startswith('/share'):
        log("[force_splash] /share route, bypass splash", level="debug")
        log("[force_splash] Exit", level="info")
        return
    if request.path in ('/', '/splash.html', '/wifi_qr.png') \
        or re.search(r'\.(png|jpe?g|gif)$', request.path):
        log(f"[force_splash] Static or image route {request.path}, bypass splash", level="debug")
        log("[force_splash] Exit", level="info")
        return
    log(f"[force_splash] Redirecting to splash.html for {request.path}", level="info")
    log("[force_splash] Exit", level="info")
    return send_from_directory(SPLASH_DIR, 'splash.html')



if __name__ == '__main__':
    """
    Entry: __main__
    Exit: None
    Starts the Flask application server.
    """
    app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'))
