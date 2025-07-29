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

        # Supprimer la redirection automatique pour iOS
        content = re.sub(
            r'<meta http-equiv="refresh" content="[0-9]+;url=[^"]+"',
            '',  # Pas de redirection automatique
            content
        )
        log("Meta refresh removed for iOS compatibility", level="debug")

        content = re.sub(
            r'href="/[^"]+"\s+download',
            f'href="/{self.image}" download',
            content
        )
        log("Download link updated", level="debug")

        # HTML amélioré pour iOS
        injected_html = f'''
        <div style="text-align:center;margin-top:20px;">
            <h2>Votre photo est prête !</h2>
            
            <!-- Image principale avec gestion iOS -->
            <div style="margin: 20px 0;">
                <img id="shared-image" src="/{self.image}" alt="Photo partagée" 
                     style="max-width:90%;height:auto;border-radius:8px;box-shadow:0 4px 8px rgba(0,0,0,0.1);cursor:pointer;"
                     oncontextmenu="return true;" 
                     onclick="openImageFullscreen()">
            </div>
            
            <!-- Instructions spécifiques par plateforme -->
            <div id="ios-instructions" style="display:none;background:#f0f8ff;padding:15px;margin:10px;border-radius:8px;">
                <h3>📱 Sur iPhone/iPad :</h3>
                <p><strong>1.</strong> Appuyez longuement sur l'image ci-dessus</p>
                <p><strong>2.</strong> Sélectionnez "Enregistrer dans Photos"</p>
                <p><strong>3.</strong> L'image sera sauvegardée dans votre galerie</p>
                <p style="color:#007AFF;"><em>Ou cliquez sur "Voir en grand" puis maintenez appuyé sur l'image</em></p>
            </div>
            
            <div id="android-instructions" style="display:none;background:#e8f5e8;padding:15px;margin:10px;border-radius:8px;">
                <h3>🤖 Sur Android :</h3>
                <p><strong>1.</strong> Cliquez sur le bouton de téléchargement ci-dessous</p>
                <p><strong>2.</strong> Ou appuyez longuement sur l'image et "Télécharger"</p>
            </div>
            
            <!-- Boutons de téléchargement multiples -->
            <div style="margin:20px 0;">
                <a href="/download/{self.image}" 
                   style="display:inline-block;background:#007AFF;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;margin:5px;font-weight:bold;"
                   onclick="trackDownload('button')">
                   📥 Télécharger la photo
                </a>
                
                <a href="/{self.image}" target="_blank"
                   style="display:inline-block;background:#34C759;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;margin:5px;font-weight:bold;"
                   onclick="trackDownload('view')">
                   👁️ Voir en grand
                </a>
            </div>
            
            <!-- Lien de secours -->
            <div style="margin-top:20px;">
                <p style="font-size:0.9em;color:#666;">
                    <strong>Problème de téléchargement ?</strong><br>
                    <a href="/{self.image}" target="_blank" style="color:#007AFF;">
                        Cliquez ici pour afficher l'image en plein écran
                    </a>
                </p>
            </div>
            
            <!-- Aide supplémentaire -->
            <details style="margin-top:20px;text-align:left;max-width:500px;margin-left:auto;margin-right:auto;">
                <summary style="cursor:pointer;color:#007AFF;font-weight:bold;">🆘 Besoin d'aide ?</summary>
                <div style="padding:10px;background:#f9f9f9;border-radius:4px;margin-top:10px;">
                    <p><strong>Si l'image ne se télécharge pas :</strong></p>
                    <ul style="text-align:left;">
                        <li><strong>iPhone/iPad :</strong> Maintenez appuyé sur l'image → "Enregistrer dans Photos"</li>
                        <li><strong>Android :</strong> Clic long sur l'image → "Télécharger l'image"</li>
                        <li><strong>PC :</strong> Clic droit → "Enregistrer l'image sous"</li>
                    </ul>
                    <p style="margin-top:10px;color:#007AFF;">
                        <strong>Alternative :</strong> Cliquez sur "Voir en grand" puis sauvegardez depuis la nouvelle page
                    </p>
                    <p style="margin-top:10px;">
                        <a href="https://neverssl.com" target="_blank" style="color:#007AFF;">
                            Problème de connexion ? Essayez neverssl.com
                        </a>
                    </p>
                </div>
            </details>
        </div>

        <script>
        // Variables globales
        let platformInfo = null;
        
        // Détection de la plateforme
        function detectPlatform() {{
            if (platformInfo) return platformInfo;
            
            const userAgent = navigator.userAgent.toLowerCase();
            const isIOS = /iphone|ipad|ipod/.test(userAgent) || 
                         (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
            const isAndroid = /android/.test(userAgent);
            const isSafari = /safari/.test(userAgent) && !/chrome/.test(userAgent);
            const isChrome = /chrome/.test(userAgent);
            const isMobile = /mobile/.test(userAgent) || isIOS || isAndroid;
            
            platformInfo = {{ isIOS, isAndroid, isSafari, isChrome, isMobile, userAgent }};
            
            // Afficher les instructions appropriées
            if (isIOS) {{
                const iosDiv = document.getElementById('ios-instructions');
                if (iosDiv) iosDiv.style.display = 'block';
                console.log('iOS detected - showing iOS instructions');
            }} else if (isAndroid) {{
                const androidDiv = document.getElementById('android-instructions');
                if (androidDiv) androidDiv.style.display = 'block';
                console.log('Android detected - showing Android instructions');
            }}
            
            return platformInfo;
        }}
        
        // Suivi des téléchargements
        function trackDownload(method) {{
            console.log('Download attempted via:', method);
            const platform = detectPlatform();
            
            // Pour iOS, on évite le téléchargement automatique
            if (platform.isIOS && method === 'auto') {{
                console.log('iOS detected - skipping auto download');
                return false;
            }}
            
            return true;
        }}
        
        // Fonction pour ouvrir l'image en plein écran
        function openImageFullscreen() {{
            console.log('Opening image fullscreen');
            const platform = detectPlatform();
            
            if (platform.isIOS) {{
                // Sur iOS, ouvrir dans la même fenêtre pour éviter les blocages popup
                window.location.href = '/{self.image}';
            }} else {{
                // Sur autres plateformes, essayer popup puis fallback
                const newWindow = window.open('/{self.image}', '_blank', 'noopener,noreferrer');
                if (!newWindow) {{
                    console.log('Popup blocked, using same window');
                    window.location.href = '/{self.image}';
                }}
            }}
        }}
        
        // Gestion spéciale pour iOS
        function handleImageInteraction() {{
            const img = document.getElementById('shared-image');
            if (!img) return;
            
            const platform = detectPlatform();
            
            if (platform.isIOS) {{
                // Sur iOS, améliorer l'expérience tactile
                img.style.webkitTouchCallout = 'default';
                img.style.webkitUserSelect = 'none';
                
                // Gérer les événements tactiles
                img.addEventListener('touchstart', function(e) {{
                    console.log('Touch started on image (iOS)');
                    this.style.opacity = '0.8';
                }}, {{ passive: true }});
                
                img.addEventListener('touchend', function(e) {{
                    console.log('Touch ended on image (iOS)');
                    this.style.opacity = '1';
                }}, {{ passive: true }});
                
                img.addEventListener('touchcancel', function(e) {{
                    this.style.opacity = '1';
                }}, {{ passive: true }});
            }}
        }}
        
        // Fonction pour le téléchargement automatique (non-iOS uniquement)
        function attemptAutoDownload() {{
            const platform = detectPlatform();
            
            if (platform.isIOS) {{
                console.log('iOS detected - skipping auto download for better UX');
                return;
            }}
            
            console.log('Non-iOS platform - attempting auto download');
            setTimeout(function() {{
                try {{
                    const link = document.createElement('a');
                    link.href = '/download/{self.image}';
                    link.download = '{self.image}';
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    
                    link.click();
                    console.log('Auto download triggered');
                    
                    // Nettoyer
                    setTimeout(() => document.body.removeChild(link), 100);
                }} catch(e) {{
                    console.log('Auto download failed:', e);
                }}
            }}, 1000);
        }}
        
        // Gestion des erreurs d'image
        function handleImageError() {{
            const img = document.getElementById('shared-image');
            if (img) {{
                img.onerror = function() {{
                    console.error('Failed to load image');
                    this.alt = 'Erreur de chargement de l\'image';
                    this.style.border = '2px dashed #ccc';
                    this.style.padding = '20px';
                }};
            }}
        }}
        
        // Fonction pour forcer le captive portal bypass sur iOS
        function bypassCaptivePortal() {{
            const platform = detectPlatform();
            if (platform.isIOS) {{
                // Tenter de déclencher la détection de portail captif
                setTimeout(() => {{
                    const testImg = new Image();
                    testImg.src = 'http://captive.apple.com/hotspot-detect.html?' + Date.now();
                    console.log('Attempted iOS captive portal bypass');
                }}, 500);
            }}
        }}
        
        // Initialisation principale
        function initializePage() {{
            console.log('Page loaded - initializing...');
            const platform = detectPlatform();
            console.log('Platform detection:', platform);
            
            // Configurer les interactions
            handleImageInteraction();
            handleImageError();
            
            // Bypass captive portal pour iOS
            bypassCaptivePortal();
            
            // Tentative de téléchargement automatique (sauf iOS)
            attemptAutoDownload();
            
            // Ajouter des événements pour debug
            if (platform.isIOS) {{
                document.addEventListener('visibilitychange', function() {{
                    console.log('Visibility changed:', document.visibilityState);
                }});
                
                window.addEventListener('pagehide', function() {{
                    console.log('Page hide event (iOS)');
                }});
            }}
        }}
        
        // Lancement à la fin du chargement
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initializePage);
        }} else {{
            initializePage();
        }}
        
        // Fallback sur window.onload
        window.addEventListener('load', function() {{
            console.log('Window load event');
            if (!platformInfo) {{
                initializePage();
            }}
        }});
        </script>
        
        <style>
        /* Styles spécifiques pour iOS */
        @supports (-webkit-touch-callout: none) {{
            #shared-image {{
                -webkit-touch-callout: default !important;
                -webkit-user-select: none;
                -webkit-tap-highlight-color: rgba(0,0,0,0.1);
            }}
        }}
        
        /* Amélioration de l'accessibilité */
        a {{
            transition: all 0.2s ease;
        }}
        
        a:hover, a:focus {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        a:active {{
            transform: translateY(0);
        }}
        
        /* Image interactive */
        #shared-image {{
            transition: opacity 0.2s ease, transform 0.1s ease;
        }}
        
        #shared-image:hover {{
            transform: scale(1.02);
        }}
        
        #shared-image:active {{
            transform: scale(0.98);
        }}
        
        /* Responsive design */
        @media (max-width: 480px) {{
            div {{
                padding: 10px !important;
                margin: 10px 5px !important;
            }}
            
            #shared-image {{
                max-width: 95% !important;
            }}
            
            a {{
                display: block !important;
                margin: 10px auto !important;
                max-width: 280px;
            }}
        }}
        
        /* Animation d'apparition */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        #shared-image {{
            animation: fadeIn 0.5s ease-out;
        }}
        </style>
        '''

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
    if request.path.startswith('/share') or request.path.startswith('/download'):
        log(f"[force_splash] {request.path} route, bypass splash", level="debug")
        log("[force_splash] Exit", level="info")
        return
    if request.path in ('/', '/splash.html', '/wifi_qr.png') \
        or re.search(r'\.(png|jpe?g|gif|webp), request.path):
        log(f"[force_splash] Static or image route {request.path}, bypass splash", level="debug")
        log("[force_splash] Exit", level="info")
        return
    log(f"[force_splash] Redirecting to splash.html for {request.path}", level="info")
    log("[force_splash] Exit", level="info")
    return send_from_directory(SPLASH_DIR, 'splash.html')


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

@app.route('/download/<filename>')
def force_download(filename):
    """Force le téléchargement pour tous les appareils, spécialement iOS"""
    log(f"[force_download] Forcing download for {filename}", level="info")
    
    file_path = Path(SPLASH_DIR) / filename
    if not file_path.exists():
        log(f"[force_download] File not found: {filename}", level="error")
        return "File not found", 404
    
    # Headers spéciaux pour forcer le téléchargement sur iOS
    response = send_from_directory(
        SPLASH_DIR, 
        filename, 
        as_attachment=True,
        download_name=filename,
        mimetype='application/octet-stream'
    )
    
    # Headers additionnels pour iOS
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'application/force-download'
    response.headers['Content-Transfer-Encoding'] = 'binary'
    response.headers['Cache-Control'] = 'must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'public'
    
    log(f"[force_download] Download headers set for {filename}", level="info")
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

@app.errorhandler(404)
def not_found(error):
    """Gestionnaire d'erreur 404 - redirige vers splash"""
    log(f"[404] Path not found: {request.path}", level="warning")
    return send_from_directory(SPLASH_DIR, 'splash.html')

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
