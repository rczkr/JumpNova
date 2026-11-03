from app import app, db, WorkoutVideo

with app.app_context():
    # Zeige alle vorhandenen Workouts mit ihrer ID an
    workouts = WorkoutVideo.query.all()
    print("--- Aktuelle Workouts in der Datenbank ---")
    for w in workouts:
        print(f"ID: {w.id} | Titel: {w.title} | Pfad: {w.video_path}")

    # Hier den Titel des zu löschenden Videos eintragen:
    titel_zum_loeschen = "Monster Dance" # <--- Hier den Titel anpassen

    verwaist = WorkoutVideo.query.filter_by(title=titel_zum_loeschen).first()
    if verwaist:
        db.session.delete(verwaist)
        db.session.commit()
        print(f"✅ Workout '{titel_zum_loeschen}' wurde erfolgreich aus der Datenbank gelöscht!")
    else:
        print(f"❌ Kein Workout mit dem Titel '{titel_zum_loeschen}' gefunden.")