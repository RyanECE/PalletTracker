import sys
import math
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QPainter, QPen, QColor
from paho.mqtt import client as mqtt_client

class RollerHockeyField(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 400)  # Échelle: 1m = 20px
        
        # Position du palet (initialement au centre)
        self.puck_pos = QPoint(400, 200)
        
        # Position des capteurs (en pixels)
        self.sensor1_pos = QPoint(0, 0)  # Haut gauche
        self.sensor2_pos = QPoint(800, 0)  # Haut droite
        self.sensor3_pos = QPoint(400, 400)  # Milieu bas
        
        # État du drag & drop
        self.dragging = False
        
        # Configuration MQTT
        self.mqtt_setup()
        
        # Labels pour afficher les distances
        self.distance_label = QLabel(self)
        self.distance_label.setStyleSheet("background-color: white;")
        self.distance_label.move(10, 10)
        
        # Timer pour l'envoi périodique
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.send_position)
        self.timer.start(100)  # Envoie toutes les 100ms
        
    def mqtt_setup(self):
        self.client = mqtt_client.Client(client_id="ESP32-HG", protocol=mqtt_client.MQTTv311)
        self.client.on_connect = self.on_connect
        try:
            self.client.connect("localhost", 1883)
            self.client.loop_start()
        except Exception as e:
            print(f"Erreur de connexion MQTT: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connecté au broker MQTT!")
        else:
            print(f"Erreur de connexion MQTT, code: {rc}")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Dessiner le terrain (blanc)
        painter.fillRect(0, 0, 800, 400, QColor(255, 255, 255))
        
        # Dessiner les capteurs (rouge)
        painter.setPen(QPen(Qt.red, 10))
        painter.drawPoint(self.sensor1_pos)
        painter.drawPoint(self.sensor2_pos)
        painter.drawPoint(self.sensor3_pos)
        
        # Dessiner le palet (noir)
        painter.setPen(QPen(Qt.black, 20))
        painter.drawPoint(self.puck_pos)
    
    def mousePressEvent(self, event):
        # Vérifier si le clic est proche du palet
        if self.is_near_puck(event.pos()):
            self.dragging = True
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            # Mettre à jour la position du palet
            self.puck_pos = self.constrain_to_field(event.pos())
            self.update()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
    
    def is_near_puck(self, pos):
        # Vérifier si le clic est à moins de 20 pixels du centre du palet
        return self.calculate_distance(pos, self.puck_pos) < 20
    
    def constrain_to_field(self, pos):
        # Garantir que le palet reste dans les limites du terrain
        x = max(0, min(pos.x(), self.width()))
        y = max(0, min(pos.y(), self.height()))
        return QPoint(x, y)
    
    def send_position(self):
        # Calculer les distances réelles (en mètres)
        d1 = self.calculate_distance(self.puck_pos, self.sensor1_pos) / 20  # Conversion pixels vers mètres
        d2 = self.calculate_distance(self.puck_pos, self.sensor2_pos) / 20
        d3 = self.calculate_distance(self.puck_pos, self.sensor3_pos) / 20
        
        # Afficher les distances
        self.distance_label.setText(f"Distances (m):\nCapteur 1: {d1:.2f}\nCapteur 2: {d2:.2f}\nCapteur 3: {d3:.2f}")
        
        # Envoyer via MQTT
        payload = f"84:{d3:.2f};85:{d2:.2f};86:{d1:.2f}"
        try:
            self.client.publish("palet/rollerhockey", payload)
            print(f"Envoyé: {payload}")
        except Exception as e:
            print(f"Erreur d'envoi MQTT: {e}")
    
    def calculate_distance(self, p1, p2):
        return math.sqrt((p1.x() - p2.x())**2 + (p1.y() - p2.y())**2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulateur de terrain de roller hockey")
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout
        layout = QVBoxLayout(central_widget)
        
        # Terrain
        self.field = RollerHockeyField()
        layout.addWidget(self.field)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())