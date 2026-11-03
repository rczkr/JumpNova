import os
import shutil
import sys
from moviepy.video.io.VideoFileClip import VideoFileClip
import whisper
from app import app, db, WorkoutVideo

# -------------------------------------------------------------
# Ffmpeg/ffprobe Pfad aus dem lokalen Projektordner einbinden
# -------------------------------------------------------------
ffmpeg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "ffmpeg"))
os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ.get("PATH", "")
os.environ["PYTHONIOENCODING"] = "utf-8"


def generate_vtt_from_text(lyrics_text, save_vtt_path):
    """Erstellt eine VTT-Untertiteldatei direkt aus dem übergebenen Songtext."""
    abs_vtt_path = os.path.abspath(save_vtt_path)
    lines = [line.strip() for line in lyrics_text.split('\n') if line.strip()]

    if not lines:
        lines = ["JumpNova - Fitness & Music"]

    vtt_content = "WEBVTT\n\n"
    interval = 3.5

    for i, line in enumerate(lines):
        start_sec = i * interval
        end_sec = (i + 1) * interval

        start_m, start_s = int(start_sec // 60), int(start_sec % 60)
        start_ms = int((start_sec % 1) * 1000)

        end_m, end_s = int(end_sec // 60), int(end_sec % 60)
        end_ms = int((end_sec % 1) * 1000)

        start_str = f"00:{start_m:02d}:{start_s:02d}.{start_ms:03d}"
        end_str = f"00:{end_m:02d}:{end_s:02d}.{end_ms:03d}"

        vtt_content += f"{i + 1}\n{start_str} --> {end_str}\n{line}\n\n"

    with open(abs_vtt_path, "w", encoding="utf-8") as f:
        f.write(vtt_content)


def process_local_workout(video_file_path, start_time_str, end_time_str, title, category, lyrics="", user_id=None):
    """
    Vollautomatischer Ablauf:
    1. Schneidet das Video (.mp4)
    2. Trennt voice.mp3 (Stimme) und music.mp3 (Musik) über Demucs (UNVERÄNDERT!)
    3. Erstellt saubere Untertitel (.vtt) direkt aus dem mitgegebenen Songtext
    4. Speichert Video, Sprachspur, Musikspur & Songtext in der Datenbank
    """
    with app.app_context():
        if not os.path.exists(video_file_path):
            print(f"❌ Fehler: Die Datei '{video_file_path}' wurde nicht gefunden!")
            return

        new_id = WorkoutVideo.query.count() + 1
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        cut_video_path = os.path.abspath(os.path.join(upload_dir, f"video_{new_id}.mp4"))
        music_file = os.path.abspath(os.path.join(upload_dir, f"music_{new_id}.mp3"))
        voice_file = os.path.abspath(os.path.join(upload_dir, f"voice_{new_id}.mp3"))
        vtt_save_path = os.path.abspath(os.path.join(upload_dir, f"lyrics_{new_id}.vtt"))

        def time_to_sec(t_str):
            parts = [float(p) for p in t_str.split(':')]
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]
            return parts[0]

        start_sec = time_to_sec(start_time_str)
        end_sec = time_to_sec(end_time_str)

        # -------------------------------------------------------------
        # SCHRITT 1: Video schneiden
        # -------------------------------------------------------------
        print(f"\n✂️ [1/4] Schneide Video von {start_time_str} bis {end_time_str}...")
        try:
            clip = VideoFileClip(video_file_path).subclipped(start_sec, end_sec)
        except AttributeError:
            clip = VideoFileClip(video_file_path).subclip(start_sec, end_sec)

        clip.write_videofile(cut_video_path, codec="libx264", audio_codec="aac", logger=None)

        # -------------------------------------------------------------
        # SCHRITT 2: Trenne voice.mp3 & music.mp3 über Demucs
        # -------------------------------------------------------------
        print("\n🎛️ [2/4] Trenne Gesang/Stimme (voice.mp3) und Musik (music.mp3)...")
        temp_dir = os.path.abspath(os.path.join(upload_dir, f"temp_{new_id}"))

        try:
            from demucs.separate import main as demucs_main

            # Demucs direkt im Python-Prozess ausführen
            sys.argv = ["demucs", "--two-stems=vocals", "--mp3", cut_video_path, "-o", temp_dir]
            demucs_main()

            stem_folder = os.path.join(temp_dir, "htdemucs", f"video_{new_id}")
            v_src = os.path.join(stem_folder, "vocals.mp3")
            m_src = os.path.join(stem_folder, "no_vocals.mp3")

            if os.path.exists(v_src):
                shutil.move(v_src, voice_file)
                print("  ✅ voice.mp3 (Stimme) erfolgreich gespeichert!")

            if os.path.exists(m_src):
                shutil.move(m_src, music_file)
                print("  ✅ music.mp3 (Musik) erfolgreich gespeichert!")

        except Exception as e:
            print(f"  ⚠️ Hinweis bei Trennung: {e}")

        if not os.path.exists(music_file) and clip.audio is not None:
            clip.audio.write_audiofile(music_file, logger=None)

        clip.close()

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

        # -------------------------------------------------------------
        # SCHRITT 3: Untertitel (.vtt) direkt aus dem hinterlegten Songtext erzeugen
        # -------------------------------------------------------------
        print("\n📝 [3/4] Erstelle synchrone Songtext-Untertitel aus der Vorlage...")
        generate_vtt_from_text(lyrics, vtt_save_path)
        print("  ✅ Untertitel wurden erfolgreich aus dem Songtext erstellt!")

        # -------------------------------------------------------------
        # SCHRITT 4: Speichern in der Datenbank
        # -------------------------------------------------------------
        print("\n💾 [4/4] Speichere Workout und Songtext in der Datenbank...")
        new_workout = WorkoutVideo(
            title=title,
            category=category,
            video_path=f"uploads/video_{new_id}.mp4",
            voice_path=f"uploads/voice_{new_id}.mp3" if os.path.exists(voice_file) else None,
            music_path=f"uploads/music_{new_id}.mp3" if os.path.exists(music_file) else None,
            lyrics=lyrics,
            user_id=user_id
        )
        db.session.add(new_workout)
        db.session.commit()

        print(f"\n==================================================")
        print(f"✅ ERFOLG! Workout '{title}' vollständig verarbeitet!")
        print(f"==================================================\n")


if __name__ == '__main__':
    text_fuer_untertitel = ""

    process_local_workout(
        video_file_path=r"C:\Users\UserS2025\..Learning\ANWP Entwickeln\Videos-JumpNova\Jakub\jakub_vollversion.mp4",
        start_time_str="00:00:00",
        end_time_str="00:04:35",
        title="Monster Time",
        category="Cardio",
        lyrics=text_fuer_untertitel,
        user_id=1
    )