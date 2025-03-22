#!/usr/bin/env python3
"""
Generate encryption key for Aroha database
"""
import os
import re
from cryptography.fernet import Fernet
from dotenv import load_dotenv

def main():
    # Generate a new key
    key = Fernet.generate_key().decode()
    print(f"Generated new encryption key: {key}")
    
    # Load current environment
    load_dotenv()
    
    # Check if .env file exists
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
        
        # Update ENCRYPTION_KEY
        if 'ENCRYPTION_KEY=' in env_content:
            new_content = re.sub(
                r'ENCRYPTION_KEY=.*',
                f'ENCRYPTION_KEY={key}',
                env_content
            )
        else:
            new_content = env_content + f'\nENCRYPTION_KEY={key}\n'
        
        with open('.env', 'w') as f:
            f.write(new_content)
        
        print("Updated encryption key in .env file")
    else:
        # Create new .env file if it doesn't exist
        if os.path.exists('.env.template'):
            with open('.env.template', 'r') as f:
                template = f.read()
            
            new_content = re.sub(
                r'ENCRYPTION_KEY=.*',
                f'ENCRYPTION_KEY={key}',
                template
            )
            
            with open('.env', 'w') as f:
                f.write(new_content)
            
            print("Created .env file from template with new encryption key")
        else:
            with open('.env', 'w') as f:
                f.write(f"ENCRYPTION_KEY={key}\n")
            
            print("Created new .env file with encryption key")
    
    # Verify key works
    try:
        cipher = Fernet(key.encode())
        test = cipher.encrypt(b"test")
        cipher.decrypt(test)
        print("✅ Key verification successful")
    except Exception as e:
        print(f"❌ Key verification failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main() 
