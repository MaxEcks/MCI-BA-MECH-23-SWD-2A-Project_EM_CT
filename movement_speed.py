# movement_speed.py

import numpy as np
from mechanism import Mechanism
import matplotlib.pyplot as plt

# =============================================================
# Berechnung der max. Vorwärtsbewegung des Strandbeestbeins
# =============================================================
class StrandbeestSpeed:
    """ 
    Klasse zur Ermittlung der maximalen Vorwärtsbewegung eines Strandbeestbeins. 
    """
    def __init__(self, mechanism_id: str, joint_index: int, revolutions_per_minute: float, theta_range, trajectories, ground_contact_tolerance: float):
        
        if revolutions_per_minute <= 0:
            raise ValueError("Die Umdrehung pro Minute muss größer als 0 sein.")
        
        self.mechanism_id = mechanism_id
        self.joint_index = joint_index
        self.revolutions_per_minute = revolutions_per_minute
        self.theta_range = theta_range
        self.trajectories = trajectories
        self.ground_contact_tolerance = ground_contact_tolerance

        # omega in rad/s berechnen
        self.omega = (2 * np.pi * revolutions_per_minute) / 60

        if not self.trajectories:
            raise ValueError("Keine Kinematik Daten vorhanden.")
        
        # x und y Koordinaten aus der trajektion extrahieren
        self.x_values = np.array([frame[joint_index][0] for frame in self.trajectories])
        self.y_values = np.array([frame[joint_index][1] for frame in self.trajectories])

    def get_ground_contact_indices(self):
        """ Indizes finden, wo Bodenkontakt des Gelenks vorhanden ist + Toleranz. """
        # Minimale y-Hoehe ermitteln und Toleranz (Bodenkontakt) addieren
        y_min = np.min(self.y_values)
        ground_contact_level = y_min + self.ground_contact_tolerance
        # Indizes finden mit Bodenkontakt
        ground_contact_indices = np.where(self.y_values <= ground_contact_level)[0]
        
        if len(ground_contact_indices) == 0:
            raise ValueError("Kein Bodenkontakt erkannt.")
        
        return ground_contact_indices

    def calculate_stride_length(self, ground_contact_indices):
        """ Schrittlänge vom Strandbeestbein berechnen """
        # x Koordinaten während des Bodenkontakts
        x_ground_contact = self.x_values[ground_contact_indices]
        # Schrittweite berechnen
        x_max = np.max(x_ground_contact)
        x_min = np.min(x_ground_contact)
        stride_length = x_max - x_min

        if stride_length <= 0:
            raise ValueError("Keine effektive Vorwärtsbewegung möglich.")
        
        return stride_length, x_min, x_max

    def calculate_time_steps(self, ground_contact_indices, x_min, x_max):
        """ Anzahl der Zeitframes (N) zwischen x_min und x_max berechnen"""
        # Zeitindizes zwischen x_min und x_max finden
        valid_indices = []
        for idx in ground_contact_indices:
            if x_min <= self.x_values[idx] <= x_max:
                valid_indices.append(idx)
        N = len(valid_indices) 
        
        return N

    def calculate_max_speed(self):
        """ Berechnung der max Vorwärtsgeschwindigkeit eines bestimmten Gelenks """
        ground_contact_indices = self.get_ground_contact_indices()

        if len(ground_contact_indices) == 0:
            raise ValueError("Kein Bodenkontakt vorhanden.")
        
        stride_length, x_min, x_max = self.calculate_stride_length(ground_contact_indices)
        N = self.calculate_time_steps(ground_contact_indices, x_min, x_max)

        if N <= 0:
            raise ValueError("Keine Zeitschritte vorhanden.")
        #print(f"N = {N}")

        # Berechnung von delta_t
        delta_t = N * ((2*np.pi) / (self.omega * len(self.theta_range)))

        # Berechnung der maximalen Geschwindigkeit
        v_max = stride_length / delta_t

        return v_max, stride_length, delta_t

    def plot_ground_contact(self):
        """ Visualisierung der Bewegung des Gelenks als einzelne Punkte. Und der betrachteten Trajektorie für die Vorwärtsbewegung """
        ground_contact_indices = self.get_ground_contact_indices()

        fig, ax = plt.subplots(figsize=(8, 5))

        # Punkte für die gesamte Bewegung
        ax.scatter(self.x_values, self.y_values, s=25, color="blue", label="Trajektorie des Gelenks")

        # Bodenkontaktpunkte für die Vorwärtsbewegung
        ax.scatter(self.x_values[ground_contact_indices], 
                   self.y_values[ground_contact_indices], 
                   s=10, color="red", label="Bodenkontakt mit der angegebenen Toleranz", alpha=0.8)

        ax.set_xlabel("X-Koordinate")
        ax.set_ylabel("Y-Koordinate")
        ax.set_title(f"Visualisierung der Bodenkontaktpunkte")
        ax.legend()
        ax.grid()

        return fig 

# =========================================
# Test von der Bewegungsgeschwindigkeit
# =========================================
if __name__ == "__main__":
    mechanisms = Mechanism.find_all_mechanisms()
    strandbeest = [m for m in mechanisms if "Strandbeest" in m["name"]][0]
    if not strandbeest:
        print("Strandbeest nicht in der DB gefunden.")
    else:
        mechanism_id = strandbeest["id"]
        joint_index = 6                     # Beispiel Gelenk 6 betrachten (in unserem Fall das unterste Gelenk -> mit Bodenkontakt)
        revolutions_per_minute = 5          # Anzahl der Umdrehungen pro Minute
        ground_contact_tolerance = 0.1     # y_min plus diesen Abstand als Toleranz

        # Mechanismus aus DB laden
        mechanism = Mechanism.load_mechanism(mechanism_id)
        if not mechanism:
            print("Mechanismus konnte nicht geladen werden.")
        else:
            # Kinematik aus DB laden
            theta_range, trajectories = Mechanism.load_kinematics(mechanism_id, mechanism.version, steps=None)
            if not trajectories:
                print("Kinematik kann nicht geladen werden.")
            else:
                try:
                    strandbeest_vel = StrandbeestSpeed(mechanism_id, joint_index, revolutions_per_minute, theta_range, trajectories, ground_contact_tolerance)
                    v_max, stride_length, delta_t = strandbeest_vel.calculate_max_speed()
                    print(f"Max. Geschwindigkeit: {v_max:.2f}")
                    print(f"Schrittlänge: {stride_length:.2f}")
                    print(f"delta_t: {delta_t:.2f} s")

                    fig = strandbeest_vel.plot_ground_contact()
                    plt.show()
                except ValueError as e:
                    print(f"Fehler: {e}")