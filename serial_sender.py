import serial
import serial.tools.list_ports as port_list

def detect_serial_port() -> str:
    """Détecte le premier port série disponible."""
    ports = list(port_list.comports())
    print(ports)
    if not ports:
        raise Exception("Aucun port série détecté.")
    return ports[0].device

def send_position(x: float, y: float):
    """Envoie les coordonnées x, y via le port série."""
    try:
        port = detect_serial_port()  # Détection automatique du port
        baud_rate = 115200            # Vitesse de communication
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            message = f"X{x}Y{y}\n"
            print(message)
            ser.write(message.encode())  # Envoi des données encodées en bytes
            print(f"Données envoyées : {message}")
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
    except Exception as e:
        print(f"Erreur lors de l'envoi des données : {e}")
