import os
import json
import subprocess
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QScrollArea, QGridLayout, QWidget
from PySide6.QtGui import QPixmap, QIcon, QMovie
from PySide6.QtCore import Qt, QSize

from grid_button import GridButton
from utils import COVER_WIDTH, COVER_HEIGHT
from styles import LAUNCHER_STYLES

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arcade Launcher")
        self.resize(1280, 720)
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.movie = None
        self.bg_pixmap = None

        self.setup_background()
        self.setObjectName("MainWindow")
        self.setStyleSheet(LAUNCHER_STYLES)

        try:
            json_path = os.path.join(self.base_path, "data", "games.json")
            with open(json_path, "r", encoding="utf-8") as f:
                self.games = json.load(f)
        except FileNotFoundError:
            print("Error: El archivo games.json no se encontró en la carpeta 'data'.")
            self.games = []

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        right_panel_container = QWidget()
        right_panel_container.setObjectName("RightPanelContainer")
        right_layout = QVBoxLayout(right_panel_container)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        header_label = QLabel(f"ALL GAMES ({len(self.games)})")
        header_label.setStyleSheet("font-size: 20px; font-weight: bold; padding-bottom: 10px;")

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setAlignment(Qt.AlignTop)
        self.scroll.setStyleSheet("border: none;")

        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(20)

        self.scroll.setWidget(grid_container)

        right_layout.addWidget(header_label)
        right_layout.addWidget(self.scroll)

        main_layout.addWidget(right_panel_container, 1)

        self.populate_games()

    def setup_background(self):
        self.background_label = QLabel(self)
        background_path = os.path.join(self.base_path, "assets", "background.gif")

        if not os.path.exists(background_path):
            print(f"Advertencia: No se encontró el archivo de fondo en {background_path}")
            self.background_label.setStyleSheet("background-color: #0d1b2a;")
            return

        if background_path.lower().endswith('.gif'):
            self.movie = QMovie(background_path)
            self.movie.setScaledSize(self.size())
            self.background_label.setMovie(self.movie)
            self.movie.start()
        else:
            self.bg_pixmap = QPixmap(background_path)
            self._update_static_background()

    def _update_static_background(self):
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            self.background_label.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()

        self.background_label.setGeometry(0, 0, w, h)
        self.background_label.lower()

        if self.movie:
            self.movie.setScaledSize(self.background_label.size())
        elif self.bg_pixmap:
            self._update_static_background()

    def populate_games(self):
        if self.grid_layout.count():
            while self.grid_layout.count():
                child = self.grid_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        num_columns = 5
        row, col = 0, 0

        for game in self.games:
            cover_button = self.create_game_button(game, row, col)
            self.grid_layout.addWidget(cover_button, row, col)

            col += 1
            if col >= num_columns:
                col = 0
                row += 1

    def create_game_button(self, game_data, row, col):
        button = GridButton(game_data, row, col, self.grid_layout)
        button.setFixedSize(COVER_WIDTH, COVER_HEIGHT)

        image_path = game_data.get("image")
        if image_path:
            cover_full_path = os.path.join(self.base_path, image_path)
            pixmap = QPixmap(cover_full_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    QSize(COVER_WIDTH, COVER_HEIGHT),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                button.setIcon(QIcon(scaled_pixmap))
                button.setIconSize(scaled_pixmap.size())
            else:
                print(f"Error al cargar la imagen: {cover_full_path} para {game_data['name']}")

        button.clicked.connect(lambda: self.launch_game(game_data))
        return button

    def launch_game(self, game_data):
        path = game_data.get("path")
        emu = game_data.get("emulator")
        rom = game_data.get("rom")

        print(f"Lanzando {game_data['name']}...")
        try:
            if path:
                subprocess.Popen(path)
            elif emu and rom:
                subprocess.Popen([emu, rom])
            else:
                print(f"No se encontró ruta ni emulador/ROM para {game_data['name']}")
        except Exception as e:
            print(f"Error al lanzar {game_data['name']}: {e}")