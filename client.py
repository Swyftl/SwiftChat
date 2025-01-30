import socket
import threading
import os
import pygame.mixer
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QMenuBar, QMenu, QDialog, QMessageBox,
                            QListWidget, QScrollArea, QFileDialog, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QIcon, QPixmap, QImage
import sys
import json
import io
import base64
from PIL import Image
from datetime import datetime
import requests

# Global variables
HOST = '127.0.0.1'
PORT = 8080
client = None
username = None
password = None
private_chats = {}
CREDENTIALS_FILE = 'credentials.txt'
SETTINGS_FILE = 'chat_settings.json'

# Default settings
DEFAULT_SETTINGS = {
    'bg_color': '#ffffff',
    'text_color': '#000000',
    'font_family': 'Arial',
    'font_size': 10
}

def load_credentials():
    """Load saved credentials from file"""
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 4:  # Need 4 lines: username, password, host, port
                    return {
                        'username': lines[0].strip(),
                        'password': lines[1].strip(),
                        'host': lines[2].strip(),
                        'port': lines[3].strip()
                    }
    except Exception as e:
        print(f"Error loading credentials: {e}")
    return None

def save_credentials(username, password, host=None, port=None):
    """Save credentials to file"""
    try:
        with open(CREDENTIALS_FILE, 'w') as f:
            f.write(f"{username}\n{password}\n{host or HOST}\n{port or PORT}")
    except Exception as e:
        print(f"Error saving credentials: {e}")

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ChatApp - Connect to Server")
        layout = QVBoxLayout(self)

        # Server address
        layout.addWidget(QLabel("Server Address:"))
        self.host_input = QLineEdit(HOST)
        layout.addWidget(self.host_input)

        # Port
        layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit(str(PORT))
        layout.addWidget(self.port_input)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.try_connect)
        layout.addWidget(self.connect_button)

        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)

        # Load saved credentials
        self.load_saved_connection()

    def try_connect(self):
        global client, HOST, PORT
        HOST = self.host_input.text()
        try:
            PORT = int(self.port_input.text())
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((HOST, PORT))
            self.accept()
        except Exception as e:
            self.error_label.setText(f"Connection failed: {str(e)}")

    def load_saved_connection(self):
        saved = load_credentials()
        if saved:
            self.host_input.setText(saved.get('host', HOST))
            self.port_input.setText(saved.get('port', str(PORT)))

class ChatMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatApp")
        self.resize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Message input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.returnPressed.connect(self.write)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.write)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)
        
        # Add connection status
        self.status_label = QLabel("Connected")
        layout.addWidget(self.status_label)
        
        # Keep running flag
        self.running = True
        
        # Setup menu bar
        self.create_menus()
        
        # Start receive thread
        self.receive_thread = threading.Thread(target=self.receive, daemon=True)
        self.receive_thread.start()

    def create_menus(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        quit_action = file_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_app)
        
        # View menu
        view_menu = menubar.addMenu("View")
        users_action = view_menu.addAction("Show Online Users")
        users_action.triggered.connect(lambda: client.send('/online'.encode('utf-8')))  # Fixed connection
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        customize_action = settings_menu.addAction("Customize Chat")
        customize_action.triggered.connect(self.show_settings)

    def closeEvent(self, event):
        self.running = False
        if client:
            client.close()
        event.accept()

    def receive(self):
        """Handle receiving messages"""
        while self.running:
            try:
                message = client.recv(1024).decode('utf-8')
                
                if message == 'MESSAGE_HISTORY_START':
                    self.chat_display.append("=== Chat History ===\n")
                    continue
                elif message == 'MESSAGE_HISTORY_END':
                    self.chat_display.append("=== End of History ===\n\n")
                    continue
                
                if message.startswith('ONLINE_USERS:'):
                    users = message.split(':')[1].split(', ')
                    self.show_online_users_dialog(users)
                elif message.startswith('[Private]'):
                    sender = message[9:].split(':')[0].strip()
                    self.handle_private_message(sender, message)
                elif message.startswith('[Private to'):
                    recipient = message[11:].split(']')[0].strip()
                    self.handle_private_message(recipient, message)
                else:
                    self.chat_display.append(message + '\n')
            except:
                if self.running:
                    self.status_label.setText("Disconnected")
                    QMessageBox.warning(self, "Connection Lost", 
                                      "Lost connection to server.")
                    self.running = False
                break

    def write(self):
        """Send message"""
        message = self.message_input.text()
        if message and client:
            try:
                client.send(f'{username}: {message}'.encode('utf-8'))
                self.message_input.clear()
            except:
                QMessageBox.warning(self, "Error", "Failed to send message")

    def handle_private_message(self, other_user, message):
        """Handle private messages"""
        if other_user not in private_chats:
            chat_window = PrivateChatWindow(other_user, self)
            private_chats[other_user] = chat_window
            chat_window.show()
        
        private_chats[other_user].chat_display.append(message + '\n')
        private_chats[other_user].show()
        private_chats[other_user].raise_()

    def show_online_users_dialog(self, users):
        """Show online users dialog"""
        dialog = OnlineUsersDialog(users, self)
        dialog.exec()

    def quit_app(self):
        """Handle application quit"""
        try:
            # Close all private chat windows
            for window in private_chats.values():
                window.close()
            
            # Close socket and quit
            if client:
                client.close()
            
            self.close()
            QApplication.quit()
        except:
            QApplication.quit()

    def show_settings(self):
        """Show settings dialog"""
        # Placeholder for settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog coming soon!")

class PrivateChatWindow(QWidget):
    def __init__(self, other_user, parent=None):
        super().__init__(parent)
        self.other_user = other_user  # Store recipient
        self.setWindowTitle(f"Chat with {other_user}")
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

    def send_message(self):
        """Send private message"""
        message = self.message_input.text()
        if message and client:
            try:
                client.send(f'/pm:{self.other_user}:{message}'.encode('utf-8'))
                self.message_input.clear()
            except:
                QMessageBox.warning(self, "Error", "Failed to send message")

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ChatApp - Login")
        self.resize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.register_button = QPushButton("Register")
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        layout.addLayout(button_layout)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)
        
        # Connect signals
        self.login_button.clicked.connect(self.try_login)
        self.register_button.clicked.connect(self.show_register)
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
        self.password_input.returnPressed.connect(self.try_login)
        
        # Load saved credentials
        creds = load_credentials()
        if creds:
            self.username_input.setText(creds.get('username', ''))
            self.password_input.setText(creds.get('password', ''))

    def try_login(self):
        global username, password
        username = self.username_input.text()
        password = self.password_input.text()
        
        try:
            print(f"Attempting to log in as {username}")
            client.send('LOGIN'.encode('utf-8'))
            
            # Wait for USER request
            msg = client.recv(1024).decode('utf-8')
            print(f"Server says: {msg}")
            
            if msg == 'USER':
                # Send username
                client.send(username.encode('utf-8'))
                
                # Wait for PASS request
                msg = client.recv(1024).decode('utf-8')
                print(f"Server says: {msg}")
                
                if msg == 'PASS':
                    # Send password
                    client.send(password.encode('utf-8'))
                    
                    # Wait for result
                    response = client.recv(1024).decode('utf-8')
                    print(f"Server response: {response}")
                    
                    if response == 'AUTH_SUCCESS':
                        print("Login successful!")
                        save_credentials(username, password)
                        self.accept()
                        return
            
            self.error_label.setText("Authentication Failed")
        except Exception as e:
            print(f"Login error: {str(e)}")
            self.error_label.setText(f"Login failed: {str(e)}")
    
    def show_register(self):
        """Open registration dialog"""
        register_dialog = RegisterDialog(self)
        if register_dialog.exec() == QDialog.DialogCode.Accepted:
            self.accept()  # Close login dialog if registration successful

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ChatApp - Register")
        self.resize(300, 200)
        
        layout = QVBoxLayout(self)
        
        # Username
        layout.addWidget(QLabel("New Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        # Register button
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.try_register)
        layout.addWidget(self.register_button)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)
        
        # Enter key bindings
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
        self.password_input.returnPressed.connect(self.try_register)

    def try_register(self):
        global username, password
        username = self.username_input.text()
        password = self.password_input.text()
        
        try:
            client.send('REGISTER'.encode('utf-8'))
            
            msg = client.recv(1024).decode('utf-8')
            if msg == 'NEW_USER':
                client.send(username.encode('utf-8'))
                
                msg = client.recv(1024).decode('utf-8')
                if msg == 'USER_EXISTS':
                    self.error_label.setText("Username already exists")
                    return
                elif msg == 'NEW_PASS':
                    client.send(password.encode('utf-8'))
                    
                    response = client.recv(1024).decode('utf-8')
                    if response == 'REG_SUCCESS':
                        save_credentials(username, password)
                        self.accept()
                        return
            
            self.error_label.setText("Registration failed")
        except Exception as e:
            self.error_label.setText(f"Registration error: {str(e)}")

class OnlineUsersDialog(QDialog):
    def __init__(self, users_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Online Users")
        self.resize(200, 300)
        self.parent = parent  # Store parent reference
        
        layout = QVBoxLayout(self)
        
        # Users list
        self.users_list = QListWidget()
        for user in users_list:
            if user != username:  # Now username is accessible as global
                self.users_list.addItem(user)
        layout.addWidget(self.users_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        message_button = QPushButton("Message")
        message_button.clicked.connect(self.message_selected)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(message_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

    def message_selected(self):
        """Handle messaging selected user"""
        if self.users_list.currentItem():
            selected_user = self.users_list.currentItem().text()
            # Create or show private chat window
            if selected_user not in private_chats:
                chat_window = PrivateChatWindow(selected_user, self.parent)
                private_chats[selected_user] = chat_window
                chat_window.show()
            else:
                private_chats[selected_user].show()
                private_chats[selected_user].raise_()
            self.close()

def main():
    app = QApplication(sys.argv)
    
    # First show connection dialog
    conn_dialog = ConnectionDialog()
    if conn_dialog.exec() == QDialog.DialogCode.Accepted:
        # Show login dialog
        login = LoginDialog()
        if login.exec() == QDialog.DialogCode.Accepted:
            # Show main chat window
            window = ChatMainWindow()
            window.show()
            return app.exec()
    
    return 1

if __name__ == '__main__':
    sys.exit(main())
