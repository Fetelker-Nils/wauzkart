import sys, os, math, time, random, json, html, threading
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget,
    QHBoxLayout, QVBoxLayout, QGridLayout, QOpenGLWidget, QPushButton, QStackedWidget,
    QComboBox, QSizePolicy, QScrollArea, QDialog, QCheckBox, QMessageBox, QSpinBox,
    QSlider, QProgressBar, QToolButton, QInputDialog)
from PyQt5.QtCore import QTimer, Qt, QUrl, QSize, QPoint
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QIcon, QPixmap, QBrush
try:
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist, QSoundEffect
except Exception:
    QMediaPlayer = None
    QMediaContent = None
    QMediaPlaylist = None
    QSoundEffect = None
from OpenGL.GL import *
from OpenGL.GLU import *
from .paths import DATA_DIR, SOUNDS_DIR, _wauz_api
