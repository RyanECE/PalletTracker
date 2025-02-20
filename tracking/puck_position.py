import math
import numpy as np
from typing import Tuple, Optional
from networking.palet_position_sender import send_position, send_taille_terrain
from gui.terrain_config import TerrainConfig

class PuckPositionCalculator:
    def __init__(self):
        # Position des capteurs (x, y) en mètres
        self.config = TerrainConfig()
        self.config.add_observer(self)
        self._update_sensors()
        self.camera_tracking_enabled = False
        
    def set_camera_tracking(self, enabled: bool):
        """Active ou désactive le suivi caméra"""
        self.camera_tracking_enabled = enabled
        if enabled:
            # Envoyer les dimensions du terrain lors de l'activation
            send_taille_terrain(40, 20)

    def _update_sensors(self):
        self.sensor1_pos = (0, self.config.height)
        self.sensor2_pos = (self.config.width, self.config.height)
        self.sensor3_pos = (self.config.center_x, 0)

    def on_terrain_dimensions_changed(self, width, height):
        self._update_sensors()
        if self.camera_tracking_enabled:
            send_taille_terrain(width, height)

    def calculate_position(self, d1: float, d2: float, d3: float) -> Optional[Tuple[float, float]]:
        """Calcule la position du palet par trilatération"""
        try:
            # Position des capteurs
            x1, y1 = self.sensor1_pos
            x2, y2 = self.sensor2_pos
            x3, y3 = self.sensor3_pos
            
            # Vérifier si les distances sont valides
            if not all(isinstance(d, (int, float)) for d in [d1, d2, d3]) or \
            any(math.isnan(d) for d in [d1, d2, d3]) or \
            any(d <= 0 for d in [d1, d2, d3]):
                print(f"Distances invalides : d1={d1}, d2={d2}, d3={d3}")
                return self.config.center_x, self.config.center_y
            
            # Carrés des distances
            d1_sq = d1 * d1
            d2_sq = d2 * d2
            d3_sq = d3 * d3
            
            # Constantes pour simplifier les équations
            k1 = (x1*x1 + y1*y1 - d1_sq)
            k2 = (x2*x2 + y2*y2 - d2_sq)
            k3 = (x3*x3 + y3*y3 - d3_sq)
            
            # Résolution du système d'équations
            A = np.array([
                [2*(x2-x1), 2*(y2-y1)],
                [2*(x3-x1), 2*(y3-y1)]
            ])
            
            b = np.array([k2 - k1, k3 - k1])
            
            # Vérifier le conditionnement de la matrice A
            if np.linalg.cond(A) > 1e10:  # Si le conditionnement est trop grand
                print("Matrice mal conditionnée")
                return self.config.center_x, self.config.center_y
            
            # Résoudre le système de manière plus robuste
            try:
                solution = np.linalg.lstsq(A, b, rcond=None)[0]
                x, y = solution
                
                # Vérifier si la solution est valide
                if np.any(np.isnan([x, y])) or np.any(np.isinf([x, y])):
                    print("Solution invalide (NaN ou Inf)")
                    return self.config.center_x, self.config.center_y
                
                # Limiter les coordonnées aux dimensions du terrain
                x = max(0, min(self.config.width, x))
                y = max(0, min(self.config.height, y))
                
                # N'envoyer la position que si le suivi caméra est activé
                if self.camera_tracking_enabled:
                    send_position(int(x), int(y))
                
                print(f"X:{round(x, 2)}, Y:{round(y, 2)}")
                return x, y

            except np.linalg.LinAlgError as e:
                print(f"Erreur dans la résolution du système : {e}")
                return self.config.center_x, self.config.center_y

        except Exception as e:
            print(f"Erreur lors du calcul de la position: {e}")
            return self.config.center_x, self.config.center_y

    def validate_distances(self, d1: float, d2: float, d3: float) -> bool:
        """Vérifie si les distances sont physiquement possibles"""
        max_d12 = math.sqrt(self.config.width**2 + self.config.height**2) + 0.1
        max_d3 = math.sqrt(self.config.center_x**2 + self.config.center_y**2) + 0.1
        
        if d1 < 0 or d2 < 0 or d3 < 0:
            return False
            
        if d1 > max_d12 or d2 > max_d12 or d3 > max_d3:
            return False
            
        return True

    def reset_to_center(self):
        """Réinitialise la position au centre"""
        if self.camera_tracking_enabled:
            send_position(self.config.center_x, self.config.center_y)