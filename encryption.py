from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class E2EEncryption:
    def __init__(self):
        # Generate RSA key pair
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        self.session_keys = {}  # Store session keys for each user pair
        
    def get_public_key_bytes(self):
        """Get public key in bytes format for transmission"""
        from cryptography.hazmat.primitives import serialization
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
    def generate_session_key(self, other_public_key_bytes):
        """Generate a new session key"""
        from cryptography.hazmat.primitives import serialization
        
        # Deserialize other user's public key
        other_public_key = serialization.load_pem_public_key(other_public_key_bytes)
        
        # Generate session key
        session_key = Fernet.generate_key()
        
        # Encrypt session key with other user's public key
        encrypted_session_key = other_public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return session_key, encrypted_session_key
        
    def decrypt_session_key(self, encrypted_session_key):
        """Decrypt a received session key"""
        return self.private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
    def store_session_key(self, other_username, session_key):
        """Store session key for a specific user"""
        self.session_keys[other_username] = Fernet(session_key)
        
    def encrypt_message(self, recipient, message):
        """Encrypt a message for a specific recipient"""
        if recipient not in self.session_keys:
            raise ValueError("No session key for this recipient")
        return self.session_keys[recipient].encrypt(message.encode())
        
    def decrypt_message(self, sender, encrypted_message):
        """Decrypt a message from a specific sender"""
        if sender not in self.session_keys:
            raise ValueError("No session key for this sender")
        return self.session_keys[sender].decrypt(encrypted_message).decode()
