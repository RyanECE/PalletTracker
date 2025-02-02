# terrain_config.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton

class TerrainDimensionsDialog(QDialog):
    def __init__(self, current_width: float, current_height: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dimensions du terrain")
        
        layout = QVBoxLayout()
        
        # Largeur
        width_layout = QHBoxLayout()
        width_label = QLabel("Largeur (m):")
        self.width_input = QDoubleSpinBox()
        self.width_input.setRange(10, 100)
        self.width_input.setValue(current_width)
        self.width_input.setDecimals(1)
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_input)
        layout.addLayout(width_layout)
        
        # Hauteur
        height_layout = QHBoxLayout()
        height_label = QLabel("Hauteur (m):")
        self.height_input = QDoubleSpinBox()
        self.height_input.setRange(5, 50)
        self.height_input.setValue(current_height)
        self.height_input.setDecimals(1)
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_input)
        layout.addLayout(height_layout)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Annuler")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connexions
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)


class TerrainConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TerrainConfig, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.width = 40.0
        self.height = 20.0
        self.observers = []
    
    def set_dimensions(self, width: float, height: float):
        self.width = width
        self.height = height
        self._notify_observers()
    
    def add_observer(self, observer):
        self.observers.append(observer)
    
    def _notify_observers(self):
        for observer in self.observers:
            observer.on_terrain_dimensions_changed(self.width, self.height)

    @property
    def center_x(self):
        return self.width / 2

    @property
    def center_y(self):
        return self.height / 2