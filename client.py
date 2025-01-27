import socket
import threading
import os
import tkinter as tk
from tkinter import scrolledtext

# Global variables
HOST = '127.0.0.1'  # Default host
PORT = 12345        # Default port
client = None

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

def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
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
    client.close()
    chat_window.quit()

def start_chat():
    global chat_display, message_entry, chat_window
    chat_window = tk.Tk()
    chat_window.title("ChatApp")

    # Toolbar setup
    menubar = tk.Menu(chat_window)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Quit", command=quit_app)
    menubar.add_cascade(label="File", menu=file_menu)
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
