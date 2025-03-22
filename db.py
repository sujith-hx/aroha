#!/usr/bin/env python3
"""
Database module for Aroha - Handles user data and conversation storage
"""
import os
import json
import sqlite3
import base64
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants and configurations
DB_PATH = "users.db"
DB_SALT = os.getenv("DB_SALT", "aroha_default_salt").encode()
KEY_ITERATIONS = int(os.getenv("KEY_ITERATIONS", 100000))
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# Global cipher for encryption
cipher = None

def derive_key(password):
    """Derive an encryption key from a password"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=DB_SALT,
        iterations=KEY_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def initialize_database():
    """Initialize the database connection and set up tables"""
    global cipher
    
    # Generate or validate encryption key
    if not ENCRYPTION_KEY:
        print("No encryption key found. Generating a temporary key.")
        key = Fernet.generate_key()
        cipher = Fernet(key)
    else:
        try:
            # Derive key from stored password
            key = derive_key(ENCRYPTION_KEY)
            cipher = Fernet(key)
            print("Encryption key validated successfully")
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            print("Using temporary key for this session.")
            key = Fernet.generate_key()
            cipher = Fernet(key)
    
    # Create tables if they don't exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Drop old tables if they exist
    cursor.execute("DROP TABLE IF EXISTS conversations")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Create conversations table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        user_message TEXT NOT NULL,
        ai_response TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    
    print("Database initialized")
    return True

def encrypt_text(text):
    """Encrypt text data"""
    if not cipher:
        return text  # No encryption if cipher not initialized
    try:
        return cipher.encrypt(text.encode()).decode()
    except Exception as e:
        print(f"Error encrypting data: {e}")
        return text

def decrypt_text(text):
    """Decrypt encrypted text"""
    if not cipher:
        return text  # No decryption if cipher not initialized
    try:
        return cipher.decrypt(text.encode()).decode()
    except Exception as e:
        print(f"Error decrypting data: {e}")
        return text

def get_user_id(name):
    """Get user ID by name, return None if not found"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def create_user(name):
    """Create a new user and return the user ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create user with current timestamp
        timestamp = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO users (name, created_at) VALUES (?, ?)",
            (name, timestamp)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def save_conversation(user_id, user_message, ai_response):
    """Save a conversation exchange to the database"""
    if not user_id:
        return False
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Encrypt data
        encrypted_user_message = encrypt_text(user_message)
        encrypted_ai_response = encrypt_text(ai_response)
        timestamp = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO conversations (user_id, user_message, ai_response, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, encrypted_user_message, encrypted_ai_response, timestamp)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return False

def get_conversation_history(user_id, limit=10):
    """Get recent conversation history for a user"""
    if not user_id:
        return []
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT user_message, ai_response FROM conversations WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        # Decrypt and format as chat history
        history = []
        for user_message, ai_response in reversed(rows):  # Oldest first
            history.append({"role": "user", "content": decrypt_text(user_message)})
            history.append({"role": "assistant", "content": decrypt_text(ai_response)})
            
        return history
    except Exception as e:
        print(f"Error getting conversation history: {e}")
        return []