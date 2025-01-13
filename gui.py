import tkinter as tk
from mqtt_client import MQTTClient

class RollerHockeyApp:
    def __init__(self, root, mqtt_client):
        self.root = root
        self.root.title("Palet de Roller Hockey Connecté")
        self.mqtt_client = mqtt_client
        
        # Créer un canevas pour le terrain
        self.canvas = tk.Canvas(root, width=800, height=600, bg="lightgreen")
        self.canvas.pack()

        # Ajouter un titre
        self.title_label = tk.Label(root, text="Suivi de la position du palet", font=("Arial", 24))
        self.title_label.pack()

        # Ajouter un bouton pour démarrer la connexion MQTT
        self.start_button = tk.Button(root, text="Démarrer la connexion MQTT", command=self.start_mqtt)
        self.start_button.pack()

    def start_mqtt(self):
        self.mqtt_client.connect()
        print("Connexion MQTT démarrée...")
