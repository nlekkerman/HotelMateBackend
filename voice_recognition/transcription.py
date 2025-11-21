"""
Audio Transcription Service using OpenAI Speech-to-Text
Modern API for gpt-4o-transcribe
"""
import logging
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def transcribe_audio(audio_file):
    """
    Transcribe audio using latest OpenAI STT (gpt-4o-transcribe).

    Args:
        audio_file: Django UploadedFile object

    Returns:
        str: transcription text
    """

    try:
        audio_file.seek(0)

        response = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file,        # <-- pass raw file object, not tuple
            language="en",          # Helps for Irish accents too
        )

        text = (
            getattr(response, "text", None)
            or getattr(response, "output_text", None)
            or ""
        ).strip()

        logger.info(f"🎤 Whisper transcription: {text}")

        if not text:
            raise Exception("Transcription returned empty string")

        return text

    except Exception as e:
        logger.error(f"❌ Speech-to-text failed: {e}")
        raise Exception(f"Audio transcription failed: {e}")
