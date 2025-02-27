# visualization.py

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
import tempfile

class Visualizer:
# ===============================================================================================
# Darstellung der aktuellen Konfiguration 
# ===============================================================================================
    @staticmethod
    def plot_configuration(joints, links, ax=None):
        
        if ax is None:
            ax = plt.subplots()
  
        #Gelenke darstellen
        for index, joint in enumerate(joints):
            x_pos = joint["x"]
            y_pos = joint["y"]
            ax.plot(x_pos, y_pos, 'o', label=f"Gelenk {index + 1}")

            if joint["type"] == "Kreisbahnbewegung" and joint["center"]:
                center_x = joint["center"][0]
                center_y = joint["center"][1]
                radius = joint["radius"]

                theta = np.linspace(0, 2 * np.pi, 100)
                circle_x = center_x + radius * np.cos(theta)
                circle_y = center_y + radius * np.sin(theta)

                ax.plot(circle_x, circle_y, 'g--', linewidth=1)

        #Verbindungen darstellen
        for link in links:
            joint1_index = link[0]
            joint2_index = link[1]

            joint1 = joints[joint1_index]
            joint2 = joints[joint2_index]

            x_coords = [joint1["x"], joint2["x"]]
            y_coords = [joint1["y"], joint2["y"]]

            ax.plot(x_coords, y_coords, 'b-', linewidth=2, label=f"Verbindung {joint1_index + 1}-{joint2_index + 1}")

        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.axis("equal")

        if ax.get_legend_handles_labels()[1]:
            ax.legend()

        return ax

# ===============================================================================================
# Die Trajektionen animieren, um ein GIF zu erstellen 
# ===============================================================================================
    @staticmethod
    def create_gif(thetas, trajectories, joints, links, filename="simulation.gif"):
        #Erstellen der Animation
        fig, ax = plt.subplots()
        trajectories = np.array(trajectories)

        # Maximalen x und y Werte der Trajectorien herausfinden, um einen Abstand zum Bildrand zu ermöglichen
        x_coords = trajectories[:, :, 0]
        y_coords = trajectories[:, :, 1]
        x_min_traj = np.min(x_coords)
        x_max_traj = np.max(x_coords)
        y_min_traj = np.min(y_coords)
        y_max_traj = np.max(y_coords)

        x_range = x_max_traj - x_min_traj
        y_range = y_max_traj - y_min_traj

        scaling_factor = 0.1
        x_min = x_min_traj - x_range * scaling_factor
        x_max = x_max_traj + x_range * scaling_factor
        y_min = y_min_traj - y_range * scaling_factor
        y_max = y_max_traj + y_range * scaling_factor

        x_paths = []
        y_paths = []

        def update(t):
            ax.clear()
            ax.set_title(f"Simulation - Zeitpunkt {t + 1}")
            ax.set_aspect("equal")
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)

            current_positions = trajectories[t]
            x_current = current_positions[:, 0]
            y_current = current_positions[:, 1]
            
            # aktuellen Winkel in Grad anzeigen
            current_theta_rad = thetas[t]
            current_theta_degree = np.degrees(current_theta_rad)
            ax.text(x_min+0.1, y_max-0.1,     # linke, obere Ecke
                    f"Drehwinkel: {current_theta_degree:.2f}°", 
                    horizontalalignment='left',
                    verticalalignment='top',
                    fontsize='small'
                    )

            #Bahn der Gelenke
            x_paths.append(x_current)
            y_paths.append(y_current)
            ax.plot(x_paths, y_paths, 'r-', linewidth=1)

            #Verbindungen zwischen den Gelenken zeichnen
            for link in links:
                try:
                    # Ermittlung der Indizes der Gelenke in der ursprünglichen Liste
                    index_start = joints.index(link.start_joint)
                    index_end = joints.index(link.end_joint)
        
                except ValueError:
                    continue

                # Holen der aktuellen Positionen der verbundenen Gelenke
                start_pos = current_positions[index_start]
                end_pos = current_positions[index_end]
                ax.plot([start_pos[0], end_pos[0]], [start_pos[1], end_pos[1]], 'b-', linewidth=2)

            # Zeichnen der Gelenke
            for i, pos in enumerate(current_positions):
                ax.plot(pos[0], pos[1], 'o', label=f"Gelenk {i + 1}" if t == 0 else "")
            
            # Erstellung einer Legende
            if ax.get_legend_handles_labels()[1]:
                ax.legend()

        #Animation erstellen über die Frames
        animation = FuncAnimation(fig, update, frames=range(len(trajectories)))

        # temporäre Datei erstellen zum speichern
        temp_file = tempfile.NamedTemporaryFile(suffix=".gif", delete=False)
        animation.save(temp_file.name, writer=PillowWriter(fps=10))

        return temp_file.name

# ===============================================================================================
# Test für die Visualisierung - Mechanismus wird aus der DB geladen und simuliert
# ===============================================================================================
if __name__ == "__main__":

    from mechanism import Mechanism

    # Beispiel zum Testen von plot_configuration().
    joints = [
        {"x": 0, "y": 0, "type": "Fixiert", "center": None, "radius": None},
        {"x": 0.25, "y": 0.1, "type": "Kreisbahnbewegung", "center": [0, 0], "radius": 0.26925824},
        {"x": 2.0, "y": 2.0, "type": "Frei beweglich", "center": None, "radius": None},
        {"x": 2.0, "y": 0, "type": "Fixiert", "center": None, "radius": None}
    ]

    links = [
        (0, 1),
        (1, 2),
        (2, 3)
    ]

    fig, ax = plt.subplots() 
    Visualizer.plot_configuration(joints, links, ax=ax)
    plt.title("Test: Mechanismus Konfiguration")
    plt.show()

    mechanisms = Mechanism.find_all_mechanisms()

    if not mechanisms:
        print("Keine Mechanismen in der Datenbank gefunden.")
    else:
        # Als Beispiel wird der erste eingetragene Mechanismus geladen
        mechanism_info = mechanisms[1]
        print("Gefundener Mechanismus:", mechanism_info["name"], "ID=", mechanism_info["id"], "Version=", mechanism_info["version"])

        mechanism = Mechanism.load_mechanism(mechanism_info["id"])
        if mechanism is None:
            print("Mechanismus konnte nicht geladen werden")
        else:
            # Laden der Kinematik-Daten der ausgwaehlten Konfiguration
            thetas, trajectories = Mechanism.load_kinematics(mechanism.id, mechanism.version, steps=None)
            if trajectories is None:
                print("Keine Kinematik gefunden oder Kinematik ist veraltet")
            else:
                gif_filename = Visualizer.create_gif(thetas, trajectories, mechanism.joints, mechanism.links)
                print("GIF gespeichert unter:", gif_filename)