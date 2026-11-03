import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jumpnova_ihk_project_secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jumpnova.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

db = SQLAlchemy(app)


# -------------------------------------------------------------
# HILFSFUNKTION FÜR VTT-UNTERTITEL
# -------------------------------------------------------------
def generate_vtt_from_text(lyrics_text, save_vtt_path):
    abs_vtt_path = os.path.abspath(save_vtt_path)
    lines = [line.strip() for line in (lyrics_text or "").split('\n') if line.strip()]

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


# -------------------------------------------------------------
# DATENBANK MODELLE
# -------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')

    workouts = db.relationship('WorkoutVideo', backref='trainer', lazy=True)
    mixes = db.relationship('UserMix', backref='user', lazy=True, cascade="all, delete-orphan")
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade="all, delete-orphan")
    history = db.relationship('WatchHistory', backref='user', lazy=True, cascade="all, delete-orphan")


class WorkoutVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)

    schwierigkeit = db.Column(db.String(50), nullable=True)
    musicstyl = db.Column(db.String(50), nullable=True)
    special = db.Column(db.String(50), nullable=True)

    video_path = db.Column(db.String(200), nullable=False)
    voice_path = db.Column(db.String(200), nullable=True)
    music_path = db.Column(db.String(200), nullable=True)
    lyrics = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Verknüpfungen mit Löschweitergabe (Cascade)
    mix_entries = db.relationship('MixVideo', backref='video', lazy=True, cascade="all, delete-orphan")
    fav_entries = db.relationship('Favorite', backref='video', lazy=True, cascade="all, delete-orphan")
    history_entries = db.relationship('WatchHistory', backref='video', lazy=True, cascade="all, delete-orphan")


class FireStyleVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    video_path = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)


class UserMix(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mix_videos = db.relationship('MixVideo', backref='mix', lazy=True, cascade="all, delete-orphan", order_by="MixVideo.order")


class MixVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mix_id = db.Column(db.Integer, db.ForeignKey('user_mix.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('workout_video.id'), nullable=False)
    order = db.Column(db.Integer, default=1)


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('workout_video.id'), nullable=False)


class WatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('workout_video.id'), nullable=False)
    play_count = db.Column(db.Integer, default=1)
    last_watched = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# -------------------------------------------------------------
# SEITEN-ROUTEN & ZUGRIFFSSCHUTZ
# -------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/homeworkout')
@app.route('/homeworkout/<int:video_id>')
def homeworkout(video_id=None):
    if 'user_id' not in session:
        return redirect(url_for('login_user'))

    cat_filter = request.args.get('category')
    diff_filter = request.args.get('schwierigkeit')
    style_filter = request.args.get('musicstyl')
    spec_filter = request.args.get('special')

    query = WorkoutVideo.query

    if cat_filter and cat_filter != 'Alle':
        query = query.filter_by(category=cat_filter)
    if diff_filter and diff_filter != 'Alle':
        query = query.filter_by(schwierigkeit=diff_filter)
    if style_filter and style_filter != 'Alle':
        query = query.filter_by(musicstyl=style_filter)
    if spec_filter and spec_filter != 'Alle':
        query = query.filter_by(special=spec_filter)

    videos = query.all()

    active_video = None
    if video_id:
        active_video = WorkoutVideo.query.get(video_id)
    if not active_video and videos:
        active_video = videos[-1]

    if active_video and 'user_id' in session:
        user_id = session['user_id']
        history_entry = WatchHistory.query.filter_by(user_id=user_id, video_id=active_video.id).first()
        if history_entry:
            history_entry.play_count += 1
            history_entry.last_watched = datetime.utcnow()
        else:
            new_history = WatchHistory(user_id=user_id, video_id=active_video.id, play_count=1)
            db.session.add(new_history)
        db.session.commit()

    fire_videos = FireStyleVideo.query.all()
    user_mixes = UserMix.query.filter_by(user_id=session['user_id']).all()

    return render_template(
        'homeworkout.html',
        videos=videos,
        active_video=active_video,
        fire_videos=fire_videos,
        user_mixes=user_mixes,
        cat_filter=cat_filter,
        diff_filter=diff_filter,
        style_filter=style_filter,
        spec_filter=spec_filter
    )


# -------------------------------------------------------------
# USER MIX ROUTEN (ERSTELLEN, LÖSCHEN, API)
# -------------------------------------------------------------
@app.route('/mix/create', methods=['POST'])
def create_mix():
    if 'user_id' not in session:
        flash("Bitte melde dich an!", "error")
        return redirect(url_for('login_user'))

    mix_title = request.form.get('mix_title', 'Mein Workout Mix')
    selected_video_ids = request.form.getlist('video_ids')

    if not selected_video_ids:
        flash('Bitte wähle mindestens ein Video für deinen Mix aus!', 'error')
        return redirect(url_for('homeworkout'))

    new_mix = UserMix(title=mix_title, user_id=session['user_id'])
    db.session.add(new_mix)
    db.session.commit()

    for idx, vid_id in enumerate(selected_video_ids, start=1):
        mix_vid = MixVideo(mix_id=new_mix.id, video_id=int(vid_id), order=idx)
        db.session.add(mix_vid)

    db.session.commit()
    flash(f'🎶 Mix "{mix_title}" erfolgreich erstellt!', 'success')
    return redirect(url_for('homeworkout'))


@app.route('/mix/delete/<int:mix_id>', methods=['POST'])
def delete_mix(mix_id):
    if 'user_id' not in session:
        return redirect(url_for('login_user'))

    user_mix = UserMix.query.get_or_404(mix_id)
    if user_mix.user_id == session['user_id']:
        db.session.delete(user_mix)
        db.session.commit()
        flash('Mix gelöscht!', 'success')

    return redirect(url_for('homeworkout'))


@app.route('/api/mix/<int:mix_id>')
def get_mix_data(mix_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Nicht angemeldet'}), 401

    user_mix = UserMix.query.get_or_404(mix_id)

    playlist = []
    for item in user_mix.mix_videos:
        vid = item.video
        if vid:
            playlist.append({
                'id': vid.id,
                'title': vid.title,
                'category': vid.category,
                'video_path': url_for('static', filename=vid.video_path),
                'voice_path': url_for('static', filename=vid.voice_path) if vid.voice_path else '',
                'music_path': url_for('static', filename=vid.music_path) if vid.music_path else '',
                'vtt_path': url_for('static', filename=f'uploads/lyrics_{vid.id}.vtt'),
                'lyrics': vid.lyrics or 'Keine Songtexte vorhanden.'
            })

    return jsonify({
        'title': user_mix.title,
        'playlist': playlist
    })


# -------------------------------------------------------------
# REGISTRIERUNG & LOGIN
# -------------------------------------------------------------
@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash("Benutzername existiert bereits!", "error")
            return redirect(url_for('register_user'))

        new_user = User(username=username, password=password, role='user')
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['role'] = 'user'
        return redirect(url_for('homeworkout'))

    return render_template('register_user.html')


@app.route('/login/user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('homeworkout'))
        else:
            flash("Ungültige Anmeldedaten!", "error")
            return redirect(url_for('login_user'))

    return render_template('login_user.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash("Benutzername existiert bereits!", "error")
            return redirect(url_for('register'))

        new_user = User(username=username, password=password, role='trainer')
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['role'] = 'trainer'
        return redirect(url_for('vip'))

    return render_template('register_vip.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()
        if user and user.role == 'trainer':
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('vip'))
        else:
            flash("Ungültige Anmeldedaten oder kein Trainer-Account!", "error")
            return redirect(url_for('login'))

    return render_template('login_vip.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# -------------------------------------------------------------
# VIP TRAINER SEITE & VERWALTUNG (Geschützt)
# -------------------------------------------------------------
@app.route('/vip', methods=['GET', 'POST'])
def vip():
    if 'user_id' not in session or session.get('role') != 'trainer':
        flash("Nur VIP-Trainer haben Zugriff auf diesen Bereich!", "error")
        return redirect(url_for('login'))

    current_user_id = session['user_id']

    if request.method == 'POST':
        # FIRE-STYLE VIDEO UPLOAD
        if 'fire_video_file' in request.files:
            fire_file = request.files.get('fire_video_file')
            fire_title = request.form.get('fire_title', 'Fire Motivator')

            if fire_file and fire_file.filename:
                upload_dir = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)

                new_fire = FireStyleVideo(title=fire_title, video_path="", user_id=current_user_id)
                db.session.add(new_fire)
                db.session.commit()

                f_filename = f"fire_{new_fire.id}.mp4"
                fire_file.save(os.path.join(upload_dir, f_filename))
                new_fire.video_path = f"uploads/{f_filename}"
                db.session.commit()

                flash('🔥 Fire-Style Video erfolgreich hochgeladen!', 'success')
                return redirect(url_for('vip'))

        # WORKOUT UPLOAD
        title = request.form.get('title')
        category = request.form.get('category')
        schwierigkeit = request.form.get('schwierigkeit')
        musicstyl = request.form.get('musicstyl')
        special = request.form.get('special')
        lyrics = request.form.get('lyrics')

        v_file = request.files.get('video_file')
        voice_f = request.files.get('voice_file')
        music_f = request.files.get('music_file')

        if not v_file or not v_file.filename:
            flash('Bitte wähle eine gültige Video-Datei aus!', 'error')
            return redirect(url_for('vip'))

        new_workout = WorkoutVideo(
            title=title, category=category, schwierigkeit=schwierigkeit,
            musicstyl=musicstyl, special=special, video_path="",
            lyrics=lyrics, user_id=current_user_id
        )
        db.session.add(new_workout)
        db.session.commit()

        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        v_filename = f"video_{new_workout.id}.mp4"
        v_file.save(os.path.join(upload_dir, v_filename))
        new_workout.video_path = f"uploads/{v_filename}"

        if voice_f and voice_f.filename:
            voice_filename = f"voice_{new_workout.id}.mp3"
            voice_f.save(os.path.join(upload_dir, voice_filename))
            new_workout.voice_path = f"uploads/{voice_filename}"

        if music_f and music_f.filename:
            music_filename = f"music_{new_workout.id}.mp3"
            music_f.save(os.path.join(upload_dir, music_filename))
            new_workout.music_path = f"uploads/{music_filename}"

        vtt_save_path = os.path.join(upload_dir, f"lyrics_{new_workout.id}.vtt")
        generate_vtt_from_text(lyrics, vtt_save_path)

        db.session.commit()
        flash('Workout erfolgreich hochgeladen und gespeichert!', 'success')
        return redirect(url_for('vip'))

    user_workouts = WorkoutVideo.query.filter_by(user_id=current_user_id).all()
    fire_videos = FireStyleVideo.query.all()
    return render_template('vip.html', videos=user_workouts, fire_videos=fire_videos, username=session.get('username'))


# LÖSCH-ROUTE FÜR HAUPT-WORKOUTS (Inkl. Datei-Bereinigung)
@app.route('/vip/delete_workout/<int:video_id>', methods=['POST'])
def delete_workout(video_id):
    if 'user_id' not in session or session.get('role') != 'trainer':
        flash("Keine Berechtigung!", "error")
        return redirect(url_for('login'))

    workout = WorkoutVideo.query.get_or_404(video_id)

    # Alle verknüpften Dateien vom Server löschen
    paths_to_delete = [
        workout.video_path,
        workout.voice_path,
        workout.music_path,
        f"uploads/lyrics_{workout.id}.vtt"
    ]

    for p in paths_to_delete:
        if p:
            full_path = os.path.join(app.root_path, 'static', p)
            if os.path.exists(full_path):
                os.remove(full_path)

    db.session.delete(workout)
    db.session.commit()
    flash('🗑️ Workout und alle zugehörigen Dateien erfolgreich gelöscht!', 'success')
    return redirect(url_for('vip'))


# LÖSCH-ROUTE FÜR FIRE-CLIPS
@app.route('/vip/delete_fire/<int:fire_id>', methods=['POST'])
def delete_fire(fire_id):
    if 'user_id' not in session or session.get('role') != 'trainer':
        flash("Keine Berechtigung!", "error")
        return redirect(url_for('login'))

    fire_vid = FireStyleVideo.query.get_or_404(fire_id)

    if fire_vid.video_path:
        full_path = os.path.join(app.root_path, 'static', fire_vid.video_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    db.session.delete(fire_vid)
    db.session.commit()
    flash('🔥 Fire-Style Clip erfolgreich gelöscht!', 'success')
    return redirect(url_for('vip'))

@app.route('/contact-pay', methods=['GET', 'POST'])
def contact_pay():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'payment':
            flash('💳 DEMO-ZAHLUNG: Die Testzahlung wurde erfolgreich simuliert! (Es wurden keine realen Daten verarbeitet)', 'success')
        elif form_type == 'contact':
            flash('✉️ DEMO-KONTAKT: Die Nachricht wurde im Simulationsmodus erfasst. (IHK-Prüfungssystem)', 'info')

        return redirect(url_for('contact_pay'))

    return render_template('contact_pay.html')
@app.route('/impressum')
def impressum():
    return render_template('impressum.html')

@app.route('/datenschutz')
def datenschutz():
    return render_template('datenschutz.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)