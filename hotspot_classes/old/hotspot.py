import subprocess
from pathlib import Path
import re
import random
import string
import qrcode
import argparse

class HotspotShareImage:
    def __init__(self, image_path: str, qr_dir: Path = None, hidden: bool = False):
        self.hostapd_conf = Path('/etc/hostapd/hostapd.conf')
        self.splash_html = Path('/etc/nodogsplash/htdocs/splash.html')
        self.image_dst_dir = Path('/etc/nodogsplash/htdocs')
        self.image_src = Path(image_path)
        self.ssid = None
        self.password = None
        self.image = None
        self.qr_dir = Path(qr_dir) if qr_dir else Path(__file__).parent
        self.qr_path = self.qr_dir / 'wifi_qr.png'
        self.hidden = hidden
        self.interface = 'wlan0'
        self.gateway_ip = '192.168.5.1'

    def generate_random_credentials(self, ssid_length=8, pass_length=12):
        self.ssid = 'HSI_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=ssid_length))
        self.password = ''.join(random.choices(string.ascii_letters + string.digits, k=pass_length))
        print(f"SSID généré : {self.ssid} (hidden={self.hidden})")
        print(f"Mot de passe généré : {self.password}")

    def get_credentials(self):
        return self.ssid, self.password

    def update_hostapd_conf(self):
        lines = self.hostapd_conf.read_text().splitlines()
        with self.hostapd_conf.open('w') as f:
            for line in lines:
                if line.startswith('ssid='):
                    f.write(f'ssid={self.ssid}\n')
                elif line.startswith('wpa_passphrase='):
                    f.write(f'wpa_passphrase={self.password}\n')
                elif line.startswith('ignore_broadcast_ssid='):
                    val = '1' if self.hidden else '0'
                    f.write(f'ignore_broadcast_ssid={val}\n')
                else:
                    f.write(line + '\n')

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
        hidden_flag = 'true' if self.hidden else 'false'
        qr_data = f"WIFI:T:WPA;S:{self.ssid};P:{self.password};H:{hidden_flag};;"
        img = qrcode.make(qr_data)
        img.save(self.qr_path)
        print(f"QR code généré et enregistré dans {self.qr_path}")

    def configure_network(self):
        # Configure l'interface Wi-Fi en IP statique
        subprocess.run(['ip', 'addr', 'flush', 'dev', self.interface], check=True)
        subprocess.run(['ip', 'addr', 'add', f'{self.gateway_ip}/24', 'dev', self.interface], check=True)
        subprocess.run(['ip', 'link', 'set', 'dev', self.interface, 'up'], check=True)
        print(f"Interface {self.interface} configurée sur {self.gateway_ip}/24")
        # Activer le forwarding IPv4
        subprocess.run(['sysctl', '-w', 'net.ipv4.ip_forward=1'], check=True)
        print("IP forwarding activé")
        # Règles NAT pour partager la connexion via eth0
        subprocess.run(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-o', 'eth0', '-j', 'MASQUERADE'], check=True)
        subprocess.run(['iptables', '-A', 'FORWARD', '-i', 'eth0', '-o', self.interface, '-m', 'state', '--state', 'RELATED,ESTABLISHED', '-j', 'ACCEPT'], check=True)
        subprocess.run(['iptables', '-A', 'FORWARD', '-i', self.interface, '-o', 'eth0', '-j', 'ACCEPT'], check=True)
        print("Règles NAT et forwarding appliquées")
        # Configure l'interface Wi-Fi en IP statique
        subprocess.run(['ip', 'addr', 'flush', 'dev', self.interface], check=True)
        subprocess.run(['ip', 'addr', 'add', f'{self.gateway_ip}/24', 'dev', self.interface], check=True)
        subprocess.run(['ip', 'link', 'set', 'dev', self.interface, 'up'], check=True)
        print(f"Interface {self.interface} configurée sur {self.gateway_ip}/24")

    def restart_services(self):
        # Assure la configuration réseau avant dnsmasq
        self.configure_network()
        subprocess.run(['systemctl', 'restart', 'hostapd'], check=True)
        subprocess.run(['systemctl', 'restart', 'dnsmasq'], check=True)
        subprocess.run(['systemctl', 'restart', 'nodogsplash'], check=True)

    def run(self, use_random=True, ssid=None, password=None):
        if use_random:
            self.generate_random_credentials()
        else:
            self.ssid = ssid
            self.password = password
            print(f"SSID défini : {self.ssid} (hidden={self.hidden})")
            print(f"Mot de passe défini : {self.password}")

        self.update_hostapd_conf()
        self.copy_image()
        self.generate_qrcode()
        self.update_splash_html()
        try:
            self.restart_services()
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors du redémarrage des services : {e}")
            print("Vérifiez la configuration réseau et les logs de dnsmasq/hostapd")
            raise

        print('Hotspot démarré avec :')
        print(f'  SSID: {self.ssid} (hidden={self.hidden})')
        print(f'  Mot de passe: {self.password}')
        print(f'  Image partagée: {self.image}')
        print(f'  QR code: {self.qr_path.name} (dans {self.qr_dir})')


def main():
    parser = argparse.ArgumentParser(description='Lance le hotspot et partage une image avec QR code.')
    parser.add_argument('--image', required=True, help='Chemin vers l’image à partager')
    parser.add_argument('--qr-dir', help='Répertoire de sortie pour le QR code (défaut: dossier du script)')
    parser.add_argument('--hidden', action='store_true', help='Masquer le SSID')
    parser.add_argument('--no-random', action='store_true', help='Ne pas générer aléatoirement SSID et mdp')
    parser.add_argument('--ssid', help='SSID à utiliser (si --no-random)')
    parser.add_argument('--password', help='Mot de passe à utiliser (si --no-random)')
    args = parser.parse_args()

    qr_dir = Path(args.qr_dir) if args.qr_dir else None
    h = HotspotShareImage(args.image, qr_dir, hidden=args.hidden)
    if args.no_random:
        if not args.ssid or not args.password:
            print('Avec --no-random, vous devez fournir --ssid et --password.')
            return
        h.run(use_random=False, ssid=args.ssid, password=args.password)
    else:
        h.run()

    ssid, pwd = h.get_credentials()
    print(f"Getter -> SSID: {ssid}, Mot de passe: {pwd}")

if __name__ == '__main__':
    main()
