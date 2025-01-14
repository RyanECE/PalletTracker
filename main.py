import tkinter as tk
from gui import RollerHockeyApp

if __name__ == "__main__":
    root = tk.Tk()
    app = RollerHockeyApp(root)  # No need to pass an MQTT client here
    root.mainloop()
