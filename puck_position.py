import math
import serial.tools.list_ports
from typing import Tuple, Optional
import numpy as np
from palet_position_sender import send_position
class PuckPositionCalculator:
    def __init__(self):
        # Position des capteurs (x, y) en mètres
        self.sensor1_pos = (0, 20)    # Capteur en haut à gauche
        self.sensor2_pos = (40, 20)    # Capteur en bas à droite
        self.sensor3_pos = (20, 0)   # Capteur au milieu

    def calculate_position(self, d1: float, d2: float, d3: float) -> Optional[Tuple[float, float]]:
        """Calcule la position du palet par trilatération"""
        try:
            # Position des capteurs
            x1, y1 = self.sensor1_pos
            x2, y2 = self.sensor2_pos
            x3, y3 = self.sensor3_pos
            
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
            
            # Résoudre le système par la méthode des moindres carrés
            AT_A = A.T @ A
            AT_b = A.T @ b
            
            # Ajouter un petit terme de régularisation pour éviter la singularité
            epsilon = 1e-10
            AT_A = AT_A + epsilon * np.eye(2)
            
            # Résoudre le système
            solution = np.linalg.solve(AT_A, AT_b)
            x, y = solution
            
            
            # Si la solution est hors limites, projeter sur les bords du terrain
            x = max(0, min(40, x))
            y = max(0, min(20, y))
            # Envoyer les données via le port série
            send_position(int(x), int(y))
            return x, y

        except Exception as e:
            print(f"Erreur lors du calcul de la position: {e}")
            # En cas d'erreur, retourner une position par défaut au centre
            return 20, 10

    def validate_distances(self, d1: float, d2: float, d3: float) -> bool:
        """Vérifie si les distances sont physiquement possibles"""
        # Vérifier les limites max avec une petite marge de tolérance
        max_d12 = math.sqrt(40*40 + 40*40) + 0.1  # Diagonale + marge
        max_d3 = math.sqrt(20*20 + 20*20) + 0.1   # Distance max au centre + marge
        
        if d1 < 0 or d2 < 0 or d3 < 0:
            return False
            
        if d1 > max_d12 or d2 > max_d12 or d3 > max_d3:
            return False
            
        return True
