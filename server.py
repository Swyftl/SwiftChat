import socket
import threading
import os
import sqlite3
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

def load_config():
    config = {}
    try:
        with open('conf.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=')
                    config[key] = value
    except:
        config['CHATAPP_HOST'] = '127.0.0.1'
        config['CHATAPP_PORT'] = '8080'
    return config

class ServerGUI:
    def __init__(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        self.log_contents = []  # Store log messages
        self.root = tk.Tk()
        self.root.title("ChatApp Server")
        self.root.geometry("800x600")
        
        # Load configuration
        self.config = load_config()
        
        # Log display
        self.log_display = scrolledtext.ScrolledText(self.root, state=tk.DISABLED)
        self.log_display.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Server status
        self.status_label = tk.Label(self.root, text="Server Status: Starting...", fg="orange")
        self.status_label.pack(pady=5)
        
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
                        FOREIGN KEY (sender) REFERENCES users(username))''')
        conn.commit()

        cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
                      ('test', 'test123'))
        conn.commit()
        self.log("Database setup completed")

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

        def handle_client(client):
            while True:
                try:
                    message = client.recv(1024).decode('utf-8')
                    sender_name = self.nicknames[self.clients.index(client)]  # Get authenticated username
                    
                    if message == '/online':
                        online_users = ', '.join(self.nicknames)
                        client.send(f'ONLINE_USERS:{online_users}'.encode('utf-8'))
                    elif message.startswith('/pm:'):
                        _, recipient, content = message.split(':', 2)
                        self.log(f"PM from {sender_name} to {recipient}: {content}")
                        send_private_message(client, sender_name, recipient, content)
                        # Save private message
                        save_message(sender_name, content, recipient, True)
                    else:
                        # Handle regular message
                        content = message.split(':', 1)[1].strip()  # Remove username from message content
                        broadcast(f"{sender_name}: {content}".encode('utf-8'))
                        # Save public message with authenticated sender
                        save_message(sender_name, content)
                        self.log(f"Message from {sender_name}: {content}")
                except:
                    index = self.clients.index(client)
                    self.clients.remove(client)
                    client.close()
                    nickname = self.nicknames[index]
                    self.log(f"User disconnected: {nickname}")
                    broadcast(f'{nickname} left the chat!'.encode('utf-8'))
                    self.nicknames.remove(nickname)
                    break

        def authenticate(client):
            try:
                self.log("Starting authentication process...")
                
                # Ask for username
                client.send('USER'.encode('utf-8'))
                username = client.recv(1024).decode('utf-8')
                self.log(f"Got username: {username}")
                
                # Ask for password
                client.send('PASS'.encode('utf-8'))
                password = client.recv(1024).decode('utf-8')
                self.log(f"Got password for user: {username}")
                
                # Check credentials
                cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
                result = cursor.fetchone()
                self.log(f"Database query result: {result}")
                
                if result:
                    self.log(f"User {username} authenticated successfully")
                    client.send('AUTH_SUCCESS'.encode('utf-8'))
                    return username
                else:
                    self.log(f"Authentication failed for user {username}")
                    client.send('AUTH_FAIL'.encode('utf-8'))
                    return None
                    
            except Exception as e:
                self.log(f"Authentication error: {str(e)}")
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
                # Get last 50 public messages
                cursor.execute("""
                    SELECT sender, message, timestamp 
                    FROM messages 
                    WHERE is_private = 0 
                    ORDER BY timestamp DESC 
                    LIMIT 50
                """)
                messages = cursor.fetchall()
                
                if messages:
                    client.send('MESSAGE_HISTORY_START'.encode('utf-8'))
                    # Send messages in chronological order (oldest first)
                    for sender, message, timestamp in reversed(messages):
                        history_msg = f"[{timestamp}] {sender}: {message}"
                        client.send(history_msg.encode('utf-8'))
                    client.send('MESSAGE_HISTORY_END'.encode('utf-8'))
            except Exception as e:
                self.log(f"Error sending message history: {str(e)}")

        while True:
            try:
                client, address = self.server.accept()
                self.log(f"New connection from {address}")

                auth_type = client.recv(1024).decode('utf-8')
                if auth_type == 'LOGIN':
                    self.log(f"Login attempt from {address}")
                    username = authenticate(client)
                elif auth_type == 'REGISTER':
                    self.log(f"Registration attempt from {address}")
                    username = register_user(client)

                if username:
                    self.nicknames.append(username)
                    self.clients.append(client)
                    self.log(f"User authenticated: {username}")
                    
                    # Send message history before announcing new user
                    send_message_history(client)
                    
                    broadcast(f"{username} joined the chat!".encode('utf-8'))
                    client.send('Connected to the server!'.encode('utf-8'))
                    
                    thread = threading.Thread(target=handle_client, args=(client,))
                    thread.start()
                else:
                    self.log(f"Authentication failed from {address}")
                    client.close()
            except Exception as e:
                self.log(f"Error: {str(e)}")

if __name__ == "__main__":
    ServerGUI()
