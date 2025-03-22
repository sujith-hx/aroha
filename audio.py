"""
Audio module for natural voice interactions in Aroha
"""
import io
import os
import time
import random
import pygame
import speech_recognition as sr
from elevenlabs import generate, set_api_key, voices
from elevenlabs.api import Voice
from dotenv import load_dotenv

# Initialize pygame for audio playback
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()

# Load environment variables
load_dotenv()

# Get API keys
ELEVENLABS_API_KEYS = [
    os.getenv("ELEVENLABS_API_KEY_1"),
    os.getenv("ELEVENLABS_API_KEY_2"),
    os.getenv("ELEVENLABS_API_KEY_3", "")  # Optional backup keys
]

# Filter out empty keys
ELEVENLABS_API_KEYS = [key for key in ELEVENLABS_API_KEYS if key]

# Default voice ID - using Rachel (female voice)
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice (female)

# Alternative female voices to try if the main one fails
FEMALE_VOICE_IDS = [
    "21m00Tcm4TlvDq8ikWAM",  # Rachel
    "EXAVITQu4vr4xnSDxMaL",  # Bella
    "MF3mGyEYCl7XYWbV9V6O",  # Elli
    "D38z5RcWu1voky8WS1ja"   # Grace
]

# Global variables
current_key_index = 0
recognizer = sr.Recognizer()
ffmpeg_available = False  # Track if ffmpeg is available

def check_ffmpeg():
    """Check if ffmpeg is available in the system"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        if result.returncode == 0:
            print("ffmpeg detected: Audio conversion capabilities available")
            return True
        else:
            print("ffmpeg not found: Audio conversion will be limited")
            return False
    except Exception as e:
        print(f"Error checking for ffmpeg: {e}")
        print("Audio conversion capabilities will be limited")
        return False

def set_eleven_api_key():
    """Set the ElevenLabs API key from our list of keys"""
    global current_key_index
    
    if not ELEVENLABS_API_KEYS:
        raise ValueError("No ElevenLabs API keys found. Please add at least one key to .env file.")
    
    # Try to use the current key
    try:
        set_api_key(ELEVENLABS_API_KEYS[current_key_index])
        return True
    except Exception as e:
        print(f"Error with ElevenLabs key {current_key_index + 1}: {e}")
        
        # Try other keys if available
        for i in range(len(ELEVENLABS_API_KEYS)):
            if i != current_key_index:
                try:
                    current_key_index = i
                    set_api_key(ELEVENLABS_API_KEYS[i])
                    return True
                except:
                    continue
        
        # If we get here, all keys failed
        raise ValueError("All ElevenLabs API keys failed. Please check your API keys.")

def _adjust_voice_settings(emotion, urgency):
    """
    Adjust voice settings based on emotional context
    Returns stability, similarity_boost, speaking_rate
    """
    if emotion == "crisis" or emotion == "urgent":
        # Calm, steady, reassuring for crisis
        return 0.8, 0.7, 0.9  # High stability, medium similarity, slightly slower
    elif emotion == "sad":
        # Warm, empathetic for sadness
        return 0.7, 0.8, 0.85  # Medium stability, higher similarity, slower
    elif emotion == "anxious":
        # Calm, grounding for anxiety
        return 0.9, 0.6, 0.95  # High stability, lower similarity, medium pace
    elif emotion == "angry":
        # Matching energy but not escalating
        return 0.6, 0.7, 1.0  # Lower stability, medium similarity, normal pace
    elif emotion == "tired":
        # Gentle, supportive for fatigue
        return 0.7, 0.7, 0.9  # Medium stability, medium similarity, slightly slower
    else:
        # Default - balanced, neutral
        return 0.7, 0.7, 1.0  # Balanced settings

def _add_speech_variations(text, emotion):
    """
    Add human-like speech variations like pauses, fillers
    based on detected emotion
    """
    # Simple replacements for human-like speech
    text = text.replace("I am ", "I'm ")
    text = text.replace("you are ", "you're ")
    text = text.replace("cannot ", "can't ")
    text = text.replace("will not ", "won't ")
    
    # Add appropriate pauses based on emotion
    if emotion == "crisis" or emotion == "urgent":
        # Add calming pauses for crisis
        text = text.replace(". ", "... ")
        text = text.replace("? ", "?... ")
    elif emotion == "sad":
        # Add empathetic pauses for sadness
        text = text.replace(". ", "... ")
    elif emotion == "anxious":
        # Add grounding pauses for anxiety
        text = text.replace(". ", "... ")
    
    return text

def play_audio(text, emotion="neutral", urgency=0.5, voice_id=None, username="user"):
    """
    Generate and play audio response based on text without saving files
    """
    if not ELEVENLABS_API_KEYS:
        print("No ElevenLabs API keys available. Skipping audio generation.")
        return None
    
    try:
        # Set the API key
        set_eleven_api_key()
        
        # Get the voice settings based on emotion
        stability, similarity_boost, speaking_rate = _adjust_voice_settings(emotion, urgency)
        
        # Add variations to the text for more natural speech
        text = _add_speech_variations(text, emotion)
        
        # Use a specified voice or default
        if not voice_id:
            voice_id = DEFAULT_VOICE_ID
            
        # Print info about the generation
        print(f"Generating audio for emotional context: {emotion}")
        
        # Generate the audio - for elevenlabs v0.2.27 we don't pass stability directly
        audio_data = generate(
            text=text,
            voice=voice_id,
            model="eleven_monolingual_v1"
        )
        
        # Create a temporary file in memory
        temp_file = io.BytesIO(audio_data)
        
        # Load and play the audio with pygame directly from memory
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        # Wait for audio to finish playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        return True
        
    except Exception as e:
        print(f"Error with audio: {e}")
        # Try an alternative voice if the current one failed
        if voice_id not in FEMALE_VOICE_IDS:
            for alt_voice in FEMALE_VOICE_IDS:
                if alt_voice != voice_id:
                    try:
                        print(f"Trying alternative voice: {alt_voice}")
                        return play_audio(text, emotion, urgency, alt_voice, username)
                    except:
                        continue
        return None

def listen_for_speech(timeout=10, from_file=None):
    """
    Listen for speech input and convert to text with extended timeout
    """
    try:
        # Use microphone for input
        with sr.Microphone() as source:
            print("Listening... (speak clearly)")
            # Adjust for ambient noise with longer duration
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            try:
                # Increase timeout for better chance of capturing speech
                print("Recording... (speak now)")
                audio_data = recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
                print("Processing speech...")
                
                # Try multiple recognition services for better results
                text = None
                try:
                    # Try Google first (most reliable)
                    text = recognizer.recognize_google(audio_data, language="en-US").strip()
                except:
                    try:
                        # Fall back to Sphinx (works offline)
                        text = recognizer.recognize_sphinx(audio_data).strip()
                    except:
                        # If both fail, report error
                        raise sr.UnknownValueError("Speech not recognized by any service")
                
                if text:
                    print(f"Recognized: {text}")
                    return text
                    
            except sr.WaitTimeoutError:
                print("No speech detected - please try again")
                return None
            except sr.UnknownValueError:
                print("Could not understand - please speak more clearly")
                return None
    except Exception as e:
        print(f"Speech recognition error: {e}")
        return None

def initialize_audio():
    """Initialize audio components and verify they work"""
    global ffmpeg_available
    
    print("Initializing audio components...")
    
    # Check for API keys
    if not ELEVENLABS_API_KEYS:
        print("Warning: No ElevenLabs API keys found. Voice output will be disabled.")
        return False
        
    # Validate API key and voice ID
    try:
        set_eleven_api_key()
        print(f"Text-to-speech initialized with voice {DEFAULT_VOICE_ID}")
    except Exception as e:
        print(f"Error initializing text-to-speech: {e}")
        return False
    
    # Check for ffmpeg
    ffmpeg_available = check_ffmpeg()
    
    # Initialize speech recognition
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Speech recognition initialized successfully")
    except Exception as e:
        print(f"Error initializing speech recognition: {e}")
        # Don't fail completely, we can still use text input
    
    return True 