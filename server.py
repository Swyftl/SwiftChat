import socket
import threading
import os
import sqlite3

# Check if conf.env exists, if not create it
if not os.path.exists('conf.env'):
    print("First run detected. Creating configuration file...")
    with open('conf.env', 'w') as f:
        f.write("CHATAPP_HOST=127.0.0.1\nCHATAPP_PORT=8080")
    print("Created conf.env with default settings.")
    print("Please review the configuration file and restart the server.")
    exit()

# Load configuration from conf.env
HOST = os.getenv('CHATAPP_HOST', '127.0.0.1')
PORT = int(os.getenv('CHATAPP_PORT', 8080))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
nicknames = []

# Database setup
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Create users table if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL)''')
conn.commit()

# Add test user if not exists
cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('test', 'test123'))
conn.commit()
print("Database setup completed")

def broadcast(message):
    for client in clients:
        client.send(message)

def handle_client(client):
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            broadcast(message.encode('utf-8'))
        except:
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            broadcast(f'{nickname} left the chat!'.encode('utf-8'))
            nicknames.remove(nickname)
            break

def authenticate(client):
    try:
        print("Starting authentication process...")
        
        # Ask for username
        client.send('USER'.encode('utf-8'))
        username = client.recv(1024).decode('utf-8')
        print(f"Got username: {username}")
        
        # Ask for password
        client.send('PASS'.encode('utf-8'))
        password = client.recv(1024).decode('utf-8')
        print(f"Got password for user: {username}")
        
        # Check credentials
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        print(f"Database query result: {result}")
        
        if result:
            print(f"User {username} authenticated successfully")
            client.send('AUTH_SUCCESS'.encode('utf-8'))
            return username
        else:
            print(f"Authentication failed for user {username}")
            client.send('AUTH_FAIL'.encode('utf-8'))
            return None
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None

def register_user(client):
    try:
        print("Starting registration process...")
        
        # Ask for new username
        client.send('NEW_USER'.encode('utf-8'))
        username = client.recv(1024).decode('utf-8')
        print(f"Got new username: {username}")
        
        # Check if username exists
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        if cursor.fetchone():
            print(f"Username {username} already exists")
            client.send('USER_EXISTS'.encode('utf-8'))
            return None
            
        # Ask for password
        client.send('NEW_PASS'.encode('utf-8'))
        password = client.recv(1024).decode('utf-8')
        
        # Add new user
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print(f"New user {username} registered successfully")
        client.send('REG_SUCCESS'.encode('utf-8'))
        return username
            
    except Exception as e:
        print(f"Registration error: {str(e)}")
        client.send('REG_FAIL'.encode('utf-8'))
        return None

def receive():
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        # Receive auth type
        auth_type = client.recv(1024).decode('utf-8')
        
        if auth_type == 'LOGIN':
            username = authenticate(client)
        elif auth_type == 'REGISTER':
            username = register_user(client)
            
        if username:
            nicknames.append(username)
            clients.append(client)
            print(f"Nickname of the client is {username}")
            broadcast(f"{username} joined the chat!".encode('utf-8'))
            client.send('Connected to the server!'.encode('utf-8'))

            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()
        else:
            client.close()

print("Server is listening...")
receive()
