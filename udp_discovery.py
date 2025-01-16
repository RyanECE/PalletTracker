# udp_discovery.py
import socket
import threading
import json
from typing import Dict, Callable

class UDPDiscoveryServer:
    def __init__(self, callback: Callable[[str, str], None]):
        self.esp32_devices: Dict[str, str] = {}  # mac_address: device_name
        self.callback = callback
        self.running = False
        self.udp_socket = None
        self.server_thread = None
        self.esp32_responses = {}  # Pour stocker les adresses des ESP32

    def start(self):
        """Démarre le serveur UDP de découverte"""
        self.running = True
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('', 12345))  # Port 12345 pour la découverte
        
        self.server_thread = threading.Thread(target=self._listen_for_devices)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Arrête le serveur UDP"""
        self.running = False
        if self.udp_socket:
            self.udp_socket.close()
        if self.server_thread:
            self.server_thread.join()

    def _listen_for_devices(self):
        """Écoute les broadcasts UDP des ESP32"""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                esp_info = data.decode().split(',')
                if len(esp_info) == 2:
                    device_name, mac_address = esp_info
                    
                    # Stocker les informations du dispositif
                    self.esp32_devices[mac_address] = device_name
                    self.esp32_responses[mac_address] = addr
                    
                    # Appeler le callback
                    if self.callback:
                        self.callback(device_name, mac_address)
                        
            except Exception as e:
                print(f"Erreur lors de l'écoute UDP: {e}")
                if not self.running:
                    break

    def send_response(self, mac_address: str, message: dict):
        """Envoie une réponse à un ESP32 spécifique"""
        try:
            if mac_address in self.esp32_responses:
                addr = self.esp32_responses[mac_address]
                print(f"Envoi du message à {mac_address} à l'adresse {addr}: {message}")
                self.udp_socket.sendto(json.dumps(message).encode(), addr)
                return True
            else:
                print(f"Adresse MAC {mac_address} non trouvée dans les réponses")
                return False
        except Exception as e:
            print(f"Erreur lors de l'envoi de la réponse UDP: {e}")
            return False