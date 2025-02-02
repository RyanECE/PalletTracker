# hockey_rink.py
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from puck_position import PuckPositionCalculator

class HockeyRink(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Dimensions réelles du terrain en mètres
        self.real_width = 40.0
        self.real_height = 20.0
        # Marges en pixels pour le dessin
        self.margin = 9
        
        # Position du palet en mètres
        self.puck_x = self.real_width / 2
        self.puck_y = self.real_height / 2
        
        # Taille du palet
        self.puck_size = 0.5 * (self.real_width / 40.0)
        
        # Positions des capteurs
        self.sensors = [
            (0, 20),    # Capteur 1: haut gauche
            (40, 20),   # Capteur 2: haut droite
            (20, 0)     # Capteur 3: bas milieu
        ]
        
        # Calculateur de position
        self.position_calculator = PuckPositionCalculator()
        
        # Définir une taille minimum pour le widget
        self.setMinimumSize(600, 400)

    def update_from_distances(self, d1: float, d2: float, d3: float):
        """Met à jour la position du palet à partir des distances des capteurs"""
        if self.position_calculator.validate_distances(d1, d2, d3):
            position = self.position_calculator.calculate_position(d1, d2, d3)
            if position:
                x, y = position
                self.set_puck_position(x, y)
                return True
        return False

    def set_puck_position(self, x: float, y: float):
        """Met à jour la position du palet (en mètres)"""
        self.puck_x = x
        self.puck_y = y

        # Notifier le callback si présent
        if self.position_callback:
            self.position_callback(x, y)

        self.update()  # Redessiner le widget

    def get_scale(self):
        """Calcule l'échelle de dessin actuelle"""
        scale_x = (self.width() - 2 * self.margin) / self.real_width
        scale_y = (self.height() - 2 * self.margin) / self.real_height
        return min(scale_x, scale_y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        scale = self.get_scale()
        
        # Calculer les dimensions du terrain en pixels
        rink_width = self.real_width * scale
        rink_height = self.real_height * scale
        
        # Centrer le terrain
        x = (self.width() - rink_width) / 2
        y = (self.height() - rink_height) / 2
        
        # Dessiner le terrain
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        
        # Rectangle principal (bandes)
        rink_rect = QRect(int(x), int(y), int(rink_width), int(rink_height))
        painter.drawRect(rink_rect)
        
        # Ligne centrale
        center_x = x + rink_width / 2
        painter.drawLine(int(center_x), int(y), int(center_x), int(y + rink_height))
        
        # Cercle central
        circle_diameter = 9 * (self.real_width / 40.0) * scale
        circle_x = center_x - circle_diameter / 2
        circle_y = y + (rink_height - circle_diameter) / 2
        painter.drawEllipse(int(circle_x), int(circle_y), int(circle_diameter), int(circle_diameter))
        
        # Zones de but
        goal_width = 5.5 * (self.real_width / 40.0) * scale
        goal_height = 4.5 * (self.real_width / 40.0) * scale
        painter.drawRect(int(x), int(y + (rink_height - goal_height) / 2), 
                        int(goal_width), int(goal_height))
        painter.drawRect(int(x + rink_width - goal_width), int(y + (rink_height - goal_height) / 2),
                        int(goal_width), int(goal_height))

        # Dessiner les capteurs (points rouges)
        painter.setBrush(QBrush(QColor(255, 0, 0)))  # Rouge
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        sensor_size = 10  # Taille en pixels des points des capteurs
        
        for sensor_pos in self.sensors:
            sensor_x, sensor_y = sensor_pos
            # Convertir les coordonnées des capteurs
            pixel_x = x + sensor_x * scale
            pixel_y = y + (self.real_height - sensor_y) * scale  # Inversion de Y
            painter.drawEllipse(
                int(pixel_x - sensor_size/2),
                int(pixel_y - sensor_size/2),
                sensor_size,
                sensor_size
            )
        
        # Dessiner le palet
        puck_pixel_x = x + self.puck_x * scale
        puck_pixel_y = y + (self.real_height - self.puck_y) * scale  # Inversion de Y
        puck_pixel_size = self.puck_size * scale
        
        painter.setBrush(QBrush(QColor(0, 0, 0)))  # Noir
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawEllipse(
            int(puck_pixel_x - puck_pixel_size/2),
            int(puck_pixel_y - puck_pixel_size/2),
            int(puck_pixel_size),
            int(puck_pixel_size)
        )
