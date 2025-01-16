# esp32_simulator.py
import time
import json
import random
import socket
from paho.mqtt import client as mqtt_client
import threading

class ESP32Simulator:
    def __init__(self, device_name: str, mac_address: str):
        self.device_name = device_name
        self.mac_address = mac_address
        self.broker_ip = None
        self.broker_port = 1883
        self.mqtt_client = None
        self.is_running = False
        self.can_send_data = False
        self.discovery_socket = None

    def start(self):
        """Démarre le simulateur ESP32"""
        self.is_running = True
        self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.discovery_socket.bind(('', 0))  # Port aléatoire
        
        print("Attente de l'IP...")
        
        # Démarrer la découverte
        self._start_discovery()

    def _start_discovery(self):
        """Envoie périodiquement des messages de découverte"""
        while self.is_running and not self.broker_ip:
            try:
                message = f"{self.device_name},{self.mac_address}"
                self.discovery_socket.sendto(message.encode(), ('<broadcast>', 12345))
                
                # Attendre une réponse
                data, addr = self.discovery_socket.recvfrom(1024)
                response = json.loads(data.decode())
                
                if 'broker_ip' in response:
                    self.broker_ip = response['broker_ip']
                    print(f"IP reçue - connexion au broker MQTT ({self.broker_ip})")
                    self._connect_mqtt()
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Erreur: {e}")
            
            time.sleep(1)

    def _connect_mqtt(self):
        """Configure et connecte le client MQTT"""
        try:
            self.mqtt_client = mqtt_client.Client(
                client_id=f"{self.device_name}-{self.mac_address}",
                protocol=mqtt_client.MQTTv311
            )
            
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_message = self._on_message
            
            self.mqtt_client.connect(self.broker_ip, self.broker_port)
            self.mqtt_client.subscribe(f"control/{self.mac_address}")
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"Erreur de connexion MQTT: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT Connecté - attente de l'envoi des données")
        else:
            print(f"Échec de connexion MQTT, code: {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            
            if payload.get('start_data', False):
                self.can_send_data = True
                threading.Thread(target=self._send_data_loop, daemon=True).start()
            else:
                self.can_send_data = False
                
        except Exception as e:
            print(f"Erreur de traitement du message: {e}")

    def _send_data_loop(self):
        """Boucle d'envoi des données"""
        while self.is_running and self.can_send_data:
            try:
                data = {
                    'vitesse': round(random.uniform(10, 30), 2),
                    'x': round(random.uniform(0, 100), 2),
                    'y': round(random.uniform(0, 100), 2)
                }
                
                self.mqtt_client.publish('capteurs/data', json.dumps(data))
                print(f"Données envoyées: {data}")
                
            except Exception as e:
                print(f"Erreur d'envoi: {e}")
                
            time.sleep(2)

    def stop(self):
        """Arrête le simulateur"""
        self.is_running = False
        self.can_send_data = False
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        if self.discovery_socket:
            self.discovery_socket.close()

if __name__ == "__main__":
    esp = ESP32Simulator("ESP32-1", "00:1A:2B:3C:4D:5E")
    try:
        esp.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        esp.stop()