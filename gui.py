import tkinter as tk
import paho.mqtt.client as mqtt
import json

class RollerHockeyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Palet de Roller Hockey Connecté")
        
        # Créer un canevas pour le terrain
        self.canvas = tk.Canvas(root, width=800, height=600, bg="lightgreen")
        self.canvas.pack()

        # Ajouter un titre
        self.title_label = tk.Label(root, text="Suivi de la position du palet", font=("Arial", 24))
        self.title_label.pack()

        # Ajouter un bouton pour démarrer la connexion MQTT
        self.start_button = tk.Button(root, text="Démarrer la connexion MQTT", command=self.start_mqtt)
        self.start_button.pack()

        # Ajouter une zone de texte pour afficher les messages
        self.message_area = tk.Text(root, height=10, width=80)
        self.message_area.pack()

        # Initialiser le client MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

    def start_mqtt(self):
        broker = "localhost"
        port = 1883
        self.mqtt_client.connect(broker, port)
        self.mqtt_client.loop_start()
        print("Connexion MQTT démarrée...")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connecté au broker MQTT")
            client.subscribe("capteurs/data")
            print("Abonné au topic: capteurs/data")
        else:
            print(f"Échec de connexion, code: {rc}")

    def on_message(self, client, userdata, msg):
        print("\n=== Message Reçu ===")
        print(f"Topic: {msg.topic}")
        try:
            # Tentative de décodage JSON
            payload = json.loads(msg.payload.decode())
            message = f"Données: {payload}\n"
        except json.JSONDecodeError:
            # Si ce n'est pas du JSON, affichage du message brut
            message = f"Message: {msg.payload.decode()}\n"
        
        # Afficher le message dans la zone de texte
        self.message_area.insert(tk.END, message)
        self.message_area.see(tk.END)  # Faire défiler vers le bas

# Lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = RollerHockeyApp(root)
    root.mainloop()
