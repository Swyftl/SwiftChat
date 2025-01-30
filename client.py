import socket
import os
import pygame.mixer
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QDialog, QMessageBox,
                            QListWidget,
                            QColorDialog, QFontDialog, QCheckBox)  # Add these imports
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QColor
import sys
import requests
import webbrowser
import subprocess
import json

# Version control constants
CURRENT_VERSION = "V0.1.8"
GITHUB_REPO = "swyftl/swiftChat"  # Replace with your actual GitHub repo

def is_running_as_exe():
    """Check if we're running as a bundled exe"""
    return getattr(sys, 'frozen', False)

def check_for_updates():
    try:
        print("Checking for client updates...")
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release["tag_name"].strip("v")
            
            print(f"Current version: {CURRENT_VERSION}")
            print(f"Latest version: {latest_version}")
            
            if latest_version > CURRENT_VERSION:
                if QMessageBox.question(
                    None,
                    "Update Available",
                    f"A new version ({latest_version}) is available!\n"
                    f"You are currently running version {CURRENT_VERSION}\n\n"
                    "Would you like to download and install the update?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
                    for asset in latest_release['assets']:
                        if asset['name'].lower() == 'swiftchat.exe':
                            try:
                                current_exe = sys.executable if is_running_as_exe() else "SwiftChat.exe"
                                temp_exe = "SwiftChat_update.exe"
                                update_script = "update_helper.bat"
                                
                                # Download update
                                response = requests.get(asset['browser_download_url'], stream=True)
                                if response.status_code == 200:
                                    with open(temp_exe, 'wb') as f:
                                        for chunk in response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    
                                    # Create update helper script
                                    with open(update_script, 'w') as f:
                                        f.write('@echo off\n')
                                        f.write('echo Updating SwiftChat...\n')
                                        f.write('timeout /t 1 /nobreak >nul\n')
                                        f.write(f'move /Y "{temp_exe}" "{current_exe}"\n')
                                        f.write(f'start "" "{current_exe}"\n')
                                        f.write('del "%~f0"\n')

                                    # Start update script and exit
                                    QMessageBox.information(
                                        None,
                                        "Update Ready",
                                        "Update downloaded successfully!\n"
                                        "The application will now restart to complete the update."
                                    )
                                    subprocess.Popen([update_script], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                                    os._exit(0)
                            except Exception as e:
                                print(f"Error during update: {e}")
                                QMessageBox.critical(
                                    None,
                                    "Update Error",
                                    f"Failed to download update: {str(e)}"
                                )
                            break
                    else:
                        print("No SwiftChat.exe found in release assets")
                        webbrowser.open(latest_release['html_url'])
                        
    except Exception as e:
        print(f"Update check failed: {e}")

# Global variables
HOST = '127.0.0.1'
PORT = 8080
client = None
username = None
password = None
private_chats = {}
CREDENTIALS_FILE = 'credentials.txt'
SETTINGS_FILE = 'chat_settings.txt'  # Changed from .json to .txt

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

class MessageReceiver(QObject):
    message_received = pyqtSignal(str)
    private_message_received = pyqtSignal(str, str)
    online_users_received = pyqtSignal(list)
    connection_lost = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            try:
                message = client.recv(1024).decode('utf-8')
                
                if message.startswith('ONLINE_USERS:'):
                    users = message.split(':')[1].split(', ')
                    self.online_users_received.emit(users)
                elif message.startswith('[Private]'):
                    sender = message[9:].split(':')[0].strip()
                    self.private_message_received.emit(sender, message)
                elif message.startswith('[Private to'):
                    recipient = message[11:].split(']')[0].strip()
                    self.private_message_received.emit(recipient, message)
                else:
                    self.message_received.emit(message)
            except:
                if self.running:
                    self.connection_lost.emit()
                    self.running = False
                break

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class ChatMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize sound system
        pygame.mixer.init()
        self.sound_enabled = True
        try:
            self.sounds = {
                'sent': pygame.mixer.Sound(resource_path('resources/sounds/message_sent.mp3')),
                'received': pygame.mixer.Sound(resource_path('resources/sounds/message_received.mp3')),
                'joined': pygame.mixer.Sound(resource_path('resources/sounds/user_joined.mp3')),
                'left': pygame.mixer.Sound(resource_path('resources/sounds/user_left.mp3')),
                'dm_start': pygame.mixer.Sound(resource_path('resources/sounds/DM_Started.mp3'))
            }
        except Exception as e:
            print(f"Could not load notification sounds: {e}")
            self.sound_enabled = False
        
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
        
        # Setup message receiver
        self.receiver = MessageReceiver()
        self.receiver_thread = QThread()
        self.receiver.moveToThread(self.receiver_thread)
        
        # Connect signals
        self.receiver.message_received.connect(self.handle_message)
        self.receiver.private_message_received.connect(self.handle_private_message)
        self.receiver.online_users_received.connect(self.show_online_users_dialog)
        self.receiver.connection_lost.connect(self.handle_connection_lost)
        
        # Start receiver thread
        self.receiver_thread.started.connect(self.receiver.run)
        self.receiver_thread.start()

        # Store dialogs as instance variables
        self.online_users_dialog = None

        # Load saved settings
        self.load_settings()

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
        """Handle window closing"""
        try:
            # Notify server we're disconnecting
            if client:
                try:
                    client.send('/quit'.encode('utf-8'))
                except:
                    pass
                    
            # Stop receiver thread first
            if hasattr(self, 'receiver'):
                self.receiver.running = False
                if hasattr(self, 'receiver_thread'):
                    self.receiver_thread.quit()
                    self.receiver_thread.wait()
            
            # Close all private chat windows
            for chat_window in private_chats.values():
                chat_window.close()
            
            # Close socket last
            if client:
                try:
                    client.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                client.close()
            
            # Save any settings if needed
            self.save_settings()
            
            # Accept the close event
            event.accept()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            # Make sure the app quits
            QApplication.quit()

    def save_settings(self):
        """Save current settings before exit"""
        try:
            settings = {
                'font_family': self.chat_display.font().family(),
                'font_size': self.chat_display.font().pointSize(),
                'text_color': self.chat_display.textColor().name(),
                'bg_color': self.chat_display.palette().color(self.chat_display.backgroundRole()).name(),
                'sound_enabled': self.sound_enabled
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def handle_message(self, message):
        """Handle regular messages"""
        if ' joined the chat!' in message:
            self.play_sound('joined')
        elif ' left the chat!' in message:
            self.play_sound('left')
        elif not message.startswith((f'{username}:', 'MESSAGE_HISTORY', '===')):
            self.play_sound('received')
        
        self.chat_display.append(message + '\n')

    def handle_connection_lost(self):
        """Handle connection lost"""
        self.status_label.setText("Disconnected")
        QMessageBox.warning(self, "Connection Lost", "Lost connection to server.")
        self.receiver.running = False
        self.close()

    def write(self):
        """Send message"""
        message = self.message_input.text()
        if message and client:
            try:
                client.send(f'{username}: {message}'.encode('utf-8'))
                self.message_input.clear()
                self.play_sound('sent')  # Play sent sound
            except:
                QMessageBox.warning(self, "Error", "Failed to send message")

    def play_sound(self, sound_type):
        """Play notification sound"""
        if self.sound_enabled and sound_type in self.sounds:
            try:
                self.sounds[sound_type].play()
            except Exception as e:
                print(f"Error playing sound: {e}")

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
        if not self.online_users_dialog:
            self.online_users_dialog = OnlineUsersDialog(users, self)
        else:
            # Update users list
            self.online_users_dialog.update_users(users)
        self.online_users_dialog.show()

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
        dialog = SettingsDialog(self)
        dialog.exec()

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            settings[key] = value
                    
                    # Apply font
                    font = QFont(
                        settings.get('font_family', 'Arial'),
                        int(settings.get('font_size', '10'))
                    )
                    self.chat_display.setFont(font)
                    
                    # Apply colors
                    self.chat_display.setTextColor(QColor(settings.get('text_color', '#000000')))
                    palette = self.chat_display.palette()
                    palette.setColor(self.chat_display.backgroundRole(), 
                                   QColor(settings.get('bg_color', '#ffffff')))
                    self.chat_display.setPalette(palette)
                    
                    # Apply sound setting
                    self.sound_enabled = settings.get('sound_enabled', 'true').lower() == 'true'
        except Exception as e:
            print(f"Error loading settings: {e}")

class PrivateChatWindow(QMainWindow):  # Change from QWidget to QMainWindow
    def __init__(self, other_user, parent=None):
        super().__init__(parent)
        self.other_user = other_user
        self.parent = parent
        
        # Play DM start sound when window is created
        if hasattr(self.parent, 'play_sound'):
            self.parent.play_sound('dm_start')
        
        self.setWindowTitle(f"Chat with {other_user}")
        self.resize(400, 500)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
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
        
        # Add status bar
        self.statusBar().showMessage("Connected")
        
        # Handle window close
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    def closeEvent(self, event):
        """Hide instead of close"""
        event.ignore()
        self.hide()

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
        close_button.clicked.connect(self.hide)  # Change close() to hide()
        button_layout.addWidget(message_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        # Don't destroy on close
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    def update_users(self, users_list):
        """Update the users list"""
        self.users_list.clear()
        for user in users_list:
            if user != username:
                self.users_list.addItem(user)

    def closeEvent(self, event):
        """Hide instead of close"""
        event.ignore()
        self.hide()

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
            self.hide()  # Change close() to hide()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Chat Settings")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Font settings
        font_layout = QHBoxLayout()
        self.font_label = QLabel("Current Font: Default")
        font_button = QPushButton("Change Font")
        font_button.clicked.connect(self.choose_font)
        font_layout.addWidget(self.font_label)
        font_layout.addWidget(font_button)
        layout.addLayout(font_layout)
        
        # Color settings
        colors_group = QVBoxLayout()
        
        # Text color
        text_color_layout = QHBoxLayout()
        self.text_color_preview = QLabel("   ")
        self.text_color_preview.setStyleSheet("background-color: black; border: 1px solid gray")
        text_color_button = QPushButton("Text Color")
        text_color_button.clicked.connect(self.choose_text_color)
        text_color_layout.addWidget(QLabel("Text Color:"))
        text_color_layout.addWidget(self.text_color_preview)
        text_color_layout.addWidget(text_color_button)
        colors_group.addLayout(text_color_layout)
        
        # Background color
        bg_color_layout = QHBoxLayout()
        self.bg_color_preview = QLabel("   ")
        self.bg_color_preview.setStyleSheet("background-color: white; border: 1px solid gray")
        bg_color_button = QPushButton("Background Color")
        bg_color_button.clicked.connect(self.choose_bg_color)
        bg_color_layout.addWidget(QLabel("Background Color:"))
        bg_color_layout.addWidget(self.bg_color_preview)
        bg_color_layout.addWidget(bg_color_button)
        colors_group.addLayout(bg_color_layout)
        
        layout.addLayout(colors_group)
        
        # Sound settings
        sound_layout = QHBoxLayout()
        self.sound_enabled = QCheckBox("Enable Sound Effects")
        self.sound_enabled.setChecked(self.parent.sound_enabled)
        self.sound_enabled.stateChanged.connect(self.toggle_sound)
        sound_layout.addWidget(self.sound_enabled)
        layout.addLayout(sound_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Store current settings
        self.current_font = self.parent.chat_display.font()
        self.current_text_color = self.parent.chat_display.textColor()
        self.current_bg_color = self.parent.chat_display.palette().color(self.parent.chat_display.backgroundRole())
        
        # Update previews
        self.update_font_preview()
        self.text_color_preview.setStyleSheet(f"background-color: {self.current_text_color.name()}; border: 1px solid gray")
        self.bg_color_preview.setStyleSheet(f"background-color: {self.current_bg_color.name()}; border: 1px solid gray")

    def choose_font(self):
        font, ok = QFontDialog.getFont(self.current_font, self)
        if ok:
            self.current_font = font
            self.update_font_preview()

    def choose_text_color(self):
        color = QColorDialog.getColor(self.current_text_color, self)
        if color.isValid():
            self.current_text_color = color
            self.text_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray")

    def choose_bg_color(self):
        color = QColorDialog.getColor(self.current_bg_color, self)
        if color.isValid():
            self.current_bg_color = color
            self.bg_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray")

    def update_font_preview(self):
        self.font_label.setText(f"Current Font: {self.current_font.family()} {self.current_font.pointSize()}pt")

    def toggle_sound(self, state):
        self.parent.sound_enabled = bool(state)

    def apply_settings(self):
        # Apply to main chat
        self.parent.chat_display.setFont(self.current_font)
        self.parent.chat_display.setTextColor(self.current_text_color)
        palette = self.parent.chat_display.palette()
        palette.setColor(self.parent.chat_display.backgroundRole(), self.current_bg_color)
        self.parent.chat_display.setPalette(palette)
        
        # Apply to private chat windows
        for chat_window in private_chats.values():
            chat_window.chat_display.setFont(self.current_font)
            chat_window.chat_display.setTextColor(self.current_text_color)
            palette = chat_window.chat_display.palette()
            palette.setColor(chat_window.chat_display.backgroundRole(), self.current_bg_color)
            chat_window.chat_display.setPalette(palette)
        
        # Save settings to text file
        settings = [
            f"font_family={self.current_font.family()}",
            f"font_size={self.current_font.pointSize()}",
            f"text_color={self.current_text_color.name()}",
            f"bg_color={self.current_bg_color.name()}",
            f"sound_enabled={str(self.sound_enabled.isChecked()).lower()}"
        ]
        
        try:
            with open(SETTINGS_FILE, 'w') as f:
                f.write('\n'.join(settings))
        except Exception as e:
            print(f"Error saving settings: {e}")
        
        self.accept()

def main():
    app = QApplication(sys.argv)
    
    # Check for updates before showing any windows
    check_for_updates()
    
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
