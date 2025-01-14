import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
        # Souscription aux topics
        client.subscribe("capteurs/data")
        client.subscribe("capteurs/data1")
        client.subscribe("capteurs/data2")
        print("Abonné aux topics: capteurs/data, capteurs/data1, capteurs/data2")
    else:
        print(f"Échec de connexion, code: {rc}")

def on_message(client, userdata, msg):
    print("\n=== Message Reçu ===")
    if msg.topic == "capteurs/data":
        print("Message du publisher principal:")
    elif msg.topic == "capteurs/data1":
        print("Message du publisher 1:")
    elif msg.topic == "capteurs/data2":
        print("Message du publisher 2:")
    
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
broker = "localhost"  # Remplacez par l'adresse IP locale de votre machine si nécessaire
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
