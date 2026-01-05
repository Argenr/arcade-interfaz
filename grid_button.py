from PySide6.QtWidgets import QPushButton, QLabel, QGraphicsDropShadowEffect
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, QRect, QPoint, QPropertyAnimation, QEasingCurve, QTimer
from utils import COVER_WIDTH, COVER_HEIGHT, rounded_pixmap

class GridButton(QPushButton):
    OVERLAY_GROW = 1.30
    OVERLAY_DURATION = 150
    # Tiempo de espera antes de mostrar el overlay (evita bugs al scrollear rápido)
    DEBOUNCE_DELAY = 100 

    def __init__(self, game_data, row, col, parent_grid, parent=None):
        super().__init__(parent)
        self.game_data = game_data
        self.row = row
        self.col = col
        self.parent_grid = parent_grid
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.base_w = COVER_WIDTH
        self.base_h = COVER_HEIGHT
        self.setFixedSize(self.base_w, self.base_h)

        # Efecto glow estático (el del botón normal)
        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor(0, 220, 255))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)

        self._overlay = None
        self._anim_geo = None
        self._anim_glow = None

        # Timer para el debounce (la clave para solucionar el bug)
        self._focus_timer = QTimer(self)
        self._focus_timer.setSingleShot(True)
        self._focus_timer.setInterval(self.DEBOUNCE_DELAY)
        self._focus_timer.timeout.connect(self._show_overlay_safe)

    def _create_overlay_label(self, pixmap: QPixmap) -> QLabel:
        top = self.window()
        overlay = QLabel(top)
        overlay.setAttribute(Qt.WA_TranslucentBackground, True)
        overlay.setAttribute(Qt.WA_DeleteOnClose, True)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True) # Importante para no bloquear clicks
        overlay.setWindowFlags(Qt.SubWindow)
        overlay.setAlignment(Qt.AlignCenter)
        overlay.setScaledContents(True)
        
        # Forzamos fondo transparente en CSS para evitar cuadros blancos
        overlay.setStyleSheet("background-color: transparent; border-radius: 12px;")
        
        overlay.setPixmap(rounded_pixmap(pixmap, 12))
        return overlay

    def _get_global_rect(self) -> QRect:
        top = self.window()
        origin = self.mapTo(top, QPoint(0, 0))
        return QRect(origin.x(), origin.y(), self.width(), self.height())

    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Iniciamos el contador. Si te mueves antes de 100ms, el overlay NUNCA nace.
        self._focus_timer.start()

    def _show_overlay_safe(self):
        """Este método solo se ejecuta si el usuario se quedó en el botón."""
        if not self.hasFocus(): 
            return # Doble chequeo de seguridad

        pix = self.icon().pixmap(self.base_w, self.base_h)
        if pix.isNull():
            return

        self._overlay = self._create_overlay_label(pix)
        
        start_rect = self._get_global_rect()
        cx, cy = start_rect.center().x(), start_rect.center().y()
        final_w, final_h = int(self.base_w * self.OVERLAY_GROW), int(self.base_h * self.OVERLAY_GROW)
        final_rect = QRect(cx - final_w // 2, cy - final_h // 2, final_w, final_h)

        self._overlay.setGeometry(start_rect)
        self._overlay.show()
        self._overlay.raise_()

        # Animación
        self._anim_geo = QPropertyAnimation(self._overlay, b"geometry")
        self._anim_geo.setDuration(self.OVERLAY_DURATION)
        self._anim_geo.setStartValue(start_rect)
        self._anim_geo.setEndValue(final_rect)
        self._anim_geo.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_geo.start()

        # Glow Overlay
        overlay_glow = QGraphicsDropShadowEffect(self._overlay)
        overlay_glow.setColor(QColor(0, 220, 255))
        overlay_glow.setOffset(0, 0)
        overlay_glow.setBlurRadius(0)
        self._overlay.setGraphicsEffect(overlay_glow)

        self._anim_glow = QPropertyAnimation(overlay_glow, b"blurRadius")
        self._anim_glow.setDuration(self.OVERLAY_DURATION)
        self._anim_glow.setStartValue(0)
        self._anim_glow.setEndValue(25)
        self._anim_glow.start()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        
        # 1. Si el timer estaba corriendo (pasaste rápido), lo matamos.
        # Resultado: El overlay nunca se creó, cero consumo, cero bugs.
        if self._focus_timer.isActive():
            self._focus_timer.stop()
        
        # 2. Si el overlay ya existía, lo destruimos suavemente.
        if self._overlay:
            self._close_overlay()

    def _close_overlay(self):
        if not self._overlay: return
        
        # Capturamos referencia local para evitar conflictos
        overlay_ref = self._overlay
        self._overlay = None # Desvinculamos inmediatamente de la clase
        
        # Animación de salida (opcional, para que se vea fluido)
        start_rect = overlay_ref.geometry()
        end_rect = self._get_global_rect()

        anim = QPropertyAnimation(overlay_ref, b"geometry", overlay_ref)
        anim.setDuration(100) # Salida rápida
        anim.setStartValue(start_rect)
        anim.setEndValue(end_rect)
        anim.setEasingCurve(QEasingCurve.InQuad)
        
        # Función de limpieza final
        def cleanup():
            overlay_ref.hide()
            overlay_ref.deleteLater()

        anim.finished.connect(cleanup)
        anim.start()
        
        # Guardamos la referencia de la animación en el objeto overlay 
        # para que no sea recolectada por el garbage collector antes de terminar
        overlay_ref._temp_anim = anim 

def keyPressEvent(self, event):
    key = event.key()

    # --- ACTIVAR JUEGO ---
    if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
        self.click()
        return

    # --- NAVEGACIÓN ---
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

    # --- CLAMP ---
    new_row = max(0, min(layout.rowCount() - 1, new_row))
    new_col = max(0, min(num_cols - 1, new_col))

    item = layout.itemAtPosition(new_row, new_col)
    if item and item.widget():
        target = item.widget()
        target.setFocus()

        # Scroll automático
        parent = self.parent()
        while parent:
            if hasattr(parent, "ensureWidgetVisible"):
                parent.ensureWidgetVisible(target)
                break
            parent = parent.parent()
