# markup_language.py 

from mechanism import Mechanism

# ========================================================================================================================
# Erstellung eines LaTex Dokuments mit Tabelle von Gelenken und Verbindungen und einer Grafik von der Grundkonfigurierung
# ========================================================================================================================

class MechanismLatex:
    """ 
    Erstellt ein LaTex Dokument zu einem Mechanismus
    Im Dokument wird die ID, der Name und die Version des Mechanismus gezeigt. 
    Eine Tabelle für Gelenke und eine Tabelle für Verbindungen und deren Eigenschaften wird erstellt.
    Ein TikZ-Diagramm zur Veranschaulichung des Mechanismus wird erzeugt.

    """
    @staticmethod
    def create_document(mechanism: Mechanism) -> str:
        # LaTex-Dokument-Kopf
        header = r"""\documentclass{article}  
\usepackage{geometry}
\usepackage{array}
\usepackage{tikz}
\geometry{a4paper, margin=1in}
\usepackage{booktabs}
%TikZ-Stile definieren
\tikzset{
   joint/.style={circle, draw, fill=blue!70, inner sep=1pt},
   link/.style={thick, draw=black} }

\begin{document}
"""
                        
        # Mechanismus Details
        title = r"""\section*{Stueckliste und Visualisierung von: %s}""" % mechanism.name
        details = r"""
\textbf{ID:} %s \\
\textbf{Version:} %s\\
""" % (mechanism.id, mechanism.version) # wird dem Platzhalter %s (für str) übergeben
        
        # Tabelle mit Gelenke erstellen
        # Zwischenüberschrift
        joints_section = r"""\subsection*{Gelenke} """
        # Tabellen erstellen
        joints_section = joints_section + r"""
\begin{table}[h]
    \centering
    \begin{tabular}{|c|c|c|c|c|}
    \toprule """
        joints_section = joints_section + r""" 
        Gelenk Nr. & x & y & Typ & Drehmittelpunkt und Radius \\ \midrule """
        for idx, joint in enumerate(mechanism.joints):
            circle_movement = ""
            if joint.type == "Kreisbahnbewegung" and joint.center:
                circle_movement = "Center: (%.2f, %.2f), Radius: %.2f" % (joint.center[0], joint.center[1], joint.radius)
            joints_section = joints_section + "%d & %.2f & %.2f & %s & %s \\\\ \\hline\n" % (idx+1, joint.x, joint.y, joint.type, circle_movement)
        joints_section = joints_section + r"""  
    \end{tabular}
\end{table} """

        
        # Zwischenüberschrift Verbindungen
        links_section = r"""
\subsection*{Verbindungen} """

        # Tabelle mit Verbindungen
        links_section = links_section + r""" 
\begin{table}[h]
    \centering
    \begin{tabular}{|c|c|c|c|}
    \toprule """
        links_section = links_section + r""" 
        Verbindung Nr. & Start Gelenk & End Gelenk & Laenge \\ \midrule """
        for idx, link in enumerate(mechanism.links):
            try:
                start_index = mechanism.joints.index(link.start_joint) + 1
                end_index = mechanism.joints.index(link.end_joint) + 1
            except ValueError:
                start_index, end_index = "/", "/"
            links_section = links_section + "%d & %s & %s & %.2f \\\\ \\hline\n" %(idx+1, start_index, end_index, link.length if link.length is not None else 0)
        links_section = links_section + r""" 
    \end{tabular} 
\end{table} """

        # Mechanismus zeichnen
        tikz_section = r"""
\subsection*{Grafik vom Mechanismus}
\resizebox{\textwidth}{!}{
    \begin{tikzpicture} """
        for idx, joint in enumerate(mechanism.joints):
            # Zeichnet alle Knoten mit Beschriftung
            tikz_section = tikz_section + r"""
        \node[joint] (J%d) at (%.2f, %.2f); """ % (idx+1, joint.x, joint.y)
            if joint.type == "Kreisbahnbewegung" and joint.center is not None and joint.radius is not None:
                tikz_section = tikz_section + r"""
        # Kreis zeichnen - strichliert in blau
        \draw[dashed, blue] (%.2f, %.2f) circle (%.2f); """ % (joint.center[0], joint.center[1], joint.radius)
    
        # Zeichnen der Verbindungen
        for idx, link in enumerate(mechanism.links):
            start_index = mechanism.joints.index(link.start_joint) + 1
            end_index = mechanism.joints.index(link.end_joint) + 1
            tikz_section = tikz_section + r"""
        \draw (J%d) -- (J%d); """ % (start_index, end_index)
        
        tikz_section = tikz_section + r"""
    \end{tikzpicture} 
}"""
    
        # LaTex Dokument Ende
        doc_end = r""" 
\end{document} """

        latex_document = header + title + details + joints_section + links_section + tikz_section + doc_end

        return latex_document

# ==========================================
# Modultest für das Erstellen eines LaTex Dokuments
# ==========================================
if __name__ == "__main__":

    mechanisms = Mechanism.find_all_mechanisms()
    if not mechanisms:
        print("Keine Mechanismen in der DB gefunden")
    else:
        mech_info = mechanisms[0]
        mechanism_id = mech_info["id"]

        # Mechanismus laden
        mechanism = Mechanism.load_mechanism(mechanism_id)
        if not mechanism:
            print("Konnte nicht geladen werden")
        else:
            latex_str = MechanismLatex.create_document(mechanism)
            output_file = "mechanism_document.tex"
            with open(output_file, "w") as f:
                f.write(latex_str)
            print("Erfolgreich abgeschlossen: " + output_file)
