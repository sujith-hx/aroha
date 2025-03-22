#!/usr/bin/env python3
"""
Connectivity test utility for Aroha
Tests connections to all required APIs and services
"""
import os
import time
import requests
import openai
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# Load environment variables
load_dotenv()

# API endpoints to test
ENDPOINTS = {
    "OpenAI": {
        "url": "https://api.openai.com/v1/chat/completions",
        "method": "POST",
        "headers": {"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"},
        "data": {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Test message"}],
            "max_tokens": 5
        }
    },
    "ElevenLabs": {
        "api_key": os.getenv("ELEVENLABS_API_KEY_1")
    }
}

def test_endpoint(name, config):
    """Test an API endpoint connection"""
    try:
        print(f"\nTesting connection to {name}...", end="")
        
        # Special handling for ElevenLabs
        if name == "ElevenLabs":
            if not config.get("api_key"):
                print(" SKIPPED (No API key)")
                return
            
            # Initialize ElevenLabs client
            client = ElevenLabs(api_key=config["api_key"])
            
            # Try to list voices (lightweight operation)
            voices = client.voices.get_all()
            print(" SUCCESS")
            print(f"  → Available voices: {len(voices)}")
            return
        
        # For standard REST APIs
        if config.get("method") == "POST":
            response = requests.post(
                config["url"],
                headers=config.get("headers", {}),
                json=config.get("data", {})
            )
        else:
            response = requests.get(
                config["url"],
                headers=config.get("headers", {})
            )
        
        if response.ok:
            print(" SUCCESS")
        else:
            print(f" ERROR (Status: {response.status_code})")
            print(f"  → Response: {response.text}")
            
    except Exception as e:
        print(f" ERROR")
        print(f"  → Exception: {str(e)}")

def main():
    """Main test function"""
    start_time = time.time()
    
    print("==================================================")
    print("              AROHA CONNECTIVITY TEST")
    print("==================================================")
    
    for name, config in ENDPOINTS.items():
        test_endpoint(name, config)
    
    # Test OpenAI direct API access
    print("\nTesting OpenAI Python client...", end="")
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        print(" SUCCESS")
    except Exception as e:
        print(" ERROR")
        print(f"  → Exception: {str(e)}")
    
    print("\n==================================================")
    elapsed = time.time() - start_time
    print(f"All tests completed in {elapsed:.2f} seconds")
    print("==================================================")

if __name__ == "__main__":
    main() 