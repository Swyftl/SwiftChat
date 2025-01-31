THEMES = {
    "Light": {
        "name": "Light Theme",
        "style": """
            QMainWindow, QDialog {
                background-color: #f0f0f0;
            }
            QTextEdit, QLineEdit {
                background-color: white;
                color: #333333;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QLabel {
                color: #333333;
            }
            QMenuBar, QStatusBar {
                background-color: #f8f8f8;
                color: #333333;
            }
            .chat-window {
                background-color: white;
                color: #333333;
            }
            .message-input {
                background-color: white;
                color: #333333;
                border: 2px solid #0078d4;
                border-radius: 20px;
            }
        """
    },
    "Dark": {
        "name": "Dark Theme",
        "style": """
            QMainWindow, QDialog {
                background-color: #1e1e1e;
            }
            QTextEdit, QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QLabel {
                color: #ffffff;
            }
            QMenuBar, QStatusBar {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            .chat-window {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            .message-input {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #0078d4;
                border-radius: 20px;
            }
        """
    },
    "Forest": {
        "name": "Forest Theme",
        "style": """
            QMainWindow, QDialog {
                background-color: #2c3639;
            }
            QTextEdit, QLineEdit {
                background-color: #3f4e4f;
                color: #dcd7c9;
                border: 1px solid #a27b5c;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #a27b5c;
                color: #dcd7c9;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #8b6b4f;
            }
            QLabel {
                color: #dcd7c9;
            }
            QMenuBar, QStatusBar {
                background-color: #3f4e4f;
                color: #dcd7c9;
            }
            .chat-window {
                background-color: #3f4e4f;
                color: #dcd7c9;
            }
            .message-input {
                background-color: #3f4e4f;
                color: #dcd7c9;
                border: 2px solid #a27b5c;
                border-radius: 20px;
            }
        """
    },
    "Nord": {
        "name": "Nord Theme",
        "style": """
            QMainWindow, QDialog {
                background-color: #2e3440;
            }
            QTextEdit, QLineEdit {
                background-color: #3b4252;
                color: #eceff4;
                border: 1px solid #4c566a;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #5e81ac;
                color: #eceff4;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #81a1c1;
            }
            QLabel, QMenuBar, QMenu {
                color: #eceff4;
            }
            QMenuBar, QStatusBar {
                background-color: #3b4252;
            }
            .chat-window {
                background-color: #3b4252;
                color: #eceff4;
            }
        """
    },

    "Dracula": {
        "name": "Dracula Theme",
        "style": """
            QMainWindow, QDialog {
                background-color: #282a36;
            }
            QTextEdit, QLineEdit {
                background-color: #44475a;
                color: #f8f8f2;
                border: 1px solid #6272a4;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #bd93f9;
                color: #f8f8f2;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #ff79c6;
            }
            QLabel, QMenuBar, QMenu {
                color: #f8f8f2;
            }
            QMenuBar, QStatusBar {
                background-color: #44475a;
            }
            .chat-window {
                background-color: #44475a;
                color: #f8f8f2;
            }
        """
    },

    "Material Ocean": {
        "name": "Material Ocean Theme",
        "style": """
            QMainWindow, QDialog {
                background-color: #0f111a;
            }
            QTextEdit, QLineEdit {
                background-color: #1a1c25;
                color: #8f93a2;
                border: 1px solid #464b5d;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #84ffff;
                color: #0f111a;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #18ffff;
            }
            QLabel, QMenuBar, QMenu {
                color: #8f93a2;
            }
            QMenuBar, QStatusBar {
                background-color: #1a1c25;
            }
            .chat-window {
                background-color: #1a1c25;
                color: #8f93a2;
            }
        """
    },

    "Solarized Light": {
        "name": "Solarized Light Theme",
        "style": """
            QMainWindow, QDialog {
                background-color: #fdf6e3;
            }
            QTextEdit, QLineEdit {
                background-color: #eee8d5;
                color: #657b83;
                border: 1px solid #93a1a1;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #2aa198;
                color: #fdf6e3;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #268bd2;
            }
            QLabel, QMenuBar, QMenu {
                color: #657b83;
            }
            QMenuBar, QStatusBar {
                background-color: #eee8d5;
            }
            .chat-window {
                background-color: #eee8d5;
                color: #657b83;
            }
        """
    },

    "Monokai": {
        "name": "Monokai Theme",
        "style": """
            QMainWindow, QDialog {
                background-color: #272822;
            }
            QTextEdit, QLineEdit {
                background-color: #3e3d32;
                color: #f8f8f2;
                border: 1px solid #75715e;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #a6e22e;
                color: #272822;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #f92672;
                color: #f8f8f2;
            }
            QLabel, QMenuBar, QMenu {
                color: #f8f8f2;
            }
            QMenuBar, QStatusBar {
                background-color: #3e3d32;
            }
            .chat-window {
                background-color: #3e3d32;
                color: #f8f8f2;
            }
        """
    }
}
