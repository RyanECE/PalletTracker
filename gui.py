import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QTextEdit, 
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout,
    QMessageBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Signal, QObject, Slot
from mqtt_client import MQTTClient
from udp_discovery import UDPDiscoveryServer
from hockey_rink import HockeyRink
import json
import socket
import threading

class SignalManager(QObject):
    esp32_discovered = Signal(str, str)  # device_name, mac_address

class ESPListItem(QWidget):
    def __init__(self, device_name, mac_address, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.mac_address = mac_address
        self.is_connected = False
        self.is_sending = False
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        self.setLayout(layout)
        
        info_label = QLabel(f"{device_name} ({mac_address})")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        self.connect_button = QPushButton("Connecter")
        self.connect_button.setFixedWidth(100)
        layout.addWidget(self.connect_button)
        
        self.send_button = QPushButton("Démarrer")
        self.send_button.setFixedWidth(80)
        self.send_button.setEnabled(False)
        layout.addWidget(self.send_button)

class RollerHockeyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.d1 = None
        self.d2 = None
        self.d3 = None
        self.setWindowTitle("Palet de Roller Hockey Connecté")
        self.mqtt_client = None
        self.is_connected = False
        self.discovery_server = None
        self.esp_widgets = {}
        
        # Créer le gestionnaire de signaux
        self.signal_manager = SignalManager()
        self.signal_manager.esp32_discovered.connect(self.on_esp32_discovered)
        
        self._init_ui()
        self._start_discovery_server()
        
    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        # Titre
        self.title_label = QLabel("Suivi de la position du palet")
        self.title_label.setStyleSheet("font-size: 24px; margin: 10px;")
        self.layout.addWidget(self.title_label)
        
        # Terrain de hockey
        self.hockey_rink = HockeyRink()
        self.layout.addWidget(self.hockey_rink)
        
        # Bouton de test
        # test_button = QPushButton("Tester position aléatoire")
        # test_button.clicked.connect(self.test_random_position)
        # self.layout.addWidget(test_button)

        # Contrôles MQTT
        mqtt_container = QWidget()
        mqtt_layout = QVBoxLayout(mqtt_container)  
        mqtt_layout.setContentsMargins(10, 10, 10, 10)

        # Status et boutons sur la même ligne
        status_button_layout = QHBoxLayout()

        # Status
        self.status_label = QLabel("Status: Déconnecté")
        self.status_label.setStyleSheet("color: red;")
        status_button_layout.addWidget(self.status_label)
            
        status_button_layout.addStretch()

        # Boutons MQTT
        self.start_button = QPushButton("Démarrer MQTT")
        self.start_button.clicked.connect(self.start_mqtt)
        status_button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Arrêter MQTT")
        self.stop_button.clicked.connect(self.stop_mqtt)
        self.stop_button.setEnabled(False)
        status_button_layout.addWidget(self.stop_button)

        mqtt_layout.addLayout(status_button_layout)
        self.layout.addWidget(mqtt_container)

        # Liste des ESP32 avec titre
        devices_container = QWidget()
        devices_layout = QVBoxLayout(devices_container)
        devices_layout.setContentsMargins(10, 10, 10, 10)
        
        self.esp_list_label = QLabel("ESP32 détectés:")
        self.esp_list_label.setStyleSheet("font-weight: bold;")
        devices_layout.addWidget(self.esp_list_label)
        
        self.esp_list = QListWidget()
        self.esp_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)
        devices_layout.addWidget(self.esp_list)
        self.layout.addWidget(devices_container)

    def update_puck_position(self, d1=None, d2=None, d3=None):
        if d1 is not None:
            self.d1 = d1
        if d2 is not None:
            self.d2 = d2
        if d3 is not None:
            self.d3 = d3

        print(f"Données reçues HG: {self.d1}")
        print(f"Données reçues HD: {self.d2}")
        print(f"Données reçues BM: {self.d3}")
        if self.d1 is not None and self.d2 is not None and self.d3 is not None:
            try:
                self.hockey_rink.update_from_distances(self.d1, self.d2, self.d3)
            except Exception as e:
                print(f"Erreur lors de la mise à jour de la position du palet: {str(e)}")

    def update_message_area(self, message):
        """Mettre à jour la zone de message"""
        try:
            self.message_area.append(message)
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la zone de message: {e}")

    def show_error(self, title, message):
        """Afficher une boîte de dialogue d'erreur"""
        QMessageBox.critical(self, title, message)

    def _start_discovery_server(self):
        """Démarrer le serveur de découverte UDP"""
        def discovery_callback(device_name, mac_address):
            # Émettre le signal depuis le thread UDP
            self.signal_manager.esp32_discovered.emit(device_name, mac_address)
            
        self.discovery_server = UDPDiscoveryServer(discovery_callback)
        self.discovery_server.start()

    @Slot(str, str)

    def start_mqtt(self):
        """Démarrer le client MQTT"""
        try:
            if self.mqtt_client is None:
                self.mqtt_client = MQTTClient(
                message_callback=self.update_puck_position,
                    connection_callback=self.connection_status_changed
                )
                self.mqtt_client.start_mqtt()
                self.message_area.append("Démarrage du client MQTT...\n")

                # Démarrer MQTT dans un thread séparé
                thread = threading.Thread(target=self.mqtt_handler.run, daemon=True)
                thread.start()

                print("MQTT démarré via le bouton.")
        except Exception as e:
            self.show_error("Erreur de démarrage", f"Impossible de démarrer le client MQTT: {str(e)}")
            self.mqtt_client = None
            self.connection_status_changed(False)

    def stop_mqtt(self):
        """Arrêter le client MQTT"""
        if self.mqtt_client:
            try:
                self.mqtt_client.stop_mqtt()
                self.mqtt_client = None
                self.message_area.append("Client MQTT arrêté\n")
                self.connection_status_changed(False)
            except Exception as e:
                self.show_error("Erreur d'arrêt", f"Erreur lors de l'arrêt du client MQTT: {str(e)}")

    def connection_status_changed(self, connected):
        """Mise à jour de l'interface selon l'état de la connexion"""
        try:
            self.is_connected = connected
            
            # Mettre à jour les boutons
            self.start_button.setEnabled(not connected)
            self.stop_button.setEnabled(connected)
            
            # Mettre à jour le label de status
            if connected:
                self.status_label.setText("Status: Connecté")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("Status: Déconnecté")
                self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.show_error("Erreur lors de la mise à jour du statut", str(e))

    def on_esp32_discovered(self, device_name: str, mac_address: str):
        """Callback appelé quand un nouvel ESP32 est découvert (exécuté dans le thread principal)"""
        if mac_address not in self.esp_widgets:
            # Créer le widget pour l'ESP
            esp_widget = ESPListItem(device_name, mac_address)
            
            # Connexion des signaux des boutons
            esp_widget.connect_button.clicked.connect(
                lambda checked, esp=esp_widget, mac=mac_address: 
                self.handle_esp_connect(mac, not esp.is_connected)
            )
            esp_widget.send_button.clicked.connect(
                lambda checked, esp=esp_widget, mac=mac_address: 
                self.handle_esp_send(mac, not esp.is_sending)
            )
            
            # Créer l'item de liste
            item = QListWidgetItem()
            item.setSizeHint(esp_widget.sizeHint())
            self.esp_list.addItem(item)
            self.esp_list.setItemWidget(item, esp_widget)
            
            # Stocker le widget
            self.esp_widgets[mac_address] = esp_widget

    def handle_esp_connect(self, mac_address: str, should_connect: bool):
        """Gère la connexion/déconnexion d'un ESP32"""
        try:
            esp_widget = self.esp_widgets[mac_address]
            
            if should_connect:
                # Obtenir l'IP locale
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    s.connect(('8.8.8.8', 80))
                    local_ip = s.getsockname()[0]
                finally:
                    s.close()

                # Créer le message avec uniquement l'IP
                message = {
                    'broker_ip': local_ip
                }
                print(f"Envoi de l'IP {local_ip} à l'ESP32 {mac_address}")
                
                # Envoyer l'IP à l'ESP32 via UDP
                if self.discovery_server.send_response(mac_address, message):
                    # Mettre à jour l'interface seulement si l'envoi a réussi
                    esp_widget.is_connected = True
                    esp_widget.connect_button.setText("Déconnecter")
                    esp_widget.connect_button.setStyleSheet("background-color: #ffcccc;")
                    esp_widget.send_button.setEnabled(True)
                    self.message_area.append(f"IP {local_ip} envoyée à l'ESP32 {mac_address}\n")
                else:
                    self.message_area.append(f"Erreur: Impossible d'envoyer l'IP à l'ESP32 {mac_address}\n")
            else:
                esp_widget.is_connected = False
                esp_widget.connect_button.setText("Connecter")
                esp_widget.connect_button.setStyleSheet("")
                esp_widget.send_button.setEnabled(False)
                esp_widget.is_sending = False
                esp_widget.send_button.setText("Démarrer")
                esp_widget.send_button.setStyleSheet("")
                self.message_area.append(f"ESP32 {mac_address} déconnecté\n")
                
        except Exception as e:
            self.show_error("Erreur de contrôle", f"Erreur lors de la gestion de la connexion: {str(e)}")
            print(f"Erreur détaillée: {str(e)}")

    def handle_esp_send(self, mac_address: str, should_send: bool):
        """Gère l'autorisation d'envoi des données"""
        try:
            if not self.mqtt_client:
                print("MQTT client n'est pas initialisé")
                self.message_area.append("Erreur: Le client MQTT n'est pas démarré. Démarrez d'abord le serveur MQTT.\n")
                return

            esp_widget = self.esp_widgets[mac_address]
            esp_widget.is_sending = should_send
            
            # Format du message modifié pour correspondre à ce qu'attend l'ESP32
            message = {
                'start_data': should_send
            }
            
            print(f"Envoi du message MQTT à {mac_address}: {message}")
            
            # Envoi de la commande via MQTT
            result = self.mqtt_client.mqtt_client.publish(
                f"control/{mac_address}",
                json.dumps(message)
            )
            
            # Vérifier si l'envoi a réussi
            if result.rc == 0:
                print("Message MQTT envoyé avec succès")
                
                # Mise à jour de l'interface
                if should_send:
                    esp_widget.send_button.setText("Arrêter")
                    esp_widget.send_button.setStyleSheet("background-color: #ffcccc;")
                    self.message_area.append(f"Démarrage de l'envoi des données pour {mac_address}\n")
                else:
                    esp_widget.send_button.setText("Démarrer")
                    esp_widget.send_button.setStyleSheet("")
                    self.message_area.append(f"Arrêt de l'envoi des données pour {mac_address}\n")
            else:
                print(f"Échec de l'envoi MQTT avec code: {result.rc}")
                self.message_area.append(f"Erreur lors de l'envoi de la commande (code {result.rc})\n")
                
        except Exception as e:
            error_msg = f"Erreur lors de la commande d'envoi: {str(e)}"
            print(f"Erreur détaillée: {error_msg}")
            self.show_error("Erreur de contrôle", error_msg)


    def closeEvent(self, event):
        """Gérer la fermeture propre de l'application"""
        try:
            if self.mqtt_client:
                self.stop_mqtt()
            if self.discovery_server:
                self.discovery_server.stop()
            event.accept()
        except Exception as e:
            self.show_error("Erreur de fermeture", f"Erreur lors de la fermeture de l'application: {str(e)}")
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Application du style
    app.setStyle("Fusion")
    window = RollerHockeyApp()
    window.show()
    sys.exit(app.exec())