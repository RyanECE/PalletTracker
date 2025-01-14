import sys
from PySide6.QtWidgets import QApplication
from gui_pyside6 import RollerHockeyApp

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Créer l'instance QApplication en premier
    window = RollerHockeyApp()
    window.show()
    sys.exit(app.exec())
