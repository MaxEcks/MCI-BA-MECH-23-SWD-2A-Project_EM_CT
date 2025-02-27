# MCI-BA-MECH-23-SWD-2A-Project_EM_CT
Abschlussprojekt Softwaredesign BA-MECH-23: Eckstein Maximilian, Czermak Tobias
# Projekt Simulation ebener Mechanismen

## Kurzer Projektüberblick der Mindestanforderungen

Mittels diesem objektorientierten Python Projekts ist auf einer Benutzeroberfläche (Streamlit) die Konfiguration ebener Mechanismen mit vorgegebenen Einschränkungen möglich. Außerdem kann der modellierte Mechanismus und seine Bahnkurven simuliert werden. Der Nutzer kann die Mechanismen speichern, laden und löschen. Die berechnete Kinematik (als Optimierungsproblem mit Scipy‘s least\_squares gelöst) kann ebenso in einer Datenbank gespeichert, geladen und gelöscht werden. Es ist möglich die Kinematik eines konfigurierten Mechanismus als CSV-Datei herunterzuladen. Der Mechanismus wird außerdem auch auf Validität überprüft. Die Funktion der Implementierung wird am Strandbeestbein getestet und als GIF-Animation beigefügt. Außerdem wird die Anwendung auf Streamlit deployed. 

Link zur Streamlit Anwendung (auf Streamlit Community Cloude deployed): https://2d-mechanism-sim-mci-ba-mech-23-swd.streamlit.app/ 

Die zuvor genannten Einschränkungen: Es werden ausschließlich Drehgelenke verwendet, die mit starren Gliedern verbunden sind. Nur ein Gelenk – der Antrieb – hat einen rotatorischen Freiheitsgrad und dreht sich um einen fixen Drehpunkt. Dieser Drehpunkt bildet imaginär mit einem zweiten fixierten Gelenk das Gestell für den Mechanismus. Damit zum Beispiel der Mechanismus eines Viergelenks funktioniert, muss ein weiteres frei bewegliches Gelenk bestehen, dessen Position in der Ebene durch die Verbindung mit starren Gliedern (Verbindung zum Gelenk mit dem rotatorischen Freiheitsgrad und zum fixierten Gelenk) definiert wird. Damit der Mechanismus simuliert werden kann, wird für das Gelenk mit der Kreisbahnbewegung ein konstanter Drehwinkel Theta betrachtet (von Startwinkel der Konfiguration bis 360° + Startwinkel).

Zu diesen Minimalanforderungen werden Erweiterungen implementiert, die später gezeigt werden.
## Verifizierung anhand vom Strandbeestbein
GIF von unserer Anwendung heruntergeladen:

![Strandbeestbein](https://github.com/user-attachments/assets/0ffc61eb-8891-4e3b-a218-cd6710f3bfcf)

## UML-Diagramm vom Projekt

![UML_Diagramm_SWD_Projekt](https://github.com/user-attachments/assets/f18626f0-e032-40c3-b3d0-6e61e65acf57)


## Installation und Ausführung der Anwendung
### 1. Repository klonen
```
git clone https://github.com/MaxEcks/MCI-BA-MECH-23-SWD-2A-Project_EM_CT.git
cd ordner_vom_projekt
```

### 2. Virtuelle Umgebung erstellen und aktivieren
```
python -m venv .venv
.\.venv\Scripts\activate
```

### 3. Abhängigkeiten installieren
```
pip install -r requirements.txt
```

### 4. Anwendung starten (User Interface mit Streamlit)
```
streamlit run .\main.py
```
## Projektstruktur und Grundlagen
Das Projekt ist in mehrere Module unterteilt mit welchen alle Minimalanforderungen, sowie einige Erweiterungen in das Projekt implementiert sind:

1. **main.py**

   Dieses Modul enthält die Streamlit-Web-UI zur Konfiguration, Visualisierung und Simulation der Mechanismen. Der Benutzer kann einzelne Gelenke mit den genannten Einschränkungen konfigurieren und diese miteinander verbinden. Man kann zur Hilfestellung auch nur gültige Gelenktyp-Konfigurationen zulassen (Typ-Auswahl sperren). Des Weiteren können Mechanismen gespeichert, geladen und gelöscht werden. In der rechten Spalte der Benutzeroberfläche wird Live die Konfiguration dargestellt. Darunter kann die Simulation von einem gespeicherten Mechanismus geladen (Selectbox), sowie als GIF dargestellt werden. Die ausgeführte Simulation kann dann als GIF exportiert werden. Die berechneten Bahnkurven der Gelenke können ebenfalls als CSV-Datei heruntergeladen werden. Außerdem ist es möglich die Vorwärtsbewegungs-Geschwindigkeit eines Strandbeestbeins zu berechnen und darzustellen. Zusätzlich ist ein Download eines LaTex Dokuments von einem gespeicherten Mechanismus möglich. Die Datenbank kann als Backup heruntergeladen bzw. umgekehrt ein Backup wieder hochgeladen werden. 

1. **mechanism.py**

   Dieses Modul enthält grundlegend die Klassen Joint, Link und Mechanism. In der Klasse Mechanism wird die Kinematik des Mechanismus mit Hilfe von Scipy Optimierung (least\_squares) berechnet. Die berechneten Trajektorien können als CSV-Datei gespeichert werden. Außerdem ist das Speichern, Laden, Suchen und Löschen von Mechanismus-Konfigurationen, sowie das Speichern, Laden und Löschen von berechneten Kinematiken in einer TinyDB möglich. Zusätzlich wird in diesem Modul der Mechanismus validiert.

1. **database.py**

   Dient zur Verwaltung des Zugriffs auf die TinyDB-Datenbank, in welcher die Mechanismus-Konfigurationen und Kinematik-Daten in Tabellen gespeichert werden. 

1. **visualization.py**

   Die Klasse Visualizer enthält eine Funktion zur Darstellung der Live-Konfiguration (plottet die Gelenke, Verbindungen und Legende). Eine zweite Funktion (create\_gif) ermöglicht die Erstellung eines animierten GIFs des Mechanismus mittels Matplotlib und FuncAnimation.

1. **movement\_speed.py**

   Dieses Modul enthält die Klasse StrandbeestSpeed. Damit kann anhand von Kinematik-Daten eines Strandbeestbeins und dessen ausgewählten Gelenks (welches Bodenkontakt hat) die maximale Vorwärtsbewegung-Geschwindigkeit berechnet werden. Die Kontaktpunkte mit dem Boden werden visuell dargestellt. Im UI kann die eine Längeneinheit definiert werden, welche dann in die Berechnungen miteinfließt.

1. **markup\_language.py**

   Mit Hilfe von diesem Modul kann für einen gespeicherten Mechanismus ein LaTex-Dokument erzeugt werden. Es werden alle Details des Mechanismus (ID, Name, Version) dokumentiert, eine Tabelle für die verwendeten Gelenke und Verbindungen erstellt und die Eigenschaften wie Gelenktyp oder Verbindungslänge ausgegeben. Die Konfiguration des Mechanismus wird grafisch mit Hilfe von TikZ dargestellt. Es wird eine .tex-Datei generiert. Diese kann mit einem LaTex-Compiler in eine PDF-Datei umgewandelt werden.
   
## Erweiterungen
1) In der Benutzeroberfläche wird durch die Auswahl von „Nur gültige Gelenktypen-Konfigurationen zulassen (Typ-Auswahl sperren)“ der Benutzer unterstützt und die Wahrscheinlichkeit für eine fehlerhafte Eingabe minimiert. 
2) Zur Erleichterung der Modellierung wird der aktuelle Konfigurationsstand des Mechanismus dargestellt (Beispiel am Viergelenkgetriebe siehe Bild).


![Konfiguration_Darstellung](https://github.com/user-attachments/assets/59254bad-dbc7-4aba-b00c-bdc489ff592e)



3) Im User Interface kann der Mechanismus animiert werden. Ist die Animation fertig geladen, so kann eine CSV-Datei oder ein GIF per Button klick exportiert werden.
4) Eine weitere Zusatzaufgabe ist die Implementierung der Berechnung der maximalen Vorwärtsbewegungs-Geschwindigkeit eines Strandbeestbeins. Für die Berechnung muss im UI ein gespeichertes Strandbeestbein ausgewählt werden, für welches bereits eine Kinematik-Simulation existiert. Dann kann das Gelenk, welches in Kontakt mit dem Boden kommt, ausgewählt werden. Für die Berechnung wird zusätzlich die Umdrehung pro Minute für die Kurbel benötigt (Radius vom Gelenk mit Kreisbahnbewegung bildet die Kurbel), sowie eine Toleranz, welche den maximalen Abstand des Gelenks zum Boden definiert. Nach erfolgreicher Berechnung wird die Geschwindigkeit, die Schrittlänge, die Bodenkontaktzeit, sowie eine Visualisierung der Kontaktpunkte ausgegeben (siehe Bilder).
<p align="center">
<img width="800" alt="Vorwaertsbewegung_ausgabe" src="https://github.com/user-attachments/assets/52a4a141-1a8a-4d00-b992-16bc05687505" />
</p>

![Visualisierung_bodenkontaktpunkte](https://github.com/user-attachments/assets/324deb70-6ac8-4837-acb4-74fa441b1c9e)


5) Als nächste Erweiterung ist das Exportieren eines LaTex-Dokuments in der Benutzeroberfläche implementiert. Dazu kann ein gespeicherter Mechanismus geladen werden und per Download-Button „LaTex Dokument herunterladen“ zum Download freigegeben werden. In der LaTex Datei wird der Name des Mechanismus, die ID, die Version, eine Tabelle für die Gelenke, eine Tabelle für die Verbindungen, sowie eine Grafische Darstellung der Anfangskonfiguration ersichtlich (siehe Bilder).

<img width="308" alt="Latex_tabellen" src="https://github.com/user-attachments/assets/78341993-d579-4f99-8249-868dceb30d5e" />

<img width="236" alt="Latex_grafik" src="https://github.com/user-attachments/assets/2bb012c2-f2ff-4404-8d49-7f76ac1d2e6b" />



6) Mit einer weiteren zusätzlichen Implementierung ist es nun möglich ein Backup von der Datenbank zu erstellen. Außerdem kann man einen gespeicherten Zwischenstand der Datenbank wieder hochladen.
Als Benutzer der Streamlit-Webanwendung greift man auf eine temporäre Datenbank zu. Wird die Seite beispielsweise neu geladen, wird die Datenbank auf die Standard-Datenbank im Repository zurückgesetzt. Dank dieser Implementierung ist es für den Benutzer möglich, seine Konfigurationen und Kinematiken zu behalten.

7) Generell bietet das UI viele zusätzliche Erweiterungen, Abfragen, Fallback-Funktionen, etc. (z.B. das Laden von Mechanismen, die Gleichheitskontrolle, ...) 

## Weitere Informationen
Im Zuge des Projekts wurde KI (ChatGPT) für die grundlegende Konzeptentwicklung, sowie zur Ideengenerierung verwendet. Ebenfalls wurde dieses Tool für die Fehlersuche zum Beispiel in der error\_funktion und optimization\_function im Modul mechanism.py genutzt. Der Datenbank Export und Import, sowie die Gleichheitsüberprüfung bei der Mechanismus-Konfigurationsabspeicherung wurde ebenfalls mit KI Unterstützung ausgearbeitet.
