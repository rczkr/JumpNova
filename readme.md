# 🚴‍♀️ JumpNova – Interactive Jumping Fitness Platform

Eine moderne Web-Anwendung für interaktive Jumping-Fitness-Workouts mit automatisierter Video-Verarbeitungs-Pipeline, getrennter Audio-Steuerung (Dual Audio) und synchronem Songtext-Player.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat&logo=flask&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.0+-06B6D4?style=flat&logo=tailwindcss&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-SQLAlchemy-003B57?style=flat&logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Status-In_Active_Development-orange?style=flat)

---

## 🚧 Projekt-Status & Ausblick (Work in Progress)

Dieses Projekt befindet sich aktuell in der **aktiven Weiterentwicklung**. 

**Geplante nächste Features & Erweiterungen:**
* 🎯 Erweiterung der Workout-Mix-Funktion um spezielle Motivations-Einspieler (`fire_style_video_id`).
* ⏱️ Auswählbare Timer-Designs (z. B. Klassisch vs. Fire & Power Overlay).
* 📊 Erweiterte Statistiken für den persönlichen Trainingsverlauf im Mitgliederbereich.

---

## ℹ️ Rechtliche Hinweise & Videomaterial

> **Hinweis zur Nutzung von Videomaterial:**  
> Für die Entwicklung und Demonstration dieses Prototyps liegt die **ausdrückliche Erlaubnis des Rechteinhabers** (Jumping Fitness) vor, das Videomaterial zu verwenden, zuzuschneiden und im Rahmen der Anwendungslogik zu bearbeiten. Alle Rechte am ursprünglichen Bild- und Tonmaterial verbleiben bei den jeweiligen Urhebern.

---

## 🌟 Key Features

* **🎛️ Dual-Audio Control:** Getrennte Lautstärkeregelung für die Musik- und die Trainer-Tonspur im Player.
* **📝 Synchrone Songtexte:** Automatische Generierung von VTT-Untertiteln für eine synchrone Songtext-Einblendung während des Workouts.
* **⚙️ Automated Video Pipeline:** Automatisches Schneiden von MP4-Videos (MoviePy) und KI-gestützte Audiotrennung von Gesang & Musik (Demucs).
* **🔀 Custom Workout Mixer:** Mitglieder können sich eigene individuelle Workout-Playlists zusammenstellen und die Reihenfolge anpassen.
* **🎯 Dynamic Filtering:** Ausführliche Filteroptionen nach Kategorie, Schwierigkeit, Musikstil und Special-Events (z. B. *Summer-Vibes*).
* **🔒 Rolle & Rechteverwaltung:** Unterscheidung zwischen regulären Mitgliedern und VIP-Trainern mit eigenem Upload- und Verwaltungsbereich.

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask, Flask-SQLAlchemy (SQLite)
* **Frontend:** HTML5, Jinja2 Templates, Tailwind CSS (Custom Dark Mode / Cyberpunk Aesthetic)
* **Media & Audio Processing:** MoviePy, Demucs (Facebook Research Stem Separation), FFmpeg
* **Database & ORM:** SQLAlchemy (Entity-Relationship-Design mit Cascading Deletes)

---

## 📂 Projektdatenbank-Struktur (ERD)

Die Datenbank umfasst folgende Haupt-Entitäten:
* `User`: Benutzerverwaltung (Mitglieder & VIP-Trainer)
* `WorkoutVideo`: Metadaten, Video- & Pfadangaben (Voice/Music), Songtexte
* `FireStyleVideo`: Motivations-Einspieler für den Mixer
* `UserMix` / `MixVideo`: m:n-Verknüpfung für benutzerspezifische Workout-Mixe
* `WatchHistory` & `Favorite`: Wiedergabeverlauf und Favoritenliste

---

## 🚀 Installation & Lokale Ausführung

1. **Repository klonen:**
   ```bash
   git clone [https://github.com/DEIN-GITHUB-NAME/JumpNova.git](https://github.com/DEIN-GITHUB-NAME/JumpNova.git)
   cd JumpNova