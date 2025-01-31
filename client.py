import socket
import os
import pygame.mixer
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTextEdit, QDialog, QMessageBox,
                            QListWidget, QComboBox, QFormLayout,  # Add QComboBox, QFormLayout
                            QColorDialog, QFontDialog, QCheckBox, QListWidgetItem,
                            QTabWidget, QSpinBox, QGroupBox, QScrollArea)  # Add these imports
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer  # Add QTimer
from PyQt6.QtGui import QFont, QColor
import sys
import requests
import webbrowser
import subprocess
import json
from encryption import E2EEncryption
import base64
from profiles import ProfileManager  # Add this import
from datetime import datetime  # Change the import
from styles import MODERN_STYLE  # Add this import
from themes import THEMES  # Add this import

# Version control constants
CURRENT_VERSION = "V0.2.3"
GITHUB_REPO = "swyftl/swiftChat"  # Replace with your actual GitHub repo

# Global user data dictionary
user_data = {}

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

class ProfileDialog(QDialog):
    def __init__(self, profile_manager, parent=None):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.setWindowTitle("Profile Management")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Profile list
        self.profile_list = QListWidget()
        self.profile_list.addItems(profile_manager.get_profile_names())
        layout.addWidget(self.profile_list)
        
        # Profile details
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        
        form_layout.addRow("Profile Name:", self.name_input)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Port:", self.port_input)
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save Profile")
        delete_button = QPushButton("Delete Profile")
        close_button = QPushButton("Close")
        
        save_button.clicked.connect(self.save_profile)
        delete_button.clicked.connect(self.delete_profile)
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # Connect selection changed
        self.profile_list.currentItemChanged.connect(self.profile_selected)

    def profile_selected(self, current):
        if current:
            profile = self.profile_manager.get_profile(current.text())
            if profile:
                self.name_input.setText(current.text())
                self.username_input.setText(profile['username'])
                self.password_input.setText(profile['password'])
                self.host_input.setText(profile['host'])
                self.port_input.setText(str(profile['port']))

    def save_profile(self):
        name = self.name_input.text()
        if name:
            self.profile_manager.add_profile(
                name,
                self.username_input.text(),
                self.password_input.text(),
                self.host_input.text(),
                self.port_input.text()
            )
            self.profile_list.clear()
            self.profile_list.addItems(self.profile_manager.get_profile_names())

    def delete_profile(self):
        current = self.profile_list.currentItem()
        if current:
            self.profile_manager.delete_profile(current.text())
            self.profile_list.clear()
            self.profile_list.addItems(self.profile_manager.get_profile_names())

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile_manager = ProfileManager()
        self.setWindowTitle("ChatApp - Connect to Server")
        layout = QVBoxLayout(self)

        # Profile selection
        profile_layout = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(self.profile_manager.get_profile_names())
        profile_button = QPushButton("Manage Profiles")
        profile_layout.addWidget(QLabel("Profile:"))
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addWidget(profile_button)
        layout.addLayout(profile_layout)

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

        # Connect signals
        profile_button.clicked.connect(self.manage_profiles)
        self.profile_combo.currentTextChanged.connect(self.load_profile)

    def manage_profiles(self):
        dialog = ProfileDialog(self.profile_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.profile_combo.clear()
            self.profile_combo.addItems(self.profile_manager.get_profile_names())

    def load_profile(self, profile_name):
        if profile_name:
            profile = self.profile_manager.get_profile(profile_name)
            if profile:
                self.host_input.setText(profile['host'])
                self.port_input.setText(str(profile['port']))
                user_data.update({
                    'username': profile['username'],
                    'password': profile['password'],
                    'host': profile['host'],
                    'port': profile['port']
                })

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

class MessageReceiver(QObject):
    message_received = pyqtSignal(str)
    private_message_received = pyqtSignal(str, str)
    online_users_received = pyqtSignal(list)
    connection_lost = pyqtSignal()
    friends_list_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        # Add buffer for incomplete messages
        self.message_buffer = ""
        # Configure client socket (if not already configured)
        if client:
            client.settimeout(0.1)  # 100ms timeout
            # Enable TCP keepalive
            client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            # Set TCP keepalive time
            if hasattr(socket, "TCP_KEEPIDLE"):  # Linux
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
            elif hasattr(socket, "TCP_KEEPALIVE"):  # macOS
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, 30)
            # Set TCP keepalive interval
            if hasattr(socket, "TCP_KEEPINTVL"):
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
            # Set TCP keepalive retry count
            if hasattr(socket, "TCP_KEEPCNT"):
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)

    def run(self):
        while self.running:
            try:
                try:
                    data = client.recv(4096)  # Increased buffer size
                    if not data:
                        if self.running:
                            self.connection_lost.emit()
                            self.running = False
                        break
                    
                    # Append received data to buffer
                    self.message_buffer += data.decode('utf-8')
                    
                    # Process complete messages
                    while '\n' in self.message_buffer:
                        message, self.message_buffer = self.message_buffer.split('\n', 1)
                        self.process_message(message)
                        
                except socket.timeout:
                    # Handle timeout - just continue loop
                    continue
                except ConnectionResetError:
                    if self.running:
                        self.connection_lost.emit()
                        self.running = False
                    break
                    
            except Exception as e:
                print(f"Receiver error: {e}")
                if self.running:
                    self.connection_lost.emit()
                    self.running = False
                break

    def process_message(self, message):
        """Process a single complete message"""
        try:
            if not message:
                return
                
            if message.startswith('FRIENDS_LIST:'):
                _, friends_data = message.split(':', 1)
                self.friends_list_received.emit(friends_data)
            elif message.startswith('ONLINE_USERS:'):
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
        except Exception as e:
            print(f"Error processing message: {e}")

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class ChatMainWindow(QMainWindow):
    def __init__(self, encryption_instance=None):
        super().__init__()
        
        # Initialize username from user_data
        self.username = user_data.get('username')
        if not self.username:
            raise ValueError("Username not set")
            
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
        self.receiver.friends_list_received.connect(self.update_friends_list)
        
        # Start receiver thread
        self.receiver_thread.started.connect(self.receiver.run)
        self.receiver_thread.start()

        # Store dialogs as instance variables
        self.online_users_dialog = None

        # Load saved settings
        self.load_settings()

        # Use passed encryption instance if available
        self.encryption = encryption_instance or E2EEncryption()
        self.secure_chats = {}  # Track encrypted chats

        self.friends_dialog = None

        # Apply custom classes
        self.message_input.setProperty('class', 'message-input')
        self.send_button.setProperty('class', 'send-button')
        self.chat_display.setProperty('class', 'chat-window')
        
        # Set window minimum size
        self.setMinimumSize(600, 400)
        
        # Add margins to layout
        layout = self.centralWidget().layout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Add theme attribute
        self.current_theme = "Light"

        # Load and apply saved settings
        self.apply_saved_settings()

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

        # Add Friends menu item
        friends_action = view_menu.addAction("Friends List")
        friends_action.triggered.connect(self.show_friends_dialog)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        settings_action = settings_menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)

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
        if message.startswith('PUBLIC_KEY:'):
            # Handle received public key
            _, sender, key_data = message.split(':', 2)
            try:
                # Generate and send session key
                session_key, encrypted_key = self.encryption.generate_session_key(key_data.encode())
                client.send(f"SESSION_KEY:{sender}:{base64.b64encode(encrypted_key).decode()}\n".encode())
                self.encryption.store_session_key(sender, session_key)
                self.secure_chats[sender] = True
            except Exception as e:
                print(f"Key exchange error: {e}")
            return
            
        if message.startswith('SESSION_KEY:'):
            # Handle received session key
            _, sender, enc_key = message.split(':', 2)
            try:
                session_key = self.encryption.decrypt_session_key(base64.b64decode(enc_key))
                self.encryption.store_session_key(sender, session_key)
                self.secure_chats[sender] = True
            except Exception as e:
                print(f"Session key error: {e}")
            return
            
        if message.startswith('ENCRYPTED_MSG:'):
            # Handle encrypted message
            _, sender, enc_data = message.split(':', 2)
            try:
                decrypted = self.encryption.decrypt_message(sender, base64.b64decode(enc_data))
                self.chat_display.append(f"{sender}: {decrypted}")
            except Exception as e:
                print(f"Decryption error: {e}")
            return

        if message.startswith('FRIENDS_LIST:'):
            _, friends_data = message.split(':', 1)
            if self.friends_dialog:
                self.friends_dialog.update_friends_list(friends_data)
            return
            
        if message.startswith('FRIEND_REQUEST_RECEIVED:'):
            _, sender = message.split(':', 1)
            response = QMessageBox.question(
                self,
                "Friend Request",
                f"{sender} wants to add you as a friend. Accept?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            accept = "accept" if response == QMessageBox.StandardButton.Yes else "reject"
            client.send(f"FRIEND_RESPONSE:{sender}:{accept}\n".encode())
            return
            
        if message.startswith('FRIEND_RESPONSE_RECEIVED:'):
            _, sender, status = message.split(':', 2)
            QMessageBox.information(
                self,
                "Friend Request Response",
                f"{sender} has {status} your friend request."
            )
            # Refresh friends list
            client.send('GET_FRIENDS\n'.encode())
            return
            
        if message.startswith('FRIEND_STATUS:'):
            _, status = message.split(':', 1)
            if status == 'REQUEST_EXISTS':
                QMessageBox.warning(
                    self,
                    "Friend Request",
                    "Friend request already exists."
                )
            elif status == 'REQUEST_SENT':
                QMessageBox.information(
                    self,
                    "Friend Request",
                    "Friend request sent successfully."
                )
            return

        if ' joined the chat!' in message:
            self.play_sound('joined')
        elif ' left the chat!' in message:
            self.play_sound('left')
        elif not message.startswith((f'{self.username}:', 'MESSAGE_HISTORY', '===')):
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
                client.send(f'{self.username}: {message}\n'.encode('utf-8'))
                self.message_input.clear()
                self.play_sound('sent')  # Play sent sound
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to send message: {str(e)}")

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

                    # Load theme
                    self.current_theme = settings.get('theme', 'Light')
                    if self.current_theme in THEMES:
                        QApplication.instance().setStyleSheet(THEMES[self.current_theme]["style"])
        except Exception as e:
            print(f"Error loading settings: {e}")

    def send_private_message(self, recipient, message):
        """Send encrypted private message"""
        if recipient not in self.secure_chats:
            # Initiate key exchange
            client.send(f"KEY_EXCHANGE:{recipient}\n".encode())
            self.chat_display.append(f"Establishing secure connection with {recipient}...")
            return
            
        try:
            encrypted = self.encryption.encrypt_message(recipient, message)
            client.send(f"ENCRYPTED_MSG:{recipient}:{base64.b64encode(encrypted).decode()}\n".encode())
        except Exception as e:
            print(f"Encryption error: {e}")

    def show_friends_dialog(self):
        """Show friends management dialog"""
        if not self.friends_dialog:
            self.friends_dialog = FriendsDialog(self)
            # Request friends list after dialog is created
            try:
                client.send('GET_FRIENDS\n'.encode())
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to request friends list: {str(e)}")
        self.friends_dialog.show()
        self.friends_dialog.raise_()

    def update_friends_list(self, friends_data):
        """Update friends list when data received"""
        if self.friends_dialog and self.friends_dialog.isVisible():
            self.friends_dialog.update_friends_list(friends_data)

    def apply_saved_settings(self):
        """Apply saved settings on startup"""
        settings = self.load_settings()
        
        # Apply theme
        self.current_theme = settings.get('theme', 'Light')
        if self.current_theme in THEMES:
            QApplication.instance().setStyleSheet(THEMES[self.current_theme]["style"])
        
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
        
        # Apply sound settings
        self.sound_enabled = settings.get('sound_enabled', 'true').lower() == 'true'

    def load_settings(self):
        """Load settings with defaults"""
        settings = DEFAULT_SETTINGS.copy()
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            settings[key] = value
        except Exception as e:
            print(f"Error loading settings: {e}")
        return settings

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

        # Apply custom classes
        self.message_input.setProperty('class', 'message-input')
        self.send_button.setProperty('class', 'send-button')
        self.chat_display.setProperty('class', 'chat-window')
        
        # Set window minimum size
        self.setMinimumSize(400, 300)
        
        # Add margins to layout
        layout = self.centralWidget().layout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

    def closeEvent(self, event):
        """Hide instead of close"""
        event.ignore()
        self.hide()

    def send_message(self):
        """Send private message"""
        message = self.message_input.text()
        if message and client:
            try:
                # Add newline terminator to message
                client.send(f'/pm:{self.other_user}:{message}\n'.encode('utf-8'))
                self.message_input.clear()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to send message: {str(e)}")

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ChatApp - Login")
        self.resize(300, 200)
        self.encryption_instance = None  # Add this line to store encryption instance
        
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

        # Pre-fill credentials if they're set from profile
        if user_data.get('username') and user_data.get('password'):
            self.username_input.setText(user_data['username'])
            self.password_input.setText(user_data['password'])
            # Optionally auto-login
            QTimer.singleShot(0, self.try_login)

    def try_login(self):
        try:
            username = self.username_input.text()
            password = self.password_input.text()
            
            print(f"Attempting to log in as {username}")
            client.send('LOGIN\n'.encode('utf-8'))
            
            # Wait for USER prompt
            response = client.recv(1024).decode('utf-8').strip()
            print(f"Server response: {response}")
            
            if response != 'USER':
                raise Exception("Unexpected server response")
                
            # Send username
            client.send(f"{username}\n".encode('utf-8'))
            
            # Wait for PASS prompt
            response = client.recv(1024).decode('utf-8').strip()
            print(f"Server response: {response}")
            
            if response != 'PASS':
                raise Exception("Unexpected server response")
                
            # Send password
            client.send(f"{password}\n".encode('utf-8'))
            
            # Wait for key exchange request
            response = client.recv(1024).decode('utf-8').strip()
            print(f"Server response: {response}")
            
            if response != 'SEND_KEY':
                raise Exception("Key exchange failed")
                
            # Send public key
            self.encryption_instance = E2EEncryption()
            public_key = self.encryption_instance.get_public_key_bytes()
            client.send(public_key)
            
            # Wait for authentication result
            response = client.recv(1024).decode('utf-8').strip()
            print(f"Final server response: {response}")
            
            if response == 'AUTH_SUCCESS':
                print("Login successful!")
                user_data.update({
                    'username': username,
                    'password': password
                })
                save_credentials(username, password)
                self.accept()
            else:
                print(f"Authentication failed: {response}")
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
            client.send('REGISTER\n'.encode('utf-8'))
            
            msg = client.recv(1024).decode('utf-8')
            if msg == 'NEW_USER':
                client.send(f"{username}\n".encode('utf-8'))
                
                msg = client.recv(1024).decode('utf-8')
                if msg == 'USER_EXISTS':
                    self.error_label.setText("Username already exists")
                    return
                elif msg == 'NEW_PASS':
                    client.send(f"{password}\n".encode('utf-8'))
                    
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
        self.parent = parent
        self.setWindowTitle("Online Users")
        self.resize(200, 300)
        
        # Store username reference from parent
        self.username = self.parent.username if self.parent else None
        
        layout = QVBoxLayout(self)
        
        # Users list
        self.users_list = QListWidget()
        for user in users_list:
            if user != self.username:  # Use instance variable instead of global
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
            if user != self.username:  # Use instance variable
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
        self.setWindowTitle("Settings")
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.add_general_tab()
        self.add_appearance_tab()
        self.add_notifications_tab()
        self.add_privacy_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        apply_button = QPushButton("Apply")
        cancel_button = QPushButton("Cancel")
        apply_button.clicked.connect(self.apply_settings)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(apply_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Load current settings
        self.load_current_settings()

    def add_general_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        general_widget = QWidget()
        layout = QVBoxLayout(general_widget)
        
        # Message Settings
        msg_group = QGroupBox("Message Settings")
        msg_layout = QVBoxLayout()
        
        self.show_timestamps = QCheckBox("Show timestamps")
        self.message_preview = QCheckBox("Show message previews")
        self.auto_scroll = QCheckBox("Auto-scroll to new messages")
        
        msg_layout.addWidget(self.show_timestamps)
        msg_layout.addWidget(self.message_preview)
        msg_layout.addWidget(self.auto_scroll)
        msg_group.setLayout(msg_layout)
        layout.addWidget(msg_group)
        
        # History Settings
        history_group = QGroupBox("History Settings")
        history_layout = QFormLayout()
        
        self.history_limit = QSpinBox()
        self.history_limit.setRange(10, 1000)
        self.history_limit.setSingleStep(10)
        
        history_layout.addRow("Message history limit:", self.history_limit)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        scroll.setWidget(general_widget)
        self.tab_widget.addTab(scroll, "General")

    def add_appearance_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        appearance_widget = QWidget()
        layout = QVBoxLayout(appearance_widget)
        
        # Theme Selection
        theme_group = QGroupBox("Theme")
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.currentTextChanged.connect(self.preview_theme)
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Font Settings
        font_group = QGroupBox("Font")
        font_layout = QVBoxLayout()
        
        font_button = QPushButton("Change Font")
        font_button.clicked.connect(self.choose_font)
        self.font_label = QLabel("Current Font: Default")
        
        font_layout.addWidget(self.font_label)
        font_layout.addWidget(font_button)
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # Colors
        colors_group = QGroupBox("Colors")
        colors_layout = QVBoxLayout()
        
        # Text color
        text_color_layout = QHBoxLayout()
        self.text_color_preview = QLabel("   ")
        text_color_button = QPushButton("Text Color")
        text_color_button.clicked.connect(self.choose_text_color)
        text_color_layout.addWidget(QLabel("Text:"))
        text_color_layout.addWidget(self.text_color_preview)
        text_color_layout.addWidget(text_color_button)
        colors_layout.addLayout(text_color_layout)
        
        # Background color
        bg_color_layout = QHBoxLayout()
        self.bg_color_preview = QLabel("   ")
        bg_color_button = QPushButton("Background Color")
        bg_color_button.clicked.connect(self.choose_bg_color)
        bg_color_layout.addWidget(QLabel("Background:"))
        bg_color_layout.addWidget(self.bg_color_preview)
        bg_color_layout.addWidget(bg_color_button)
        colors_layout.addLayout(bg_color_layout)
        
        colors_group.setLayout(colors_layout)
        layout.addWidget(colors_group)
        
        scroll.setWidget(appearance_widget)
        self.tab_widget.addTab(scroll, "Appearance")

    def add_notifications_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        notifications_widget = QWidget()
        layout = QVBoxLayout(notifications_widget)
        
        # Sound Settings
        sound_group = QGroupBox("Sound")
        sound_layout = QVBoxLayout()
        
        self.sound_enabled = QCheckBox("Enable sound effects")
        self.sound_enabled.setChecked(self.parent.sound_enabled)
        
        self.notification_sounds = QCheckBox("Play notification sounds")
        self.message_sounds = QCheckBox("Play message sounds")
        self.startup_sound = QCheckBox("Play startup sound")
        
        sound_layout.addWidget(self.sound_enabled)
        sound_layout.addWidget(self.notification_sounds)
        sound_layout.addWidget(self.message_sounds)
        sound_layout.addWidget(self.startup_sound)
        
        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)
        
        scroll.setWidget(notifications_widget)
        self.tab_widget.addTab(scroll, "Notifications")

    def add_privacy_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        privacy_widget = QWidget()
        layout = QVBoxLayout(privacy_widget)
        
        # Privacy Settings
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QVBoxLayout()
        
        self.show_online = QCheckBox("Show when I'm online")
        self.read_receipts = QCheckBox("Send read receipts")
        self.typing_indicator = QCheckBox("Show typing indicator")
        
        privacy_layout.addWidget(self.show_online)
        privacy_layout.addWidget(self.read_receipts)
        privacy_layout.addWidget(self.typing_indicator)
        
        privacy_group.setLayout(privacy_layout)
        layout.addWidget(privacy_group)
        
        scroll.setWidget(privacy_widget)
        self.tab_widget.addTab(scroll, "Privacy")

    # ... existing settings methods (choose_font, choose_text_color, etc.) ...

    def load_current_settings(self):
        """Load current settings into dialog"""
        settings = self.load_settings_from_file()
        
        # Apply theme
        self.theme_combo.setCurrentText(settings.get('theme', 'Light'))
        
        # Apply appearance settings
        font = QFont(
            settings.get('font_family', 'Arial'),
            int(settings.get('font_size', '10'))
        )
        self.current_font = font
        self.current_text_color = QColor(settings.get('text_color', '#000000'))
        self.current_bg_color = QColor(settings.get('bg_color', '#ffffff'))
        
        # Update previews
        self.update_font_preview()
        self.text_color_preview.setStyleSheet(f"background-color: {self.current_text_color.name()}; border: 1px solid gray")
        self.bg_color_preview.setStyleSheet(f"background-color: {self.current_bg_color.name()}; border: 1px solid gray")
        
        # Load checkboxes
        self.show_timestamps.setChecked(settings.get('show_timestamps', 'true').lower() == 'true')
        self.message_preview.setChecked(settings.get('message_preview', 'true').lower() == 'true')
        self.auto_scroll.setChecked(settings.get('auto_scroll', 'true').lower() == 'true')
        self.history_limit.setValue(int(settings.get('history_limit', '100')))
        self.sound_enabled.setChecked(settings.get('sound_enabled', 'true').lower() == 'true')
        self.notification_sounds.setChecked(settings.get('notification_sounds', 'true').lower() == 'true')
        self.message_sounds.setChecked(settings.get('message_sounds', 'true').lower() == 'true')
        self.startup_sound.setChecked(settings.get('startup_sound', 'true').lower() == 'true')
        self.show_online.setChecked(settings.get('show_online', 'true').lower() == 'true')
        self.read_receipts.setChecked(settings.get('read_receipts', 'true').lower() == 'true')
        self.typing_indicator.setChecked(settings.get('typing_indicator', 'true').lower() == 'true')

    def load_settings_from_file(self):
        """Load settings from file with defaults"""
        settings = DEFAULT_SETTINGS.copy()
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            settings[key] = value
        except Exception as e:
            print(f"Error loading settings: {e}")
        return settings

    def save_settings(self):
        """Save all settings to file"""
        settings = [
            f"theme={self.theme_combo.currentText()}",
            f"font_family={self.current_font.family()}",
            f"font_size={self.current_font.pointSize()}",
            f"text_color={self.current_text_color.name()}",
            f"bg_color={self.current_bg_color.name()}",
            f"sound_enabled={str(self.sound_enabled.isChecked()).lower()}",
            f"show_timestamps={str(self.show_timestamps.isChecked()).lower()}",
            f"message_preview={str(self.message_preview.isChecked()).lower()}",
            f"auto_scroll={str(self.auto_scroll.isChecked()).lower()}",
            f"history_limit={self.history_limit.value()}",
            f"show_online={str(self.show_online.isChecked()).lower()}",
            f"read_receipts={str(self.read_receipts.isChecked()).lower()}",
            f"typing_indicator={str(self.typing_indicator.isChecked()).lower()}",
            f"notification_sounds={str(self.notification_sounds.isChecked()).lower()}",
            f"message_sounds={str(self.message_sounds.isChecked()).lower()}",
            f"startup_sound={str(self.startup_sound.isChecked()).lower()}"
        ]
        
        try:
            with open(SETTINGS_FILE, 'w') as f:
                f.write('\n'.join(settings))
        except Exception as e:
            print(f"Error saving settings: {e}")

    def apply_settings(self):
        # ...existing apply_settings code...
        
        # Save settings to file
        self.save_settings()
        
        self.accept()

    def preview_theme(self, theme_name):
        """Preview the selected theme"""
        if theme_name in THEMES:
            QApplication.instance().setStyleSheet(THEMES[theme_name]["style"])

    def choose_font(self):
        """Choose new font"""
        font, ok = QFontDialog.getFont(self.current_font, self)
        if ok:
            self.current_font = font
            self.update_font_preview()

    def choose_text_color(self):
        """Choose new text color"""
        color = QColorDialog.getColor(self.current_text_color, self)
        if color.isValid():
            self.current_text_color = color
            self.text_color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid gray")

    def choose_bg_color(self):
        """Choose new background color"""
        color = QColorDialog.getColor(self.current_bg_color, self)
        if color.isValid():
            self.current_bg_color = color
            self.bg_color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid gray")

    def update_font_preview(self):
        """Update font preview label"""
        self.font_label.setText(
            f"Current Font: {self.current_font.family()} {self.current_font.pointSize()}pt")

class FriendsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        # Store username reference from parent
        self.username = self.parent.username if self.parent else None
        self.setWindowTitle("Friends List")
        self.resize(300, 400)
        
        layout = QVBoxLayout(self)
        
        # Friends list with status
        self.status_label = QLabel("Loading friends list...", self)
        layout.addWidget(self.status_label)
        
        self.friends_list = QListWidget(self)
        layout.addWidget(self.friends_list)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.message_button = QPushButton("Message", self)
        self.refresh_button = QPushButton("Refresh", self)
        action_layout.addWidget(self.message_button)
        action_layout.addWidget(self.refresh_button)
        layout.addLayout(action_layout)
        
        # Add friend section
        add_layout = QHBoxLayout()
        self.add_input = QLineEdit(self)
        self.add_input.setPlaceholderText("Enter username to add")
        self.add_button = QPushButton("Add Friend", self)
        add_layout.addWidget(self.add_input)
        add_layout.addWidget(self.add_button)
        layout.addLayout(add_layout)
        
        # Connect signals
        self.add_button.clicked.connect(self.send_friend_request)
        self.message_button.clicked.connect(self.message_selected)
        self.refresh_button.clicked.connect(self.refresh_list)
        self.add_input.returnPressed.connect(self.send_friend_request)
        
        # Request friends list in a safe way
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_list)
        self.refresh_timer.setInterval(5000)  # Refresh every 5 seconds
        
        # Initial request after dialog shown
        QTimer.singleShot(100, self.refresh_list)

    def showEvent(self, event):
        """Called when dialog is shown"""
        super().showEvent(event)
        self.refresh_timer.start()

    def hideEvent(self, event):
        """Called when dialog is hidden"""
        super().hideEvent(event)
        self.refresh_timer.stop()
        
    def refresh_list(self):
        """Request fresh friends list"""
        try:
            if not client:
                self.status_label.setText("Not connected to server")
                return
                
            self.status_label.setText("Refreshing friends list...")
            client.send('GET_FRIENDS\n'.encode())
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")

    def update_friends_list(self, friends_data):
        """Update friends list display"""
        try:
            self.friends_list.clear()
            if friends_data:
                for friend_info in friends_data.split(';'):
                    if ':' in friend_info:
                        friend, status = friend_info.split(':')
                        item = QListWidgetItem(f"{friend} ({status})")
                        self.friends_list.addItem(item)
            
            current_time = datetime.now().strftime('%H:%M:%S')
            self.status_label.setText(f"Last updated: {current_time}")
            self.friends_list.show()
        except Exception as e:
            self.status_label.setText(f"Error updating list: {str(e)}")

    def send_friend_request(self):
        """Send friend request"""
        friend = self.add_input.text().strip()
        if friend:
            if friend == self.username:  # Use instance variable
                QMessageBox.warning(self, "Error", "You cannot add yourself as a friend")
                return
                
            try:
                client.send(f"FRIEND_REQUEST:{friend}\n".encode())
                self.add_input.clear()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to send friend request: {str(e)}")

    def message_selected(self):
        """Message selected friend"""
        current = self.friends_list.currentItem()
        if current:
            # Extract username from "username (status)" format
            friend = current.text().split(' (')[0]
            if friend in private_chats:
                private_chats[friend].show()
                private_chats[friend].raise_()
            else:
                chat_window = PrivateChatWindow(friend, self.parent)  # Changed from self.parent() to self.parent
                private_chats[friend] = chat_window
                chat_window.show()
            self.hide()

def main():
    app = QApplication(sys.argv)
    
    # Apply initial theme (Light theme by default)
    app.setStyle("Fusion")
    app.setStyleSheet(THEMES["Light"]["style"])
    
    # Check for updates before showing any windows
    check_for_updates()
    
    # First show connection dialog
    conn_dialog = ConnectionDialog()
    if conn_dialog.exec() == QDialog.DialogCode.Accepted:
        # Show login dialog
        login = LoginDialog()
        if login.exec() == QDialog.DialogCode.Accepted:
            try:
                # Create main window with user data
                window = ChatMainWindow(login.encryption_instance)
                if not user_data.get('username'):
                    raise ValueError("No username set")
                window.username = user_data['username']
                window.show()
                return app.exec()
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to start chat: {str(e)}")
    
    return 1

if __name__ == '__main__':
    sys.exit(main())