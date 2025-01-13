import tkinter as tk
from gui import RollerHockeyApp
from mqtt_client import MQTTClient

if __name__ == "__main__":
    root = tk.Tk()
    mqtt_client = MQTTClient("broker.hivemq.com", 1883, "roller_hockey/palet")
    app = RollerHockeyApp(root, mqtt_client)
    root.mainloop()
