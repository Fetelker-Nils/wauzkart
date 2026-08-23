from ..runtime import *

# 
# KONSTANTEN
# 
OUTER_R = 40
INNER_R = 18
MID_R   = (OUTER_R + INNER_R) / 2   # ~29
WIN_LAPS = 3
SOUND_DIRS = [
    SOUNDS_DIR,
]

def _is_wsl():
    if os.environ.get("WSL_DISTRO_NAME") or os.environ.get("WSL_INTEROP"):
        return True
    try:
        return "microsoft" in Path("/proc/sys/kernel/osrelease").read_text(errors="ignore").lower()
    except Exception:
        return False


class WauzCartAudio:
    def __init__(self):
        self.disabled = _is_wsl() and os.environ.get("WAUZKART_ENABLE_WSL_AUDIO") != "1"
        self.effect_available = (not self.disabled) and QSoundEffect is not None
        self.media_available = (not self.disabled) and all([QMediaPlayer, QMediaContent, QMediaPlaylist])
        self.available = self.effect_available or self.media_available
        self._player = None
        self._playlist = None
        self._effect = None
        self._is_playing = False
        self._backend_ready = False

    def _ensure_backend(self):
        if self._backend_ready:
            return
        # Qt multimedia objects must be created after QApplication exists.
        if QApplication.instance() is None:
            return
        if self.effect_available and self._effect is None:
            self._effect = QSoundEffect()
            self._effect.setLoopCount(QSoundEffect.Infinite)
            self._effect.setVolume(0.34)
        if self.media_available and self._player is None:
            self._player = QMediaPlayer()
            self._playlist = QMediaPlaylist()
            self._playlist.setPlaybackMode(QMediaPlaylist.Loop)
            self._player.setPlaylist(self._playlist)
            self._player.setVolume(34)
        self._backend_ready = True

    def _find_music(self, names):
        for folder in SOUND_DIRS:
            for name in names:
                p = folder / name
                if p.exists():
                    return p
        return None

    def _play_music(self, names):
        if not self.available:
            return
        try:
            self._ensure_backend()
            p = self._find_music(names)
            if p is None:
                return
            self.stop()
            if self._effect is not None and p.suffix.lower() == ".wav":
                self._effect.setSource(QUrl.fromLocalFile(str(p)))
                self._effect.play()
                self._is_playing = True
                return
            if self._playlist is None or self._player is None:
                return
            self._playlist.clear()
            self._playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(p))))
            self._playlist.setCurrentIndex(0)
            self._player.play()
            self._is_playing = True
        except Exception:
            self.available = False
            self._is_playing = False

    def play_race_music(self):
        self._play_music(("music_game.wav", "music_game.mp3", "music_game.ogg", "wauz_cart_music.wav"))

    def play_menu_music(self):
        self._play_music(("music_menu.wav", "music_menu.mp3", "music_menu.ogg"))

    def play_end_music(self):
        self._play_music(("music_end.wav", "music_end.mp3", "music_end.ogg"))

    def play_highlight_music(self):
        self._play_music(("music_highlight.wav", "music_highlight.mp3", "music_highlight.ogg"))

    def stop(self):
        try:
            if self._effect is not None and self._is_playing:
                self._effect.stop()
            if self._player is not None and self._is_playing:
                self._player.stop()
        except Exception:
            pass
        self._is_playing = False


wauz_audio = WauzCartAudio()
