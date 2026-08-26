from PyQt5.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from ..runtime import QDesktopServices, QFont, Qt, QUrl


TERMS_TEXT = """
Nutzungsbedingungen

Wauz Kart ist ein Fan-/Hobby-Spielprojekt. Mit dem Start bestaetigst du, dass du das Spiel auf eigenes Risiko nutzt.

Spiel und Updates
- Wauz Kart darf beim Start nach neuen Releases suchen.
- Updates koennen automatisch heruntergeladen und installiert werden.
- Fuer Linux kann der Installer Systempakete installieren, die fuer Grafik oder Audio noetig sind.
- Unter macOS kann die DMG geoeffnet werden; die Installation muss eventuell manuell abgeschlossen werden.

Speicherung
- Fortschritt, Scores, Abzeichen, Rennen und die AGB-Zustimmung werden lokal in deinem Benutzerprofil gespeichert.
- Unter Windows ist das normalerweise AppData/Roaming/Wauzkart.
- Es werden keine Spielstaende in den Assets gespeichert.

LAN und Online
- LAN-Spiele laufen in deinem lokalen Netzwerk.
- Andere Spieler im selben Netzwerk koennen Host-IP, Spielername und Rennstatus sehen.
- Oeffentliche Internet-Server sind noch nicht Teil dieses LAN-Modus.

Fairness und Sicherheit
- Nutze das Spiel nicht, um fremde Netzwerke zu stoeren.
- Starte Wauz Kart unter Linux nicht mit sudo, ausser du fuehrst nur den Installer aus.
- Installer und Updates sollten nur von der offiziellen GitHub-Release-Seite oder der Wauz-Kart-Website geladen werden.
""".strip()


AGB_TEXT = """
AGB

1. Geltung
Diese AGB gelten fuer die Nutzung von Wauz Kart, der Website und der bereitgestellten Installer.

2. Kosten
Wauz Kart wird kostenlos bereitgestellt. Es besteht kein Anspruch auf dauerhafte Verfuegbarkeit, bestimmte Funktionen oder Support.

3. Updates
Das Spiel kann automatisch nach Updates suchen. Wenn ein Update fehlschlaegt, bleibt die vorhandene Installation normalerweise erhalten. Du kannst den aktuellen Installer jederzeit manuell erneut laden.

4. Haftung
Das Spiel wird ohne Gewaehr bereitgestellt. Fuer Schaeden durch falsche Installation, fehlende Systempakete, Treiberprobleme, Firewall-Regeln oder lokale Systemkonfiguration wird keine Haftung uebernommen, soweit gesetzlich zulaessig.

5. Spielstaende
Lokale Daten koennen geloescht oder zurueckgesetzt werden. Sichere wichtige Dateien selbst, bevor du Experimente mit Installationsordnern oder Systemrechten machst.

6. Aenderungen
Diese Bedingungen koennen mit neuen Versionen angepasst werden. Dann kann beim Start erneut eine Zustimmung erforderlich sein.
""".strip()


class TermsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wauz Kart Nutzungsbedingungen und AGB")
        self.setModal(True)
        self.setMinimumSize(760, 620)
        self.setStyleSheet("""
            QDialog {
                background: #070b13;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QScrollArea {
                border: 1px solid rgba(255, 204, 0, 130);
                border-radius: 8px;
                background: #0d1420;
            }
            QWidget#legalContent {
                background: #0d1420;
            }
            QCheckBox {
                color: #ffffff;
                font-weight: bold;
                spacing: 8px;
            }
            QPushButton {
                background: #172234;
                color: #ffffff;
                border: 2px solid #2e4163;
                border-radius: 7px;
                padding: 10px 18px;
                min-width: 150px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #f4c945;
            }
            QPushButton#acceptButton {
                background: #f4c945;
                color: #111111;
                border-color: #ffe37a;
            }
            QPushButton#acceptButton:disabled {
                background: #63572d;
                color: #c7c0a5;
                border-color: #7a6b37;
            }
        """)

        outer = QVBoxLayout()
        outer.setContentsMargins(24, 22, 24, 22)
        outer.setSpacing(14)
        self.setLayout(outer)

        title = QLabel("NUTZUNGSBEDINGUNGEN UND AGB")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#ffdd55;")
        outer.addWidget(title)

        subtitle = QLabel("Bitte lies die Bedingungen beim ersten Start. Danach startet Wauz Kart normal.")
        subtitle.setFont(QFont("Arial", 11, QFont.Bold))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, 1)

        content = QWidget()
        content.setObjectName("legalContent")
        lay = QVBoxLayout()
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(18)
        content.setLayout(lay)

        for header, body in (("Nutzungsbedingungen", TERMS_TEXT), ("AGB", AGB_TEXT)):
            label = QLabel(header)
            label.setFont(QFont("Arial", 17, QFont.Bold))
            label.setStyleSheet("color:#ffdd55;")
            lay.addWidget(label)

            text = QLabel(body)
            text.setWordWrap(True)
            text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            text.setFont(QFont("Arial", 11))
            text.setStyleSheet("line-height: 140%; color:#e8edf7;")
            lay.addWidget(text)

        scroll.setWidget(content)

        self.check = QCheckBox("Ich akzeptiere die Nutzungsbedingungen und AGB.")
        outer.addWidget(self.check)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.reject_btn = QPushButton("Beenden")
        self.accept_btn = QPushButton("Akzeptieren")
        self.accept_btn.setObjectName("acceptButton")
        self.accept_btn.setEnabled(False)
        self.reject_btn.clicked.connect(self.reject)
        self.accept_btn.clicked.connect(self.accept)
        self.check.toggled.connect(self.accept_btn.setEnabled)
        buttons.addWidget(self.reject_btn)
        buttons.addWidget(self.accept_btn)
        outer.addLayout(buttons)


class UpdateHelpDialog(QDialog):
    HELP_URL = "https://wauzkart.vercel.app/hilfe"

    def __init__(self, error_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update-Hilfe")
        self.setModal(True)
        self.setFixedSize(620, 420)
        self.setStyleSheet("""
            QDialog { background:#070b13; color:#ffffff; }
            QLabel { color:#ffffff; background:transparent; }
            QPushButton {
                background:#172234;
                color:#ffffff;
                border:2px solid #2e4163;
                border-radius:7px;
                padding:10px 16px;
                min-width:145px;
                font-weight:bold;
            }
            QPushButton:hover { border-color:#f4c945; }
            QPushButton#helpButton { background:#f4c945; color:#111111; border-color:#ffe37a; }
        """)

        outer = QVBoxLayout()
        outer.setContentsMargins(24, 22, 24, 22)
        outer.setSpacing(14)
        self.setLayout(outer)

        title = QLabel("UPDATE FEHLGESCHLAGEN")
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#ffdd55;")
        outer.addWidget(title)

        text = QLabel(
            "Das automatische Update konnte nicht abgeschlossen werden.\n\n"
            "Du kannst Wauz Kart weiter benutzen und spaeter den aktuellen Installer manuell herunterladen.\n"
            "Die Hilfe-Seite erklaert Windows-, Linux- und macOS-Installation, Firewall, Rechte und Update-Probleme."
        )
        text.setWordWrap(True)
        text.setFont(QFont("Arial", 11, QFont.Bold))
        outer.addWidget(text)

        detail = QLabel(str(error_text or "Unbekannter Fehler."))
        detail.setWordWrap(True)
        detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        detail.setStyleSheet("background:#0d1420; border:1px solid #2e4163; border-radius:8px; padding:12px; color:#e8edf7;")
        outer.addWidget(detail, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        help_btn = QPushButton("Hilfe oeffnen")
        help_btn.setObjectName("helpButton")
        close_btn = QPushButton("Schliessen")
        help_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.HELP_URL)))
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(help_btn)
        buttons.addWidget(close_btn)
        outer.addLayout(buttons)
