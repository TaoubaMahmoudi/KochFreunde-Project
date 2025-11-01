# KochFreunde: Webanwendung für Kochrezepte

## 1. Projektübersicht
Dies ist das finale Code-Repository für das Portfolio-Projekt "KochFreunde" (DLMCSPSE01_D).

**Ziel:** Entwicklung einer Dreischicht-Anwendung (Flask/SQLite) zur Verwaltung von Nutzerprofilen, Rezepten (CRUD), Bewertungen, Favoriten und einer KI-gestützten Rezeptsuche.

**Technologien:**
* **Backend:** Python 3.x, Flask, Flask-SQLAlchemy, Flask-Login
* **Datenbank:** SQLite
* **Frontend:** HTML5, Jinja2, Bootstrap

---

## 2. Quick Start Guide (Anwendung ausführen)

Diese Anleitung beschreibt, wie das Projekt lokal ausgeführt werden kann.

### 2.1. Voraussetzungen
* Python 3.x ist installiert.
* Das Terminal ist geöffnet.

### 2.2. Installation
1.  **Repository klonen / ZIP entpacken:** Stellen Sie sicher, dass Sie sich im Stammverzeichnis des Projekts befinden.
2.  **Virtuelle Umgebung erstellen und aktivieren:**
    ```bash
    python -m venv venv
    # Unter Windows:
    .\venv\Scripts\activate
    # Unter Linux/MacOS:
    source venv/bin/activate
    ```
3.  **Abhängigkeiten installieren:** Alle benötigten Python-Pakete sind in der `requirements.txt` gelistet.
    ```bash
    pip install -r requirements.txt
    ```

### 2.3. Anwendung starten
1.  **Datenbank prüfen:** Das Projekt enthält bereits die Datei `site.db` mit vorbereiteten Testdaten.
2.  **Flask-Server starten:**
    ```bash
    flask run
    ```
3.  **Im Browser öffnen:**
    Öffnen Sie Ihren Webbrowser und navigieren Sie zu: `http://127.0.0.1:5000/`

