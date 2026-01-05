import os
import json
import subprocess
import sys
from PySide6.QtWidgets import (QWidget, QApplication, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea, QGridLayout)
from PySide6.QtGui import QPixmap, QIcon, QMovie
from PySide6.QtCore import Qt, QSize
from PySide6.QtCore import QRect, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPainterPath

# Constantes para el tamaño de las carátulas
COVER_WIDTH = 200
COVER_HEIGHT = 262

def rounded_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
    # QPixmap con esquinas redondeadas
    size = pixmap.size()
    rounded = QPixmap(size)
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(0, 0, size.width(), size.height(), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    return rounded

class GridButton(QPushButton):
    OVERLAY_GROW = 1.30        # cuánto crece la portada en el overlay
    OVERLAY_DURATION = 160     # ms de la animación

    def __init__(self, game_data, row, col, parent_grid, parent=None):
        super().__init__(parent)
        self.game_data = game_data
        self.row = row
        self.col = col
        self.parent_grid = parent_grid
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)

        # tamaño base
        self.base_w = COVER_WIDTH
        self.base_h = COVER_HEIGHT
        self.setFixedSize(self.base_w, self.base_h)

        image_path = game_data.get("image", "")
        if image_path:
            pix = QPixmap(image_path)
            if not pix.isNull():
                icon = QIcon(pix)
                self.setIcon(icon)
                self.setIconSize(pix.scaled(self.base_w, self.base_h, Qt.KeepAspectRatio, Qt.SmoothTransformation).size())
            else:
                print(f"Error al cargar la imagen: {image_path} para {game_data.get('name')}")

        # Efecto glow
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor(0, 220, 255))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)

        # Overlay
        self._overlay = None
        self._overlay_anim = None
        self._overlay_glow_anim = None

        # Click normal
        self.clicked.connect(lambda: self.parent().parent().parent().launch_game(self.game_data) if hasattr(self.parent(), 'parent') else None)

    def _create_overlay_label(self, pixmap: QPixmap) -> QLabel:
        top = self.window()  # ventana principal
        overlay = QLabel(top)
        overlay.setAttribute(Qt.WA_TranslucentBackground, True)
        overlay.setWindowFlags(Qt.SubWindow)  #widget sobre la ventana
        overlay.setAlignment(Qt.AlignCenter)
        overlay.setScaledContents(True)
        overlay.setPixmap(pixmap)
        overlay.setStyleSheet("border-radius:8px;")  
        return overlay

    def _map_button_global_rect(self) -> QRect:
        top = self.window()
        # esquina superior izquierda del botón en coordenadas globales de la ventana
        top_left_global = self.mapTo(top, QPoint(0, 0))
        return QRect(top_left_global.x(), top_left_global.y(), self.width(), self.height())

    def focusInEvent(self, event):
        super().focusInEvent(event)

        # si ya hay overlay, no hacer doble
        if self._overlay is not None:
            return

        # obtener pixmap original
        icon = self.icon()
        if icon.isNull():
            return  

        # pixmap
        image_path = self.game_data.get("image", "")
        pix = QPixmap(image_path) if image_path else icon.pixmap(self.base_w, self.base_h)
        if pix.isNull():
            pix = icon.pixmap(self.base_w, self.base_h)

        # overlay
        overlay = self._create_overlay_label(pix)
        self._overlay = overlay

        # rects
        start_rect = self._map_button_global_rect()
        # center del start
        cx = start_rect.center().x()
        cy = start_rect.center().y()

        # tamaño final
        final_w = int(self.base_w * self.OVERLAY_GROW)
        final_h = int(self.base_h * self.OVERLAY_GROW)
        final_rect = QRect(cx - final_w//2, cy - final_h//2, final_w, final_h)

        # colocar overlay inicialmente en start_rect
        overlay.setGeometry(start_rect)
        overlay.show()
        overlay.raise_()

        # animación de geometría (start -> final)
        anim = QPropertyAnimation(overlay, b"geometry", overlay)
        anim.setDuration(self.OVERLAY_DURATION)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(start_rect)
        anim.setEndValue(final_rect)
        anim.start()
        self._overlay_anim = anim  # mantener referencia

        # animar blur del glow del overlay
        overlay_glow = QGraphicsDropShadowEffect(overlay)
        overlay_glow.setColor(QColor(0, 220, 255))
        overlay_glow.setOffset(0, 0)
        overlay_glow.setBlurRadius(0)
        overlay.setGraphicsEffect(overlay_glow)

        glow_anim = QPropertyAnimation(overlay_glow, b"blurRadius", overlay)
        glow_anim.setDuration(self.OVERLAY_DURATION)
        glow_anim.setStartValue(0)
        glow_anim.setEndValue(30)
        glow_anim.setEasingCurve(QEasingCurve.OutCubic)
        glow_anim.start()
        self._overlay_glow_anim = glow_anim

    def focusOutEvent(self, event):
        super().focusOutEvent(event)

        if self._overlay is None:
            return

        overlay = self._overlay
        # rects
        end_rect = self._map_button_global_rect()  # a dónde volver
        start_rect = overlay.geometry()

        # animar vuelta
        anim = QPropertyAnimation(overlay, b"geometry", overlay)
        anim.setDuration(self.OVERLAY_DURATION)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.setStartValue(start_rect)
        anim.setEndValue(end_rect)

        # cuando termine, ocultar y destruir overlay
        def on_finished():
            nonlocal overlay
            try:
                overlay.hide()
                overlay.deleteLater()
            finally:
                # limpiar referencias
                self._overlay = None
                self._overlay_anim = None
                self._overlay_glow_anim = None

        anim.finished.connect(on_finished)
        anim.start()
        self._overlay_anim = anim

        # reducir glow si existe
        effect = overlay.graphicsEffect()
        if effect:
            glow_anim = QPropertyAnimation(effect, b"blurRadius", overlay)
            glow_anim.setDuration(self.OVERLAY_DURATION)
            glow_anim.setStartValue(effect.blurRadius())
            glow_anim.setEndValue(0)
            glow_anim.setEasingCurve(QEasingCurve.OutCubic)
            glow_anim.start()
            self._overlay_glow_anim = glow_anim

    # Mantener comportamiento normal del teclado
    def keyPressEvent(self, event):
        key = event.key()
        layout = self.parent_grid
        num_cols = 5
        new_row, new_col = self.row, self.col

        if key == Qt.Key_Right:
            new_col += 1
            if new_col >= num_cols:
                new_col = 0
                new_row += 1
        elif key == Qt.Key_Left:
            new_col -= 1
            if new_col < 0:
                new_col = num_cols - 1
                new_row -= 1
        elif key == Qt.Key_Down:
            new_row += 1
        elif key == Qt.Key_Up:
            new_row -= 1
        else:
            super().keyPressEvent(event)
            return

        new_row = max(0, min(layout.rowCount() - 1, new_row))
        new_col = max(0, min(num_cols - 1, new_col))

        item = layout.itemAtPosition(new_row, new_col)
        if item and item.widget():
            target = item.widget()
            target.setFocus()
            # scroll follow
            parent_scroll = self.parent()
            while parent_scroll and not isinstance(parent_scroll, QScrollArea):
                parent_scroll = parent_scroll.parent()
            if parent_scroll:
                parent_scroll.ensureWidgetVisible(target)
                
class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arcade Launcher")
        self.resize(1280, 720)

        self.setup_background()
        self.setObjectName("MainWindow")
        self.setStyleSheet(f"""
            #MainWindow {{
                font-family: Segoe UI;
                color: #f0f0f0;
                /* El fondo transparente para el QLabel */
                background-color: transparent; 
            }}

            QScrollBar:vertical {{
                border: none;
                background: #2a2a2a;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #555555;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}

            #RightPanelContainer {{
                background-color: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
            }}

            QPushButton {{
                /* Estilo del contenedor del botón (background) */
                background-color: transparent;
                border: none;
                padding: 0px; 
            }}
            
            /* Redondeo de la imagen */
            QPushButton::icon {{
                border-radius: 12px; 
            }}

            QPushButton:focus {{ /* El estado de foco es más relevante que el hover*/
                border: 4px solid #0078d7; /* Borde */
                border-radius: 12px;
                padding: -4px;
            }}
            
            /* Nota a mi mismo: Quitar el estilo 'hover' si el 'focus' es el indicador principal */
            QPushButton:hover {{
                 background-color: transparent; 
                 border: none;
            }}
        """)

        # Cargar los juegos
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(script_dir, "data", "games.json")
            with open(json_path, "r", encoding="utf-8") as f:
                self.games = json.load(f)
        except FileNotFoundError:
            print("Error: El archivo games.json no se encontró en la carpeta 'data'.")
            self.games = [] 

        # Panel izquierdo que no usé
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Panel derecho
        right_panel_container = QWidget()
        right_panel_container.setObjectName("RightPanelContainer")
        right_layout = QVBoxLayout(right_panel_container)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        header_label = QLabel(f"ALL GAMES ({len(self.games)})")
        header_label.setStyleSheet("font-size: 20px; font-weight: bold; padding-bottom: 10px;")
        
        self.scroll_area_right = QScrollArea()
        self.scroll_area_right.setWidgetResizable(True)
        self.scroll_area_right.setStyleSheet("border: none;")

        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(20)

        right_layout.addWidget(header_label)
        self.scroll_area_right.setWidget(grid_container)
        right_layout.addWidget(self.scroll_area_right)

        main_layout.addWidget(right_panel_container, 1)

        self.populate_games()

    def setup_background(self):
        # Fondo
        self.background_label = QLabel(self)
        self.background_label.setScaledContents(True) # Hace que el gif escale

        script_dir = os.path.dirname(os.path.abspath(__file__))
        background_path = os.path.join(script_dir, "assets", "xbox.gif")

        if not os.path.exists(background_path):
            print(f"Advertencia: No se encontró el archivo de fondo en {background_path}")
            self.background_label.setStyleSheet("background-color: #0d1b2a;") # Color de respaldo
            return

        if background_path.lower().endswith('.gif'):
            #  gif
            self.movie = QMovie(background_path)
            self.background_label.setMovie(self.movie)
            self.movie.start()
            print("Reproduciendo fondo animado (GIF).")
        else:
            # Por si no hay gif
            pixmap = QPixmap(background_path)
            self.background_label.setPixmap(pixmap)
            print("Mostrando fondo estático.")
    def resizeEvent(self, event):
        """Ajusta el tamaño del fondo cuando la ventana cambia de tamaño."""
        super().resizeEvent(event)
        # Que ocupe toda la ventana
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        # Siempre detrás de otros widgets
        self.background_label.lower()

    def populate_games(self):
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
            script_dir = os.path.dirname(os.path.abspath(__file__))
            cover_full_path = os.path.join(script_dir, image_path)
            
            pixmap = QPixmap(cover_full_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    QSize(COVER_WIDTH, COVER_HEIGHT),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                # El redondeo de esquinas
                rounded = rounded_pixmap(scaled_pixmap, 9)

                button.setIcon(QIcon(rounded))
                button.setIconSize(rounded.size())

            else:
                print(f"Error al cargar la imagen: {cover_full_path} para {game_data['name']}")

        button.clicked.connect(lambda: self.launch_game(game_data))
        return button

    def launch_game(self, game_data):
        path = game_data.get("path")
        emu = game_data.get("emulator")
        rom = game_data.get("rom")

        print(f"Lanzando {game_data['name']}...")
        if path:
            subprocess.Popen(path)
        elif emu and rom:
            subprocess.Popen([emu, rom])
        else:
            print(f"No se encontró una ruta o emulador/rom para {game_data['name']}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec())
