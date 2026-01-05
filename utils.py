from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath

# Constantes para el tamaño de las carátulas
COVER_WIDTH = 200
COVER_HEIGHT = 262

def rounded_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
    if pixmap.isNull():
        return pixmap

    rounded = QPixmap(pixmap.size())
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)

    path = QPainterPath()
    rect = pixmap.rect()
    path.addRoundedRect(rect, radius, radius)

    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    return rounded
