
LAUNCHER_STYLES = """
#MainWindow {
    font-family: Segoe UI;
    color: #f0f0f0;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #2a2a2a;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #555555;
    min-height: 20px;
    border-radius: 5px;
    min-height: 30px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

#RightPanelContainer {
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
}

QPushButton {
    background-color: transparent;
    border: none;
    padding: 0px;
}

QPushButton::icon {
    border-radius: 12px;
}

QPushButton:focus {
    border: 4px solid #0078d7;
    border-radius: 12px;
    padding: -4px;
}

QPushButton:hover {
    background-color: transparent;
    border: none;
}
"""
