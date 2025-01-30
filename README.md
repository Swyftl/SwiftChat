# SwiftChat

SwiftChat is a secure, feature-rich chat application with both client and server components built in Python. It provides real-time messaging with end-to-end encryption for private messages.

## Features

### Security
- End-to-end encryption for private messages
- Secure user authentication
- Password-protected accounts
- Encrypted session management

### Messaging
- Public chat room
- Private messaging between users
- Message history
- Online user list
- Image sharing support
- Sound notifications for messages

### User Interface
- Modern GUI built with PyQt6
- Customizable chat appearance
  - Font selection
  - Color themes
  - Text colors
- Notification sounds for:
  - Message received
  - Message sent
  - User joined
  - User left
  - Private message started

### Server Features
- SQLite database for user management
- Message history storage
- Server command console
- User activity monitoring
- Auto-backup functionality
- Configurable settings via conf.env

### Additional Features
- Auto-update system
- Saved credentials
- Customizable settings
- Connection status indicators
- Multiple private chat windows
- Sound toggle options

## Technical Details
- Built with Python 3.x
- GUI: PyQt6
- Server: Socket-based with threading
- Database: SQLite3
- Encryption: RSA & Fernet (AES)
- Sound: Pygame mixer

## Requirements
- Python 3.x
- PyQt6
- Pygame
- Cryptography
- Requests
- Pillow (PIL)