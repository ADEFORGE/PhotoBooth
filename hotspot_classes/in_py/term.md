# 1) IP statique sur wlan0
sudo ip addr flush dev wlan0
sudo ip addr add 192.168.5.1/24 dev wlan0
sudo ip link set dev wlan0 up

# 2) Activer le forwarding IPv4
sudo sysctl -w net.ipv4.ip_forward=1

# 3) Règles NAT et forwarding
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT

# 4) (Re)démarrage des services
sudo systemctl restart flask_rpi.service
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
sudo systemctl restart nodogsplash

# 5) (Optionnel) Pour qu’ils démarrent automatiquement au boot
sudo systemctl enable hostapd dnsmasq nodogsplash

# Statut général de chaque service
systemctl status hostapd
systemctl status dnsmasq
systemctl status nodogsplash
systemctl status flask_rpi.service

# Pour voir les logs récents de chacun
journalctl -u hostapd    -n 30 --no-pager
journalctl -u dnsmasq    -n 30 --no-pager
journalctl -u nodogsplash -n 30 --no-pager
journalctl -u flask_rpi.service -n 30 --no-pager

# Pour suivre les logs en temps réel
journalctl -u hostapd     -f
journalctl -u dnsmasq     -f
journalctl -u nodogsplash  -f
journalctl -u flask_rpi.service -f


