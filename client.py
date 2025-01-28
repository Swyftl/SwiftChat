import socket
import threading
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
import webbrowser
import requests
from pygame import mixer
import sys

# Version control
CURRENT_VERSION = "V0.1.4"
GITHUB_REPO = "swyftl/swiftChat"  # Replace with your actual GitHub repo

def check_for_updates():
    try:
        # Get latest release from GitHub
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        if response.status_code == 200:
            latest_version = response.json()["tag_name"].strip("v")
            if latest_version > CURRENT_VERSION:
                if messagebox.askyesno(
                    "Update Available",
                    f"A new version ({latest_version}) is available!\n"
                    f"You are currently running version {CURRENT_VERSION}\n\n"
                    "Would you like to download the update?"
                ):
                    webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases/latest")
                    os._exit(0)
    except Exception as e:
        print(f"Failed to check for updates: {e}")

# Add update check before starting
if __name__ == "__main__":
    check_for_updates()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Initialize pygame mixer
mixer.init()
try:
    received_sound_path = resource_path('resources/sounds/message_received.mp3')
    sent_sound_path = resource_path('resources/sounds/message_sent.mp3')
    mixer.music.load(received_sound_path)  # Load received sound by default
    sound_enabled = True
except Exception as e:
    print(f"Could not load notification sounds: {e}")
    sound_enabled = False

def play_sound(sound_type='received'):
    if sound_enabled:
        try:
            if sound_type == 'sent':
                mixer.music.load(sent_sound_path)
            else:
                mixer.music.load(received_sound_path)
            mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")

# Global variables
HOST = '127.0.0.1'  # Default host
PORT = 8080         # Update default port to match server
client = None
username = None     # Add global username
password = None     # Add global password
private_chats = {}  # Store private chat windows
CREDENTIALS_FILE = 'credentials.txt'

def save_credentials(username, password, host=None, port=None):
    try:
        with open(CREDENTIALS_FILE, 'w') as f:
            f.write(f"{username}\n{password}\n{host or HOST}\n{port or PORT}")
    except Exception as e:
        print(f"Error saving credentials: {e}")

def load_credentials():
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 4:  # Need 4 lines now: username, password, host, port
                    return {
                        'username': lines[0].strip(),
                        'password': lines[1].strip(),
                        'host': lines[2].strip(),
                        'port': lines[3].strip()
                    }
    except Exception as e:
        print(f"Error loading credentials: {e}")
    return None

def init_connection(event=None):  # Add event parameter
    global client, HOST, PORT
    HOST = host_entry.get()
    PORT = int(port_entry.get())
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        connection_screen.destroy()
        show_login_screen()
    except Exception as e:
        print(f"Connection error: {str(e)}")
        connection_error_label.config(text="Failed to connect to server")

def register(event=None):  # Add event parameter
    global username, password
    username = reg_username_entry.get()
    password = reg_password_entry.get()
    
    try:
        print(f"Attempting to register as {username}")
        client.send('REGISTER'.encode('utf-8'))
        
        msg = client.recv(1024).decode('utf-8')
        if msg == 'NEW_USER':
            client.send(username.encode('utf-8'))
            
            msg = client.recv(1024).decode('utf-8')
            if msg == 'USER_EXISTS':
                reg_error_label.config(text="Username already exists")
                return
            elif msg == 'NEW_PASS':
                client.send(password.encode('utf-8'))
                
                response = client.recv(1024).decode('utf-8')
                if response == 'REG_SUCCESS':
                    register_screen.destroy()
                    start_chat()
                    return
        
        reg_error_label.config(text="Registration Failed. Try again.")
    except Exception as e:
        print(f"Registration error: {str(e)}")
        reg_error_label.config(text=f"Connection error: {str(e)}")

def show_register_screen():
    global register_screen, reg_username_entry, reg_password_entry, reg_error_label
    register_screen = tk.Toplevel(login_screen)
    register_screen.title("ChatApp - Register")

    tk.Label(register_screen, text="Username:").pack(padx=20, pady=5)
    reg_username_entry = tk.Entry(register_screen)
    reg_username_entry.pack(padx=20, pady=5)

    tk.Label(register_screen, text="Password:").pack(padx=20, pady=5)
    reg_password_entry = tk.Entry(register_screen, show='*')
    reg_password_entry.pack(padx=20, pady=5)

    # Add Enter key bindings
    reg_username_entry.bind('<Return>', lambda e: reg_password_entry.focus())
    reg_password_entry.bind('<Return>', register)

    register_button = tk.Button(register_screen, text="Register", command=register)
    register_button.pack(padx=20, pady=20)

    reg_error_label = tk.Label(register_screen, text="", fg="red")
    reg_error_label.pack(padx=20, pady=5)

def reconnect_to_server():
    global client
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        return True
    except Exception as e:
        print(f"Reconnection error: {str(e)}")
        return False

def login(event=None):  # Add event parameter
    global username, password
    username = username_entry.get()
    password = password_entry.get()
    
    try:
        if not client or client._closed:
            if not reconnect_to_server():
                error_label.config(text="Cannot connect to server")
                return

        print(f"Attempting to log in as {username}")
        client.send('LOGIN'.encode('utf-8'))
        # Wait for initial USER request from server
        msg = client.recv(1024).decode('utf-8')
        print(f"Server says: {msg}")
        
        if msg == 'USER':
            # Send username
            print(f"Sending username: {username}")
            client.send(username.encode('utf-8'))
            
            # Wait for PASS request
            msg = client.recv(1024).decode('utf-8')
            print(f"Server says: {msg}")
            
            if msg == 'PASS':
                # Send password
                print(f"Sending password: {password}")
                client.send(password.encode('utf-8'))
                
                # Wait for result
                response = client.recv(1024).decode('utf-8')
                print(f"Server response: {response}")
                
                if response == 'AUTH_SUCCESS':
                    print("Login successful!")
                    # Save credentials after successful login
                    save_credentials(username, password)
                    login_screen.destroy()
                    start_chat()
                    return
        
        error_label.config(text="Authentication Failed. Try again.")
        # Reconnect for next attempt
        reconnect_to_server()
    except Exception as e:
        print(f"Login error: {str(e)}")
        error_label.config(text=f"Connection error: {str(e)}")
        # Attempt to reconnect after error
        reconnect_to_server()

def show_login_screen():
    global login_screen, username_entry, password_entry, error_label
    login_screen = tk.Tk()
    login_screen.title("ChatApp - Login")

    tk.Label(login_screen, text="Username:").pack(padx=20, pady=5)
    username_entry = tk.Entry(login_screen)
    username_entry.pack(padx=20, pady=5)

    tk.Label(login_screen, text="Password:").pack(padx=20, pady=5)
    password_entry = tk.Entry(login_screen, show='*')
    password_entry.pack(padx=20, pady=5)

    # Load and fill saved credentials
    saved_credentials = load_credentials()
    if saved_credentials:
        username_entry.insert(0, saved_credentials.get('username', ''))
        password_entry.insert(0, saved_credentials.get('password', ''))

    # Add Enter key bindings
    username_entry.bind('<Return>', lambda e: password_entry.focus())
    password_entry.bind('<Return>', login)

    login_button = tk.Button(login_screen, text="Login", command=login)
    login_button.pack(padx=20, pady=5)

    register_button = tk.Button(login_screen, text="Register New Account", command=show_register_screen)
    register_button.pack(padx=20, pady=5)

    error_label = tk.Label(login_screen, text="", fg="red")
    error_label.pack(padx=20, pady=5)

    login_screen.mainloop()

def show_online_users():
    client.send('/online'.encode('utf-8'))

def create_private_chat(other_user):
    if (other_user in private_chats):
        private_chats[other_user][0].lift()  # Bring existing window to front
        return
        
    # Create new private chat window
    pm_window = tk.Toplevel(chat_window)
    pm_window.title(f"Chat with {other_user}")
    pm_window.geometry("400x500")
    
    # Chat display
    pm_display = scrolledtext.ScrolledText(pm_window, state=tk.DISABLED)
    pm_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    # Message entry
    pm_entry = tk.Entry(pm_window, width=40)
    pm_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
    
    def send_pm(event=None):  # Add event parameter for key binding
        message = pm_entry.get()
        if message:
            client.send(f'/pm:{other_user}:{message}'.encode('utf-8'))
            pm_entry.delete(0, tk.END)
    
    def on_close():
        del private_chats[other_user]
        pm_window.destroy()
    
    # Bind Enter key to send message
    pm_entry.bind('<Return>', send_pm)
    
    # Send button
    tk.Button(pm_window, text="Send", command=send_pm).pack(pady=(0, 10))
    
    pm_window.protocol("WM_DELETE_WINDOW", on_close)
    private_chats[other_user] = (pm_window, pm_display)

def update_private_chat(sender, message):
    if sender in private_chats:
        window, display = private_chats[sender]
        display.config(state=tk.NORMAL)
        display.insert(tk.END, f"{message}\n")
        display.config(state=tk.DISABLED)
        display.yview(tk.END)
    else:
        create_private_chat(sender)
        update_private_chat(sender, message)

def send_private_message(recipient):
    create_private_chat(recipient)

def create_online_users_window(users_list):
    online_window = tk.Toplevel(chat_window)
    online_window.title("Online Users")
    online_window.geometry("200x300")
    
    # Create a listbox to display users
    users_listbox = tk.Listbox(online_window)
    users_listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    # Add users to listbox, excluding current user
    for user in users_list:
        if user != username:  # Only add other users
            users_listbox.insert(tk.END, user)
    
    def on_user_select():
        selection = users_listbox.curselection()
        if selection:
            selected_user = users_listbox.get(selection[0])
            send_private_message(selected_user)  # No need to check for self, as we filtered the list
    
    # Buttons frame
    button_frame = tk.Frame(online_window)
    button_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Button(button_frame, text="Message", command=on_user_select).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Close", command=online_window.destroy).pack(side=tk.RIGHT, padx=5)

def receive():
    receiving_history = False
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            
            # Check if message is from current user before playing sound
            is_system_message = message.startswith(('MESSAGE_HISTORY', 'ONLINE_USERS:', '==='))
            is_own_message = message.startswith(f'{username}:') or message.startswith(f'[Private to]')
            
            # Only play sound for messages from others
            if not receiving_history and not is_system_message and not is_own_message:
                play_sound('received')  # Play received sound
            
            if message == 'MESSAGE_HISTORY_START':
                receiving_history = True
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, "=== Chat History ===\n\n")
                chat_display.config(state=tk.DISABLED)
                continue
            elif message == 'MESSAGE_HISTORY_END':
                receiving_history = False
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, "\n=== End of History ===\n\n")
                chat_display.config(state=tk.DISABLED)
                chat_display.yview(tk.END)
                continue
            
            chat_display.config(state=tk.NORMAL)
            
            if receiving_history:
                # Split messages by newline and process each one
                messages = [msg for msg in message.split('\n') if msg.strip()]
                for msg in messages:
                    chat_display.insert(tk.END, f"{msg}\n")  # Add newline after each message
                if messages:  # Add extra newline between groups of messages
                    chat_display.insert(tk.END, "\n")
            elif message.startswith('ONLINE_USERS:'):
                users = message.split(':')[1].split(', ')
                chat_window.after(0, create_online_users_window, users)
            elif message.startswith('[Private]'):
                sender = message[9:].split(':')[0].strip()
                chat_window.after(0, update_private_chat, sender, message)
            elif message.startswith('[Private to'):
                recipient = message[11:].split(']')[0].strip()
                chat_window.after(0, update_private_chat, recipient, message)
            else:
                chat_display.insert(tk.END, f"{message}\n\n")  # Add double newline for regular messages
            
            chat_display.config(state=tk.DISABLED)
            chat_display.yview(tk.END)
        except:
            print("An error occurred!")
            client.close()
            break

def write(event=None):  # Add event parameter for key binding
    message = message_entry.get()
    if message:  # Don't send empty messages
        client.send(f'{username}: {message}'.encode('utf-8'))
        message_entry.delete(0, tk.END)
        play_sound('sent')  # Play sent sound

def quit_app():
    try:
        # Close all private chat windows
        for window, _ in private_chats.values():
            window.destroy()
        
        # Close socket and main window
        client.close()
        chat_window.destroy()
        
        # Force quit the application
        os._exit(0)
    except:
        os._exit(0)

def start_chat():
    global chat_display, message_entry, chat_window
    chat_window = tk.Tk()
    chat_window.title("ChatApp")
    
    # Add window close handler
    chat_window.protocol("WM_DELETE_WINDOW", quit_app)
    
    # Toolbar setup
    menubar = tk.Menu(chat_window)
    
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Quit", command=quit_app)
    menubar.add_cascade(label="File", menu=file_menu)
    
    view_menu = tk.Menu(menubar, tearoff=0)
    view_menu.add_command(label="Show Online Users", command=show_online_users)
    menubar.add_cascade(label="View", menu=view_menu)
    
    chat_window.config(menu=menubar)

    chat_display = scrolledtext.ScrolledText(chat_window, state=tk.DISABLED)
    chat_display.pack(padx=20, pady=5)

    message_entry = tk.Entry(chat_window, width=50)
    message_entry.pack(padx=20, pady=5)
    
    # Replace keyboard module with Tkinter binding
    message_entry.bind('<Return>', write)
    
    send_button = tk.Button(chat_window, text="Send", command=write)
    send_button.pack(padx=20, pady=5)

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    chat_window.mainloop()

# Initial connection screen setup
connection_screen = tk.Tk()
connection_screen.title("ChatApp - Connect to Server")

# Load saved credentials including connection details
saved_credentials = load_credentials()
if saved_credentials:
    HOST = saved_credentials.get('host', HOST)
    try:
        PORT = int(saved_credentials.get('port', PORT))
    except:
        PORT = 8080

tk.Label(connection_screen, text="Server Address:").pack(padx=20, pady=5)
host_entry = tk.Entry(connection_screen)
host_entry.insert(0, HOST)
host_entry.pack(padx=20, pady=5)

tk.Label(connection_screen, text="Port:").pack(padx=20, pady=5)
port_entry = tk.Entry(connection_screen)
port_entry.insert(0, str(PORT))
port_entry.pack(padx=20, pady=5)

# Add Enter key binding for connection screen
host_entry.bind('<Return>', lambda e: port_entry.focus())
port_entry.bind('<Return>', init_connection)

connect_button = tk.Button(connection_screen, text="Connect", command=init_connection)
connect_button.pack(padx=20, pady=20)

connection_error_label = tk.Label(connection_screen, text="", fg="red")
connection_error_label.pack(padx=20, pady=5)

connection_screen.mainloop()
