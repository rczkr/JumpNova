document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("workoutVideo");
    const videoSource = document.getElementById("videoSource");
    const lyricsTrack = document.getElementById("lyricsTrack");

    const musicAudio = document.getElementById("musicAudio");
    const trainerAudio = document.getElementById("trainerAudio");

    const timerOverlay = document.getElementById("timerOverlay");
    const timerDisplay = document.getElementById("timerDisplay");
    const timerSelect = document.getElementById("timerSelect");

    const fireStyleSelect = document.getElementById("fireStyleSelect");
    const fireOverlayVideo = document.getElementById("fireOverlayVideo");
    const fireVideoSource = document.getElementById("fireVideoSource");

    const lyricsToggleSelect = document.getElementById("lyricsToggleSelect");

    const musicVol = document.getElementById("musicVol");
    const trainerVol = document.getElementById("trainerVol");

    const activeVideoTitle = document.getElementById("activeVideoTitle");
    const activeVideoCategory = document.getElementById("activeVideoCategory");
    const lyricsContainer = document.getElementById("lyricsContainer");

    let lastTriggeredMinute = -1;

    // PLAYLIST / MIX LOGIK
    let currentPlaylist = [];
    let currentPlaylistIndex = 0;
    let cumulativeTime = 0; // Gesamtzeit vorheriger Videos im Mix

    if (video) {
        video.muted = true;
        video.volume = 0;
    }

    // LYRICS / UNTERTITEL EIN- & AUSSCHALTEN
    function updateLyricsVisibility(mode) {
        if (!video) return;

        // Greife auf die TextTracks des Videos zu
        if (video.textTracks && video.textTracks.length > 0) {
            for (let i = 0; i < video.textTracks.length; i++) {
                video.textTracks[i].mode = mode; // 'showing' oder 'disabled'
            }
        }
    }

    if (lyricsToggleSelect) {
        lyricsToggleSelect.addEventListener("change", (e) => {
            updateLyricsVisibility(e.target.value);
        });
    }

    // Mix-Playlist starten
    window.startMixPlaylist = function(mixId) {
        fetch(`/api/mix/${mixId}`)
            .then(res => res.json())
            .then(data => {
                if (data.playlist && data.playlist.length > 0) {
                    currentPlaylist = data.playlist;
                    currentPlaylistIndex = 0;
                    cumulativeTime = 0;
                    lastTriggeredMinute = -1;
                    loadPlaylistItem(0);
                }
            })
            .catch(err => console.error("Fehler beim Laden des Mixes:", err));
    };

    function loadPlaylistItem(index) {
        if (index >= currentPlaylist.length) {
            console.log("Mix-Playlist beendet!");
            return;
        }

        const item = currentPlaylist[index];

        if (videoSource) videoSource.src = item.video_path;
        if (lyricsTrack) lyricsTrack.src = item.vtt_path;

        video.load();

        // Lyrics-Einstellung nach dem Laden beibehalten
        if (lyricsToggleSelect) {
            updateLyricsVisibility(lyricsToggleSelect.value);
        }

        if (musicAudio) {
            musicAudio.src = item.music_path;
            musicAudio.load();
        }
        if (trainerAudio) {
            trainerAudio.src = item.voice_path;
            trainerAudio.load();
        }

        if (activeVideoTitle) activeVideoTitle.textContent = item.title;
        if (activeVideoCategory) activeVideoCategory.textContent = item.category;
        if (lyricsContainer) lyricsContainer.textContent = item.lyrics;

        video.play().then(() => {
            if (musicAudio) musicAudio.play().catch(() => {});
            if (trainerAudio) trainerAudio.play().catch(() => {});
        }).catch(err => console.log("Playlist Play-Fehler:", err));
    }

    // Automatischer Übergang zum nächsten Video im Mix
    if (video) {
        video.addEventListener("ended", () => {
            if (currentPlaylist.length > 0) {
                cumulativeTime += Math.floor(video.duration || 0);
                currentPlaylistIndex++;
                if (currentPlaylistIndex < currentPlaylist.length) {
                    loadPlaylistItem(currentPlaylistIndex);
                }
            }
        });
    }

    // 1. Synchronisation der MP3-Spuren
    if (video && musicAudio && trainerAudio) {
        video.addEventListener("play", () => {
            video.muted = true;
            video.volume = 0;
            musicAudio.currentTime = video.currentTime;
            trainerAudio.currentTime = video.currentTime;
            musicAudio.play().catch(e => console.log("Musik Sperre:", e));
            trainerAudio.play().catch(e => console.log("Trainer Sperre:", e));
        });

        video.addEventListener("pause", () => {
            musicAudio.pause();
            trainerAudio.pause();
        });

        video.addEventListener("seeking", () => {
            musicAudio.currentTime = video.currentTime;
            trainerAudio.currentTime = video.currentTime;
        });

        video.addEventListener("waiting", () => {
            musicAudio.pause();
            trainerAudio.pause();
        });

        video.addEventListener("playing", () => {
            musicAudio.currentTime = video.currentTime;
            trainerAudio.currentTime = video.currentTime;
            musicAudio.play().catch(() => {});
            trainerAudio.play().catch(() => {});
        });
    }

    // 2. Unabhängige Lautstärkeregelung
    if (musicVol && musicAudio) {
        musicVol.addEventListener("input", (e) => {
            musicAudio.volume = e.target.value;
        });
    }

    if (trainerVol && trainerAudio) {
        trainerVol.addEventListener("input", (e) => {
            trainerAudio.volume = e.target.value;
        });
    }

    // 3. Timer & Fire-Overlay Logik
    function updateTimerAndEffects() {
        if (!video) return;

        const currentVideoTime = Math.floor(video.currentTime);
        const totalWorkoutTime = cumulativeTime + currentVideoTime;

        const minutes = Math.floor(totalWorkoutTime / 60);
        const seconds = totalWorkoutTime % 60;

        if (timerDisplay) {
            timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        // Fire-Style Overlay alle 60 Sek (Test) oder 300 Sek basierend auf der GESAMTZEIT
        if (fireStyleSelect && fireOverlayVideo && fireStyleSelect.value !== "none") {
            if (totalWorkoutTime > 0 && totalWorkoutTime % 60 === 0 && lastTriggeredMinute !== minutes) {
                lastTriggeredMinute = minutes;

                fireOverlayVideo.classList.remove("hidden");
                fireOverlayVideo.currentTime = 0;
                fireOverlayVideo.muted = true;

                fireOverlayVideo.play().then(() => {
                    fireOverlayVideo.muted = false;
                    fireOverlayVideo.volume = 1.0;
                }).catch(e => console.log("Fire Video Fehler:", e));

                fireOverlayVideo.onended = () => {
                    fireOverlayVideo.classList.add("hidden");
                };
            }
        }
    }

    function applyTimerStyle(selectedStyle) {
        if (!timerOverlay) return;
        timerOverlay.classList.remove("hidden");

        if (selectedStyle === "standard") {
            timerOverlay.className = "video-overlay timer-standard";
            timerOverlay.style.display = "block";
        } else if (selectedStyle === "fire") {
            timerOverlay.className = "video-overlay timer-fire";
            timerOverlay.style.display = "block";
        } else if (selectedStyle === "hidden") {
            timerOverlay.className = "video-overlay";
            timerOverlay.style.display = "none";
        }
    }

    if (video) {
        video.addEventListener("timeupdate", updateTimerAndEffects);
        video.addEventListener("seeked", updateTimerAndEffects);
    }

    if (timerSelect) {
        timerSelect.addEventListener("change", (e) => {
            applyTimerStyle(e.target.value);
        });
        applyTimerStyle(timerSelect.value);
    }

    if (fireStyleSelect && fireOverlayVideo && fireVideoSource) {
        fireStyleSelect.addEventListener("change", (e) => {
            if (e.target.value !== "none") {
                fireVideoSource.src = e.target.value;
                fireOverlayVideo.load();
            } else {
                fireOverlayVideo.classList.add("hidden");
            }
        });
    }
});