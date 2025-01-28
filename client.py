import socket
import threading
import os
import tkinter as tk
from tkinter import scrolledtext

# Global variables
HOST = '127.0.0.1'  # Default host
PORT = 8080         # Update default port to match server
client = None
private_chats = {}  # Store private chat windows: {username: (window, textbox)}

def init_connection():
    global client, HOST, PORT
    HOST = host_entry.get()
    PORT = int(port_entry.get())
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        connection_screen.destroy()
        show_login_screen()
    except:
        connection_error_label.config(text="Failed to connect to server")

def register():
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

    register_button = tk.Button(register_screen, text="Register", command=register)
    register_button.pack(padx=20, pady=20)

    reg_error_label = tk.Label(register_screen, text="", fg="red")
    reg_error_label.pack(padx=20, pady=5)

def login():
    global username, password
    username = username_entry.get()
    password = password_entry.get()
    
    try:
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
                    login_screen.destroy()
                    start_chat()
                    return
        
        error_label.config(text="Authentication Failed. Try again.")
    except Exception as e:
        print(f"Login error: {str(e)}")
        error_label.config(text=f"Connection error: {str(e)}")

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
    
    def send_pm():
        message = pm_entry.get()
        if message:
            client.send(f'/pm:{other_user}:{message}'.encode('utf-8'))
            pm_entry.delete(0, tk.END)
    
    def on_close():
        del private_chats[other_user]
        pm_window.destroy()
    
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
            
            if message == 'MESSAGE_HISTORY_START':
                receiving_history = True
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, "=== Chat History ===\n")
                continue
            elif message == 'MESSAGE_HISTORY_END':
                receiving_history = False
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, "=== End of History ===\n\n")
                chat_display.config(state=tk.DISABLED)
                chat_display.yview(tk.END)
                continue
            
            if message.startswith('ONLINE_USERS:'):
                users = message.split(':')[1].split(', ')
                chat_window.after(0, create_online_users_window, users)
            elif message.startswith('[Private]'):
                # Extract sender from "[Private] username: message"
                sender = message[9:].split(':')[0].strip()
                chat_window.after(0, update_private_chat, sender, message)
            elif message.startswith('[Private to'):
                # Message sent by us, update the recipient's chat window
                recipient = message[11:].split(']')[0].strip()
                chat_window.after(0, update_private_chat, recipient, message)
            else:
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, message + '\n')
                chat_display.config(state=tk.DISABLED)
                chat_display.yview(tk.END)
        except:
            print("An error occurred!")
            client.close()
            break

def write():
    message = f'{username}: {message_entry.get()}'
    client.send(message.encode('utf-8'))
    message_entry.delete(0, tk.END)

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

    send_button = tk.Button(chat_window, text="Send", command=write)
    send_button.pack(padx=20, pady=5)

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    chat_window.mainloop()

# Initial connection screen setup
connection_screen = tk.Tk()
connection_screen.title("ChatApp - Connect to Server")

tk.Label(connection_screen, text="Server Address:").pack(padx=20, pady=5)
host_entry = tk.Entry(connection_screen)
host_entry.insert(0, HOST)
host_entry.pack(padx=20, pady=5)

tk.Label(connection_screen, text="Port:").pack(padx=20, pady=5)
port_entry = tk.Entry(connection_screen)
port_entry.insert(0, str(PORT))
port_entry.pack(padx=20, pady=5)

connect_button = tk.Button(connection_screen, text="Connect", command=init_connection)
connect_button.pack(padx=20, pady=20)

connection_error_label = tk.Label(connection_screen, text="", fg="red")
connection_error_label.pack(padx=20, pady=5)

connection_screen.mainloop()
