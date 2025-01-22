import os
import platform
import subprocess
import json
import time
import paho.mqtt.client as mqtt


class MQTTClient:
    def __init__(self, message_callback, connection_callback):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.message_callback = message_callback
        self.connection_callback = connection_callback
        self.system = platform.system().lower()  # Détecte l'OS en cours

    def start_mosquitto(self):
        """Démarrer le service Mosquitto."""
        if self._is_service_active():
            print("Le service Mosquitto est déjà actif.")
            return

        print("Démarrage du service Mosquitto...")
        start_cmd = self._get_service_command("start")
        self._run_command(start_cmd)
        print("Service Mosquitto démarré avec succès.")

    def stop_mosquitto(self):
        """Arrêter le service Mosquitto."""
        if not self._is_service_active():
            print("Le service Mosquitto est déjà inactif.")
            return

        print("Arrêt du service Mosquitto...")
        stop_cmd = self._get_service_command("stop")
        self._run_command(stop_cmd)
        print("Service Mosquitto arrêté avec succès.")

    def _is_service_active(self):
        """Vérifie si le service Mosquitto est actif."""
        if self.system == "linux":
            status_cmd = "systemctl is-active mosquitto"
        elif self.system == "windows":
            status_cmd = "sc query mosquitto | findstr /i RUNNING"
        elif self.system == "darwin":  # macOS
            status_cmd = "brew services list | grep mosquitto | grep started"
        else:
            raise NotImplementedError(f"Gestion des services non prise en charge pour {self.system}.")

        try:
            self._run_command(status_cmd)
            return True
        except RuntimeError:
            return False

    def _get_service_command(self, action):
        """Obtenir la commande pour démarrer ou arrêter Mosquitto."""
        if self.system == "linux":
            return f"sudo systemctl {action} mosquitto"
        elif self.system == "windows":
            return f"sc {action} mosquitto"
        elif self.system == "darwin":  # macOS
            if action == "start":
                return "brew services start mosquitto"
            elif action == "stop":
                return "brew services stop mosquitto"
        raise NotImplementedError(f"Commandes pour {action} non prises en charge pour {self.system}.")

    def _run_command(self, command):
        """Exécuter une commande système."""
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Erreur : {result.stderr.strip()}")
            return result.stdout.strip()
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'exécution de la commande '{command}': {e}")

    def start_mqtt(self):
        try:
            self.start_mosquitto()  # Assurez-vous que Mosquitto est démarré
            broker = "localhost"
            port = 1883
            self.mqtt_client.connect(broker, port)
            self.mqtt_client.loop_start()
            print("Connexion MQTT démarrée...")
        except Exception as e:
            print(f"Erreur lors du démarrage MQTT: {e}")
            self.stop_mqtt()
            raise

    def stop_mqtt(self):
        """Arrêter proprement le client MQTT et le service Mosquitto."""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                time.sleep(0.1)  # Petit délai pour permettre la déconnexion

            if self.connection_callback:
                self.connection_callback(False)

            self.stop_mosquitto()  # Arrête le service Mosquitto
            print("Arrêt du client MQTT réussi")
        except Exception as e:
            print(f"Erreur lors de l'arrêt du client MQTT: {e}")
            raise

    def on_disconnect(self, client, userdata, rc):
        """Appelé lors de la déconnexion du broker MQTT"""
        print(f"Déconnecté du broker MQTT avec code: {rc}")
        if self.connection_callback:
            self.connection_callback(False)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connecté au broker MQTT")
            topic = "pallet/rollerhockey"
            client.subscribe(topic, 0)
            print("Abonné aux topics: pallet/rollerhockey")
            if self.connection_callback:
                self.connection_callback(True)
        else:
            print(f"Échec de connexion, code: {rc}")
            if self.connection_callback:
                self.connection_callback(False)

    def on_message(self, client, userdata, msg):
        try:
            print("\n=== Message Reçu ===")
            payload = msg.payload.decode()
            data = json.loads(payload)
            indices = data.get("index", [])
            values = data.get("values", [])
            distances = dict(zip(indices, values))
            self.message_callback(distances.get("HG", None), distances.get("HD", None), distances.get("BM", None))
        except Exception as e:
            print(f"Erreur lors du traitement du message: {e}")
