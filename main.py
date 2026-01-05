import sys
from PySide6.QtWidgets import QApplication
from launcher import Launcher

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec())