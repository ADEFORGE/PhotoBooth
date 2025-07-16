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
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
sudo systemctl restart nodogsplash

# 5) (Optionnel) Pour qu’ils démarrent automatiquement au boot
sudo systemctl enable hostapd dnsmasq nodogsplash
