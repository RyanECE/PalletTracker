import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
    else:
        print(f"Échec de connexion, code: {rc}")

# Création du client
client = mqtt.Client()
client.on_connect = on_connect

# Configuration de la connexion
broker = "Ptracker.local"
port = 1883
topic = "capteurs/data2"  # Topic pour le deuxième publisher

# Connexion au broker
client.connect(broker, port)
client.loop_start()

try:
    print(f"Envoi de messages au topic: {topic}")
    print("Tapez 'quit' pour quitter")
    
    while True:
        message = input("Entrez votre message: ")
        if message.lower() == 'quit':
            break
            
        try:
            # Tentative de conversion en JSON si le message est au format dict
            data = eval(message)
            if isinstance(data, dict):
                message = json.dumps(data)
        except:
            # Si ce n'est pas un dict valide, on envoie le message tel quel
            pass
            
        client.publish(topic, message)
        print(f"Message envoyé: {message}")

except KeyboardInterrupt:
    print("\nArrêt de l'émetteur...")

finally:
    client.loop_stop()
    client.disconnect()
    print("Déconnecté du broker")
