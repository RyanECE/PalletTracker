import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port, topic):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        self.client.subscribe(self.topic)

    def on_connect(self, client, userdata, flags, rc):
        print("Connecté avec le code de résultat: " + str(rc))

    def on_message(self, client, userdata, msg):
        print(f"Message reçu: {msg.payload.decode()} sur le topic {msg.topic}")

    def publish(self, message):
        self.client.publish(self.topic, message)
