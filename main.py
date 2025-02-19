import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mechanism import Mechanism, Database_editing
from visualization import Visualizer
import time

st.set_page_config(page_title="Simulation ebener Mechanismen", layout="wide")
st.title("Simulation ebener Mechanismen")

Database_editing = Database_editing()

#Session states initialisieren
if "joints" not in st.session_state:
    st.session_state["joints"] = []
if "links" not in st.session_state:
    st.session_state["links"] = []

#Zwei Spalten - für Konfiguration und Visualisierung
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Gelenkkonfiguration")

    #Gelenkpunkte hinzufügen
    if st.button("Neuen Gelenkpunkt hinzufügen"):
        st.session_state["joints"].append({"x": 0.0, "y": 0.0, "type": "Fixiert", "center": None, "radius": None})
    #Gelenkpunkt entfernen
    if st.button("Letztes Gelenk entfernen"):
        if st.session_state["joints"]:
            st.session_state["joints"].pop()
            st.rerun()

    for i, joint in enumerate(st.session_state["joints"]):
        st.markdown(f"### Gelenk {i + 1}")
        col_x, col_y = st.columns(2)
        with col_x:
            joint["x"] = st.number_input(f"x-Koordinate Gelenk {i + 1}", value=joint["x"], step=0.1, key=f"x_{i}")
        with col_y:
            joint["y"] = st.number_input(f"y-Koordinate Gelenk {i + 1}", value=joint["y"], step=0.1, key=f"y_{i}")

        joint["type"] = st.selectbox(f"Typ Gelenk {i + 1}", ["Fixiert", "Frei beweglich", "Kreisbahnbewegung"], key=f"type_{i}")

        if joint["type"] == "Kreisbahnbewegung":
            col_center_x, col_center_y = st.columns(2)
            with col_center_x:
                center_x = st.number_input(
                    f"x-Mittelpunkt Gelenk {i + 1}", 
                    value=joint["center"][0] if joint["center"] else 0.0, 
                    step=0.1, 
                    key=f"center_x_{i}"
                )
            with col_center_y:
                center_y = st.number_input(
                    f"y-Mittelpunkt Gelenk {i + 1}", 
                    value=joint["center"][1] if joint["center"] else 0.0, 
                    step=0.1, 
                    key=f"center_y_{i}"
                )

            joint["center"] = (center_x, center_y)

            suggested_radius = np.sqrt((joint["x"] - joint["center"][0])**2 + (joint["y"] - joint["center"][1])**2)
            joint["radius"] = st.number_input(f"Radius Gelenk {i + 1}", value=suggested_radius, step=0.1, key=f"radius_{i}")

    #Verbindungen hinzufügen
    st.subheader("Verbindungen hinzufügen")
    joint_indices = [f"Gelenk {i + 1}" for i in range(len(st.session_state["joints"]))]
    joint1 = st.selectbox("Gelenk 1", joint_indices, key="link_joint1")
    joint2 = st.selectbox("Gelenk 2", joint_indices, key="link_joint2")

    if st.button("Verbindung hinzufügen"):
        joint1_index = joint_indices.index(joint1)
        joint2_index = joint_indices.index(joint2)

        is_same_joint = joint1_index == joint2_index
        is_link_existing = (joint1_index, joint2_index) in st.session_state["links"] or (joint2_index, joint1_index) in st.session_state["links"]

        if not is_same_joint and not is_link_existing:
            st.session_state["links"].append((joint1_index, joint2_index))
            st.success(f"Verbindung zwischen Gelenk {joint1} und Gelenk {joint2} hinzugefügt.")
        else:
            st.warning("Ungültige Verbindung oder Verbindung bereits vorhanden.")
            time.sleep(1)
            st.rerun()

    #Konfiguration speichern
    st.subheader("Konfiguration speichern")
    config_name = st.text_input("Name der Konfiguration")
    if st.button("Speichern"):
        message = Database_editing.save_configuration(config_name, st.session_state["joints"], st.session_state["links"])
        st.success(message)
        time.sleep(1)
        st.rerun()
    
    #Gespeicherte Konfiguration löschen
    st.subheader("Gespeicherte Konfigurationen löschen")
    saved_configs = Database_editing.find_all_configurations()
    if saved_configs:
        selected_config_to_delete = st.selectbox("Wähle eine zu löschende Konfiguration", saved_configs, key="delete_config")
        if st.button("Löschen"):
            message = Database_editing.delete_configuration(selected_config_to_delete)
            st.success(message)
            time.sleep(1)
            st.rerun()


with col2:
    st.subheader("Live-Vorschau der Gelenkkonfiguration")

    fig, ax = plt.subplots()
    Visualizer.plot_configuration(st.session_state["joints"], st.session_state["links"], ax=ax)
    st.pyplot(fig) 

    #Simulation
    st.subheader("Simulation starten")
    saved_configs = Database_editing.find_all_configurations()
    if saved_configs:
        selected_config = st.selectbox("Wähle eine gespeicherte Konfiguration aus", saved_configs)
        if st.button("Simulation ausführen"):
            joints, links = Database_editing.load_configuration(selected_config)
            if joints and links:
                mechanism = Mechanism(joints, links)
                theta_range = np.linspace(0, 2 * np.pi, 100)
                trajectories = mechanism.kinematics(theta_range)
                
                gif_path = Visualizer.create_gif(trajectories, links)

                st.subheader("Simulation als GIF:")
                st.image(gif_path, use_container_width=True)

                csv_data = mechanism.save_kinematics_to_csv(theta_range, trajectories)

                #GIF herunterladen
                with open(gif_path, "rb") as file:
                    st.download_button(
                        label="GIF herunterladen",
                        data=file,
                        file_name="simulation.gif",
                        mime="image/gif"
                    )
                    

                #Download der Koordinaten als .csv Datei
                with open(csv_data, "rb") as file:
                    st.download_button(
                        label="Simulationsergebnisse als CSV herunterladen",
                        data=file,
                        file_name="Coords_results.csv",
                        mime="text/csv"
                    )
                    
            else:
                st.error("Konfiguration konnte nicht geladen werden.")
                time.sleep(1)
                st.rerun()

