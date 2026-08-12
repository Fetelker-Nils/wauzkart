import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
ASSETS = ROOT / "assets"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

try:
    from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
except Exception:
    QMediaContent = None
    QMediaPlayer = None
    QMediaPlaylist = None


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wauz Kart Hilfe")
        self.setFixedSize(620, 560)
        self.setStyleSheet("""
            QDialog {
                background:#070a10;
                color:#f4f0df;
            }
            QLabel {
                background:transparent;
                border:none;
            }
            QPushButton {
                background:#f0c84b;
                color:#111111;
                border:2px solid #fff0a3;
                border-bottom:5px solid #9b6f18;
                border-radius:6px;
                padding:10px 18px;
            }
            QPushButton:hover {
                background:#ffe06a;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        self.setLayout(layout)

        title = QLabel("ANLEITUNG")
        title.setFont(QFont("Arial", 26, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#ffdd55;")
        layout.addWidget(title)

        text = QLabel(
            "Ziel\n"
            "Fahre die Runden fertig, sammle Items und halte die KI hinter dir.\n\n"
            "Steuerung\n"
            "Spieler 1: W A S D\n"
            "Spieler 2: Pfeiltasten\n"
            "Spieler 3: T F G H\n"
            "Spieler 4: I J K L\n"
            "F3: Kamera wechseln\n"
            "ESC: Rennen verlassen\n\n"
            "Items\n"
            "Boxen geben dir automatisch ein Item. Abknaller, Wirbler, Frost,\n"
            "Schild, Turbo und Oelspur koennen das Rennen drehen.\n\n"
            "Tipps\n"
            "Bei '2!' schon Gas geben fuer den Schnellstart.\n"
            "Nach dem Ziel faehrst du kurz als Ghost weiter.\n"
            "In den Highlights sieht man die besten Szenen des Rennens."
        )
        text.setFont(QFont("Arial", 11))
        text.setWordWrap(True)
        text.setStyleSheet("""
            QLabel {
                background:#101722;
                color:#f4f0df;
                border:2px solid #303a49;
                border-left:6px solid #f0c84b;
                border-radius:6px;
                padding:16px;
            }
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background:transparent;
                border:none;
            }
            QScrollArea QWidget {
                background:transparent;
            }
            QScrollBar:vertical {
                background:#101722;
                width:10px;
                border-radius:5px;
            }
            QScrollBar::handle:vertical {
                background:#f0c84b;
                border-radius:5px;
            }
        """)
        scroll.setWidget(text)
        layout.addWidget(scroll, 1)

        close_btn = QPushButton("SCHLIESSEN")
        close_btn.setFont(QFont("Arial", 12, QFont.Bold))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class WauzKartLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.music_enabled = True
        self.music_player = None
        self.music_playlist = None
        self.setWindowTitle("Wauz Kart")
        icon_path = ASSETS / "icon.ico"
        if not icon_path.is_file():
            icon_path = ASSETS / "icon.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setFixedSize(720, 560)
        bg_path = ASSETS / "background_launcher.png"
        self.bg_pixmap = QPixmap(str(bg_path)) if bg_path.is_file() else QPixmap()
        self.setObjectName("launcherRoot")
        self.setStyleSheet("""
            QWidget#launcherRoot {
                background-color:#070a10;
                color:#f4f0df;
            }
            QLabel {
                background:transparent;
                border:none;
            }
            QPushButton {
                background:#f0c84b;
                color:#111111;
                border:2px solid #fff0a3;
                border-bottom:5px solid #9b6f18;
                border-radius:6px;
                padding:12px 18px;
            }
            QPushButton:hover {
                background:#ffe06a;
            }
            QPushButton:pressed {
                background:#c79522;
                border-bottom:2px solid #9b6f18;
                padding-top:15px;
            }
            QPushButton#darkButton {
                background:#141b26;
                color:#f4f0df;
                border:2px solid #384658;
                border-bottom:5px solid #0b1018;
            }
            QPushButton#darkButton:hover {
                background:rgba(32, 43, 58, 230);
                border-color:#f0c84b;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(44, 28, 44, 26)
        layout.setSpacing(10)
        self.setLayout(layout)
        layout.addStretch(1)

        title = QLabel("WAUZ KART")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("""
            QLabel {
                color:#ffdd55;
                background:rgba(0,0,0,150);
                border:2px solid rgba(255, 220, 85, 150);
                border-left:6px solid #f0c84b;
                border-radius:6px;
                padding:7px 12px;
            }
        """)
        layout.addWidget(title)

        subtitle = QLabel("Bereit fuer Rennen, Items, KI-Gegner und Highlights.")
        subtitle.setFont(QFont("Arial", 11, QFont.Bold))
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignLeft)
        subtitle.setStyleSheet("""
            QLabel {
                color:#f4f0df;
                background:rgba(0,0,0,135);
                border-radius:5px;
                padding:8px 12px;
            }
        """)
        layout.addWidget(subtitle)

        info = QLabel("RENNZENTRALE\nStarte dein Rennen, sammle Items, schalte neue Karts frei und schaue dir danach deine besten Highlights an.")
        info.setFont(QFont("Arial", 11))
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignLeft)
        info.setMinimumHeight(88)
        info.setStyleSheet("""
            QLabel {
                background:rgba(16, 23, 34, 210);
                color:#f4f0df;
                border:2px solid rgba(240, 200, 75, 180);
                border-left:6px solid #f0c84b;
                border-radius:6px;
                padding:14px;
            }
        """)
        layout.addWidget(info)

        feature_row = QHBoxLayout()
        feature_row.setSpacing(10)
        layout.addLayout(feature_row)
        for text in ("RENNSPORT", "ITEMS", "KI", "HIGHLIGHTS"):
            label = QLabel(text)
            label.setFont(QFont("Arial", 10, QFont.Bold))
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    background:rgba(21, 29, 41, 210);
                    color:#ffdd55;
                    border:2px solid rgba(240, 200, 75, 130);
                    border-radius:5px;
                    padding:8px;
                }
            """)
            feature_row.addWidget(label)

        layout.addSpacing(2)

        start = QPushButton("SPIEL STARTEN")
        start.setFont(QFont("Arial", 16, QFont.Bold))
        start.clicked.connect(self.start_game)
        layout.addWidget(start)

        secondary = QHBoxLayout()
        secondary.setSpacing(10)
        layout.addLayout(secondary)

        help_btn = QPushButton("HILFE")
        help_btn.setObjectName("darkButton")
        help_btn.setFont(QFont("Arial", 11, QFont.Bold))
        help_btn.clicked.connect(self.show_help)
        secondary.addWidget(help_btn)

        music_btn = QPushButton("MUSIK AUS")
        music_btn.setObjectName("darkButton")
        music_btn.setFont(QFont("Arial", 11, QFont.Bold))
        music_btn.clicked.connect(lambda: self.toggle_music(music_btn))
        secondary.addWidget(music_btn)

        quit_btn = QPushButton("BEENDEN")
        quit_btn.setObjectName("darkButton")
        quit_btn.setFont(QFont("Arial", 11, QFont.Bold))
        quit_btn.clicked.connect(self.close)
        layout.addWidget(quit_btn)

        self.start_music()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.bg_pixmap.isNull():
            painter.drawPixmap(self.rect(), self.bg_pixmap)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 55))
        else:
            painter.fillRect(self.rect(), QColor("#070a10"))
        painter.end()
        super().paintEvent(event)

    def start_music(self):
        if not all([QMediaPlayer, QMediaContent, QMediaPlaylist]):
            return
        music_path = ASSETS / "sounds" / "music_menu.wav"
        if not music_path.is_file():
            return
        self.music_player = QMediaPlayer(self)
        self.music_playlist = QMediaPlaylist(self)
        self.music_playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.music_playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(music_path))))
        self.music_player.setPlaylist(self.music_playlist)
        self.music_player.setVolume(28)
        self.music_player.play()

    def toggle_music(self, button):
        self.music_enabled = not self.music_enabled
        if self.music_player is not None:
            if self.music_enabled:
                self.music_player.play()
                button.setText("MUSIK AUS")
            else:
                self.music_player.pause()
                button.setText("MUSIK AN")

    def show_help(self):
        dlg = HelpDialog(self)
        dlg.exec_()

    def start_game(self):
        if self.music_player is not None:
            self.music_player.stop()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
        creationflags = 0
        if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW
        subprocess.Popen([self._game_python(), str(ROOT / "wauz_kart.py")], cwd=str(ROOT), env=env, creationflags=creationflags)
        self.close()

    def _game_python(self):
        exe = Path(sys.executable)
        if os.name == "nt" and exe.name.lower() != "pythonw.exe":
            candidate = exe.with_name("pythonw.exe")
            if candidate.exists():
                return str(candidate)
        return str(exe)


def main():
    app = QApplication(sys.argv)
    win = WauzKartLauncher()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
