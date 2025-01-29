import socket
import threading
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
import webbrowser
import requests
from pygame import mixer
import sys
import subprocess
import time
import json
import io
import base64
from tkinter import colorchooser, font
import json
from tkinter import filedialog
from PIL import Image, ImageTk
from datetime import datetime  # Add this at the top with other imports

# Version control
CURRENT_VERSION = "V0.1.5"
GITHUB_REPO = "swyftl/swiftChat"  # Replace with your actual GitHub repo

# Add settings file constant
SETTINGS_FILE = 'chat_settings.json'

# Add default settings
DEFAULT_SETTINGS = {
    'bg_color': '#ffffff',
    'text_color': '#000000',
    'font_family': 'Arial',
    'font_size': 10
}

def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        print(f"Error saving settings: {e}")

def apply_chat_settings(settings=None):
    if settings is None:
        settings = load_settings()
    
    # Apply settings to main chat display
    chat_display.configure(
        bg=settings['bg_color'],
        fg=settings['text_color'],
        font=(settings['font_family'], settings['font_size'])
    )
    
    # Apply to private chat windows
    for _, (_, display) in private_chats.items():
        display.configure(
            bg=settings['bg_color'],
            fg=settings['text_color'],
            font=(settings['font_family'], settings['font_size'])
        )

def show_settings_window():
    settings = load_settings()
    settings_window = tk.Toplevel(chat_window)
    settings_window.title("Chat Settings")
    settings_window.geometry("300x400")
    
    def choose_bg_color():
        color = colorchooser.askcolor(color=settings['bg_color'])[1]
        if color:
            settings['bg_color'] = color
            bg_preview.config(bg=color)
    
    def choose_text_color():
        color = colorchooser.askcolor(color=settings['text_color'])[1]
        if color:
            settings['text_color'] = color
            text_preview.config(fg=color)
    
    def update_font_preview():
        preview_font = (font_var.get(), size_var.get())
        text_preview.config(font=preview_font)
    
    # Color settings
    tk.Label(settings_window, text="Colors:").pack(pady=5)
    
    # Background color
    bg_frame = tk.Frame(settings_window)
    bg_frame.pack(fill='x', padx=20)
    tk.Label(bg_frame, text="Background:").pack(side='left')
    bg_preview = tk.Label(bg_frame, text="   ", bg=settings['bg_color'])
    bg_preview.pack(side='left', padx=5)
    tk.Button(bg_frame, text="Choose", command=choose_bg_color).pack(side='left')
    
    # Text color
    text_frame = tk.Frame(settings_window)
    text_frame.pack(fill='x', padx=20, pady=5)
    tk.Label(text_frame, text="Text Color:").pack(side='left')
    text_preview = tk.Label(text_frame, text="Sample", fg=settings['text_color'])
    text_preview.pack(side='left', padx=5)
    tk.Button(text_frame, text="Choose", command=choose_text_color).pack(side='left')
    
    # Font settings
    tk.Label(settings_window, text="Font:").pack(pady=5)
    
    # Font family
    available_fonts = sorted(font.families())
    font_var = tk.StringVar(value=settings['font_family'])
    font_menu = tk.OptionMenu(settings_window, font_var, *available_fonts, command=lambda _: update_font_preview())
    font_menu.pack(pady=5)
    
    # Font size
    size_frame = tk.Frame(settings_window)
    size_frame.pack(pady=5)
    tk.Label(size_frame, text="Size:").pack(side='left')
    size_var = tk.IntVar(value=settings['font_size'])
    size_spin = tk.Spinbox(size_frame, from_=8, to=24, width=5, textvariable=size_var, command=update_font_preview)
    size_spin.pack(side='left')
    
    # Preview area
    tk.Label(settings_window, text="Preview:").pack(pady=5)
    text_preview = tk.Label(settings_window, text="Sample Text", 
                           font=(settings['font_family'], settings['font_size']),
                           fg=settings['text_color'], bg=settings['bg_color'])
    text_preview.pack(pady=5)
    
    def apply_settings():
        settings.update({
            'font_family': font_var.get(),
            'font_size': size_var.get()
        })
        save_settings(settings)
        apply_chat_settings(settings)
        settings_window.destroy()
    
    # Buttons
    button_frame = tk.Frame(settings_window)
    button_frame.pack(pady=20)
    tk.Button(button_frame, text="Apply", command=apply_settings).pack(side='left', padx=5)
    tk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side='left', padx=5)

def is_running_as_exe():
    """Check if we're running as a bundled exe"""
    return getattr(sys, 'frozen', False)

def check_for_updates():
    try:
        print("Checking for updates...")
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release["tag_name"].strip("v")
            
            print(f"Current version: {CURRENT_VERSION}")
            print(f"Latest version: {latest_version}")
            
            if latest_version > CURRENT_VERSION:
                if messagebox.askyesno(
                    "Update Available",
                    f"A new version ({latest_version}) is available!\n"
                    f"You are currently running version {CURRENT_VERSION}\n\n"
                    "Would you like to download and install the update?"
                ):
                    for asset in latest_release['assets']:
                        if asset['name'].lower() == 'swiftchat.exe':
                            print(f"Found update asset: {asset['name']}")
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
                                    messagebox.showinfo(
                                        "Update Ready",
                                        "Update downloaded successfully!\n"
                                        "The application will now restart to complete the update."
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
                        print("No SwiftChat.exe found in release assets")
                        webbrowser.open(latest_release['html_url'])
                        
    except Exception as e:
        print(f"Update check failed: {e}")

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
    join_sound_path = resource_path('resources/sounds/user_joined.mp3')
    leave_sound_path = resource_path('resources/sounds/user_left.mp3')
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
            elif sound_type == 'joined':
                mixer.music.load(join_sound_path)
            elif sound_type == 'left':
                mixer.music.load(leave_sound_path)
            else:  # 'received'
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
last_pm_user = None  # To track which PM window should receive history

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
        # Add keep-alive settings
        client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
    global last_pm_user  # Add this at the start of the function
    last_pm_user = other_user  # Store the user for history handling
    
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
    
    # Request chat history when creating new PM window
    client.send(f'/pmhistory:{other_user}'.encode('utf-8'))
    
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
        
        # Handle history markers for private messages
        if message == 'PM_HISTORY_START':
            display.insert(tk.END, "=== Private Message History ===\n\n")
        elif message == 'PM_HISTORY_END':
            display.insert(tk.END, "\n=== End of Private History ===\n\n")
        else:
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

def send_image_thread(filename):
    try:
        print("\n=== Starting Image Upload ===")
        print(f"Opening image: {filename}")
        
        with Image.open(filename) as img:
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Even more aggressive compression
            max_size = (400, 400)  # Further reduced size
            img.thumbnail(max_size)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', optimize=True, quality=50)  # Changed to JPEG with lower quality
            img_byte_arr = img_byte_arr.getvalue()
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            total_size = len(img_base64)
            
            if total_size > 256 * 1024:  # Even smaller limit (256KB)
                raise Exception("Image too large after compression. Please use a smaller image.")
            
            print(f"Starting upload ({total_size/1024:.1f} KB)")
            
            # No timeout for initial handshake
            client.settimeout(None)
            
            try:
                # Initial handshake
                client.send('IMAGE_START'.encode('utf-8'))
                print("Waiting for server ready signal...")
                response = client.recv(1024).decode('utf-8')
                print(f"Server response: {response}")
                
                if response != 'READY_FOR_IMAGE':
                    raise Exception(f"Unexpected server response: {response}")
                
                # Send size info
                size_info = f"SIZE:{total_size}".encode('utf-8')
                client.send(size_info)
                print("Waiting for size acknowledgment...")
                
                size_response = client.recv(1024).decode('utf-8')
                if size_response != 'SIZE_OK':
                    raise Exception(f"Size not acknowledged: {size_response}")
                
                # Send data in tiny chunks with minimal delay
                chunk_size = 256  # Even smaller chunks
                bytes_sent = 0
                last_progress_update = time.time()
                
                print("Starting chunk transfer...")
                for i in range(0, len(img_base64), chunk_size):
                    chunk = img_base64[i:i+chunk_size]
                    client.send(chunk.encode('utf-8'))
                    bytes_sent += len(chunk)
                    
                    # Update progress every second
                    current_time = time.time()
                    if current_time - last_progress_update >= 1.0:
                        progress = (bytes_sent / total_size) * 100
                        print(f"Progress: {progress:.1f}%", end='\r')
                        chat_window.after(0, lambda p=progress: update_chat_status(
                            f"Sending image... {p:.1f}%"))
                        last_progress_update = current_time
                    
                    # Tiny delay every 4 chunks
                    if (i // chunk_size) % 4 == 0:
                        time.sleep(0.01)
                
                print("\nSending end marker...")
                client.send('END_IMAGE'.encode('utf-8'))
                
                print("Waiting for final confirmation...")
                final_response = client.recv(1024).decode('utf-8')
                print(f"Final server response: {final_response}")
                
                if final_response != 'IMAGE_RECEIVED':
                    raise Exception(f"Transfer failed: {final_response}")
                
                print("\nImage sent successfully!")
                chat_window.after(0, lambda: play_sound('sent'))
                chat_window.after(0, lambda: update_chat_status("Image sent successfully ✓"))
                
            except socket.timeout:
                raise Exception("Connection timed out during image transfer")
            except Exception as e:
                raise Exception(f"Transfer error: {str(e)}")
            finally:
                client.settimeout(None)
                
    except Exception as e:
        error_msg = f"Error sending image: {str(e)}"
        print(f"\nERROR: {error_msg}")
        chat_window.after(0, lambda: update_chat_status(error_msg))

def update_chat_status(message):
    """Update chat display with status message"""
    try:
        chat_display.config(state=tk.NORMAL)
        
        # Get all lines of text
        text_content = chat_display.get("1.0", tk.END).split('\n')
        
        # Find and remove the last status message
        for i in range(len(text_content) - 1, -1, -1):
            if "Sending image..." in text_content[i]:
                # Delete the line containing the status
                chat_display.delete(f"{i+1}.0", f"{i+2}.0")
                break
        
        # Add new status message
        chat_display.insert(tk.END, f"{message}\n")
        chat_display.config(state=tk.DISABLED)
        chat_display.see(tk.END)
    except Exception as e:
        print(f"Error updating chat status: {e}")

def send_image():
    filetypes = [
        ('Image files', '*.png *.jpg *.jpeg *.gif *.bmp'),
        ('All files', '*.*')
    ]
    filename = filedialog.askopenfilename(filetypes=filetypes)
    if filename:
        update_chat_status("Sending image... Please wait...")
        threading.Thread(target=send_image_thread, args=(filename,), daemon=True).start()

def display_image(filename, sender):
    try:
        img_path = os.path.join('images', filename)
        with Image.open(img_path) as img:
            # Resize image for display while maintaining aspect ratio
            display_size = (300, 300)
            img.thumbnail(display_size)
            photo = ImageTk.PhotoImage(img)
            
            # Create frame for image with better styling
            frame = tk.Frame(chat_display, relief=tk.RAISED, borderwidth=1)
            
            # Add sender label with timestamp (fixed timestamp reference)
            timestamp = datetime.now().strftime("%H:%M:%S")
            sender_label = tk.Label(frame, text=f"{sender} sent an image at {timestamp}:", 
                                  anchor='w', font=('Arial', 9, 'bold'))
            sender_label.pack(fill='x', padx=5, pady=2)
            
            # Create a container frame for the image
            img_container = tk.Frame(frame)
            img_container.pack(padx=5, pady=5)
            
            # Add image label with white background
            img_label = tk.Label(img_container, image=photo, cursor="hand2", bg='white')
            img_label.image = photo  # Keep reference
            img_label.pack()
            
            # Add click handler to open full image
            def open_full_image(event):
                try:
                    # Create new window for full image
                    img_window = tk.Toplevel()
                    img_window.title(f"Image from {sender}")
                    
                    # Load original image
                    with Image.open(img_path) as full_img:
                        # Resize if too large for screen
                        screen_w = img_window.winfo_screenwidth() - 100
                        screen_h = img_window.winfo_screenheight() - 100
                        
                        # Calculate scaling factor
                        scale_w = screen_w / full_img.width
                        scale_h = screen_h / full_img.height
                        scale = min(scale_w, scale_h, 1.0)  # Don't upscale
                        
                        new_size = (int(full_img.width * scale), 
                                  int(full_img.height * scale))
                        
                        # Create a copy before resizing to prevent modifying original
                        display_img = full_img.copy()
                        display_img = display_img.resize(new_size, Image.Resampling.LANCZOS)
                        full_photo = ImageTk.PhotoImage(display_img)
                        
                        # Display full image
                        full_label = tk.Label(img_window, image=full_photo)
                        full_label.image = full_photo
                        full_label.pack()
                        
                        # Add save button
                        def save_image():
                            save_path = filedialog.asksaveasfilename(
                                defaultextension=".png",
                                filetypes=[("PNG files", "*.png"), 
                                         ("JPEG files", "*.jpg"),
                                         ("All files", "*.*")]
                            )
                            if save_path:
                                full_img.save(save_path)
                        
                        tk.Button(img_window, text="Save Image", 
                                command=save_image).pack(pady=5)
                
                except Exception as e:
                    print(f"Error opening full image: {e}")
                    messagebox.showerror("Error", f"Failed to open image: {str(e)}")
            
            img_label.bind('<Button-1>', open_full_image)
            
            # Add "Click to view full image" hint
            hint_label = tk.Label(frame, text="Click image to view full size", 
                                font=('Arial', 8, 'italic'), fg='blue')
            hint_label.pack(pady=(0, 5))
            
            # Insert frame into chat
            chat_display.window_create(tk.END, window=frame)
            chat_display.insert(tk.END, '\n\n')
            chat_display.see(tk.END)  # Make sure the new image is visible
            
    except Exception as e:
        print(f"Error displaying image: {e}")
        # Show error message in chat
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, f"[Error loading image from {sender}: {str(e)}]\n\n")
        chat_display.config(state=tk.DISABLED)
        chat_display.see(tk.END)

def receive():
    receiving_history = False
    receiving_pm_history = False
    receiving_image = False
    current_image_data = []
    current_image_sender = None
    
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            
            if message.startswith('IMAGE_START:'):
                receiving_image = True
                current_image_data = []
                current_image_sender = message.split(':', 1)[1]
                continue
                
            if receiving_image:
                if message == 'END_IMAGE':
                    receiving_image = False
                    # Process the complete image
                    try:
                        image_bytes = base64.b64decode(''.join(current_image_data))
                        # Create temporary file in memory
                        img_file = io.BytesIO(image_bytes)
                        # Display image
                        display_image_from_bytes(img_file, current_image_sender)
                        if current_image_sender != username:
                            play_sound('received')
                    except Exception as e:
                        print(f"Error processing received image: {e}")
                    current_image_data = []
                    current_image_sender = None
                    continue
                else:
                    current_image_data.append(message)
                    continue
                    
            # Handle join/leave sounds
            if ' joined the chat!' in message:
                play_sound('joined')
            elif ' left the chat!' in message:
                play_sound('left')
            
            # Handle PM history
            if message.startswith('PM_HISTORY:'):
                _, user, content = message.split(':', 2)
                # Split content by newlines
                if content.strip():
                    messages = content.split('\n')
                    for msg in messages:
                        if msg.strip():
                            update_private_chat(user, f"{msg.strip()}\n")
                continue
            
            # Handle main chat history and messages
            is_system_message = message.startswith(('MESSAGE_HISTORY', 'ONLINE_USERS:', '==='))
            is_own_message = message.startswith(f'{username}:') or message.startswith(f'[Private to]')
            
            if not (receiving_history or receiving_pm_history) and not is_system_message and not is_own_message:
                play_sound('received')
            
            chat_display.config(state=tk.NORMAL)
            
            if message == 'MESSAGE_HISTORY_START':
                receiving_history = True
                chat_display.insert(tk.END, "=== Chat History ===\n\n")
            elif message == 'MESSAGE_HISTORY_END':
                receiving_history = False
                chat_display.insert(tk.END, "\n=== End of History ===\n\n")
            elif receiving_history:
                # Handle the batch of messages
                if message.strip():
                    messages = message.split('\n')
                    # Process each message in the batch
                    for msg in messages:
                        if msg.strip():  # Only process non-empty messages
                            # Add each message with proper spacing
                            chat_display.insert(tk.END, f"{msg.strip()}\n\n")
                    chat_display.see(tk.END)  # Scroll to the latest message
            elif message.startswith('[Private]'):
                sender = message[9:].split(':')[0].strip()
                update_private_chat(sender, message)
            elif message.startswith('[Private to'):
                recipient = message[11:].split(']')[0].strip()
                update_private_chat(recipient, message)
            elif message.startswith('ONLINE_USERS:'):
                users = message.split(':')[1].split(', ')
                chat_window.after(0, create_online_users_window, users)
            else:
                chat_display.insert(tk.END, f"{message}\n")
            
            chat_display.config(state=tk.DISABLED)
            chat_display.yview(tk.END)
            
        except Exception as e:
            print(f"Receive error: {str(e)}")
            client.close()
            break

def display_image_from_bytes(img_bytes, sender):
    """Display image directly from bytes without saving to disk"""
    try:
        with Image.open(img_bytes) as img:
            # Resize image for display while maintaining aspect ratio
            display_size = (300, 300)
            img.thumbnail(display_size)
            photo = ImageTk.PhotoImage(img)
            
            # Create frame for image with better styling
            frame = tk.Frame(chat_display, relief=tk.RAISED, borderwidth=1)
            
            # Add sender label with timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            sender_label = tk.Label(frame, text=f"{sender} sent an image at {timestamp}:", 
                                  anchor='w', font=('Arial', 9, 'bold'))
            sender_label.pack(fill='x', padx=5, pady=2)
            
            # Create a container frame for the image
            img_container = tk.Frame(frame)
            img_container.pack(padx=5, pady=5)
            
            # Add image label with white background
            img_label = tk.Label(img_container, image=photo, cursor="hand2", bg='white')
            img_label.image = photo  # Keep reference
            img_label.pack()
            
            # Add click handler to open full image
            def open_full_image(event):
                try:
                    # Create new window for full image
                    img_window = tk.Toplevel()
                    img_window.title(f"Image from {sender}")
                    
                    # Reset image bytes position
                    img_bytes.seek(0)
                    with Image.open(img_bytes) as full_img:
                        # Resize if too large for screen
                        screen_w = img_window.winfo_screenwidth() - 100
                        screen_h = img_window.winfo_screenheight() - 100
                        
                        # Calculate scaling factor
                        scale_w = screen_w / full_img.width
                        scale_h = screen_h / full_img.height
                        scale = min(scale_w, scale_h, 1.0)  # Don't upscale
                        
                        new_size = (int(full_img.width * scale), 
                                  int(full_img.height * scale))
                        
                        display_img = full_img.copy()
                        display_img.thumbnail(new_size)
                        full_photo = ImageTk.PhotoImage(display_img)
                        
                        # Display full image
                        full_label = tk.Label(img_window, image=full_photo)
                        full_label.image = full_photo
                        full_label.pack()
                        
                        # Add save button
                        def save_image():
                            save_path = filedialog.asksaveasfilename(
                                defaultextension=".png",
                                filetypes=[("PNG files", "*.png"), 
                                         ("JPEG files", "*.jpg"),
                                         ("All files", "*.*")]
                            )
                            if save_path:
                                img_bytes.seek(0)
                                with open(save_path, 'wb') as f:
                                    f.write(img_bytes.getvalue())
                                
                        tk.Button(img_window, text="Save Image", 
                                command=save_image).pack(pady=5)
                
                except Exception as e:
                    print(f"Error opening full image: {e}")
                    messagebox.showerror("Error", f"Failed to open image: {str(e)}")
            
            img_label.bind('<Button-1>', open_full_image)
            
            # Add hint label
            hint_label = tk.Label(frame, text="Click image to view full size", 
                                font=('Arial', 8, 'italic'), fg='blue')
            hint_label.pack(pady=(0, 5))
            
            # Insert frame into chat
            chat_display.config(state=tk.NORMAL)
            chat_display.window_create(tk.END, window=frame)
            chat_display.insert(tk.END, '\n\n')
            chat_display.config(state=tk.DISABLED)
            chat_display.see(tk.END)
            
    except Exception as e:
        print(f"Error displaying image: {e}")
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, f"[Error displaying image from {sender}: {str(e)}]\n\n")
        chat_display.config(state=tk.DISABLED)
        chat_display.see(tk.END)

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
    
    # Add Settings menu
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_command(label="Customize Chat", command=show_settings_window)
    menubar.add_cascade(label="Settings", menu=settings_menu)
    
    chat_window.config(menu=menubar)

    chat_display = scrolledtext.ScrolledText(chat_window, state=tk.DISABLED)
    chat_display.pack(padx=20, pady=5)

    message_entry = tk.Entry(chat_window, width=50)
    message_entry.pack(padx=20, pady=5)
    
    # Replace keyboard module with Tkinter binding
    message_entry.bind('<Return>', write)
    
    # Add image button
    button_frame = tk.Frame(chat_window)
    button_frame.pack(fill=tk.X, padx=20)
    
    send_button = tk.Button(button_frame, text="Send", command=write)
    send_button.pack(side=tk.LEFT, padx=5)
    
    # Temporarily disable image button while fixing functionality
    # image_button = tk.Button(button_frame, text="Send Image", command=send_image)
    # image_button.pack(side=tk.LEFT, padx=5)

    receive_thread = threading.Thread(target=receive)
    receive_thread.start()

    # Apply saved settings
    apply_chat_settings()

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
