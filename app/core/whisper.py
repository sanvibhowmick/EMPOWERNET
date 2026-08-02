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
    """
    Transcribes audio voice notes (OGG, MP3, etc.) into text for the
    EmpowerNet Supervisor swarm to process.

    FIX (weak point #10, docstring hygiene): this previously referenced
    "the VESTA Supervisor agent" -- a leftover from an earlier/different
    project name that was never updated.

    FIX (weak point #18): previously always called with `language=None`
    (full auto-detect) even when the user's preferred language is already
    known from their saved profile. When `known_language` is provided
    ("Bengali"/"English"/"Hindi"), we now pass the matching Whisper language
    code, which both removes ambiguity for code-switched speech and
    generally improves accuracy versus blind auto-detection. If it's
    unknown (e.g. a brand-new user), we still fall back to auto-detect.
    """
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
