import socket
import threading
import json
from typing import Dict, Callable

class UDPDiscoveryServer:
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        self.running = False
        self.udp_socket = None
        self.server_thread = None
        self.esp32_addr = None
        
    def start(self):
        self.running = True
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(('', 12345))
        
        self.server_thread = threading.Thread(target=self._listen_for_devices)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        self.running = False
        if self.udp_socket:
            self.udp_socket.close()
        if self.server_thread:
            self.server_thread.join()

    def _listen_for_devices(self):
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = data.decode()
                print(f"UDP reçu de {addr}: {message}")
                
                if message == "REQUEST_IP":
                    # Ne traite la requête que si aucun ESP32 n'est connecté
                    # ou si c'est le même ESP32 qui redemande une IP
                    if self.esp32_addr is None or self.esp32_addr == addr:
                        self.esp32_addr = addr
                        device_name = f"ESP32_{addr[0]}"
                        device_id = addr[0]
                        
                        print(f"ESP32 détecté à {addr}")
                        
                        if self.callback:
                            self.callback(device_name, device_id)
                    
            except Exception as e:
                print(f"Erreur UDP: {e}")
                if not self.running:
                    break

    def send_response(self, device_id: str, message: dict):
        """Envoie une réponse à l'ESP32"""
        try:
            if self.esp32_addr is None:
                print("Aucun ESP32 n'a été détecté")
                return False
            
            if 'broker_ip' in message:
                # Envoi de l'IP
                broker_ip = message['broker_ip']
                print(f"Envoi IP {broker_ip} à {self.esp32_addr}")
                sent = self.udp_socket.sendto(broker_ip.encode(), self.esp32_addr)
                print(f"Envoyé {sent} octets")
                return True
            elif 'stop' in message:
                # Envoi du signal d'arrêt
                print(f"Envoi signal 'stop' à {self.esp32_addr}")
                sent = self.udp_socket.sendto("stop".encode(), self.esp32_addr)
                self.esp32_addr = None  # On oublie l'ESP32
                print(f"Envoyé {sent} octets")
                return True
            else:
                # Envoi du signal de démarrage
                print(f"Envoi 'true' à {self.esp32_addr}")
                sent = self.udp_socket.sendto("true".encode(), self.esp32_addr)
                print(f"Envoyé {sent} octets")
                return True
                
        except Exception as e:
            print(f"Erreur envoi UDP: {e}")
            return False