# app/core/whisper.py

import logging
import openai
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# FIX (weak point #18): Whisper's ISO-639-1 language codes for the
# languages this app cares about. `preferred_lang` in user_profile is stored
# as a human-readable name ("Bengali"/"English"/"Hindi") -- this maps it to
# the code Whisper expects when we already know it, instead of always
# passing language=None (pure auto-detect) even for a returning user.
_LANGUAGE_NAME_TO_CODE = {
    "bengali": "bn",
    "english": "en",
    "hindi": "hi",
}


def transcribe_audio(file_path: str, known_language: Optional[str] = None) -> str:
    
    client = openai.OpenAI()

    language_code = None
    if known_language:
        language_code = _LANGUAGE_NAME_TO_CODE.get(known_language.strip().lower())

    try:
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language_code,  # None -> auto-detect, otherwise forced
            )
            return transcript.text
    except Exception as e:
        logger.error(f"Whisper Transcription Error: {e}")
        # Return an empty string so the supervisor knows the audio was unreadable
        return ""
