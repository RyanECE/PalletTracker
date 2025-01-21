# mqtt_client.py
import paho.mqtt.client as mqtt
import json
import time

class MQTTClient:
    def __init__(self, message_callback, connection_callback):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.message_callback = message_callback
        self.connection_callback = connection_callback

    def start_mqtt(self):
        try:
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
        """Arrêter proprement le client MQTT"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                time.sleep(0.1)  # Petit délai pour permettre la déconnexion
            
            if self.connection_callback:
                self.connection_callback(False)
                
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