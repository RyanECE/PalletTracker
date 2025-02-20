import socket
import threading
from typing import Dict, Callable

class UDPDiscoveryServer:
    def __init__(self, callback: Callable[[str, str], None]):
        self.callback = callback
        self.running = False
        self.udp_socket = None
        self.server_thread = None
        self.esp32_addr = None
        self.last_esp32_ip = None  # Stockage de la dernière IP
    
    def get_last_esp32(self):
        return self.esp32_addr, self.last_esp32_ip

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
                
                if message == "REQUEST_IP":
                    if self.esp32_addr is None or self.esp32_addr == addr:
                        self.esp32_addr = addr
                        self.last_esp32_ip = addr[0]  # Stocker l'IP
                        device_name = f"ESP32_{addr[0]}"
                        device_id = addr[0]

                        if self.callback:
                            self.callback(device_name, device_id)
                    
            except Exception as e:
                print(f"Erreur UDP: {e}")
                if not self.running:
                    break
                    
            except Exception as e:
                print(f"Erreur UDP: {e}")
                if not self.running:
                    break

    def send_response(self, device_id: str, message):
        try:
            if self.esp32_addr is None:
                return False
                
            if isinstance(message, str):
                sent = self.udp_socket.sendto(message.encode(), self.esp32_addr)
                if message == "deconnect":
                    self.esp32_addr = None
                return True
            elif isinstance(message, dict):
                if 'broker_ip' in message:
                    broker_ip = message['broker_ip']
                    sent = self.udp_socket.sendto(broker_ip.encode(), self.esp32_addr)
                    return True
                    
            return False
        except Exception as e:
            print(f"Erreur envoi UDP: {e}")
            return False