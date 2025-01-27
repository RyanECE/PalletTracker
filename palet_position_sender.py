import socket

udp_ip = "esp32-device.local"  # Utilisez le nom mDNS de l'ESP32
udp_port = 4210  # Le port UDP sur lequel l'ESP32 écoute

def send_position(x: float, y: float):
    try:
        message = f"X{x}Y{y}\n"
        print(f"Envoi du message : {message}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), (udp_ip, udp_port))
        sock.close()
    except Exception as e:
        print(f"Erreur : {e}")