import serial
import serial.tools.list_ports as port_list

ser = None  # Variable globale pour maintenir la connexion

def detect_serial_port() -> str:
    """Détecte le premier port série disponible."""
    ports = list(port_list.comports())
    
    if not ports:
        raise Exception("Aucun port série détecté.")
    
    # Cherche d'abord un port Arduino
    for port in ports:
        if "usbserial" in port.device.lower():
            return port.device
            
    raise Exception("Aucun port série détecté.")

def init_serial():
   global ser
   if ser is None:
       port = detect_serial_port()
       ser = serial.Serial(port, 115200, timeout=1)

def send_position(x: float, y: float):
   global ser
   try:
       init_serial()
       message = f"X{x}Y{y}\n"
       print(message)
       ser.write(message.encode())
       line = ser.readline().decode('utf-8').rstrip()
       print(line)
   except Exception as e:
       print(f"Erreur: {e}")
