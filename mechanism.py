# mechanism.py

import numpy as np
from scipy.optimize import least_squares
from database import DatabaseConnector
from tinydb import Query
import networkx as nx # zur Validierung der Konnektivität des Mechanismus
import uuid # zur Generierung von eindeutiger Mechanismus-ID
import csv  

# =================================================================================================
# Joint und Link Klassen
# =================================================================================================
class Joint:
    """
    Repräsentiert ein einzelnes Gelenk.
    """
    def __init__(self, x = 0.0, y = 0.0, joint_type = "Frei beweglich", center = None, radius = None):
        self.x = x
        self.y = y
        self.type = joint_type  # "Fixiert", "Frei beweglich", "Kreisbahnbewegung"
        self.center = center    # [x, y] Koordinaten des Drehpunkts (nur für Kreisbahnbewegung)
        self.radius = radius    # Radius der Kreisbahn (nur für Kreisbahnbewegung)

    def __repr__(self):
        return f"Joint(x={self.x:.2f}, y={self.y:.2f}, type={self.type})"

    def __eq__(self, other):
        # Vergleich von Joint-Objekten (zwei Joints sind gleich, wenn alle Attribute gleich sind)
        if not isinstance(other, Joint):
            return False
        return (
            self.x == other.x 
            and self.y == other.y 
            and self.type == other.type 
            and self.center == other.center
            and self.radius == other.radius
        )

class Link:
    """
    Repräsentiert eine Verbindung zwischen zwei Joint-Objekten.
    length = feste Soll-Länge (wird aus der Startkonfiguration abgeleitet)
    """
    def __init__(self, start_joint: Joint, end_joint: Joint, length = None, protected = False):
        self.start_joint = start_joint
        self.end_joint = end_joint
        self.length = length
        self.protected = protected
    
    def __repr__(self):
        l_str = f"{self.length:.2f}" if self.length is not None else "None"
        return f"Link(start={self.start_joint}, end={self.end_joint}, length={l_str})"

    def __eq__(self, other):
        # Vergleich von Link-Objekten (zwei Links sind gleich, wenn alle Attribute gleich sind)
        if not isinstance(other, Link):
            return False
        return (
            self.start_joint == other.start_joint 
            and self.end_joint == other.end_joint 
            and self.length == other.length
            and self.protected == other.protected
        )

# =================================================================================================
# Mechanismus Validierung
# =================================================================================================
def mechanism_is_valid(joints: list, links: list):
    """
    Prüft:
    - mindestens vier Gelenke
    - genau zwei fixierte Gelenke
    - genau ein Gelenk mit Kreisbahnbewegung
    - Freiheitsgrad-Bedingung F = 2n - 2f - 2k - (g - 1) = 0
    - Graphen-Konnektivität: alle Gelenke sind zusammenhängend
    """
    # ---------------------------------------------------------
    # 1) Basischecks
    # ---------------------------------------------------------
    n = len(joints)
    if n < 4:
        return False, "Konfiguration ungültig: Mindestens 4 Gelenke erforderlich."

    f = sum(j.type == "Fixiert" for j in joints)
    if f != 2:
        return False, "Konfiguration ungültig: Es müssen genau 2 Gelenke fixiert sein."

    k = sum(j.type == "Kreisbahnbewegung" for j in joints)
    if k != 1:
        return False, "Konfiguration ungültig: Es muss genau 1 Gelenk eine Kreisbahnbewegung sein."
    
    # ---------------------------------------------------------
    # 2) Freiheitsgrad-Check
    # ---------------------------------------------------------
    g = len(links)  # Anzahl Links
    # abgewandelte Grübler-Formel (für unsere Anforderungen):
    F = 2 * n - 2 * f - 2 * k - (g - 1) # (g - 1), weil Verbindung zwischen Drehmittelpunkt und Kreisbahngelenk mit angelegt wird
    if F != 0:
        return False, f"Konfiguration ungültig: Freiheitsgrad F = {F} (erwartet: 0)."
    
    # ---------------------------------------------------------
    # 3) Graphen-Konnektivität prüfen
    # ---------------------------------------------------------
    # Graph mit NetworkX aufbauen
    # Python Objekte sind nicht hashbar, daher werden Indizes verwendet
    G = nx.Graph()
    # Gelenke (Index) als Knoten hinzufügen
    for i, j in enumerate(joints):
        G.add_node(i)
    # Gestelle / Links basierend auf Indizes der Gelenke als Kanten hinzufügen
    for link in links:
        start_idx = joints.index(link.start_joint)
        end_idx = joints.index(link.end_joint)
        G.add_edge(start_idx, end_idx)

    # Konnektivität prüfen
    if not nx.is_connected(G):
        return False, "Konfiguration ungültig: Mechanismus ist nicht zusammenhängend."
    
    # ---------------------------------------------------------
    # Wenn alle Checks bestanden sind, ist der Mechanismus gültig
    # ---------------------------------------------------------
    return True, "Gültiger Mechanismus"

# =================================================================================================
# Mechanism Klasse (Kinematik und Datenbank-Methoden)
# =================================================================================================
class Mechanism:
    """
    - Hat eine ID (UUID) und eine Versions-Nummer (int).
    - Nutzt Joint- und Link-Objekte.
    - Kann Mechanismus-Konfiguration in 'mechanism_configurations' speichern/laden.
    - Kann Mechanismus-Kinematik in 'mechanism_kinematics' speichern/laden.
    """
    def __init__(self, name = "", joints = None, links = None, mechanism_id = None, version = None):
        self.name = name
        self.joints = joints if joints else []  # Liste von Joint-Objekten
        self.links = links if links else []     # Liste von Link-Objekten

        # ID und Versions-Logik:
        self.id = mechanism_id  # wenn mechanism_id None ist, wird diese beim Speichern generiert (save_mechanism())
        self.version = version if version is not None else 1 # Versionsnummer (int) für Mechanismus-Änderungen 

        # Berechnung der Soll-Längen der Links
        self.calculate_lengths()

    def __repr__(self):
        return f"Mechanismus: {self.name}, ID: {self.id}, Version: {self.version}"
    
    def __eq__(self, other):
        # Vergleich von Mechanismus-Objekten (zwei Mechanismen sind gleich, wenn alle Attribute gleich sind)
        if not isinstance(other, Mechanism):
            return False
        # Vergleich Name
        if self.name != other.name:
            return False
        
        # Vergleich Joints:
        if len(self.joints) != len(other.joints):
            return False
        for i in range(len(self.joints)):
            if self.joints[i] != other.joints[i]:
                return False
        
        # Vergleich Links:
        if len(self.links) != len(other.links):
            return False
        for i in range(len(self.links)):
            if self.links[i] != other.links[i]:
                return False
        
        return True
    # ==============================
    # Kinematik-Methoden:
    # ==============================
    def calculate_lengths(self):
        """
        Falls ein Link noch keine "length" hat, wird sie aus den Joint-Koordinaten abgeleitet.
        """
        for link in self.links:
            if link.length is None:
                dx = link.end_joint.x - link.start_joint.x
                dy = link.end_joint.y - link.start_joint.y
                link.length = np.sqrt(dx**2 + dy**2)

    def compute_theta_range(self, steps=100):
        """
        Berechnet ein theta_range (NumPy-Array) für die Simulation.
        Falls ein Gelenk vom Typ 'Kreisbahnbewegung' existiert, 
        wird dessen aktueller Winkel (Startposition) als Startwinkel genommen, 
        sonst (kein Kreisgelenk) beginnt es bei 0.
        """ 
        for joint in self.joints:
            if joint.type == "Kreisbahnbewegung" and joint.center and joint.radius:
                cx, cy = joint.center
                dx = joint.x - cx
                dy = joint.y - cy
                start_angle = np.arctan2(dy, dx)
                return np.linspace(start_angle, start_angle + 2 * np.pi, steps)
        
        # Kein Kreisgelenk gefunden -> Startwinkel = 0° (Fallback)
        return np.linspace(0, 2 * np.pi, steps)

    def error_function(self, positions: list):
        """
        Fehlerfunktion für least_squares:
        positions: [x1, y1, x2, y2, ...] aller Frei beweglichen Gelenke.
        Vergleicht die aktuellen Längen der Links mit den Soll-Längen.
        """
        # Erstellung einer Kopie der Gelenkpositionen
        temp_positions = {}
        
        # Aktualisieren der Positionen der frei beweglichen Gelenke
        index = 0
        for i, joint in enumerate(self.joints):
            if joint.type == "Frei beweglich":
                # Updaten mit den Optimierungswerten
                temp_positions[i] = {"x": positions[index], "y": positions[index + 1]}
                index += 2
            else:
                # den aktuellen Wert beibehalten für Gelenke mit Kreisbahnbewegung und fixierten Gelenken
                temp_positions[i] = {"x": joint.x, "y": joint.y}
        
        # Berechnung der aktuellen Längen der Links basierend auf den temp_positions
        current_lengths = []
        for link in self.links:
            index_start = self.joints.index(link.start_joint)
            index_end = self.joints.index(link.end_joint)
            dx = temp_positions[index_end]["x"] - temp_positions[index_start]["x"]
            dy = temp_positions[index_end]["y"] - temp_positions[index_start]["y"]
            current_lengths.append(np.sqrt(dx**2 + dy**2))

        # Soll-Längen aus Link-Objekten extrahieren
        target_lengths = [link.length for link in self.links]

        # Fehler berechnen
        error = np.array(current_lengths) - np.array(target_lengths)
        return error 

    def optimization_function(self):
        """
        Ruft least_squares auf, um die Positionen der freien Gelenke
        an die Soll-Längen anzupassen.
        """
        # Startwerte für die frei beweglichen Gelenke
        free_joints = [joint for joint in self.joints if joint.type == "Frei beweglich"]
        positions = []
        for joint in free_joints:
            positions.append(joint.x)
            positions.append(joint.y)

        initial_positions = np.array(positions, dtype=float)

        result = least_squares(
            self.error_function, # Fehlerfunktion
            initial_positions,   # Startpositionen
            method='dogbox'      # Optimierungsmethode
        )

        # Positionen der beweglichen Gelenke nach dem Optimieren aktualisieren
        # result ist OptimizeResult-Objekt mit Attribut 'x' (Koordinaten der Gelenke)
        index = 0
        for joint in free_joints:
            joint.x = result.x[index]
            joint.y = result.x[index + 1]
            index += 2

        return result # für Auswertung von result.succes in kinematics()-Methode

    def kinematics(self, theta_range):
        """
        Führt eine Simulation für alle Winkel in theta_range durch.
        Setzt Kreisbahn-Gelenke, ruft optimization_function() auf
        und speichert die Positionen in 'trajectories'.
        """
        # Für ebenen Mechanismus mit den Voraussetzungen bzw. Randbedingungen lt. Aufgabenstellung, sind mindestens 4 Gelenke erforderlich
        if len(self.joints) < 4:
            raise ValueError("Mechanismus unvollständig. Mindestens 4 Gelenke erforderlich.")

        trajectories = []
        fail_count = 0  # Zähler für fehlgeschlagene Optimierungen

        for theta in theta_range:
            # Kreisbahngelenke setzen
            for joint in self.joints:
                if joint.type == "Kreisbahnbewegung" and joint.center and joint.radius:
                    cx, cy = joint.center
                    r = joint.radius
                    joint.x = cx + r * np.cos(theta)
                    joint.y = cy + r * np.sin(theta)
            
            # Optimierung
            result = self.optimization_function()
            if not result.success:
                fail_count += 1

            # aktuelle Gelenkposition speichern
            current_positions = [(joint.x, joint.y) for joint in self.joints]
            trajectories.append(current_positions)

        # ggf. Warnung ausgeben (für wie viele Frames die Optimierung fehlgeschlagen ist)
        if fail_count > 0:
            print(f"Warnung: Bei {fail_count} von {len(theta_range)} Frames war die Optimierung nicht erfolgreich.")

        return trajectories, fail_count if fail_count > 0 else None

    def save_kinematics_to_csv(self, theta_range, trajectories, filename="coords_results.csv"):
        """
        Exportiert Winkel + Gelenkpositionen in eine CSV-Datei.
        """
        with open(filename, mode="w", newline="") as file:
            writer = csv.writer(file) 
            # Header
            header = ["Theta (rad) | "] 
            for i in range(len(self.joints)):  
                header.append(f"Gelenk_{i+1}_x | ") 
                header.append(f"Gelenk_{i+1}_y | ")  
            writer.writerow(header) 
            
            # Daten
            for i, theta in enumerate(theta_range):  
                row = [theta] 
                for (x, y) in trajectories[i]: 
                    row.append(x)  
                    row.append(y)  
                writer.writerow(row)    
        return filename 

    # ==============================
    # Speichern und Laden von Mechanismus-Konfigurationen:
    # ==============================
    def save_mechanism(self):
        """
        Speichert diesen Mechanismus in der 'mechanism_configurations'-Tabelle.
        - Falls self.id = None, wird eine neue UUID erzeugt und version = 1.
        - Wenn bereits eine ID existiert, version += 1, da wir davon ausgehen, 
          dass sich der Mechanismus geändert hat.
        """
        # Datenbankverbindung herstellen
        db_conn = DatabaseConnector()
        mechanism_table = db_conn.get_table('mechanism_configurations')

        if not self.id:
            # neuer Mechanismus
            self.id = str(uuid.uuid4())
            self.version = 1
        else:
            # Mechanismus existiert bereits -> Versionsnummer erhöhen
            self.version += 1

        """
        Es können keine Python-Objekte direkt in die Datenbank gespeichert werden.
        Daher werden die Joint- und Link-Objekte in Listen von Dictionaries umgewandelt.
        Die Verwendung von self.__dict__ zur Speicherung ist hier nicht möglich, 
        da wir verschachtelte Objekte (Joint-Objekte in Link-Objekten) haben.
        """
        joints_list = []
        for joint in self.joints:
            entry = {
                "x": joint.x,
                "y": joint.y,
                "type": joint.type,
                "center": joint.center,
                "radius": joint.radius
            }
            joints_list.append(entry)

        links_list = []
        for link in self.links:
            start_index = self.joints.index(link.start_joint)
            end_index = self.joints.index(link.end_joint)
            entry = {
                "start": start_index,
                "end": end_index,
                "length": link.length,
                "protected": link.protected
            }
            links_list.append(entry)
        
        data = {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "joints": joints_list,
            "links": links_list
        }
        mechanism_query = Query()
        existing = mechanism_table.get(mechanism_query.id == self.id)
        if existing:
            mechanism_table.update(data, mechanism_query.id == self.id)
        else:
            mechanism_table.insert(data)

        # Datenbankverbindung schließen
        db_conn.close()

    @classmethod
    def load_mechanism(cls, mechanism_id: str):
        """
        Lädt einen Mechanismus anhand seiner 'id'.
        Gibt ein Mechanism-Objekt zurück oder None, wenn nicht gefunden.
        """
        db_conn = DatabaseConnector()
        mechanism_table = db_conn.get_table('mechanism_configurations')

        mechanism_query = Query()
        found = mechanism_table.get(mechanism_query.id == mechanism_id) # .get() statt .search(), da id eindeutig ist
        if not found:
            return None
        
        """
        Umgekehrte Umwandlung von Dictionaries in Joint- und Link-Objekte.
        """
        # Joint-Objekte rekonstruieren
        joints_data = found["joints"]
        joint_objects = []
        for jd in joints_data:
            j = Joint(
                x=jd["x"],
                y=jd["y"],
                joint_type=jd["type"],
                center=jd["center"],
                radius=jd["radius"]
            )
            joint_objects.append(j)

        # Link-Objekte rekonstruieren
        links_data = found["links"]
        link_objects = []
        for ld in links_data:
            start_joint = joint_objects[ld["start"]]
            end_joint = joint_objects[ld["end"]]
            l = Link(start_joint, end_joint, ld["length"], protected=ld.get("protected", False))
            link_objects.append(l)
        
        # Mechanismus-Objekt erstellen
        mechanism = Mechanism(
            name=found["name"],
            joints=joint_objects,
            links=link_objects,
            mechanism_id=found["id"],
            version=found["version"]
        )

        db_conn.close()
        
        return mechanism

    @classmethod
    def find_all_mechanisms(cls) -> list:
        """
        Gibt eine Liste von Mechanismus-Konfigurationen zurück ({id, name, version}-Dictionaries).
        In UI kann dann beispielsweise nur der Name angezeit werden.
        Mechanismus-Objekt wird erst beim Laden der Konfiguration erstellt.
        """
        db_conn = DatabaseConnector()
        mechanism_table = db_conn.get_table('mechanism_configurations')

        results = []
        for entry in mechanism_table.all():
            results.append({
                "id": entry["id"],
                "name": entry["name"],
                "version": entry.get("version", 1)
            })

        db_conn.close()

        return results

    @classmethod
    def delete_mechanism(cls, mechanism_id: str):
        """
        Löscht den Mechanismus und den dazugehörigen Kinematik-Eintrag (falls vorhanden) anhand der ID.
        """
        db_conn = DatabaseConnector()
        mechanism_table = db_conn.get_table('mechanism_configurations')
        kinematics_table = db_conn.get_table('mechanism_kinematics')

        mechanism_query = Query()
        mechanism_table.remove(mechanism_query.id == mechanism_id)
        kinematics_table.remove(mechanism_query.mechanism_id == mechanism_id)

        db_conn.close()

    # ==============================
    # Speichern und Laden von Mechanismus-Kinematik:
    # ==============================
    def save_kinematics(self, theta_range, trajectories, steps):
        """
        Speichert Kinematik-Daten in 'mechanism_kinematics'.
        - self.id muss existieren (Mechanismus muss gespeichert sein)
        - self.version = Mechanismus-Version
        - Überschreibt ggf. den alten Eintrag für diesen Mechanismus
        """
        db_conn = DatabaseConnector()
        kinematics_table = db_conn.get_table('mechanism_kinematics')

        # Prüfen, ob Mechanismus gespeichert ist
        if not self.id:
            raise ValueError("Mechanismus hat keine ID. Bitte speichern Sie den Mechanismus zuerst (Aufruf von save_mechanism()).")
        
        kinematic_query = Query()
        # Alten Eintrag löschen (falls vorhanden) - ein Mechanismus hat genau einen Kinematik-Eintrag
        kinematics_table.remove(kinematic_query.mechanism_id == self.id)

        data = {
            "mechanism_id": self.id,
            "mechanism_name": self.name,
            "mechanism_version": self.version,
            "steps": steps,
            "theta_values": list(theta_range),
            "trajectories": [[(x, y) for (x, y) in frame] for frame in trajectories]
        }

        kinematics_table.insert(data)

        db_conn.close()

    @classmethod
    def load_kinematics(cls, mechanism_id: str, mechanism_version: int, steps: int):
        """
        Lädt Kinematik-Daten (theta_values, trajectories) aus 'mechanism_kinematics'.
        Falls die Version nicht übereinstimmt, ist die Kinematik veraltet.
        Gibt (theta_values, trajectories) zurück oder (None, None).
        """
        db_conn = DatabaseConnector()
        kinematics_table = db_conn.get_table('mechanism_kinematics')

        kinematic_query = Query()
        found = kinematics_table.get(kinematic_query.mechanism_id == mechanism_id)
        if not found:
            return None, None
        
        # Version prüfen
        if steps == None:
            steps = found["steps"]

        if found["mechanism_version"] != mechanism_version and found["steps"] != steps:
            # Mechanismus wurde seitdem geändert -> Kinematik ist veraltet
            return None, None
        
        db_conn.close()

        return found["theta_values"], found["trajectories"]

    @classmethod
    def delete_kinematics(cls, mechanism_id: str):
        """
        Löscht Kinematik-Eintrag für einen Mechanismus.
        """
        db_conn = DatabaseConnector()
        kinematics_table = db_conn.get_table('mechanism_kinematics')

        kinematic_query = Query()
        kinematics_table.remove(kinematic_query.mechanism_id == mechanism_id)

        db_conn.close()

# =================================================================================================
# Modul-Tests:
# =================================================================================================
if __name__ == "__main__":
    # Beispiel: Viergelenkgetriebe (Simulation Eingabe Konfiguration in UI)
    print("Test: Viergelenkgetriebe")
    # Gelenke anlegen
    j0 = Joint(x=0.0, y=0.0, joint_type="Fixiert")
    j1 = Joint(x=0.25, y=0.0, joint_type="Kreisbahnbewegung", center=[0.0, 0.0], radius=0.25)
    j2 = Joint(x=2.0, y=2.0, joint_type="Frei beweglich")
    j3 = Joint(x=2.0, y=0.0, joint_type="Fixiert")

    # Glieder anlegen
    l0 = Link(j0, j1, protected=True)
    l1 = Link(j2, j1)
    l2 = Link(j3, j2)
    
    joints = [j0, j1, j2, j3]
    links = [l0, l1, l2]

    # Mechanismus-Objekt erzeugen
    mechanism = Mechanism(name="Viergelenkgetriebe", joints=joints, links=links)
    # Kontrolle, ob Mechanismus gültig ist
    valid, msg = mechanism_is_valid(joints, links)
    print(f"Validierung: {valid}, {msg}")

    # Mechanismus speichern
    mechanism.save_mechanism()
    print(f"Mechanismus gespeichert: {mechanism.name}, ID={mechanism.id}, Version={mechanism.version}")

    # Kinematik berechnen und speichern
    theta_range = mechanism.compute_theta_range(steps=100)
    trajectories, fail_count = mechanism.kinematics(theta_range)
    mechanism.save_kinematics(theta_range, trajectories, 100)
    print("Kinematik für Viergelenkgetriebe berechnet und gespeichert.")
    if fail_count:
        print(f"Anzahl fehlgeschlagener Optimierungen: {fail_count}")
    else:
        print("Keine fehlgeschlagenen Optimierungen.")

    # Laden aus Datenbank
    mechanism_loaded = Mechanism.load_mechanism(mechanism.id)
    if mechanism_loaded:
        print("Geladener Mechanismus:", mechanism_loaded.name, mechanism_loaded.id, "Version =", mechanism_loaded.version)
        # Kinematik laden
        thetas, trajs = Mechanism.load_kinematics(mechanism_loaded.id, mechanism_loaded.version, 100)
        if thetas is None:
            print("Keine Kinematik gefunden oder Kinematik veraltet.")
        else:
            print("Kinematik geladen, Anzahl Frames =", len(trajs))
    else:
        print("Mechanismus nicht gefunden...")
    
    # =================================================================================================
    # Beispiel: Strandbeest (Simulation Eingabe Konfiguration in UI)
    print("Test: Strandbeest")
    # Gelenke anlegen
    j0 = Joint(0.0, 0.0, "Fixiert")
    j1 = Joint(38.0, 7.81, "Fixiert")
    j2 = Joint(49.73, -1.55, "Kreisbahnbewegung", [38.0, 7.81], 15.000513324549928)
    j3 = Joint(18.2, 37.3, "Frei beweglich")
    j4 = Joint(-34.82, 19.9, "Frei beweglich")
    j5 = Joint(-30.5, -19.22, "Frei beweglich")
    j6 = Joint(-19.33, -84.03, "Frei beweglich")
    j7 = Joint(0.67, -39.3, "Frei beweglich")

    # Glieder anlegen
    l0 = Link(j1, j2, protected=True)
    l1 = Link(j3, j2)
    l2 = Link(j3, j4)
    l3 = Link(j5, j4)
    l4 = Link(j5, j6)
    l5 = Link(j7, j6)
    l6 = Link(j7, j2)
    l7 = Link(j7, j5)
    l8 = Link(j0, j7)
    l9 = Link(j0, j4)
    l10 = Link(j0, j3)

    joints = [j0, j1, j2, j3, j4, j5, j6, j7]
    links = [l0, l1, l2, l3, l4, l5, l6, l7, l8, l9, l10]

    # Mechanismus-Objekt erzeugen
    mechanism = Mechanism(name="Strandbeest", joints=joints, links=links)
    # Kontrolle, ob Mechanismus gültig ist
    valid, msg = mechanism_is_valid(joints, links)
    print(f"Validierung: {valid}, {msg}")

    # Mechanismus speichern
    mechanism.save_mechanism()
    print(f"Mechanismus gespeichert: {mechanism.name}, ID={mechanism.id}, Version={mechanism.version}")

    # Kinematik berechnen und speichern
    theta_range = mechanism.compute_theta_range(steps=100)
    trajectories, fail_count = mechanism.kinematics(theta_range)
    mechanism.save_kinematics(theta_range, trajectories, 100)
    print("Kinematik für Strandbeest berechnet und gespeichert.")
    if fail_count:
        print(f"Anzahl fehlgeschlagener Optimierungen: {fail_count}")
    else:
        print("Keine fehlgeschlagenen Optimierungen.")

    # Laden aus Datenbank
    mechanism_loaded = Mechanism.load_mechanism(mechanism.id)
    if mechanism_loaded:
        print("Geladener Mechanismus:", mechanism_loaded.name, mechanism_loaded.id, "Version =", mechanism_loaded.version)
        # Kinematik laden
        thetas, trajs = Mechanism.load_kinematics(mechanism_loaded.id, mechanism_loaded.version, 100)
        if thetas is None:
            print("Keine Kinematik gefunden oder Kinematik veraltet.")
        else:
            print("Kinematik geladen, Anzahl Frames =", len(trajs))
    else:
        print("Mechanismus nicht gefunden...")