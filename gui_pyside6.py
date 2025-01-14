import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit, QVBoxLayout, QWidget
import paho.mqtt.client as mqtt
import json

class RollerHockeyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Palet de Roller Hockey Connecté")
        
        # Créer un widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Créer un layout vertical
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Ajouter un titre
        self.title_label = QLabel("Suivi de la position du palet")
        self.title_label.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.title_label)

        # Ajouter une zone de texte pour afficher les messages
        self.message_area = QTextEdit()
        self.message_area.setReadOnly(True)
        self.layout.addWidget(self.message_area)

        # Initialiser le client MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Démarrer la connexion MQTT automatiquement
        self.start_mqtt()

    def start_mqtt(self):
        broker = "localhost"  # Remplacez par l'adresse IP locale de votre machine si nécessaire
        port = 1883
        self.mqtt_client.connect(broker, port)
        self.mqtt_client.loop_start()
        print("Connexion MQTT démarrée...")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connecté au broker MQTT")
            client.subscribe("capteurs/data")
            client.subscribe("capteurs/data1")
            client.subscribe("capteurs/data2")
            print("Abonné aux topics: capteurs/data, capteurs/data1, capteurs/data2")
        else:
            print(f"Échec de connexion, code: {rc}")

    def on_message(self, client, userdata, msg):
        print("\n=== Message Reçu ===")
        if msg.topic == "capteurs/data":
            message_prefix = "Message du publisher principal:"
        elif msg.topic == "capteurs/data1":
            message_prefix = "Message du publisher 1:"
        elif msg.topic == "capteurs/data2":
            message_prefix = "Message du publisher 2:"
        
        try:
            # Tentative de décodage JSON
            payload = json.loads(msg.payload.decode())
            message = f"{message_prefix} Données: {payload}\n"
        except json.JSONDecodeError:
            # Si ce n'est pas du JSON, affichage du message brut
            message = f"{message_prefix} Message: {msg.payload.decode()}\n"
        
        # Afficher le message dans la zone de texte
        self.message_area.append(message)  # Utiliser append pour QTextEdit

# Lancer l'application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RollerHockeyApp()
    window.show()
    sys.exit(app.exec())
