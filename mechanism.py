import numpy as np
from scipy.optimize import least_squares
from database import DatabaseConnector
from tinydb import Query
import csv  

class Mechanism:
    def __init__(self, joints=[], links=[]):
        self.joints = joints
        self.links = links
        self.target_lengths = self.calculate_lengths()

    def calculate_lengths(self):
        #Berechnung der Länge zwischen den Gelenken
        lengths = []
        for link in self.links:
            i = link[0]
            j = link[1]

            joint1_x = self.joints[i]["x"]
            joint1_y = self.joints[i]["y"]
            joint2_x = self.joints[j]["x"]
            joint2_y = self.joints[j]["y"]
            
            length = np.sqrt((joint2_x - joint1_x)**2 + (joint2_y - joint1_y)**2)
            lengths.append(length)
        return lengths

    def error_function(self, positions, target_lengths):
        #Funktion zur Berechnung des Längenunterschieds
        array_index = 0

        for joint_index in range(len(self.joints)):
            joint = self.joints[joint_index]

            if joint["type"] != "Fixiert":
                joint["x"] = positions[array_index]
                joint["y"] = positions[array_index + 1]

                array_index = array_index + 2
        
        current_lengths = self.calculate_lengths()

        error = np.array(current_lengths) - np.array(target_lengths)

        return error 

    def optimization_function(self, target_lengths):
        #Funktion zur Optimierung der Position der beweglichen Gelenke
        free_joints = []
        for joint in self.joints:
            if joint["type"] != "Fixiert":
                free_joints.append(joint)

        positions = []
        for joint in free_joints:
            positions.append(joint["x"])
            positions.append(joint["y"])

        #Erstellung eines eindimensionales NumPy-Array
        initial_positions = np.array(positions)

        optimization = least_squares(self.error_function, initial_positions, args=(target_lengths,), method='dogbox')

        #optimiertes Ergebnis als Array
        result = optimization.x

        #Position der beweglichen Gelenke nach dem Optimieren aktualisieren
        array_index = 0
        for joint in self.joints:
            if joint["type"] != "Fixiert":
                joint["x"] = result[array_index]
                joint["y"] = result[array_index + 1]

                array_index = array_index + 2
        return True
    

    def kinematics(self, theta_range):
        #Berechnung der Kinematik des Mechanismus
        if len(self.joints) < 3:
            raise ValueError("Mechanismus unvollständig. Mindestens 3 Gelenke erforderlich.")
        
        trajectories = []
        target_lengths = self.calculate_lengths()

        for index, theta in enumerate(theta_range):
            for joint in self.joints:
                if joint["type"] == "Kreisbahnbewegung":
                    center_x = joint["center"][0]
                    center_y = joint["center"][1]
                    radius = joint["radius"]
                    joint["x"] = center_x + radius * np.cos(theta)
                    joint["y"] = center_y + radius * np.sin(theta)
                                
            self.optimization_function(target_lengths)
        
            #aktuelle Gelenkposition speichern
            current_positions = []
            for joint in self.joints:
                joint_position = (joint["x"], joint["y"])

                current_positions.append(joint_position)

            trajectories.append(current_positions)

        if len(trajectories) < len(theta_range):
            print(f"Warnung: Nur {len(trajectories)} von {len(theta_range)} Frames erfolgreich simuliert.")

        return trajectories


    def save_kinematics_to_csv(self, theta_range, trajectories, filename="Coords_results.csv"):
        
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file) 
            
            header = ["Theta (rad) | "] 
            for i in range(len(self.joints)):  
                header.append(f"Gelenk_{i+1}_x | ") 
                header.append(f"Gelenk_{i+1}_y | ")  
            writer.writerow(header) 
            
            for i in range(len(theta_range)):  
                row = [theta_range[i]] 
                for joint in trajectories[i]: 
                    row.append(joint[0])  
                    row.append(joint[1])  
                writer.writerow(row)  
            
        return filename 


class Database_editing:
    #Mechanismus speichern, laden und löschen
    db_connector = DatabaseConnector().get_table('mechanism_configurations')

    def save_configuration(self, config_name: str, joints: list, links: list) -> (str):
        Config = Query()
        result = self.db_connector.search(Config.name == config_name)
        if result:
            self.db_connector.update({'joints': joints, 'links': links})
            return f"Konfiguration upgedated"
        else:
            self.db_connector.insert({'name': config_name, 'joints': joints, 'links': links})
            return f"Konfiguration gespeichert"

    @classmethod
    def load_configuration(cls, config_name: str) -> tuple:
        Config = Query()
        result = cls.db_connector.get(Config.name == config_name)
        if result:
            joints = result.get("joints")
            links = result.get("links")
            return joints, links
        else:
            return {}

    @classmethod
    def find_all_configurations(cls) -> list:
        configurations = []
        for config in cls.db_connector.all():
            configuration_name = config["name"]
            configurations.append(configuration_name)
        return configurations

    def delete_configuration(self, config_name: str) -> str:
        Config = Query()
        result = self.db_connector.search(Config.name == config_name)
        if result:
            self.db_connector.remove(Config.name == config_name)
            return f"Konfiguration '{config_name}' erfolgreich gelöscht."
        else:
            return "Konfiguration nicht gefunden."
        