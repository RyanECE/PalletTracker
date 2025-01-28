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
        self.architecture = self._get_architecture()  # Detects the architecture
        print(f"Architecture detected: {self.architecture}")  # Debugging line
        self.mosquitto_path = self._get_mosquitto_path()
        self.mosquitto_process = None  # Stocke le processus Mosquitto

    def _get_architecture(self):
        """Detects the system architecture."""
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            return "x86_64"
        elif arch in ["arm64", "aarch64"]:
            return "arm64"
        elif arch.startswith("arm"):
            return "arm"
        elif arch in ["i386", "i686"]:
            return "x86"
        else:
            raise RuntimeError(f"Unsupported architecture: {arch}")

    def start_mosquitto(self):
        """Démarrer le service Mosquitto avec la configuration spécifique."""
        if self.mosquitto_process and self.mosquitto_process.poll() is None:
            print("Le service Mosquitto est déjà en cours d'exécution.")
            return

        print("Démarrage du service Mosquitto...")
        
        # Configure LD_LIBRARY_PATH only for Linux
        if self.system == "linux":
            mosquitto_bin_dir = os.path.join(os.path.dirname(self.mosquitto_path), 'lib')
            current_ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
            new_ld_library_path = f"{mosquitto_bin_dir}:{current_ld_library_path}"
            os.environ["LD_LIBRARY_PATH"] = new_ld_library_path

        config_path = os.path.join(os.path.dirname(__file__), 'mosquitto', 'mosquitto.conf')
        start_cmd = [self.mosquitto_path, "-c", config_path]
        self.mosquitto_process = subprocess.Popen(start_cmd)
        time.sleep(2)  # Attendez que le service Mosquitto démarre
        if self.mosquitto_process.poll() is None:
            print("Service Mosquitto démarré avec succès.")
        else:
            print("Échec du démarrage du service Mosquitto.")

    def stop_mosquitto(self):
        """Arrêter le service Mosquitto."""
        if self.mosquitto_process and self.mosquitto_process.poll() is None:
            print("Arrêt du service Mosquitto...")
            self.mosquitto_process.terminate()
            try:
                self.mosquitto_process.wait(timeout=5)
                print("Service Mosquitto arrêté avec succès.")
            except subprocess.TimeoutExpired:
                print("Le processus Mosquitto ne s'est pas arrêté, forçant l'arrêt...")
                self.mosquitto_process.kill()
        else:
            print("Le service Mosquitto n'est pas en cours d'exécution.")

    def _is_mosquitto_running(self):
        """Vérifie si le service Mosquitto est en cours d'exécution."""
        try:
            output = subprocess.check_output(["systemctl", "is-active", "mosquitto"]).decode().strip()
            return output == "active"
        except subprocess.CalledProcessError:
            return False

    def _get_mosquitto_path(self):
        """Obtient le chemin vers l'exécutable Mosquitto."""
        base_path = os.path.join(os.path.dirname(__file__), 'mosquitto')
        if self.system == "windows":
            return os.path.join(base_path, 'windows', self.architecture,'mosquitto.exe')
        elif self.system == "darwin":  # macOS
            return os.path.join(base_path, 'macos',self.architecture, 'mosquitto')
        elif self.system == "linux":  # Linux
            return os.path.join(base_path, 'linux', self.architecture, 'mosquitto')
        else:
            raise RuntimeErrror(f"Unsupported operating system: {self.system}")

    def _run_command(self, command, timeout=None, capture_output=False):
        """Exécute une commande système."""
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
                return result.stdout.strip()
            else:
                subprocess.run(command, shell=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            pass
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
            # Décodage du message MQTT
            payload = msg.payload.decode()
            # Extraction des valeurs
            data = payload.split(";")  # Séparer les paires "clé:valeur"
            values = {int(item.split(":")[0]): float(item.split(":")[1]) for item in data}

            # Condition sur les adresses
            if 84 in values:
                dist = values[84]
                print(f"L'adresse est 84, la distance est {dist}")
                self.message_callback(None, None, dist)

            if 85 in values:
                dist = values[85]
                print(f"L'adresse est 85, la distance est {dist}")
                self.message_callback(None, dist, None)

            if 86 in values:
                dist = values[86]
                print(f"L'adresse est 86, la distance est {dist}")
                self.message_callback(dist, None, None)
            else:
                print("Adresse non reconnue")
            # print(f"Données reçues: {payload}")
            # Traitement du message JSON
            # data = json.loads(payload)
            # indices = data.get("index", [])
            # values = data.get("values", [])
            # distances = dict(zip(indices, values))
            # Récupération des 3 positions
            # self.message_callback(distances.get("HG", None), distances.get("HD", None), distances.get("BM", None))
        except Exception as e:
            print(f"Erreur lors du traitement du message: {e}")
