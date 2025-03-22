#!/usr/bin/env python3
"""
Aroha - Terminal-based Crisis Counselor Bot with Voice Interaction
"""
import os
import json
import time
import sys
from dotenv import load_dotenv
import db
import audio

# Load environment variables
load_dotenv()

# API key setup - using only Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Check for Groq API key
if not GROQ_API_KEY:
    print("ERROR: GROQ_API_KEY not found in environment variables.")
    print("Please add your Groq API key to the .env file.")
    sys.exit(1)

# Configure API client
try:
    import openai
    openai.api_key = GROQ_API_KEY
    openai.api_base = "https://api.groq.com/openai/v1"
    print("Using Groq API")
except ImportError:
    print("ERROR: Failed to import OpenAI package. Please run: pip install openai")
    sys.exit(1)

# Set up default voice mode
VOICE_MODE = os.getenv("VOICE_MODE", "True").lower() in ("true", "1", "t", "yes", "y")

# Global chat history with system prompt
chat_history = []
system_prompt = """You are Aroha, an empathetic crisis counselor AI. 
Your purpose is to provide emotional support during difficult times. 
You should be compassionate, non-judgmental, and focused on helping.
Prioritize safety and well-being. For urgent crises, provide relevant crisis resources.
Keep responses conversational, warm, and concise. Never claim to be a human or mental health professional.
If someone is in danger, urge them to contact emergency services immediately.
"""

# Add system prompt to history
chat_history.append({"role": "system", "content": system_prompt})

def detect_emotion(text):
    """
    Detect emotion and urgency from user input
    Returns a dict with emotion and urgency score
    """
    try:
        response = openai.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system", 
                    "content": "Analyze the emotional tone and urgency of this message. Categorize the emotion as one of: neutral, sad, anxious, angry, crisis, or tired. Also rate urgency from 0.0 (not urgent) to 1.0 (extremely urgent)."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.1,
            max_tokens=100
        )
        
        # Parse the response text directly
        response_text = response.choices[0].message.content
        
        # Extract emotion and urgency using some simple parsing
        emotion = "neutral"
        urgency = 0.5
        
        if "emotion" in response_text.lower():
            for possible_emotion in ["neutral", "sad", "anxious", "angry", "crisis", "tired"]:
                if possible_emotion in response_text.lower():
                    emotion = possible_emotion
                    break
                    
        if "urgency" in response_text.lower():
            # Try to find a number between 0 and 1
            import re
            matches = re.findall(r"urgency[:\s]+([0-9]\.[0-9])", response_text.lower())
            if matches:
                try:
                    urgency = float(matches[0])
                except:
                    pass
        
        return {"emotion": emotion, "urgency": urgency}
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        return {"emotion": "neutral", "urgency": 0.5}

def get_ai_response(conversation_history, system_prompt, temperature=0.7):
    """
    Get response from AI model
    """
    try:
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 10 messages)
        messages.extend(conversation_history[-10:])
        
        response = openai.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=temperature,
            max_tokens=250
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "I'm having trouble connecting right now. How are you feeling?"

def handle_user_registration(use_voice=False):
    """Handle user registration process"""
    if use_voice:
        print("\nPlease say or type your name:")
        audio.play_audio("Please tell me your name for registration.", "neutral", 0.3)
        name = audio.listen_for_speech()
        if not name:
            name = input("\nI didn't catch that. Please type your name: ").strip()
        
        print("\nPlease say or type your address (or 'skip' to skip):")
        audio.play_audio("Please tell me your address, or say skip.", "neutral", 0.3)
        address = audio.listen_for_speech()
        if not address:
            address = input("\nI didn't catch that. Please type your address (or 'skip'): ").strip()
        
        if address.lower() == "skip":
            address = "Not provided"
        
        print("\nPlease say or type your gender (or 'skip' to skip):")
        audio.play_audio("Please tell me your gender, or say skip.", "neutral", 0.3)
        gender = audio.listen_for_speech()
        if not gender:
            gender = input("\nI didn't catch that. Please type your gender (or 'skip'): ").strip()
            
        if gender.lower() == "skip":
            gender = "Not provided"
    else:
        name = input("\nPlease enter your name: ").strip()
        address = input("\nPlease enter your address (or 'skip' to skip): ").strip()
        if address.lower() == "skip":
            address = "Not provided"
        gender = input("\nPlease enter your gender (or 'skip' to skip): ").strip()
        if gender.lower() == "skip":
            gender = "Not provided"
    
    # Save user to database
    try:
        db.save_user(name, address, gender, chat_history)
        print(f"\nUser profile created for {name}")
    except Exception as e:
        print(f"Error creating user profile: {e}")
    
    return name

def handle_crisis_resources(emotion):
    """Display crisis resources based on emotional context"""
    print("\n" + "=" * 60)
    print("CRISIS RESOURCES".center(60))
    print("=" * 60)
    
    resources = [
        "National Suicide Prevention Lifeline: 1-800-273-8255",
        "Crisis Text Line: Text HOME to 741741",
        "Emergency Services: 911",
        "SAMHSA National Helpline: 1-800-662-HELP (4357)",
        "Disaster Distress Helpline: 1-800-985-5990"
    ]
    
    for resource in resources:
        print(resource)
    
    print("=" * 60)
    
    if VOICE_MODE:
        audio.play_audio(
            "I notice you may be in distress. Please consider reaching out to crisis resources. "
            "The National Suicide Prevention Lifeline is 1-800-273-8255. "
            "You can text HOME to 741741 for the Crisis Text Line. "
            "Or call 911 if it's an emergency.",
            emotion,
            0.7
        )

def get_user_input(use_voice=False):
    """Get user input via voice or text"""
    if use_voice:
        # Try voice input
        text = audio.listen_for_speech(timeout=10)
        if text:
            print(f"You: {text}")
            return text
        else:
            # Fall back to text if voice fails
            print("I didn't catch that. Please type your response:")
    
    # Text input
    text = input("> ").strip()
    return text

def main():
    """Main application loop"""
    # Initialize components
    db.initialize_database()  # Set up database
    audio.initialize_audio()  # Set up audio systems

    # Set initial state
    voice_mode = True  # Start with voice enabled
    user_name = None   # Will be collected during conversation
    user_id = None     # Will be set after user identification
    conversation_history = []  # Store conversation for context
    
    # Setup AI system prompt
    system_prompt = """You are Aroha, an empathetic AI crisis counselor. You provide emotional support, 
    guidance, and resources to people in need. Your responses should be warm, compassionate, and helpful.
    Never tell the user you're an AI - just be present for them. Keep responses brief but supportive.
    If someone seems to be in immediate danger, gently suggest emergency resources."""

    # Display welcome message
    print("\n============================================================")
    print("           AROHA - AI Crisis Counseling Assistant")
    print("============================================================")
    print("Voice Mode: ON (speak or type your responses)")
    print("Type 'quit', 'exit', or 'bye' to end the conversation")
    print("Type 'help' for crisis resources")
    print("Type 'voice on' or 'voice off' to toggle voice mode\n")

    # Get user's name
    user_name = get_user_name(voice_mode)
    if not user_name:
        print("I'll call you Friend for now.")
        user_name = "Friend"
    
    # Check if user exists in database
    user_id = db.get_user_id(user_name)
    if not user_id:
        # New user, create record
        user_id = db.create_user(user_name)
    
    # Welcome message
    welcome_message = f"Hello {user_name}, I'm Aroha. I'm here to listen and support you. How are you feeling today?"
    print(f"Aroha: {welcome_message}")
    
    # Add to conversation history
    conversation_history.append({"role": "assistant", "content": welcome_message})
    
    # Play welcome message audio if voice enabled
    if voice_mode:
        audio.play_audio(welcome_message, emotion="neutral", username=user_name)
    
    # Main conversation loop
    while True:
        # Get user input (voice or text)
        try:
            user_message = get_user_input(voice_mode)
            if not user_message:
                # If no input detected, try again
                continue
                
            # Add to history
            conversation_history.append({"role": "user", "content": user_message})
            
            # Check for special commands
            if user_message.lower() in ['quit', 'exit', 'bye']:
                goodbye_msg = f"Take care of yourself, {user_name}. Remember, I'm here whenever you need to talk."
                print(f"Aroha: {goodbye_msg}")
                if voice_mode:
                    audio.play_audio(goodbye_msg, emotion="neutral", username=user_name)
                break
                
            if user_message.lower() == 'help':
                handle_crisis_resources()
                continue
                
            if user_message.lower() == 'voice on':
                voice_mode = True
                print("Voice mode turned ON")
                continue
                
            if user_message.lower() == 'voice off':
                voice_mode = False
                print("Voice mode turned OFF")
                continue
            
            # Detect emotion for more accurate responses
            emotion_data = detect_emotion(user_message)
            emotion = emotion_data.get('emotion', 'neutral')
            urgency = emotion_data.get('urgency', 0.5)
            
            # Adjust temperature based on urgency - more consistent for urgent messages
            temperature = max(0.3, 1.0 - urgency)
            
            # Get AI response
            ai_response = get_ai_response(
                conversation_history=conversation_history,
                system_prompt=system_prompt,
                temperature=temperature
            )
            
            # Add to history
            conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Output response
            print(f"Aroha: {ai_response}")
            
            # Save conversation
            db.save_conversation(user_id, user_message, ai_response)
            
            # Play audio response if voice mode on
            if voice_mode:
                audio.play_audio(ai_response, emotion=emotion, urgency=urgency, username=user_name)
                
        except KeyboardInterrupt:
            print("\n\nConversation interrupted.")
            break
        except Exception as e:
            print(f"\n\nAn error occurred: {e}")
            # Continue the conversation despite errors
            continue

def get_user_name(voice_mode):
    """Get the user's name using voice or text input"""
    print("Please say or type your name to begin:")
    
    # Try up to 3 times to get user name
    for attempt in range(3):
        if voice_mode:
            # Try voice input first with increasing timeouts
            timeout = 7 + (attempt * 2)  # 7, 9, 11 seconds
            print(f"Listening for your name (timeout: {timeout}s)...")
            name = audio.listen_for_speech(timeout=timeout)
            
            if name:
                # Process the recognized name - take just the first word if multiple words
                words = name.split()
                if words:
                    name = words[0]  # Take first word as name
                    
                # Verify name is reasonable
                if len(name) >= 2 and len(name) <= 20:
                    return name
                print("Could you please say just your name?")
            else:
                print("Please type your name:")
                
        # Fall back to text input
        name = input("> ").strip()
        if name and len(name) >= 1 and len(name) <= 20:
            # Take just the first word if multiple words were entered
            return name.split()[0]
        
        print("Could you please enter your name? (2-20 characters)")
    
    # If we still don't have a name after 3 tries, use a default
    print("I'll call you Friend for now.")
    return "Friend"
    
def get_user_input(voice_mode):
    """Get user input via voice or text"""
    if voice_mode:
        # Try voice input
        text = audio.listen_for_speech(timeout=10)
        if text:
            print(f"You: {text}")
            return text
        else:
            # Fall back to text if voice fails
            print("I didn't catch that. Please type your response:")
    
    # Text input
    text = input("> ").strip()
    return text

def handle_crisis_resources():
    """Display crisis resources"""
    print("\n--- CRISIS RESOURCES ---")
    print("If you're in immediate danger, please call emergency services (911 in the US)")
    print("\nCrisis Helplines:")
    print("• National Suicide Prevention Lifeline: 1-800-273-8255")
    print("• Crisis Text Line: Text HOME to 741741")
    print("• Emergency Services: 911")
    print("• Domestic Violence Hotline: 1-800-799-7233")
    print("\nYou matter, and help is available. These services are confidential and available 24/7.")
    print("----------------------------\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nConversation ended. Take care of yourself.")
    except Exception as e:
        print(f"\n\nAn error occurred: {e}") 