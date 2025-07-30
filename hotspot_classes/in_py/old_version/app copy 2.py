import base64
import subprocess
import threading
from pathlib import Path
import re
import random
import string
import qrcode
from PIL import Image, UnidentifiedImageError
from flask import Flask, request, send_file, jsonify, send_from_directory, redirect, url_for, Response
import logging
from typing import Optional, Any, List, Dict, Tuple
import os

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
        Updates the splash HTML file with iOS-compatible image sharing.
        """
        log("[update_splash_html] Enter", level="info")
        content = self.splash_template

        # Remove automatic redirection for iOS compatibility
        content = re.sub(
            r'<meta http-equiv="refresh" content="[0-9]+;url=[^"]+"',
            '',  # No auto-redirect
            content
        )
        log("Meta refresh removed for iOS compatibility", level="debug")

        # Update download link
        content = re.sub(
            r'href="/[^"]+"\s+download',
            f'href="/{self.image}" download',
            content
        )
        log("Download link updated", level="debug")

        # Inject enhanced HTML
        injected_html = f'''
        <div style="text-align:center;margin-top:20px;">
            <h2>Your photo is ready!</h2>

            <!-- Main image with iOS compatibility -->
            <div style="margin: 20px 0;">
                <img id="shared-image" src="/{self.image}" alt="Shared photo"
                    style="max-width:90%;height:auto;border-radius:8px;box-shadow:0 4px 8px rgba(0,0,0,0.1);cursor:pointer;"
                    oncontextmenu="return true;"
                    onclick="openImageFullscreen()">
            </div>

            <!-- Platform-specific instructions -->
            <div id="ios-instructions" style="display:none;background:#f0f8ff;padding:15px;margin:10px;border-radius:8px;">
                <h3>📱 On iPhone/iPad:</h3>
                <p><strong>1.</strong> Long-press the image above</p>
                <p><strong>2.</strong> Select "Save to Photos"</p>
                <p><strong>3.</strong> The image will be saved to your gallery</p>
                <p style="color:#007AFF;"><em>Or click "View Fullscreen" then long-press the image</em></p>
            </div>

            <div id="android-instructions" style="display:none;background:#e8f5e8;padding:15px;margin:10px;border-radius:8px;">
                <h3>🤖 On Android:</h3>
                <p><strong>1.</strong> Click the download button below</p>
                <p><strong>2.</strong> Or long-press the image and choose "Download"</p>
            </div>

            <!-- Download buttons -->
            <div style="margin:20px 0;">
                <a href="/download/{self.image}"
                style="display:inline-block;background:#007AFF;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;margin:5px;font-weight:bold;"
                onclick="trackDownload('button')">
                📥 Download Photo
                </a>

                <a href="/{self.image}" target="_blank"
                style="display:inline-block;background:#34C759;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;margin:5px;font-weight:bold;"
                onclick="trackDownload('view')">
                👁️ View Fullscreen
                </a>
            </div>

            <!-- Fallback link -->
            <div style="margin-top:20px;">
                <p style="font-size:0.9em;color:#666;">
                    <strong>Having trouble downloading?</strong><br>
                    <a href="/{self.image}" target="_blank" style="color:#007AFF;">
                        Click here to view the image fullscreen
                    </a>
                </p>
            </div>

            <!-- Additional help -->
            <details style="margin-top:20px;text-align:left;max-width:500px;margin-left:auto;margin-right:auto;">
                <summary style="cursor:pointer;color:#007AFF;font-weight:bold;">🆘 Need help?</summary>
                <div style="padding:10px;background:#f9f9f9;border-radius:4px;margin-top:10px;">
                    <p><strong>If the image doesn't download:</strong></p>
                    <ul style="text-align:left;">
                        <li><strong>iPhone/iPad:</strong> Long-press the image → "Save to Photos"</li>
                        <li><strong>Android:</strong> Long-press the image → "Download image"</li>
                        <li><strong>PC:</strong> Right-click → "Save image as"</li>
                    </ul>
                    <p style="margin-top:10px;color:#007AFF;">
                        <strong>Alternative:</strong> Click "View Fullscreen" and save from the new page
                    </p>
                    <p style="margin-top:10px;">
                        <a href="https://neverssl.com" target="_blank" style="color:#007AFF;">
                            Connection issue? Try neverssl.com
                        </a>
                    </p>
                </div>
            </details>
        </div>

        <!-- [JavaScript & CSS remain unchanged and already in English logic] -->
        '''  # keep full script and style blocks as-is

        content = content.replace('</body>', f'{injected_html}\n</body>')
        try:
            (self.image_dst_dir / 'splash.html').write_text(content)
            log("splash.html updated with iOS compatibility", level="info")
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
    


# Le problème : La route générique /<filename> capture tout AVANT /download/<filename>
# Solution : Modifier l'ordre des routes et la logique

# SUPPRIMEZ cette route générique problématique :
# @app.route('/<filename>')
# def serve_image(filename):

# REMPLACEZ par cette version corrigée :

@app.route('/download/<filename>')
def force_download(filename):
    """Force le téléchargement pour tous les appareils, spécialement iOS"""
    log(f"[force_download] Enter - Forcing download for {filename}", level="info")
    
    file_path = Path(SPLASH_DIR) / filename
    if not file_path.exists():
        log(f"[force_download] File not found: {filename} at {file_path}", level="error")
        return "File not found", 404
    
    try:
        log(f"[force_download] File exists, serving: {filename}", level="info")
        
        # Headers spéciaux pour forcer le téléchargement sur iOS
        response = send_from_directory(
            SPLASH_DIR, 
            filename, 
            as_attachment=True,
            download_name=filename
        )
        
        # Headers additionnels pour iOS
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Transfer-Encoding'] = 'binary'
        response.headers['Cache-Control'] = 'must-revalidate, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'public'
        
        log(f"[force_download] Download headers set for {filename}", level="info")
        return response
        
    except Exception as e:
        log(f"[force_download] Error serving file {filename}: {e}", level="error")
        return "Error serving file", 500


@app.route('/<filename>')
def serve_image(filename):
    """Sert les images directement depuis le répertoire splash - CETTE ROUTE DOIT ÊTRE APRÈS /download/"""
    log(f"[serve_image] Enter - Serving {filename}", level="debug")
    
    # Vérifier que c'est bien un fichier image
    if not re.search(r'\.(png|jpe?g|gif|webp)$', filename, re.IGNORECASE):
        log(f"[serve_image] {filename} is not an image file", level="warning")
        return send_from_directory(SPLASH_DIR, 'splash.html')
    
    file_path = Path(SPLASH_DIR) / filename
    if not file_path.exists():
        log(f"[serve_image] File not found: {filename} at {file_path}", level="error")
        return send_from_directory(SPLASH_DIR, 'splash.html')
    
    log(f"[serve_image] Serving image: {filename}", level="debug")
    return send_from_directory(SPLASH_DIR, filename)


# VERSION ALTERNATIVE : Modifiez force_splash pour être plus spécifique
@app.before_request
def force_splash() -> Optional[Response]:
    """Version corrigée avec debug supplémentaire"""
    log(f"[force_splash] Processing request: {request.path} | Method: {request.method}", level="debug")
    
    # Routes autorisées - ORDRE IMPORTANT !
    if request.path.startswith('/download/'):
        log(f"[force_splash] Download route detected: {request.path}", level="info")
        return None  # Laisser passer vers force_download()
        
    if request.path.startswith('/share'):
        log(f"[force_splash] Share route detected: {request.path}", level="debug")
        return None
        
    if request.path.startswith('/status'):
        log(f"[force_splash] Status route detected: {request.path}", level="debug")
        return None
    
    # Routes statiques autorisées
    if request.path in ('/', '/splash.html', '/wifi_qr.png') \
        or re.search(r'\.(png|jpe?g|gif|webp)$', request.path):
        log(f"[force_splash] Static or image route {request.path}, bypass splash", level="debug")
        return None
    
    log(f"[force_splash] Redirecting to splash.html for {request.path}", level="info")
    return send_from_directory(SPLASH_DIR, 'splash.html')


# SOLUTION ALTERNATIVE : Utilisez une route plus spécifique pour éviter les conflits
@app.route('/image/<filename>')
def serve_specific_image(filename):
    """Route alternative pour servir les images sans conflit"""
    log(f"[serve_specific_image] Serving {filename}", level="debug")
    
    if not re.search(r'\.(png|jpe?g|gif|webp)$', filename, re.IGNORECASE):
        return "Not an image", 404
    
    file_path = Path(SPLASH_DIR) / filename
    if not file_path.exists():
        return "File not found", 404
    
    return send_from_directory(SPLASH_DIR, filename)


# TEST DEBUG : Ajoutez cette route temporaire pour tester
@app.route('/test-download/<filename>')
def test_download(filename):
    """Route de test pour débugger"""
    log(f"[test_download] Testing download for {filename}", level="info")
    
    file_path = Path(SPLASH_DIR) / filename
    
    response_data = {
        'filename': filename,
        'file_exists': file_path.exists(),
        'file_path': str(file_path),
        'splash_dir': SPLASH_DIR,
        'files_in_dir': list(Path(SPLASH_DIR).glob('*')) if Path(SPLASH_DIR).exists() else []
    }
    
    log(f"[test_download] Debug info: {response_data}", level="info")
    return jsonify(response_data)


# Version complète du gestionnaire d'erreur 404 amélioré
@app.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404 - avec plus de debug"""
    log(f"[404] Path not found: {request.path} | Method: {request.method} | Args: {request.args}", level="warning")
    
    # Si c'est une tentative de téléchargement, essayer de servir le fichier
    if request.path.startswith('/download/'):
        filename = request.path.split('/')[-1]
        file_path = Path(SPLASH_DIR) / filename
        if file_path.exists():
            log(f"[404] File exists, attempting to serve: {filename}", level="info")
            return force_download(filename)
    
    # Sinon, rediriger vers splash
    return send_from_directory(SPLASH_DIR, 'splash.html')


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

@app.after_request
def add_ios_headers(response):
    """Ajoute des headers spécifiques pour iOS et améliore la compatibilité"""
    # Headers de sécurité
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # CSP plus permissif pour iOS
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'self' https:; "
        "font-src 'self' data:; "
        "media-src 'self' data: blob:;"
    )
    
    # Headers spécifiques iOS
    response.headers['X-WebKit-CSP'] = response.headers['Content-Security-Policy']
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # Pour les images, ajouter headers de téléchargement si demandé
    if request.path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        # Permettre le téléchargement direct
        response.headers['Content-Disposition'] = 'inline'
        
        # Headers pour iOS Safari
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Si c'est une route de téléchargement forcé
        if request.path.startswith('/download/') or 'download' in request.args:
            filename = os.path.basename(request.path)
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            response.headers['Content-Type'] = 'application/octet-stream'
    
    return response

@app.route('/status')
def status():
    """Route de status pour debug"""
    return jsonify({
        'status': 'running',
        'platform': 'raspberry-pi',
        'services': {
            'flask': 'running',
            'hotspot': 'available'
        }
    })


@app.errorhandler(500)
def internal_error(error):
    """Gestionnaire d'erreur 500"""
    log(f"[500] Internal error: {error}", level="error")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    """
    Entry: __main__
    Exit: None
    Starts the Flask application server.
    """
    log("Starting Flask application server", level="info")
    try:
        app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'), debug=DEBUG)
    except Exception as e:
        log(f"Error starting Flask server: {e}", level="error")
        # Fallback sans SSL
        log("Attempting to start without SSL", level="warning")
        app.run(host='0.0.0.0', port=5000, debug=DEBUG)
