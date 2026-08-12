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


class WauzCartAudio:
    def __init__(self):
        self.available = all([QMediaPlayer, QMediaContent, QMediaPlaylist])
        self._player = None
        self._playlist = None
        self._is_playing = False
        if self.available:
            self._player = QMediaPlayer()
            self._playlist = QMediaPlaylist()
            self._playlist.setPlaybackMode(QMediaPlaylist.Loop)
            self._player.setPlaylist(self._playlist)
            self._player.setVolume(34)

    def _find_music(self, names):
        for folder in SOUND_DIRS:
            for name in names:
                p = folder / name
                if p.exists():
                    return p
        return None

    def play_race_music(self):
        if not self.available:
            return
        p = self._find_music(("music_game.wav", "music_game.mp3", "music_game.ogg", "wauz_cart_music.wav"))
        if p is None:
            return
        self._playlist.clear()
        self._playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(p))))
        self._playlist.setCurrentIndex(0)
        self._player.play()
        self._is_playing = True

    def play_menu_music(self):
        if not self.available:
            return
        p = self._find_music(("music_menu.wav", "music_menu.mp3", "music_menu.ogg"))
        if p is None:
            return
        self._playlist.clear()
        self._playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(p))))
        self._playlist.setCurrentIndex(0)
        self._player.play()
        self._is_playing = True

    def play_end_music(self):
        if not self.available:
            return
        p = self._find_music(("music_end.wav", "music_end.mp3", "music_end.ogg"))
        if p is None:
            return
        self._playlist.clear()
        self._playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(p))))
        self._playlist.setCurrentIndex(0)
        self._player.play()
        self._is_playing = True

    def play_highlight_music(self):
        if not self.available:
            return
        p = self._find_music(("music_highlight.wav", "music_highlight.mp3", "music_highlight.ogg"))
        if p is None:
            return
        self._playlist.clear()
        self._playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(p))))
        self._playlist.setCurrentIndex(0)
        self._player.play()
        self._is_playing = True

    def stop(self):
        if self._player is not None and self._is_playing:
            self._player.stop()
        self._is_playing = False


wauz_audio = WauzCartAudio()

