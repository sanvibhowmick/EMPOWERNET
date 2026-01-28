import openai
import os
from dotenv import load_dotenv

# Load environment variables for the API key
load_dotenv()

def transcribe_audio(file_path: str) -> str:
    """
    Transcribes audio voice notes (OGG, MP3, etc.) into text 
    to be processed by the VESTA Supervisor agent.
    """
    client = openai.OpenAI()
    
    try:
        # Open the audio file from the temporary storage
        with open(file_path, "rb") as audio_file:
            # Transcribe using the whisper-1 model
            # This model is robust for various Indian accents and dialects
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                
                language=None
            )
            return transcript.text
    except Exception as e:
        print(f"Whisper Transcription Error: {e}")
        # Return an empty string so the supervisor knows the audio was unreadable
        return ""