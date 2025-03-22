# aroha
# Aroha Crisis Counselor

Aroha is a voice-enabled AI crisis counseling assistant that provides emotional support through natural conversation, combining AI from Groq with voice synthesis from ElevenLabs.

## Features

- **Voice Interaction**: Speak naturally with Aroha using your microphone
- **Emotional Intelligence**: Aroha detects your emotional state and adjusts responses
- **Crisis Resources**: Access emergency resources when needed
- **Privacy-Focused**: All data is stored only on your device

## Prerequisites

- Python 3.9+
- A microphone for voice interaction
- Internet connection
- Windows, macOS, or Linux

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/aroha.git
cd aroha
```

2. **Create a virtual environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

The application includes an `.env` file with all necessary API keys pre-configured and ready to use.

## Running Aroha

```bash
python main.py
```

## Using Aroha

### Voice Commands

- Speak into your microphone to interact
- Say "help" for crisis resources
- Say "voice on" or "voice off" to toggle voice mode
- Say "quit", "exit", or "bye" to end

### Text Commands

If voice isn't working, you can type your responses.

## Important Notes

- This is not a replacement for professional mental health support
- In case of emergency, please contact emergency services
- All conversation data is stored locally in an encrypted database

## Troubleshooting

- **Voice issues**: Ensure your microphone is working properly
- **Connection issues**: Check your internet connection

## Privacy

Conversations are stored locally in an encrypted database. No data is sent to external servers except for AI processing and voice synthesis.

## License

Open source under the MIT License.

---

Created with ❤️ to provide support when it's needed most


