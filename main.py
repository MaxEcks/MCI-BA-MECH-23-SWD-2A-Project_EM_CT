# main.py

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mechanism import Mechanism, Joint, Link, mechanism_is_valid
from visualization import Visualizer
from movement_speed import StrandbeestSpeed
import time

# ================================================================================
# Funktionen zur Validierung der Gelenktyp-Konfiguration und Berechnung der Anzahl benötigter Links
# ================================================================================ 
def validate_joint_types():
    """
    Prüft, ob die Gelenk-Typen dem gewünschten Schema entsprechen:
    - 2 Gelenke vom Typ 'Fixiert'
    - 1 Gelenk vom Typ 'Kreisbahnbewegung'
    - restliche Gelenke frei beweglich

    Gibt True, "Ok" oder False, "Fehlermeldung" zurück.
    """
    joints_dict = st.session_state["joints"]

    f = sum(jd["type"] == "Fixiert" for jd in joints_dict)             # Anzahl fixierter Gelenke 
    k = sum(jd["type"] == "Kreisbahnbewegung" for jd in joints_dict)   # Anzahl Kreisbahngelenke
    b = sum(jd["type"] == "Frei beweglich" for jd in joints_dict)      # Anzahl frei beweglicher Gelenke
    # zusätzliche Prüfung, ob mindestens 4 Gelenke vorhanden sind
    n = len(joints_dict)

    if n < 4:
        return False, "Mindestens 4 Gelenke erforderlich."
    if f != 2: 
        return False, f"Es müssen genau 2 Gelenke vom Typ 'Fixiert' vorhanden sein (aktuell: {f})."
    if k != 1:
        return False, f"Es muss genau 1 Gelenk vom Typ 'Kreisbahnbewegung' vorhanden sein (aktuell: {k})."
    if b < 1:
        return False, "Mindestens 1 Gelenk vom Typ 'Frei beweglich' erforderlich."
    
    return True, "Gelenktyp-Konfiguration ist gültig."

def required_links() -> int:
    """
    Berechnet die Anzahl der benötigten Links, damit
    F = 0 erfüllt ist (nach abgewandelter Grübler-Formel),
    sofern genau 2 Gelenke fixiert und 1 Gelenk auf Kreisbahn ist.
    
    Rückgabe:
      - Eine nichtnegative Zahl (mindestens 3).
      - Falls die Gelenktypen nicht dem Schema (2 Fix, 1 Kreis, n frei) entsprechen,
        wird -1 zurückgegeben.

    F = 2n - 2f - 2k - (g - 1) = 0  =>  g = 2n - 2f - 2k + 1
    Dabei:
      n = Anzahl aller Gelenke
      f = 2 (Anzahl fixierter Gelenke)
      k = 1 (Anzahl Kreisgelenke)
    """
    joints_dict = st.session_state["joints"]

    f = sum(jd["type"] == "Fixiert" for jd in joints_dict)
    k = sum(jd["type"] == "Kreisbahnbewegung" for jd in joints_dict)
    n = len(joints_dict)

    # Kontrolle, ob die Gelenktypen dem gewünschten Schema entsprechen
    if f != 2 or k != 1:
        return -1

    # Rückgabe der Anzahl benötigter Links (nach abgeleiteter Grübler-Formel)
    return 2 * n - 2 * f - 2 * k + 1

def reset_to_standard():
    """
    Überschreibt st.session_state['joints'] und st.session_state['links']
    mit einem Standardlayout (4 Gelenke: 2 fix, 1 kreis, 1 frei).
    """
    st.session_state["joints"] = [
        {"x": 0.0, "y": 0.0, "type": "Fixiert", "center": None, "radius": None},            # Kreismittelpunkt (c)
        {"x": 0.0, "y": 0.0, "type": "Fixiert", "center": None, "radius": None},            # Fixiertes Gelenk (p0)
        {"x": 0.0, "y": 0.0, "type": "Kreisbahnbewegung", "center": None, "radius": None},  # Kreisbahnbewegung (p2)
        {"x": 0.0, "y": 0.0, "type": "Frei beweglich", "center": None, "radius": None}      # Frei bewegliches Gelenk (p1)
    ]

    st.session_state["links"] = []

# ================================================================================
# Konfiguration der Streamlit-Seite
st.set_page_config(
    page_title="Simulation ebener Mechanismen",
    page_icon=":material/modeling:",
    layout="wide"
)

st.header(":material/modeling: Simulation ebener Mechanismen", 
          divider = True, 
          help="In dieser Web-Applikation können Sie ebene Mechanismen konfigurieren und simulieren."
)
# ================================================================================
# Session State Initialisierung
# ================================================================================
# Gelenke und Verbindungen
if "joints" not in st.session_state:
    # Initialisierung der Gelenke (Minimum 4 Gelenke mit 2 fixierten Gelenken, 1 Kreisbahnbewegung und 1 frei-beweglichem Gelenk)
    st.session_state["joints"] = [
        {"x": 0.0, "y": 0.0, "type": "Fixiert", "center": None, "radius": None},            # Kreismittelpunkt (c)
        {"x": 0.0, "y": 0.0, "type": "Fixiert", "center": None, "radius": None},            # Fixiertes Gelenk (p0)
        {"x": 0.0, "y": 0.0, "type": "Kreisbahnbewegung", "center": None, "radius": None},  # Kreisbahnbewegung (p2)
        {"x": 0.0, "y": 0.0, "type": "Frei beweglich", "center": None, "radius": None}      # Frei bewegliches Gelenk (p1)
    ]

if "links" not in st.session_state:
    st.session_state["links"] = []
if "protected_links" not in st.session_state:
    st.session_state["protected_links"] = set()

# Einheit für Längenangaben
if "unit" not in st.session_state:
    st.session_state["unit"] = ""

# Session States für aktuell geladenen Mechanismus
if "current_mech_id" not in st.session_state:
    st.session_state["current_mech_id"] = None
if "current_mech_name" not in st.session_state:
    st.session_state["current_mech_name"] = ""
if "current_mech_version" not in st.session_state:
    st.session_state["current_mech_version"] = 0

# Session States für Sperr-Logik
if "locked" not in st.session_state:
    st.session_state["locked"] = False
if "prev_locked" not in st.session_state:
    st.session_state["prev_locked"] = False
if "show_message_manually" not in st.session_state:
    st.session_state["show_message_manually"] = False
if "show_message_reset" not in st.session_state:
    st.session_state["show_message_reset"] = False
if "rerun" not in st.session_state:
    st.session_state["rerun"] = False

# ================================================================================
# Spalten-Layout (für Konfiguration und Visualisierung)
# ================================================================================
col1, col2 = st.columns([1, 3], border=True)
# ================================================================================
# Konfiguration Mechanismus (col1)
# ================================================================================
with col1:
    st.subheader(":material/manufacturing: Mechanismus Konfiguration", 
                help="Konfigurieren Sie die Gelenke und Verbindungen Ihres Mechanismus. Oder laden und bearbeiten Sie gespeicherte Konfigurationen.",
                divider="rainbow"
    )
        
    # Längeneinheit definieren
    unit = st.selectbox("**Einheit für Längenangaben *(optional)***", options=["mm", "cm", "m"], key="unit_select", index = None, placeholder = "keine Längeneinheit ausgewählt")
    if unit:
        st.session_state["unit"] = unit
    else:
        st.session_state["unit"] = ""
    # ============================================================================
    # Konfiguration der Gelenke
    # ============================================================================
    st.subheader(":material/join: Gelenke konfigurieren", help="Konfigurieren Sie die Gelenke Ihres Mechanismus.")
    
    # --------------------------------------------------
    # Gelenktyp-Auswahl sperren (um nur gültige Mechanismen bzw. Konfigurationen zu erlauben)
    # --------------------------------------------------
    st.session_state["locked"] = st.checkbox("**Nur gültige Gelenktyp-Konfigurationen zulassen *(Typ-Auswahl sperren)***", value=st.session_state["locked"])
    # Prüfung, ob Lock-Status geändert wurde
    if st.session_state["locked"] != st.session_state["prev_locked"]:
        if st.session_state["locked"]:
            # User will Gelenktypen sperren -> Validierung der Gelenktyp-Konfiguration
            valid, msg = validate_joint_types()
            if not valid:
                st.warning(f"Sperrung nicht möglich: {msg}")
                # Session-State "locked" zurücksetzen
                st.session_state["locked"] = False

                # Option: Zurücksetzen oder manuelle Anpassung
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Gelenk-Konfiguration zurücksetzen", key="reset_config", icon=":material/history:", 
                                 help="Setzt alle Gelenke auf Standardkonfiguration. Alle Änderungen gehen verloren."):
                        reset_to_standard()
                        st.session_state["show_message_reset"] = True
                with col_b:
                    if st.button("Gelenk-Konfiguration manuell anpassen", key="edit_config", icon=":material/edit:", 
                                 help="Passen Sie die Gelenk-Konfiguration manuell an."):
                        st.session_state["show_message_manually"] = True
                
                if st.session_state["show_message_manually"]:
                    st.info("Bitte Gelenke manuell anpassen. Dann erneut Button (:material/edit:) betätigen.")
                    st.session_state["rerun"] = True
                    st.session_state["show_message_manually"] = False

                if st.session_state["show_message_reset"]:
                    # erneute Vailidierung
                    valid_2, msg_2 = validate_joint_types()
                    if valid_2:
                        st.success("Gelenk-Konfiguration zurückgesetzt. Gelenktyp-Auswahl gesperrt.")
                        st.session_state["rerun"] = True
                        st.session_state["show_message_reset"] = False
                        st.session_state["locked"] = True
                    else:
                        st.error("Fehler beim Zurücksetzen der Gelenk-Konfiguration.")
                        st.session_state["rerun"] = True
                        st.session_state["show_message_reset"] = False
                        st.session_state["locked"] = False
                
            else:
                st.success("Gelenk-Konfiguration ist gültig, Typ-Auswahl gesperrt.")
                st.session_state["rerun"] = True
        else:
            # Sperrung deaktiviert -> Gelenktyp-Auswahl freigeben
            st.info("Gelenktyp-Auswahl freigegeben.")
            st.session_state["rerun"] = True
        
    
    # Update des vorherigen Sperrzustands
    st.session_state["prev_locked"] = st.session_state["locked"]
    
    if st.session_state["rerun"]:
        st.session_state["rerun"] = False
        time.sleep(1)
        st.rerun()

    # --------------------------------------------------
    # Gelenke hinzufügen/entfernen
    # --------------------------------------------------
    n_joints = len(st.session_state["joints"])
    # Gelenkpunkt hinzufügen
    if st.button(f"**Gelenkpunkt {n_joints + 1} hinzufügen**", icon=":material/add:"):
        st.session_state["joints"].append({"x": 0.0, "y": 0.0, "type": "Frei beweglich", "center": None, "radius": None})
        st.rerun()
    # Gelenkpunkt entfernen (nur wenn mehr als 4 Gelenke vorhanden sind)
    if n_joints > 4:
        if st.button(f"**Gelenkpunkt {n_joints} entfernen**", icon=":material/remove:"):
            if st.session_state["joints"]:
                st.session_state["joints"].pop()
                st.rerun()

    # --------------------------------------------------
    # Eingabefelder für jedes Gelenk
    # --------------------------------------------------
    for i, joint in enumerate(st.session_state["joints"]):
        options = ["Fixiert", "Frei beweglich", "Kreisbahnbewegung"]
        # Ermittlung des Index, der dem aktuellen joint["type"] entspricht
        try:
            idx = options.index(joint["type"])
        except ValueError:
            idx = 0
            
        st.markdown(f"##### Gelenk {i + 1}")
        col_x, col_y = st.columns(2)
        with col_x:
            joint["x"] = st.number_input(f"**x-Koordinate *Gelenk {i + 1}***", value=joint["x"], step=0.1, key=f"x_{i}")
        with col_y:
            joint["y"] = st.number_input(f"**y-Koordinate *Gelenk {i + 1}***", value=joint["y"], step=0.1, key=f"y_{i}")

        joint["type"] = st.selectbox(
            f"**Typ *Gelenk {i + 1}***",
            options = options,
            key = f"type_{i}",
            index = idx,
            disabled = st.session_state["locked"]
        )

        if joint["type"] == "Kreisbahnbewegung":
            st.write("**Wähle ein fixiertes Gelenk als Drehpunk:**")

            fixed_joint_indices = []
            fix_joint_labels = []

            for idx, j in enumerate(st.session_state["joints"]):
                if j["type"] == "Fixiert":
                    fixed_joint_indices.append(idx)
                    fix_joint_labels.append(f"Gelenk {idx + 1}")
            
            if fixed_joint_indices:
                selected_label = st.selectbox(
                    f"**Drehpunkt *Gelenk {i + 1}***",
                    options = fix_joint_labels,
                    index = None,
                    placeholder = "Bitte auswählen",
                    key=f"center_joint_{i}"
                )

            # Überprüfung, ob Auswahl durch User getroffen wurde
            if selected_label:
                label_index = fix_joint_labels.index(selected_label)
                center_joint_index = fixed_joint_indices[label_index]

                # Alte Verbindung entfernen (falls vorhanden)
                old_center = joint.get("center_joint_index", None)
                if old_center is not None and old_center != center_joint_index:
                    old_link = tuple(sorted((old_center, i)))
                    # Verbindung Drehpunkt und Kreisbahngelenk ist immer protected
                    if old_link in st.session_state["links"]:
                        st.session_state["links"].remove(old_link)
                    if old_link in st.session_state["protected_links"]:
                        st.session_state["protected_links"].remove(old_link)

                # neuen center_joint_index in "joint" speichern
                joint["center_joint_index"] = center_joint_index

                # Koordinaten des Drehpunkts speichern
                center_x = st.session_state["joints"][center_joint_index]["x"]
                center_y = st.session_state["joints"][center_joint_index]["y"]
                joint["center"] = [center_x, center_y]

                # Radius berechnen
                radius = np.sqrt((joint["x"] - center_x)**2 + (joint["y"] - center_y)**2)
                joint["radius"] = radius
                st.write(f"Radius: {radius:.2f} {st.session_state['unit']}")

                # Verbindung zw. Drehpunkt und Kreisbahngelenk hinzufügen (sortiert und protected)
                new_link = tuple(sorted((center_joint_index, i)))
                if new_link not in st.session_state["links"]:
                    st.session_state["links"].append(new_link)
                    st.session_state["protected_links"].add(new_link)
                    st.success(f"Geschützte Verbindung zwischen Drehpunkt {center_joint_index + 1} und Gelenk {i + 1} auf Kreisbahn hinzugefügt (kann nicht manuell entfernt werden).")
                    time.sleep(1)
                    st.rerun()

        st.divider()

    # ============================================================================
    # Konfiguration der Verbindungen
    # ============================================================================
    st.subheader(":material/share: Verbindungen konfigurieren", help="Fügen Sie Verbindungen zwischen Gelenken hinzu.")
    
    # aktuelle Verbindungen anzeigen
    if st.session_state["links"]:
        with st.expander("**Aktuelle Verbindungen anzeigen**", expanded=False, icon = ":material/visibility:"):
            for link in st.session_state["links"]:
                st.write(f"Gelenk {link[0] + 1} - Gelenk {link[1] + 1}")

            # Ausgabe, wie viele Links für gültige Konfiguration benötigt werden
            required = required_links() - len(st.session_state["links"])
            st.info(f"**Anzahl noch benötigter Verbindungen: *{required}***")


    joint_indices = [f"Gelenk {i + 1}" for i in range(len(st.session_state["joints"]))]
    joint1 = st.selectbox("**Verbindung von**", options = joint_indices, key="link_joint1", index = None, placeholder = "Gelenk auswählen")
    joint2 = st.selectbox("**zu**", options = joint_indices, key="link_joint2", index = None, placeholder = "Gelenk auswählen")

    if st.button("**Verbindung hinzufügen**", icon = ":material/add:"):
        j1 = joint_indices.index(joint1)
        j2 = joint_indices.index(joint2)
        new_link = tuple(sorted((j1, j2)))
        existing_link = new_link in st.session_state["links"]

        if not existing_link and j1 != j2:
            st.session_state["links"].append(new_link)
            st.success(f"Verbindung zwischen Gelenk {joint1} und Gelenk {joint2} hinzugefügt.")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Ungültige Verbindung oder Verbindung bereits vorhanden.")
            time.sleep(1)
            st.rerun()

    if st.button("**Letzte *ungeschützte* Verbindung entfernen**", icon = ":material/remove:"):
        # Suche von hinten nach vorn (um letzte ungeschützte Verbindung zu finden)
        found_unprotected = False
        for i in range(len(st.session_state["links"]) - 1, -1, -1): # Rückwerts-Schleife range(start, stop, step)
            link = st.session_state["links"][i]
            if link not in st.session_state["protected_links"]:
                st.session_state["links"].pop(i)
                st.success(f"Verbindung {link} erfolgreich entfernt.")
                found_unprotected = True
                break
        if not found_unprotected:
            st.warning("Keine ungeschützte Verbindung gefunden.")
        
        time.sleep(1)
        st.rerun()
    
    st.divider()
    # ============================================================================
    # Konfiguration speichern
    # ============================================================================
    st.subheader(":material/save: Konfiguration speichern", 
                help="Speichern Sie die aktuelle Konfiguration des Mechanismus. Geladener Mechanismus wird überschrieben.")

    default_name = st.session_state["current_mech_name"]
    if default_name:
        config_name = st.text_input("**Name der Konfiguration**", value = default_name, key="config_name")
    else:
        config_name = st.text_input("**Name der Konfiguration**", placeholder = "z.B. Viergelenkgetriebe #1", key="config_name")

    if st.button("**Speichern**", icon=":material/save:", help="Mechanismus-Konfiguration wird vor dem Speichern validiert. Ungültige Konfigurationen können nicht gespeichert werden."):
        if not config_name.strip():
            st.error("Bitte geben Sie einen Namen für die Konfiguration ein.")
            time.sleep(2)
            st.rerun()
        else:
            # Mechanismus-Ojekt aus Session-States erstellen
            # Joint und Link Objekte erzeugen
            joint_objects = []
            for j in st.session_state["joints"]:
                j_obj = Joint(
                    x = j["x"],
                    y = j["y"],
                    joint_type = j["type"],
                    center = j["center"],
                    radius = j["radius"]
                )
                joint_objects.append(j_obj)

            link_objects = []
            for (start_idx, end_idx) in st.session_state["links"]:
                link_obj = Link(
                    start_joint = joint_objects[start_idx],
                    end_joint = joint_objects[end_idx],
                    protected = False if (start_idx, end_idx) not in st.session_state["protected_links"] else True  
                )
                link_objects.append(link_obj)

            # Validierung der Mechanismus-Konfiguration
            valid, msg = mechanism_is_valid(joint_objects, link_objects)

            if not valid:
                st.error(f"{msg}")
                time.sleep(3)
                st.rerun()

            else:
                # Namensduplikate verhindern
                all_mechanisms = Mechanism.find_all_mechanisms()
                name_conflict = [m for m in all_mechanisms if m["name"] == config_name
                                and m["id"] != st.session_state["current_mech_id"]]
                
                # Fehlermeldung bei Namenskonflikt
                if name_conflict:
                    st.error(f"Name \"{config_name}\" bereits vergeben. Bitte wählen Sie einen anderen Namen.")
                    time.sleep(2)
                    st.rerun()
                
                # Update von existierendem Mechanismus
                if st.session_state["current_mech_id"] and config_name == st.session_state["current_mech_name"]:
                    mech = Mechanism(
                        name = config_name,
                        joints = joint_objects,
                        links = link_objects,
                        mechanism_id = st.session_state["current_mech_id"],
                        version = st.session_state["current_mech_version"]
                    )
                    mech.save_mechanism()

                    # Session-States aktualisieren
                    st.session_state["current_mech_id"] = mech.id
                    st.session_state["current_mech_name"] = mech.name
                    st.session_state["current_mech_version"] = mech.version

                    st.success(f"Gültige Konfiguration. Mechanismus \"{mech.name}\" erfolgreich aktualisiert. Neue Version: {mech.version}")
                    time.sleep(3)
                    st.rerun()
                
                # Neuen Mechanismus speichern
                else:
                    mech = Mechanism(name = config_name, joints = joint_objects, links = link_objects)
                    mech.save_mechanism()

                    # Session-States aktualisieren
                    st.session_state["current_mech_id"] = mech.id
                    st.session_state["current_mech_name"] = mech.name
                    st.session_state["current_mech_version"] = mech.version

                    st.success(f"Gültige Konfiguration. Mechanismus \"{mech.name}\" erfolgreich gespeichert.")
                    time.sleep(3)
                    st.rerun()

    st.divider()
    # ============================================================================
    # Konfiguration laden
    # ============================================================================
    st.subheader(":material/open_in_browser: Mechanismus laden", help="Laden Sie eine gespeicherte Konfiguration.")

    mechanisms = Mechanism.find_all_mechanisms()
    if mechanisms:
        # Mapping für die Selectbox (Anzeige: Name (Version)) -> ID
        mech_map = {f"{m["name"]} (Version {m["version"]})": m["id"] for m in mechanisms}
        chosen_mechanism = st.selectbox("**Wähle eine gespeicherte Mechanismus-Konfiguration**", options = ["Keine"] + list(mech_map.keys()), key = "load_config")

        if chosen_mechanism != "Keine":
            if st.button("**Laden**", icon = ":material/open_in_browser:"):
                mechanism_id = mech_map[chosen_mechanism]
                mechanism = Mechanism.load_mechanism(mechanism_id)
                if not mechanism:
                    st.error("Mechanismus nicht gefunden.")
                    time.sleep(2)
                    st.rerun()
                else:
                    # Session-States aktualisieren
                    st.session_state["current_mech_id"] = mechanism_id
                    st.session_state["current_mech_name"] = mechanism.name
                    st.session_state["current_mech_version"] = mechanism.version
                    # Joint und Link Session States
                    st.session_state["joints"] = []
                    st.session_state["links"] = []
                    st.session_state["protected_links"] = set()
                    for joint in mechanism.joints:
                        st.session_state["joints"].append({
                            "x": joint.x,
                            "y": joint.y,
                            "type": joint.type,
                            "center": joint.center,
                            "radius": joint.radius
                        })
                    for link in mechanism.links:
                        start_idx = mechanism.joints.index(link.start_joint)
                        end_idx = mechanism.joints.index(link.end_joint)
                        new_link = tuple(sorted((start_idx, end_idx)))
                        st.session_state["links"].append(new_link)
                        if link.protected:
                            st.session_state["protected_links"].add(new_link)

                    st.success(f"Mechanismus \"{mechanism.name}\" erfolgreich geladen.")
                    time.sleep(2)
                    st.rerun()
        else:
            st.session_state["current_mech_id"] = None
            st.session_state["current_mech_name"] = ""
            st.session_state["current_mech_version"] = 0

        if st.button("**Aktualisieren**", icon = ":material/refresh:", help="Aktualisieren Sie die Seite, um die geladene Konfiguration zu sehen."):
            st.rerun()

    st.divider()
    # ============================================================================
    # Konfiguration löschen
    # ============================================================================
    st.subheader(":material/delete: Mechanismus löschen", help="Löschen Sie eine gespeicherte Konfiguration.")

    saved_configs = Mechanism.find_all_mechanisms()
    if saved_configs:
        # Mapping für die Selectbox (Anzeige: Name (Version)) -> ID
        configs_map = {f"{m["name"]} (Version {m["version"]})": m["id"] for m in saved_configs}
        selected_config_to_delete = st.selectbox("**Wähle eine zu löschende Konfiguration**", options=configs_map, key="delete_config", index=None, placeholder="Konfiguration auswählen")
        if selected_config_to_delete:
            if st.button("Löschen", icon=":material/delete_forever:", help="Löschen Sie die ausgewählte Konfiguration."):
                mechanism_id = configs_map[selected_config_to_delete]
                Mechanism.delete_mechanism(mechanism_id)
                st.success(f"Konfiguration \"{selected_config_to_delete}\" erfolgreich gelöscht.")
                time.sleep(2)
                st.rerun()

    st.divider()

    # ============================================================================
    # Anzeige, ob Mechanismus geladen
    # ============================================================================
    if st.session_state["current_mech_id"]:
        st.write("**Aktuell geladener Mechanismus:**")
        st.info(f"{st.session_state['current_mech_name']} "
                f"(Version {st.session_state['current_mech_version']})"
        )
# ================================================================================
# Visualisierung Mechanismus (col2)
# ================================================================================
with col2:
    # ============================================================================
    # Live-Vorschau der Gelenkkonfiguration
    # ============================================================================
    st.subheader(":material/preview: Live-Vorschau der Gelenkkonfiguration", divider="blue",
                 help="Hier wird die aktuelle Mechanismus-Konfiguration visualisiert. Das gilt auch für geladene Mechanismen."
    )
    
    fig, ax = plt.subplots()
    Visualizer.plot_configuration(st.session_state["joints"], st.session_state["links"], ax=ax)
    st.pyplot(fig, use_container_width=False) 

    st.divider()
    # ============================================================================
    # Simulation Mechanismus (Kinematik)
    # ============================================================================
    st.subheader(":material/animation: Kinematik Simulation", divider="blue", 
                 help="Simulieren Sie die Kinematik eines Mechanismus. Die Simulation wird als GIF-Datei ausgegeben."
    )
    
    all_mechs = Mechanism.find_all_mechanisms()
    if not all_mechs:
        st.info("Keine gespeicherten Mechanismen gefunden.")
    else:
        mech_map = {f"{m['name']} (Version {m['version']})": m["id"] for m in all_mechs}

        # Mechanismus auswählen
        chosen_label = st.selectbox("**Wähle eine gespeicherte Konfiguration aus**", options=["Keine"] + list(mech_map.keys()))

        if chosen_label != "Keine":
            if st.button("**Simulation ausführen**", icon=":material/play_arrow:"):
                # Mechanismus laden:
                mechanism_id = mech_map[chosen_label]
                mech_object = Mechanism.load_mechanism(mechanism_id)
                if not mech_object:
                    st.error("Mechanismus konnte nicht geladen werden.")
                    time.sleep(2)
                    st.rerun()
                else:
                    # Prüfung, ob Kinematik schon berechnet wurde (mechanism_kinematics)
                    theta_range, trajectories = mech_object.load_kinematics(mechanism_id=mech_object.id, mechanism_version=mech_object.version)
                    if not theta_range or not trajectories:
                        # Keine Kinematikdaten vorhanden -> Berechnung durchführen
                        st.info("Keine Kinematik-Daten vorhanden. Berechne Simulation ...")
                        # Startwinkel
                        theta_range = mech_object.compute_theta_range(steps=100)
                        # Kinematik
                        trajectories, fail_count = mech_object.kinematics(theta_range)
                        # Kinematik in DB speichern
                        if not fail_count:
                            mech_object.save_kinematics(theta_range, trajectories)
                            st.success("Kinematik erfolgreich berechnet und in Datenbank gespeichert.")
                        else:
                            st.info(f"Kinematik nicht in Datenbank gespeichert, da {fail_count} von 100 Frames fehlerhaft berechnet wurden.")
                            st.info("Simulation wird trotzdem ausgeführt.")
                    else:
                        st.info("Kinematik wurde bereits berechnet. Lade Simulation ...")

                    print(len(theta_range))
                    print(len(trajectories))
                
                    # GIF erstellen
                    gif_path = Visualizer.create_gif(
                        thetas=theta_range,
                        trajectories=trajectories,
                        joints=mech_object.joints,
                        links=mech_object.links
                    )

                    # CSV-Datei erstellen
                    csv_file = mech_object.save_kinematics_to_csv(theta_range=theta_range, trajectories=trajectories)

                    st.subheader(":material/gif_box: Simulation als GIF:", divider="rainbow")
                    st.image(gif_path, use_container_width=True)

                    # GIF-Datei (Simulation) herunterladen
                    with open(gif_path, "rb") as gif_data:
                        st.download_button(
                            label="**GIF herunterladen**",
                            data=gif_data,
                            file_name="simulation.gif",
                            mime="image/gif",
                            icon=":material/download:"
                        )
                        
                    # CSV-Datei (Kinematikdaten) herunterladen
                    with open(csv_file, "rb") as csv_data:
                        st.download_button(
                            label="**Simulationsergebnisse als CSV herunterladen**",
                            data=csv_data,
                            file_name="Coords_results.csv",
                            mime="text/csv",
                            icon=":material/download:"
                        )

        st.divider()
        # ======================================================
        # Berechnung der Vorwärtsbewegung eines Strandbeests
        # ======================================================
        st.subheader(":material/directions_walk: Berechnung der Vorwärtsbewegung eines Strandbeestbeins", divider="blue", 
                 help="Berechnung der Vorwärtsbewegungsgeschwindigkeit eines Strandbeestbeins, mit Angabe des maximalen Abstands des Fußes zum Boden (Fuß angehoben)."
        )
                
        mechanism_speed = Mechanism.find_all_mechanisms()
        strandbeest_options = {m["name"]: m["id"] for m in mechanisms if "Strandbeest" in m["name"]}

        if not strandbeest_options:
            st.warning("Kein Strandbeest in der Datenbank gefunden.")
        else:
            selected_mechanism = st.selectbox("**Waehle ein Strandbeest**", options=strandbeest_options.keys(), index=None, placeholder="Waehle ein Strandbeest aus")

            if selected_mechanism:
                mechanism_id = strandbeest_options[selected_mechanism]

                # Mechanismus laden
                mechanism = Mechanism.load_mechanism(mechanism_id)

                if not mechanism:
                    st.error("Mechanismus konnte nicht geladen werden.")
                else:
                    theta_range, trajectories = Mechanism.load_kinematics(mechanism_id, mechanism.version)
                    if not trajectories:
                        st.warning("Keine Kinematik Daten gefunden.")
                    else:
                        # Gelenkauswahl
                        joint_options = [f"Gelenk {i + 1}" for i in range(len(trajectories[0]))]
                        selected_joint = st.selectbox(
                            "**Waehle das Gelenk mit Bodenkontakt**",
                            options=joint_options,
                            index=None,
                            help="Waehle das Gelenk, welches für die Fortbewegung (Bodenkontakt) verantwortlich ist",
                            placeholder="Waehle das Gelenk mit Bodenkontakt"
                        )
                        if selected_joint is not None:
                            joint_index = joint_options.index(selected_joint)
                        else:
                            st.stop()

                        # Eingabe für die Anzahl der Umdrehungen der Kurbel
                        revolutions_per_minute = st.number_input(
                            "**Umdrehungen pro Minute** (rpm):",
                            min_value=0.01,
                            max_value=100.0, 
                            step=1.0,
                            value=5.0, 
                            help="Anzahl der Kurbelumdrehungen pro Minute."
                        )

                        # Eingabe für den maximalen Abstand zum Boden, welcher noch zulässig ist
                        ground_contact_tolerance = st.number_input(
                            "**Maximaler Abstand zum Boden, welcher noch akzeptiert wird:**",
                            min_value=0.05,
                            max_value=5.0,
                            step=0.01,
                            help="Maximal zulässiger Abstand zum Boden für die Fortbewegung."
                        )

                        # Berechnung ausführen
                        if st.button("**Berechnung starten**"):
                            try:
                                strandbeest_vel = StrandbeestSpeed(mechanism_id, joint_index, revolutions_per_minute, theta_range, trajectories, ground_contact_tolerance)
                                v_max, stride_length, delta_t = strandbeest_vel.calculate_max_speed()

                                # Ergebnisse ausgeben
                                st.success(f"**Geschwindigkeit:** {v_max:.2f}")
                                st.info(f"**Schrittlaenge:** {stride_length:.2f}")
                                st.info(f"**Bodenkontaktzeit:** {delta_t:.2f} s")
                                                
                                # Visualisierung vom Bodenkontakt mit welchem gerechnet wurde
                                fig, ax = plt.subplots()
                                fig = strandbeest_vel.plot_ground_contact()
                                st.pyplot(fig, use_container_width=False)

                            except ValueError as e:
                                st.error(f"**Fehler:** {e}")

# ================================================================================
# Debugging (Session States anzeigen)
# ================================================================================
print("==================== Session States: ====================")
print("Sperr-Logik:")
print("locked:", st.session_state["locked"])
print("prev_locked:", st.session_state["prev_locked"])
print("---------------------------------------------------------")
print("geladener Mechanismus:")
print("ID:", st.session_state["current_mech_id"])
print("Name:", st.session_state["current_mech_name"])
print("Version:", st.session_state["current_mech_version"])
print("---------------------------------------------------------")
print("Einheit:")
print(st.session_state["unit"])
print("---------------------------------------------------------")
print("Joints:")
for i in range(len(st.session_state["joints"])):
    print(st.session_state["joints"][i])
print("---------------------------------------------------------")
print("Links:")
for i in range(len(st.session_state["links"])):
    print(st.session_state["links"][i])