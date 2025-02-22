import socket
import time
import random
import paho.mqtt.client as mqtt

# Configuration UDP
UDP_PORT = 12345
UDP_BROADCAST_IP = "255.255.255.255"
BUFFER_SIZE = 255

# Configuration MQTT
MQTT_TOPIC = "palet/rollerhockey"
MQTT_PORT = 1883
mqtt_server_ip = None
mqtt_client = mqtt.Client(client_id="palet", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)


# Variables de contrôle
ready_to_send_mqtt = False
mqtt_sending_active = False

# Simulation des ancres
anchors = [0x84, 0x85, 0x86]
lastDistances = [0.0, 0.0, 0.0]

# Fonction pour envoyer une requête UDP et attendre une IP
def request_mqtt_ip():
    global mqtt_server_ip, ready_to_send_mqtt
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(5)
    
    print("📤 Envoi de la requête UDP pour obtenir une IP...")
    sock.sendto(b"REQUEST_IP", (UDP_BROADCAST_IP, UDP_PORT))
    
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        response = data.decode("utf-8").strip()
        if response != "deconnect":
            mqtt_server_ip = response
            mqtt_client.connect(mqtt_server_ip, MQTT_PORT)
            ready_to_send_mqtt = True
            print(f"✅ MQTT IP configurée: {mqtt_server_ip}")
    except socket.timeout:
        print("⏳ Aucun serveur MQTT trouvé. Réessayer...")
    finally:
        sock.close()

# Fonction pour gérer les commandes UDP
def handle_udp_commands():
    global mqtt_sending_active, ready_to_send_mqtt
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", UDP_PORT))
    print(f"📡 Écoute des commandes UDP sur le port {UDP_PORT}...")
    
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        command = data.decode("utf-8").strip()
        
        if command == "deconnect":
            print("🚫 Signal de déconnexion reçu")
            mqtt_client.disconnect()
            ready_to_send_mqtt = False
            mqtt_sending_active = False
        elif command == "start":
            print("✅ Signal de démarrage reçu")
            mqtt_sending_active = True
        elif command == "stop":
            print("⏸ Signal d'arrêt reçu")
            mqtt_sending_active = False

# Fonction pour générer des distances aléatoires et envoyer MQTT
def send_mqtt_data():
    while True:
        if mqtt_sending_active and ready_to_send_mqtt:
            for i in range(3):
                lastDistances[i] = round(random.uniform(1.0, 5.0), 2)
            
            message = f"{anchors[0]}:{lastDistances[0]};{anchors[1]}:{lastDistances[1]};{anchors[2]}:{lastDistances[2]}"
            mqtt_client.publish(MQTT_TOPIC, message)
            print(f"📡 Données envoyées: {message}")
        time.sleep(1)

# Exécution du script
if __name__ == "__main__":
    request_mqtt_ip()
    handle_udp_commands()
    send_mqtt_data()
