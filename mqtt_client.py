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

    # def on_message(self, client, userdata, msg):
    #     try:
    #         print("\n=== Message Reçu ===")
    #         payload = msg.payload.decode()
    #         print(f"Données reçues: {payload}")
            
    #         if msg.topic == "capteur/HG":
    #             self.message_callback(float(payload), None, None)
    #         elif msg.topic == "capteur/HD":
    #             self.message_callback(None, float(payload), None)
    #         elif msg.topic == "capteur/BM":
    #             self.message_callback(None, None, float(payload))

    #     except Exception as e:
    #         print(f"Erreur lors du traitement du message: {e}")

    def on_message(self, client, userdata, msg):
        try:
            print("\n=== Message Reçu ===")
            payload = msg.payload.decode()
            # print(f"Données reçues: {payload}")
            
            data = json.loads(payload)
            indices = data.get("index", [])
            values = data.get("values", [])
            distances = dict(zip(indices, values))
            # if msg.topic == "capteur/HG":
            #     self.message_callback(float(payload), None, None)
            # elif msg.topic == "capteur/HD":
            #     self.message_callback(None, float(payload), None)
            # elif msg.topic == "capteur/BM":
            #     self.message_callback(None, None, float(payload))


            self.message_callback(distances.get("HG", None), distances.get("HD", None), distances.get("BM", None))
        except Exception as e:
            print(f"Erreur lors du traitement du message: {e}")