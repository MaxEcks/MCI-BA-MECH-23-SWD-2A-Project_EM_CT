import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
import tempfile

class Visualizer:
    #Visualisierung der Konfiguration und Simulation der Konfigurationen

    @staticmethod
    def plot_configuration(joints, links, ax=None):
        #Darstellung der Konfiguration
        if ax is None:
            ax = plt.subplots()
  
        #Gelenke darstellen
        for index, joint in enumerate(joints):
            x_pos = joint["x"]
            y_pos = joint["y"]
            ax.plot(x_pos, y_pos, 'o', label=f"Gelenk {index + 1}")

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


    @staticmethod
    def create_gif(trajectories, links, filename="simulation.gif"):
        #Erstellen der Animation
        fig, ax = plt.subplots()
        trajectories = np.array(trajectories)

        x_paths = []
        y_paths = []

        def update(t):
            ax.clear()
            ax.set_title(f"Simulation - Zeitpunkt {t + 1}")
            ax.axis("equal")
            ax.set_xlabel("x")
            ax.set_ylabel("y")

            current_positions = trajectories[t]
            x_current = current_positions[:, 0]
            y_current = current_positions[:, 1]
            
            #Bahn der Gelenke
            x_paths.append(x_current)
            y_paths.append(y_current)
            ax.plot(x_paths, y_paths, 'r-', linewidth=1)

            #Verbindungen zwischen den Gelenken
            for joint1, joint2 in links:
                x_coords = x_current[[joint1, joint2]]
                y_coords = y_current[[joint1, joint2]]
                ax.plot(x_coords, y_coords, 'b-', linewidth=2)
            
            #Gelenke
            for i in range(len(current_positions)):
                x, y = current_positions[i]
                ax.plot(x, y, 'o', label=f"Gelenk {i + 1}")
            
            if ax.get_legend_handles_labels()[1]:
                ax.legend()

        #Animation erstellen
        animation = FuncAnimation(fig, update, frames=range(len(trajectories)))

        #temporäre Datei erstellen
        temp_file = tempfile.NamedTemporaryFile(suffix=".gif", delete=False)
        animation.save(temp_file.name, writer=PillowWriter(fps=10))

        return temp_file.name

