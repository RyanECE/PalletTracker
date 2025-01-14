# subscriber.py
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
        # Souscription au topic
        client.subscribe("capteurs/data")
        print("Abonné au topic: capteurs/data")
    else:
        print(f"Échec de connexion, code: {rc}")

def on_message(client, userdata, msg):
    print("\n=== Message Reçu ===")
    print(f"Topic: {msg.topic}")
    try:
        # Tentative de décodage JSON
        payload = json.loads(msg.payload.decode())
        print(f"Données: {payload}")
    except json.JSONDecodeError:
        # Si ce n'est pas du JSON, affichage du message brut
        print(f"Message: {msg.payload.decode()}")
    print("==================\n")

# Création du client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Configuration de la connexion
broker = "localhost"
port = 1883

# Connexion au broker
print(f"Connexion au broker {broker}...")
client.connect(broker, port)

# Démarrage de la boucle de réception
try:
    print("En attente de messages... (Ctrl+C pour quitter)")
    client.loop_forever()
except KeyboardInterrupt:
    print("\nArrêt du récepteur...")
    client.disconnect()
    print("Déconnecté du broker")