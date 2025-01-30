import socket
import threading
import os
import sqlite3
import tkinter as tk
from tkinter import scrolledtext, messagebox
import select
from datetime import datetime
import time
import base64
from PIL import Image
import io
import hashlib
import requests
import webbrowser
import sys
import subprocess
from encryption import E2EEncryption

# Version control constants
CURRENT_VERSION = "V0.2.3"
GITHUB_REPO = "swyftl/swiftChat"  # Replace with your actual GitHub repo

def is_running_as_exe():
    """Check if we're running as a bundled exe"""
    return getattr(sys, 'frozen', False)

def check_for_updates():
    try:
        print("Checking for server updates...")
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release["tag_name"].strip("v")
            
            print(f"Current version: {CURRENT_VERSION}")
            print(f"Latest version: {latest_version}")
            
            if latest_version > CURRENT_VERSION:
                if messagebox.askyesno(
                    "Server Update Available",
                    f"A new server version ({latest_version}) is available!\n"
                    f"You are currently running version {CURRENT_VERSION}\n\n"
                    "Would you like to download and install the update?"
                ):
                    for asset in latest_release['assets']:
                        if asset['name'].lower() == 'swiftchatserver.exe':
                            try:
                                current_exe = sys.executable if is_running_as_exe() else "SwiftChatServer.exe"
                                temp_exe = "SwiftChatServer_update.exe"
                                update_script = "server_update_helper.bat"
                                
                                # Download update
                                response = requests.get(asset['browser_download_url'], stream=True)
                                if response.status_code == 200:
                                    with open(temp_exe, 'wb') as f:
                                        for chunk in response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    
                                    # Create update helper script
                                    with open(update_script, 'w') as f:
                                        f.write('@echo off\n')
                                        f.write('echo Updating SwiftChat Server...\n')
                                        f.write('timeout /t 1 /nobreak >nul\n')
                                        f.write(f'move /Y "{temp_exe}" "{current_exe}"\n')
                                        f.write(f'start "" "{current_exe}"\n')
                                        f.write('del "%~f0"\n')

                                    # Start update script and exit
                                    messagebox.showinfo(
                                        "Update Ready",
                                        "Update downloaded successfully!\n"
                                        "The server will now restart to complete the update."
                                    )
                                    subprocess.Popen([update_script], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                                    os._exit(0)
                            except Exception as e:
                                print(f"Error during update: {e}")
                                messagebox.showerror(
                                    "Update Error",
                                    f"Failed to download update: {str(e)}"
                                )
                            break
                    else:
                        print("No SwiftChatServer.exe found in release assets")
                        webbrowser.open(latest_release['html_url'])
                        
    except Exception as e:
        print(f"Update check failed: {e}")

def load_config():
    default_config = {
        'CHATAPP_HOST': '127.0.0.1',
        'CHATAPP_PORT': '8080',
        'MESSAGE_HISTORY_LIMIT': '50',
        'PM_HISTORY_LIMIT': '30',
        'MAX_IMAGE_SIZE': '262144',  # 256KB in bytes
        'PING_INTERVAL': '30',  # seconds
        'MAX_USERNAME_LENGTH': '20',
        'MAX_MESSAGE_LENGTH': '2000',
        'AUTO_BACKUP_INTERVAL': '3600',  # 1 hour in seconds
        'LOG_LEVEL': 'INFO',
        'DATABASE_PATH': 'users.db',
        'IMAGES_PATH': 'images',
        'LOGS_PATH': 'logs',
        'ENABLE_USER_AVATARS': 'false',
        'MAX_USERS': '100',
        'INACTIVITY_TIMEOUT': '300'  # 5 minutes in seconds
    }
    
    config = default_config.copy()
    try:
        if os.path.exists('conf.env'):
            with open('conf.env', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=')
                        config[key] = value
        else:
            # Create config file with defaults if it doesn't exist
            with open('conf.env', 'w') as f:
                for key, value in default_config.items():
                    f.write(f"{key}={value}\n")
            print("Created default configuration file conf.env")
    except Exception as e:
        print(f"Error loading configuration: {e}")
    
    return config

class ServerGUI:
    def __init__(self):
        # Check for updates before starting
        check_for_updates()
        
        # Create directories if they don't exist
        for dir in ['logs', 'images']:
            if not os.path.exists(dir):
                os.makedirs(dir)
        
        self.log_contents = []  # Store log messages
        self.root = tk.Tk()
        self.root.title("ChatApp Server")
        self.root.geometry("800x600")
        
        # Load configuration
        self.config = load_config()
        
        # Convert config values to appropriate types
        self.message_history_limit = int(self.config['MESSAGE_HISTORY_LIMIT'])
        self.pm_history_limit = int(self.config['PM_HISTORY_LIMIT'])
        self.max_image_size = int(self.config['MAX_IMAGE_SIZE'])
        self.ping_interval = int(self.config['PING_INTERVAL'])
        self.max_username_length = int(self.config['MAX_USERNAME_LENGTH'])
        self.max_message_length = int(self.config['MAX_MESSAGE_LENGTH'])
        self.auto_backup_interval = int(self.config['AUTO_BACKUP_INTERVAL'])
        self.log_level = self.config['LOG_LEVEL']
        self.max_users = int(self.config['MAX_USERS'])
        self.inactivity_timeout = int(self.config['INACTIVITY_TIMEOUT'])
        
        # Update paths from config
        self.database_path = self.config['DATABASE_PATH']
        self.images_path = self.config['IMAGES_PATH']
        self.logs_path = self.config['LOGS_PATH']
        
        # Create directories from config
        for dir_path in [self.logs_path, self.images_path]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

        # Start auto-backup timer if enabled
        if self.auto_backup_interval > 0:
            self.backup_timer = threading.Timer(self.auto_backup_interval, self.backup_database)
            self.backup_timer.daemon = True
            self.backup_timer.start()
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(self.root, state=tk.DISABLED)
        self.log_display.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Server status
        self.status_label = tk.Label(self.root, text="Server Status: Starting...", fg="orange")
        self.status_label.pack(pady=5)
        
        # Add command frame
        command_frame = tk.Frame(self.root)
        command_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Command entry
        self.command_entry = tk.Entry(command_frame)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.command_entry.bind('<Return>', self.process_command)
        
        # Execute button
        execute_button = tk.Button(command_frame, text="Execute", command=self.process_command)
        execute_button.pack(side=tk.RIGHT, padx=5)
        
        # Command help button
        help_button = tk.Button(command_frame, text="Help", command=self.show_command_help)
        help_button.pack(side=tk.RIGHT, padx=5)
        
        # Start server in separate thread
        threading.Thread(target=self.run_server, daemon=True).start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Store in memory
        self.log_contents.append(log_entry)
        
        # Display in GUI
        self.log_display.config(state=tk.NORMAL)
        self.log_display.insert(tk.END, log_entry + "\n")
        self.log_display.yview(tk.END)
        self.log_display.config(state=tk.DISABLED)
    
    def save_log(self):
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        filename = f"logs/server_{timestamp}.log"
        
        try:
            with open(filename, 'w') as f:
                f.write("\n".join(self.log_contents))
            self.log(f"Log saved to {filename}")
        except Exception as e:
            self.log(f"Error saving log: {str(e)}")
    
    def on_closing(self):
        self.log("Shutting down server...")
        self.save_log()
        try:
            self.server.close()
        except:
            pass
        self.root.destroy()
        os._exit(0)
    
    def backup_database(self):
        """Backup the database periodically"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.database_path}.{timestamp}.backup"
            with open(self.database_path, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
            self.log(f"Database backed up to {backup_path}")
            
            # Schedule next backup
            self.backup_timer = threading.Timer(self.auto_backup_interval, self.backup_database)
            self.backup_timer.daemon = True
            self.backup_timer.start()
        except Exception as e:
            self.log(f"Database backup failed: {e}")

    def run_server(self):
        # Check if conf.env exists
        if not os.path.exists('conf.env'):
            self.log("First run detected. Creating configuration file...")
            with open('conf.env', 'w') as f:
                f.write("CHATAPP_HOST=127.0.0.1\nCHATAPP_PORT=8080")
            self.log("Created conf.env with default settings.")
            self.log("Please review the configuration file and restart the server.")
            self.status_label.config(text="Server Status: Configuration Created", fg="orange")
            return

        # Database setup
        self.log("Setting up database...")
        conn = sqlite3.connect('users.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT NOT NULL)''')
        
        # Add messages table
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT NOT NULL,
                        recipient TEXT,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_private BOOLEAN DEFAULT 0,
                        is_image BOOLEAN DEFAULT 0,
                        FOREIGN KEY (sender) REFERENCES users(username))''')
        conn.commit()

        cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
                      ('test', 'test123'))
        conn.commit()
        self.log("Database setup completed")

        # Add friends table
        cursor.execute('''CREATE TABLE IF NOT EXISTS friends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user1 TEXT NOT NULL,
                        user2 TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user1) REFERENCES users(username),
                        FOREIGN KEY (user2) REFERENCES users(username),
                        UNIQUE(user1, user2))''')
        conn.commit()

        # Server setup
        HOST = self.config.get('CHATAPP_HOST', '127.0.0.1')
        PORT = int(self.config.get('CHATAPP_PORT', '8080'))
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, PORT))
        self.server.listen()
        
        self.status_label.config(text=f"Server Status: Running on {HOST}:{PORT}", fg="green")
        self.log(f"Server is listening on {HOST}:{PORT}")

        self.clients = []
        self.nicknames = []
        self.user_keys = {}  # Store public keys for each user

        def broadcast(message):
            for client in self.clients:
                client.send(message)

        def send_private_message(sender_client, sender_name, recipient, message):
            try:
                if recipient in self.nicknames:
                    recipient_index = self.nicknames.index(recipient)
                    recipient_client = self.clients[recipient_index]
                    
                    # Send to recipient
                    private_msg = f"[Private] {sender_name}: {message}"
                    recipient_client.send(private_msg.encode('utf-8'))
                    
                    # Send confirmation to sender
                    sender_client.send(f"[Private to {recipient}]: {message}".encode('utf-8'))
                else:
                    sender_client.send(f"Error: User {recipient} is not online.".encode('utf-8'))
            except Exception as e:
                self.log(f"Private message error: {str(e)}")
                sender_client.send("Error sending private message.".encode('utf-8'))

        def save_message(sender, message, recipient=None, is_private=False):
            try:
                cursor.execute("""
                    INSERT INTO messages (sender, recipient, message, is_private)
                    VALUES (?, ?, ?, ?)
                """, (sender, recipient, message, is_private))
                conn.commit()
            except Exception as e:
                self.log(f"Error saving message to database: {str(e)}")

        def save_image(image_data, sender):
            try:
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
                
                # Generate unique filename using hash
                filename = f"{hashlib.md5(image_bytes).hexdigest()}.png"
                filepath = os.path.join('images', filename)
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                # Save image reference in database
                cursor.execute("""
                    INSERT INTO messages (sender, message, is_image)
                    VALUES (?, ?, ?)
                """, (sender, filename, True))
                conn.commit()
                
                return filename
            except Exception as e:
                self.log(f"Error saving image: {e}")
                return None

        def handle_friend_request(sender, recipient):
            """Handle friend request between users"""
            try:
                # Check if request already exists
                cursor.execute("""
                    SELECT status FROM friends 
                    WHERE (user1=? AND user2=?) OR (user1=? AND user2=?)
                """, (sender, recipient, recipient, sender))
                result = cursor.fetchone()
                
                if result:
                    return "REQUEST_EXISTS"
                    
                # Add friend request
                cursor.execute("""
                    INSERT INTO friends (user1, user2, status)
                    VALUES (?, ?, 'pending')
                """, (sender, recipient))
                conn.commit()
                return "REQUEST_SENT"
            except Exception as e:
                self.log(f"Friend request error: {e}")
                return "REQUEST_FAILED"

        def handle_friend_response(user1, user2, accept):
            """Handle friend request response"""
            try:
                status = 'accepted' if accept else 'rejected'
                cursor.execute("""
                    UPDATE friends 
                    SET status = ? 
                    WHERE (user1=? AND user2=?) OR (user1=? AND user2=?)
                """, (status, user1, user2, user2, user1))
                conn.commit()
                return "RESPONSE_SENT"
            except Exception as e:
                self.log(f"Friend response error: {e}")
                return "RESPONSE_FAILED"

        def get_friends_list(username):
            """Get user's friends list"""
            try:
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN user1=? THEN user2 
                            ELSE user1 
                        END as friend,
                        status
                    FROM friends 
                    WHERE (user1=? OR user2=?)
                """, (username, username, username))
                results = cursor.fetchall()
                if not results:
                    return ""
                return ";".join([f"{friend}:{status}" for friend, status in results])
            except Exception as e:
                self.log(f"Error getting friends list: {e}")
                return ""

        def handle_client(client):
            # Configure socket
            client.settimeout(self.inactivity_timeout)
            message_buffer = ""
            sender_name = None  # Initialize sender_name to None
            
            try:
                # Configure TCP settings
                client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                
                if hasattr(socket, "TCP_KEEPIDLE"):  # Linux
                    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
                elif hasattr(socket, "TCP_KEEPALIVE"):  # macOS
                    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, 30)
                if hasattr(socket, "TCP_KEEPINTVL"):
                    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 5)
                if hasattr(socket, "TCP_KEEPCNT"):
                    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
                
                # Get the sender name safely
                try:
                    sender_name = self.nicknames[self.clients.index(client)]
                except ValueError:
                    self.log("Client not found in nicknames list")
                    return
                except Exception as e:
                    self.log(f"Error getting sender name: {e}")
                    return
                
                last_activity = time.time()
                
                while True:
                    try:
                        # Use select for non-blocking receive
                        ready = select.select([client], [], [], 0.1)  # 100ms timeout
                        if ready[0]:
                            try:
                                data = client.recv(4096)
                                if not data:
                                    break
                                    
                                # Update last activity time
                                last_activity = time.time()
                                message_buffer += data.decode('utf-8')
                                
                                # Process complete messages (split by newlines)
                                while '\n' in message_buffer:
                                    # Split on first newline
                                    message, message_buffer = message_buffer.split('\n', 1)
                                    message = message.strip()
                                    
                                    if not message:
                                        continue
                                    
                                    self.log(f"Received from {sender_name}: {message}")
                                    
                                    # Handle different message types
                                    if message == '/online':
                                        online_users = ', '.join(self.nicknames)
                                        client.send(f'ONLINE_USERS:{online_users}\n'.encode('utf-8'))
                                    elif message.startswith('/pm:'):
                                        try:
                                            _, recipient, content = message.split(':', 2)
                                            send_private_message(client, sender_name, recipient, content)
                                        except Exception as e:
                                            self.log(f"PM error: {e}")
                                    elif message == 'GET_FRIENDS':
                                        friends_data = get_friends_list(sender_name)
                                        client.send(f'FRIENDS_LIST:{friends_data}\n'.encode('utf-8'))
                                    elif message.startswith('FRIEND_REQUEST:'):
                                        _, recipient = message.split(':', 1)
                                        result = handle_friend_request(sender_name, recipient)
                                        client.send(f'FRIEND_STATUS:{result}\n'.encode('utf-8'))
                                    elif message.startswith('FRIEND_RESPONSE:'):
                                        _, sender, response = message.split(':', 2)
                                        result = handle_friend_response(sender_name, sender, response == 'accept')
                                        client.send(f'FRIEND_STATUS:{result}\n'.encode('utf-8'))
                                    else:
                                        # Regular chat message
                                        broadcast(f"{message}\n".encode('utf-8'))
                                        save_message(sender_name, message)
                            except UnicodeDecodeError:
                                self.log(f"Unicode decode error from {sender_name}")
                                continue
                                
                        # Check for inactivity
                        if time.time() - last_activity > self.inactivity_timeout:
                            self.log(f"Client {sender_name} timed out")
                            break
                            
                    except socket.timeout:
                        # Send keepalive ping
                        try:
                            client.send('PING\n'.encode('utf-8'))
                            last_activity = time.time()
                        except:
                            break
                        continue
                    except Exception as e:
                        self.log(f"Error handling client {sender_name}: {e}")
                        break
                        
            except Exception as e:
                error_user = sender_name if sender_name else "unknown"
                self.log(f"Client error ({error_user}): {e}")
            finally:
                # Handle disconnection
                try:
                    if sender_name and sender_name in self.nicknames:
                        idx = self.nicknames.index(sender_name)
                        self.clients.pop(idx)
                        self.nicknames.remove(sender_name)
                        broadcast(f"{sender_name} left the chat!\n".encode('utf-8'))
                        self.log(f"Client disconnected: {sender_name}")
                    client.close()
                except Exception as e:
                    self.log(f"Error during client cleanup: {e}")

        def authenticate(client):
            try:
                self.log("Starting authentication process...")
                
                # Send USER prompt and wait for response
                client.send('USER\n'.encode('utf-8'))
                try:
                    username_data = client.recv(1024)
                    if not username_data:
                        self.log("Error: No username data received")
                        client.send('AUTH_FAIL\n'.encode('utf-8'))
                        return None
                    username = username_data.decode('utf-8').strip()
                    self.log(f"Received username data: '{username}'")
                    
                    if not username:
                        self.log("Error: Empty username received")
                        client.send('AUTH_FAIL\n'.encode('utf-8'))
                        return None
                        
                    # Request password
                    client.send('PASS\n'.encode('utf-8'))
                    password_data = client.recv(1024)
                    if not password_data:
                        self.log("Error: No password data received")
                        client.send('AUTH_FAIL\n'.encode('utf-8'))
                        return None
                    password = password_data.decode('utf-8').strip()
                except Exception as e:
                    self.log(f"Error receiving credentials: {e}")
                    client.send('AUTH_FAIL\n'.encode('utf-8'))
                    return None

                # Verify credentials
                try:
                    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", 
                                  (username, password))
                    result = cursor.fetchone()
                    
                    if result:
                        # Request public key
                        client.send('SEND_KEY\n'.encode('utf-8'))
                        try:
                            # Wait for public key with timeout
                            public_key = client.recv(4096)
                            if public_key:
                                self.user_keys[username] = public_key
                                # Send success with newline and flush
                                client.send('AUTH_SUCCESS\n'.encode('utf-8'))
                                self.log(f"User {username} authenticated successfully")
                                # Add a small delay to ensure message order
                                time.sleep(0.1)
                                return username
                            else:
                                self.log("No public key received")
                                client.send('AUTH_FAIL\n'.encode('utf-8'))
                                return None
                        except Exception as e:
                            self.log(f"Error during key exchange: {e}")
                            client.send('AUTH_FAIL\n'.encode('utf-8'))
                            return None
                    else:
                        self.log(f"Invalid credentials for user: {username}")
                        client.send('AUTH_FAIL\n'.encode('utf-8'))
                        return None
                except Exception as e:
                    self.log(f"Database error during authentication: {e}")
                    client.send('AUTH_FAIL\n'.encode('utf-8'))
                    return None
                    
            except Exception as e:
                self.log(f"Authentication error: {str(e)}")
                try:
                    client.send('AUTH_FAIL\n'.encode('utf-8'))
                except:
                    pass
                return None

        def register_user(client):
            try:
                self.log("Starting registration process...")
                
                # Ask for new username
                client.send('NEW_USER'.encode('utf-8'))
                username = client.recv(1024).decode('utf-8')
                self.log(f"Got new username: {username}")
                
                # Check if username exists
                cursor.execute("SELECT * FROM users WHERE username=?", (username,))
                if cursor.fetchone():
                    self.log(f"Username {username} already exists")
                    client.send('USER_EXISTS'.encode('utf-8'))
                    return None
                    
                # Ask for password
                client.send('NEW_PASS'.encode('utf-8'))
                password = client.recv(1024).decode('utf-8')
                
                # Add new user
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                self.log(f"New user {username} registered successfully")
                client.send('REG_SUCCESS'.encode('utf-8'))
                return username
                    
            except Exception as e:
                self.log(f"Registration error: {str(e)}")
                client.send('REG_FAIL'.encode('utf-8'))
                return None

        def send_message_history(client):
            try:
                cursor.execute(f"""
                    SELECT sender, message, timestamp 
                    FROM messages 
                    WHERE recipient IS NULL
                    ORDER BY timestamp DESC 
                    LIMIT {self.message_history_limit}
                """)
                messages = cursor.fetchall()
                
                if messages:
                    client.send('MESSAGE_HISTORY_START'.encode('utf-8'))
                    
                    # Send all messages with newlines between them
                    history_messages = []
                    for sender, message, timestamp in reversed(messages):
                        history_msg = f"[{timestamp}] {sender}: {message}"
                        history_messages.append(history_msg)
                    
                    # Join messages with newlines and send
                    combined_messages = "\n".join(history_messages)
                    client.send(combined_messages.encode('utf-8'))
                    client.send('MESSAGE_HISTORY_END'.encode('utf-8'))
            except Exception as e:
                self.log(f"Error sending message history: {str(e)}")

        def send_pm_history(client, user1, user2):
            try:
                cursor.execute(f"""
                    SELECT sender, recipient, message, timestamp 
                    FROM messages 
                    WHERE ((sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?))
                    ORDER BY timestamp DESC 
                    LIMIT {self.pm_history_limit}
                """, (user1, user2, user2, user1))
                messages = cursor.fetchall()
                
                if messages:
                    client.send('PM_HISTORY_START'.encode('utf-8'))
                    
                    # Send all messages with newlines between them
                    history_messages = []
                    for sender, recipient, message, timestamp in reversed(messages):
                        if sender == user1:
                            history_msg = f"[Private to {recipient}]: {message}"
                        else:
                            history_msg = f"[Private] {sender}: {message}"
                        history_messages.append(history_msg)
                    
                    # Join messages with newlines and send
                    combined_messages = "\n".join(history_messages)
                    client.send(f"PM_HISTORY:{user2}:{combined_messages}".encode('utf-8'))
                    client.send('PM_HISTORY_END'.encode('utf-8'))
            except Exception as e:
                self.log(f"Error sending PM history: {str(e)}")

        while True:
            try:
                client, address = self.server.accept()
                self.log(f"New connection from {address}")

                try:
                    auth_type = client.recv(1024).decode('utf-8').strip()
                    self.log(f"Received auth type: {auth_type}")
                    
                    # Initialize username as None
                    username = None
                    
                    # Handle authentication based on type
                    if auth_type == 'LOGIN':
                        self.log(f"Login attempt from {address}")
                        username = authenticate(client)
                        # Debug log
                        self.log(f"Authentication result for {address}: username={username}")
                        
                        if username:
                            # Add user to active lists before starting client thread
                            self.log(f"Adding {username} to active users")
                            if username not in self.nicknames:  # Prevent duplicates
                                self.nicknames.append(username)
                                self.clients.append(client)
                                
                                # Send message history
                                send_message_history(client)
                                
                                # Announce new user
                                broadcast(f"{username} joined the chat!\n".encode('utf-8'))
                                client.send('Connected to the server!\n'.encode('utf-8'))
                                
                                # Start client handler thread
                                thread = threading.Thread(target=handle_client, args=(client,))
                                thread.start()
                                
                                self.log(f"User {username} fully connected and handler started")
                            else:
                                self.log(f"Username {username} already in use")
                                client.send('ALREADY_LOGGED_IN\n'.encode('utf-8'))
                                client.close()
                                
                    elif auth_type == 'REGISTER':
                        username = register_user(client)
                        if username:
                            self.log(f"Registration successful for {username}")
                            client.close()  # Close connection after registration
                        else:
                            self.log("Registration failed")
                            client.close()
                    else:
                        self.log(f"Invalid auth type received: {auth_type}")
                        client.close()
                        continue

                    if not username:
                        self.log(f"Authentication failed from {address}")
                        try:
                            client.send('AUTH_FAIL\n'.encode('utf-8'))
                            client.close()
                        except:
                            pass
                            
                except Exception as e:
                    self.log(f"Error during authentication process: {e}")
                    try:
                        client.close()
                    except:
                        pass
                    
            except Exception as e:
                self.log(f"Error accepting connection: {str(e)}")

    def process_command(self, event=None):
        """Process server commands"""
        command = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)
        
        if not command:
            return
            
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        try:
            if cmd == "broadcast" or cmd == "bc":
                if not args:
                    self.log("Usage: broadcast <message>")
                    return
                message = f"[SERVER] {' '.join(args)}"
                self.broadcast(message.encode('utf-8'))
                self.log(f"Broadcast: {message}")
                
            elif cmd == "kick":
                if not args:
                    self.log("Usage: kick <username>")
                    return
                self.kick_user(args[0])
                
            elif cmd == "pm":
                if len(args) < 2:
                    self.log("Usage: pm <username> <message>")
                    return
                username = args[0]
                message = ' '.join(args[1:])
                self.send_private_message(username, f"[SERVER] {message}")
                
            elif cmd == "list":
                online = ', '.join(self.nicknames) if self.nicknames else "No users online"
                self.log(f"Online users: {online}")
                
            elif cmd == "shutdown":
                self.log("Shutting down server...")
                self.on_closing()
                
            elif cmd == "help":
                self.show_command_help()
                
            else:
                self.log(f"Unknown command: {cmd}")
        except Exception as e:
            self.log(f"Error executing command: {str(e)}")

    def show_command_help(self):
        """Show available commands"""
        help_text = """
Available Commands:
------------------
broadcast (bc) <message> - Send message to all users
pm <username> <message>  - Send private message to user
kick <username>         - Kick user from server
list                    - Show online users
shutdown               - Shutdown the server
help                   - Show this help message
"""
        self.log(help_text)

    def broadcast(self, message):
        """Broadcast message to all clients"""
        for client in self.clients:
            try:
                client.send(message)
            except:
                pass

    def kick_user(self, username):
        """Kick user from server"""
        if username in self.nicknames:
            idx = self.nicknames.index(username)
            client = self.clients[idx]
            
            # Send kick message to user
            try:
                client.send("[SERVER] You have been kicked from the server.".encode('utf-8'))
                client.close()
            except:
                pass
            
            # Remove from lists
            self.clients.remove(client)
            self.nicknames.remove(username)
            
            # Broadcast kick message
            self.broadcast(f"[SERVER] {username} has been kicked from the server.".encode('utf-8'))
            self.log(f"Kicked user: {username}")
        else:
            self.log(f"User not found: {username}")

    def send_private_message(self, username, message):
        """Send private message to specific user"""
        if username in self.nicknames:
            idx = self.nicknames.index(username)
            client = self.clients[idx]
            try:
                client.send(message.encode('utf-8'))
                self.log(f"PM to {username}: {message}")
            except:
                self.log(f"Error sending PM to {username}")
        else:
            self.log(f"User not found: {username}")

if __name__ == "__main__":
    ServerGUI()
