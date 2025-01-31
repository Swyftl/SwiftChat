MODERN_STYLE = """
QMainWindow, QDialog {
    background-color: #f0f0f0;
}

QTextEdit, QLineEdit {
    background-color: white;
    color: #333333;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px;
    font-size: 10pt;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QLabel {
    color: #333333;
    font-size: 10pt;
}

QMenuBar {
    background-color: #f8f8f8;
    border-bottom: 1px solid #ddd;
    color: #333333;
}

QMenuBar::item {
    padding: 8px 12px;
    color: #333333;
}

QMenuBar::item:selected {
    background-color: #0078d4;
    color: white;
}

QMenu {
    background-color: white;
    border: 1px solid #ccc;
    color: #333333;
}

QMenu::item {
    padding: 8px 20px;
    color: #333333;
}

QMenu::item:selected {
    background-color: #0078d4;
    color: white;
}

QListWidget {
    background-color: white;
    color: #333333;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 4px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 2px;
    color: #333333;
}

QListWidget::item:selected {
    background-color: #0078d4;
    color: white;
}

QComboBox {
    background-color: white;
    color: #333333;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px;
    min-width: 6em;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(down_arrow.png);
    width: 12px;
    height: 12px;
}

QStatusBar {
    background-color: #f8f8f8;
    color: #666666;
}

/* Custom classes */
.error-label {
    color: #d83b01;
    font-weight: bold;
}

.success-label {
    color: #107c10;
    font-weight: bold;
}

.chat-window {
    background-color: white;
    color: #333333;
    border: none;
}

.message-input {
    background-color: white;
    color: #333333;
    border: 2px solid #0078d4;
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 11pt;
}

.send-button {
    background-color: #0078d4;
    color: white;
    border-radius: 20px;
    padding: 8px 20px;
    font-weight: bold;
}

/* Additional fixes for specific widgets */
QCheckBox {
    color: #333333;
}

QGroupBox {
    color: #333333;
}

QTabWidget {
    color: #333333;
}

QTabBar::tab {
    color: #333333;
}

QHeaderView::section {
    color: #333333;
}

QTableWidget {
    color: #333333;
}

QScrollBar {
    background-color: #f0f0f0;
}

QToolTip {
    background-color: white;
    color: #333333;
    border: 1px solid #ccc;
}
"""
