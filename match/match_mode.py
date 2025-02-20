import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QSpinBox, QDialog, QSizePolicy,QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient

class MatchConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration du Match")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Équipe 1
        team1_layout = QHBoxLayout()
        team1_label = QLabel("Équipe 1:")
        self.team1_input = QLineEdit()
        team1_layout.addWidget(team1_label)
        team1_layout.addWidget(self.team1_input)
        layout.addLayout(team1_layout)
        
        # Équipe 2
        team2_layout = QHBoxLayout()
        team2_label = QLabel("Équipe 2:")
        self.team2_input = QLineEdit()
        team2_layout.addWidget(team2_label)
        team2_layout.addWidget(self.team2_input)
        layout.addLayout(team2_layout)
        
        # Durée du match
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Durée (minutes):")
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 60)
        self.duration_input.setValue(20)  # Valeur par défaut
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_input)
        layout.addLayout(duration_layout)
        
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

class HockeyRinkHeatmap(QWidget):
    def __init__(self, positions, parent=None):
        super().__init__(parent)
        self.positions = positions
        self.setMinimumSize(600, 400)
        
        # Dimensions réelles du terrain en mètres
        self.real_width = 40.0
        self.real_height = 20.0
        self.margin = 20
        
        # Créer une grille pour la heatmap
        self.grid_cols = 80  # Une cellule tous les 0.5 mètres
        self.grid_rows = 40
        self.intensity_grid = np.zeros((self.grid_rows, self.grid_cols))
        
        # Calculer la heatmap
        self._calculate_heatmap()

    def _calculate_heatmap(self):
        if len(self.positions) > 0:
            positions = np.array(self.positions)
            
            # Pour chaque position, calculer son influence sur la grille
            for x, y in positions:
                # S'assurer que x et y sont dans les limites
                x = max(0, min(x, self.real_width))
                y = max(0, min(y, self.real_height))
                
                # Convertir les coordonnées en indices de grille
                grid_x = int((x / self.real_width) * (self.grid_cols - 1))
                grid_y = int((y / self.real_height) * (self.grid_rows - 1))
                
                # Rayon d'influence en cellules
                influence_radius = 5
                
                # Appliquer une influence gaussienne autour du point
                for dy in range(-influence_radius, influence_radius + 1):
                    for dx in range(-influence_radius, influence_radius + 1):
                        nx = grid_x + dx
                        ny = grid_y + dy
                        
                        # Vérifier les limites avant d'accéder à la grille
                        if 0 <= nx < self.grid_cols and 0 <= ny < self.grid_rows:
                            # Calculer la distance au point en unités de grille
                            distance = np.sqrt(dx*dx + dy*dy)
                            # Influence gaussienne qui diminue avec la distance
                            if distance <= influence_radius:
                                intensity = np.exp(-0.3 * (distance * distance))
                                self.intensity_grid[ny, nx] += intensity
            
            # Normaliser la grille
            if self.intensity_grid.max() > 0:
                self.intensity_grid = self.intensity_grid / self.intensity_grid.max()

    def get_color(self, value):
        if value == 0:
            return QColor(0, 0, 0, 0)
        
        colors = [
            (0.0, QColor(0, 0, 255, 100)),     # Bleu plus transparent
            (0.3, QColor(0, 255, 0, 130)),     # Vert
            (0.6, QColor(255, 255, 0, 160)),   # Jaune
            (0.8, QColor(255, 128, 0, 180)),   # Orange
            (1.0, QColor(255, 0, 0, 200))      # Rouge
        ]
        
        for i in range(len(colors)-1):
            if colors[i][0] <= value <= colors[i+1][0]:
                t = (value - colors[i][0]) / (colors[i+1][0] - colors[i][0])
                c1 = colors[i][1]
                c2 = colors[i+1][1]
                
                return QColor(
                    int(c1.red() * (1-t) + c2.red() * t),
                    int(c1.green() * (1-t) + c2.green() * t),
                    int(c1.blue() * (1-t) + c2.blue() * t),
                    int(c1.alpha() * (1-t) + c2.alpha() * t)
                )
        return colors[-1][1]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculer l'échelle
        scale_x = (self.width() - 2 * self.margin) / self.real_width
        scale_y = (self.height() - 2 * self.margin) / self.real_height
        scale = min(scale_x, scale_y)
        
        # Dimensions et position du terrain en pixels
        rink_width = self.real_width * scale
        rink_height = self.real_height * scale
        x = (self.width() - rink_width) / 2
        y = (self.height() - rink_height) / 2
        
        # Dessiner les éléments du terrain d'abord
        self._draw_rink_base(painter, x, y, rink_width, rink_height)
        
        # Appliquer le clipping avant de dessiner la heatmap
        painter.setClipRect(int(x), int(y), int(rink_width), int(rink_height))
        
        # Dessiner la heatmap
        cell_width = rink_width / self.grid_cols
        cell_height = rink_height / self.grid_rows
        
        # Parcourir la grille pour dessiner la heatmap
        for i in range(self.grid_rows):
            for j in range(self.grid_cols):
                value = self.intensity_grid[i, j]
                if value > 0.05:  # Seuil minimum pour éviter le bruit
                    color = self.get_color(value)
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.PenStyle.NoPen)
                    
                    rect_x = x + (j * cell_width)
                    rect_y = y + (i * cell_height)
                    # Taille plus grande pour assurer le chevauchement et la fluidité
                    painter.drawEllipse(
                        int(rect_x - cell_width/2),
                        int(rect_y - cell_height/2),
                        int(cell_width * 2),
                        int(cell_height * 2)
                    )
        
        # Désactiver le clipping
        painter.setClipping(False)
        
        # Redessiner les bordures du terrain
        self._draw_rink_borders(painter, x, y, rink_width, rink_height, scale)
        
        # Dessiner la légende
        self._draw_legend(painter)

    def _draw_rink_base(self, painter, x, y, rink_width, rink_height):
        # Fond blanc du terrain
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(int(x), int(y), int(rink_width), int(rink_height))

    def _draw_rink_borders(self, painter, x, y, rink_width, rink_height, scale):
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Rectangle principal
        painter.drawRect(int(x), int(y), int(rink_width), int(rink_height))
        
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

    def _draw_legend(self, painter):
        legend_width = 200
        legend_height = 20
        legend_x = self.width() - legend_width - 20
        legend_y = self.height() - legend_height - 20
        
        gradient = QLinearGradient(legend_x, 0, legend_x + legend_width, 0)
        gradient.setColorAt(0.0, QColor(0, 0, 255, 100))
        gradient.setColorAt(0.3, QColor(0, 255, 0, 130))
        gradient.setColorAt(0.6, QColor(255, 255, 0, 160))
        gradient.setColorAt(0.8, QColor(255, 128, 0, 180))
        gradient.setColorAt(1.0, QColor(255, 0, 0, 200))
        
        painter.fillRect(legend_x, legend_y, legend_width, legend_height, gradient)
        painter.drawRect(legend_x, legend_y, legend_width, legend_height)
        
        painter.drawText(legend_x, legend_y - 5, "Fréquence de passage")
        painter.drawText(legend_x, legend_y + legend_height + 15, "Faible")
        painter.drawText(legend_x + legend_width - 40, legend_y + legend_height + 15, "Élevé")

class HeatmapDialog(QDialog):
    def __init__(self, positions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Heatmap du Match")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Création du widget de heatmap
        self.heatmap_widget = HockeyRinkHeatmap(positions)
        layout.addWidget(self.heatmap_widget)
        
        # Bouton fermer
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.setLayout(layout)

class MatchMode(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.match_running = False
        self.match_paused = False
        self.halftime_shown = False
        self.positions = []
        self.score1 = 0
        self.score2 = 0
        
        self._init_ui()
        
        # Timer pour le match
        self.match_timer = QTimer()
        self.match_timer.timeout.connect(self._on_match_time_update)
        self.remaining_seconds = 0
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 0)
        
        # En-tête du match
        match_header = QWidget()
        match_header.setMinimumHeight(150)  # Augmenté la hauteur minimale
        match_header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_layout = QHBoxLayout(match_header)
        header_layout.setContentsMargins(0, 0, 0, 20)
        
        # Style pour les textes
        big_font = "font-size: 24px; font-weight: bold;"
        score_font = "font-size: 36px; font-weight: bold;"
        score_button_style = """
            QPushButton {
                font-size: 14px;
                padding: 5px 15px;
                min-width: 30px;
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        
        # Équipe 1
        team1_widget = QWidget()
        team1_layout = QVBoxLayout(team1_widget)
        self.team1_label = QLabel("-")
        self.team1_label.setStyleSheet(big_font)
        self.team1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Boutons pour équipe 1
        self.team1_plus_button = QPushButton("+1")
        self.team1_minus_button = QPushButton("-1")
        self.team1_plus_button.setStyleSheet(score_button_style)
        self.team1_minus_button.setStyleSheet(score_button_style)
        self.team1_plus_button.setEnabled(False)
        self.team1_minus_button.setEnabled(False)
        
        team1_layout.addWidget(self.team1_label)
        team1_layout.addWidget(self.team1_plus_button)
        team1_layout.addWidget(self.team1_minus_button)
        team1_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Widget central pour le temps et le score
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        self.score_label = QLabel("0 - 0")
        self.score_label.setStyleSheet(score_font)
        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet(big_font)
        center_layout.addWidget(self.score_label)
        center_layout.addWidget(self.time_label)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Équipe 2
        team2_widget = QWidget()
        team2_layout = QVBoxLayout(team2_widget)
        self.team2_label = QLabel("-")
        self.team2_label.setStyleSheet(big_font)
        self.team2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Boutons pour équipe 2
        self.team2_plus_button = QPushButton("+1")
        self.team2_minus_button = QPushButton("-1")
        self.team2_plus_button.setStyleSheet(score_button_style)
        self.team2_minus_button.setStyleSheet(score_button_style)
        self.team2_plus_button.setEnabled(False)
        self.team2_minus_button.setEnabled(False)
        
        team2_layout.addWidget(self.team2_label)
        team2_layout.addWidget(self.team2_plus_button)
        team2_layout.addWidget(self.team2_minus_button)
        team2_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Ajouter les trois sections à l'en-tête avec des espaces
        header_layout.addWidget(team1_widget)
        header_layout.addStretch()
        header_layout.addWidget(center_widget)
        header_layout.addStretch()
        header_layout.addWidget(team2_widget)
        
        layout.addWidget(match_header)
        
        # Boutons de contrôle en bas
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Nouveau Match")
        self.pause_button = QPushButton("Pause")
        self.heatmap_button = QPushButton("Voir Heatmap")
        self.pause_button.setEnabled(False)
        self.heatmap_button.setEnabled(False)
        
        # Style des boutons de contrôle
        control_button_style = """
            QPushButton {
                font-size: 16px;
                padding: 8px 16px;
                min-width: 120px;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        
        self.start_button.setStyleSheet(control_button_style)
        self.pause_button.setStyleSheet(control_button_style)
        self.heatmap_button.setStyleSheet(control_button_style)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.heatmap_button)
        layout.addLayout(control_layout)
        
        self.setLayout(layout)
        
        # Connexions
        self.start_button.clicked.connect(self._on_start_match)
        self.pause_button.clicked.connect(self._on_pause_match)
        self.heatmap_button.clicked.connect(self._show_heatmap)
        self.team1_plus_button.clicked.connect(self._increment_team1_score)
        self.team1_minus_button.clicked.connect(self._decrement_team1_score)
        self.team2_plus_button.clicked.connect(self._increment_team2_score)
        self.team2_minus_button.clicked.connect(self._decrement_team2_score)

    def _increment_team1_score(self):
        self.score1 += 1
        self._update_total_score()
    
    def _decrement_team1_score(self):
        if self.score1 > 0:
            self.score1 -= 1
            self._update_total_score()
    
    def _increment_team2_score(self):
        self.score2 += 1
        self._update_total_score()
    
    def _decrement_team2_score(self):
        if self.score2 > 0:
            self.score2 -= 1
            self._update_total_score()
    
    def _update_total_score(self):
        self.score_label.setText(f"{self.score1} - {self.score2}")
    
    def _update_time_label(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _on_pause_match(self):
        if self.match_running and not self.match_paused:
            # Mettre en pause
            self.match_paused = True
            self.match_timer.stop()
            self.pause_button.setText("Reprendre")
            self.main_app.stop_mqtt()  # Arrêter le suivi

            # Envoyer le signal "stop" à l'ESP32
            if self.main_app.discovery_server:
                esp32_addr, esp32_ip = self.main_app.discovery_server.get_last_esp32()
                if esp32_addr:
                    self.main_app.discovery_server.send_response(esp32_ip, "stop")
            
            # Centrer le palet
            self.main_app.hockey_rink.set_puck_position(20, 10)
        else:
            # Reprendre
            self.match_paused = False
            self.match_timer.start(1000)
            self.pause_button.setText("Pause")
            self.main_app.start_mqtt()  # Reprendre le suivi

            # Envoyer le signal "start" à l'ESP32
            if self.main_app.discovery_server:
                esp32_addr, esp32_ip = self.main_app.discovery_server.get_last_esp32()
                if esp32_addr:
                    self.main_app.discovery_server.send_response(esp32_ip, "start")
    
    def _show_halftime_message(self):
        msg = QMessageBox()
        msg.setWindowTitle("Mi-temps")
        msg.setText("C'est la mi-temps !")
        msg.setIcon(QMessageBox.Information)
        msg.exec()
        # Mettre en pause automatiquement
        if not self.match_paused:
            self._on_pause_match()

    def _on_match_time_update(self):
        self.remaining_seconds -= 1
        self._update_time_label()
        
        # Vérifier si c'est la mi-temps
        total_time = self.total_match_time if hasattr(self, 'total_match_time') else 1200
        if not self.halftime_shown and self.remaining_seconds == total_time // 2:
            self.halftime_shown = True
            self._show_halftime_message()
        
        if self.remaining_seconds <= 0:
            self._end_match()

    def _on_start_match(self):
        if not self.match_running:
            dialog = MatchConfigDialog(self)
            if dialog.exec():
                # Configuration du match
                self.team1_label.setText(dialog.team1_input.text())
                self.team2_label.setText(dialog.team2_input.text())
                self.remaining_seconds = dialog.duration_input.value() * 60
                self.total_match_time = self.remaining_seconds
                self.halftime_shown = False
                
                # Réinitialiser les scores
                self.score1 = 0
                self.score2 = 0
                self._update_total_score()
                
                # Démarrer le match
                self.match_running = True
                self.match_paused = False
                self.positions = []
                self.start_button.setText("Arrêter le Match")
                self.heatmap_button.setEnabled(False)
                self.pause_button.setEnabled(True)
                self.pause_button.setText("Pause")
                
                # Activer les boutons de score
                self.team1_plus_button.setEnabled(True)
                self.team1_minus_button.setEnabled(True)
                self.team2_plus_button.setEnabled(True)
                self.team2_minus_button.setEnabled(True)
                
                # Démarrer le timer
                self._update_time_label()
                self.match_timer.start(1000)
                
                # Démarrer le suivi du palet
                self.main_app.start_mqtt()
                
                # Envoyer le signal "start" à l'ESP32
                if self.main_app.discovery_server:
                    esp32_addr, esp32_ip = self.main_app.discovery_server.get_last_esp32()
                    if esp32_addr:
                        self.main_app.discovery_server.send_response(esp32_ip, "start")
                
                # Connexion au callback de position
                self.main_app.hockey_rink.position_callback = self._on_puck_position
        else:
            self._end_match()

    def _end_match(self):
        self.match_running = False
        self.match_paused = False
        self.match_timer.stop()
        self.start_button.setText("Nouveau Match")
        self.heatmap_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText("Pause")
        
        # Désactiver les boutons de score
        self.team1_plus_button.setEnabled(False)
        self.team1_minus_button.setEnabled(False)
        self.team2_plus_button.setEnabled(False)
        self.team2_minus_button.setEnabled(False)
        
        # Arrêter le suivi du palet
        self.main_app.stop_mqtt()

        # Envoyer le signal "stop" à l'ESP32
        if self.main_app.discovery_server:
            esp32_addr, esp32_ip = self.main_app.discovery_server.get_last_esp32()
            if esp32_addr:
                self.main_app.discovery_server.send_response(esp32_ip, "stop")
        
        # Déconnecter le callback de position
        self.main_app.hockey_rink.position_callback = None
        
        # Reset du palet au centre
        self.main_app.hockey_rink.set_puck_position(20, 10)

    def _on_puck_position(self, x, y):
        if self.match_running and not self.match_paused:
            self.positions.append([x, y])

    def _show_heatmap(self):
        dialog = HeatmapDialog(self.positions, self)
        dialog.exec()