import time
import json
import random
import socket
from paho.mqtt import client as mqtt_client

# Configuration Wi-Fi
SSID = "Virus"
PASSWORD = "e8f8e0bb"

# Configuration MQTT
MQTT_SERVER = "172.20.10.2"  # IP fixe du broker Mosquitto
# MQTT_SERVER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "pallet/rollerhockey"
MQTT_CLIENT_ID = "ESP32-HG"

# Simulation de la connexion Wi-Fi
def setup_wifi(ssid, password):
    print(f"Connexion au Wi-Fi '{ssid}'...")
    time.sleep(2)  # Simule le délai de connexion
    # Obtenir une IP fictive
    ip_address = socket.gethostbyname(socket.gethostname())
    print(f"Connecté ! IP de l'ESP32 : {ip_address}")
    return ip_address

# Callback lors de la connexion au broker MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT !")
    else:
        print(f"Erreur de connexion MQTT, code : {rc}")

# Callback pour la déconnexion
def on_disconnect(client, userdata, rc):
    print("Déconnecté du broker MQTT.")

# Callback pour les messages reçus (si nécessaire dans le futur)
def on_message(client, userdata, message):
    print(f"Message reçu sur le topic {message.topic}: {message.payload.decode()}")

# Création du client MQTT
def setup_mqtt():
    client = mqtt_client.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt_client.MQTTv311)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    return client

# Envoi des données simulées
def send_mqtt_data(client, topic):
    distance1 = round(random.uniform(0, 5.305), 2)  # Génère un nombre aléatoire entre 0 et 40.78, arrondi à deux décimales
    distance2 = round(random.uniform(0, 5.305), 2)  # Génère un nombre aléatoire entre 0 et 40.78, arrondi à deux décimales
    distance3 = round(random.uniform(0, 5.305), 2)  # Génère un nombre aléatoire entre 0 et 40.78, arrondi à deux décimales
    distances = {
        "HG" : distance1,
        "HD" : distance2,
        "BM" : distance3
    }
    payload = json.dumps({"index" : list(distances.keys()), "values" : list(distances.values())})
    result = client.publish(topic, payload)  # Convertit la distance en chaîne de caractères avant de l'envoyer
    status = result[0]  # Statut de la publication (0 = succès)

    if status == 0:
        print(f"Distance publiée avec succès : {distance1}")
    else:
        print(f"Échec de publication de la distance : {distance1}")

# Diffusion UDP
def broadcast_udp():
    import socket

    # Définir l'adresse MAC pour ce simulateur
    mac_address = "00:1A:2B:3C:4D:5E"

    # Créer un socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Envoyer la diffusion UDP
    message = f"ESP32-1,{mac_address}"
    sock.sendto(message.encode(), ("<broadcast>", 12345))  # Port de diffusion
    print(f"Diffusion envoyée : {message}")

    sock.close()

if __name__ == "__main__":
    # Simuler la configuration Wi-Fi
    setup_wifi(SSID, PASSWORD)

    # Configurer et connecter le client MQTT
    client = setup_mqtt()
    print("Connexion au broker MQTT...")
    client.connect(MQTT_SERVER, MQTT_PORT)

    # Boucle principale
    client.loop_start()
    try:
        while True:
            send_mqtt_data(client, MQTT_TOPIC)
            time.sleep(2)  # Simule un envoi toutes les 2 secondes
    except KeyboardInterrupt:
        print("\nArrêt de l'émulateur ESP32.")
    finally:
        client.loop_stop()
        client.disconnect()
