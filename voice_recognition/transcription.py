"""
Audio Transcription Service using OpenAI Speech-to-Text
Modern API for gpt-4o-transcribe
"""
import io
import logging
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def transcribe_audio(audio_file):
    """
    Transcribe audio using latest OpenAI STT (gpt-4o-transcribe).

    Args:
        audio_file: Django UploadedFile object (InMemoryUploadedFile or TemporaryUploadedFile)

    Returns:
        str: transcription text
    """

    try:
        # Always rewind
        audio_file.seek(0)

        # ✅ Convert Django UploadedFile -> bytes -> BytesIO
        audio_bytes = audio_file.read()
        file_obj = io.BytesIO(audio_bytes)
        # Give it a name so OpenAI can infer extension if needed
        file_obj.name = getattr(audio_file, "name", "audio.webm")

        response = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=file_obj,   # <-- now it's a proper file-like object
            language="en",
        )

        text = (
            getattr(response, "text", None)
            or getattr(response, "output_text", None)
            or ""
        ).strip()

        logger.info(f"🎤 STT transcription: {text!r}")

        if not text:
            raise Exception("Transcription returned empty string")

        return text

    except Exception as e:
        logger.error(f"❌ Speech-to-text failed: {e}")
        raise Exception(f"Audio transcription failed: {e}")
