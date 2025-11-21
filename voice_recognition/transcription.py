"""
Audio Transcription Service using OpenAI STT (gpt-4o-mini-transcribe)

Responsible ONLY for:
    - Taking a Django UploadedFile (in-memory or temp file)
    - Converting it into a format OpenAI accepts
    - Calling STT model
    - Returning plain transcription text

Used by: voice_command_service.py
"""

import logging
import os
import tempfile
from typing import Optional

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

# Single shared client for the process
client = OpenAI(api_key=getattr(settings, "OPENAI_API_KEY", None))


class TranscriptionError(Exception):
    """Custom error for STT failures."""


def _guess_suffix(uploaded_file) -> str:
    """Return best-effort suffix to help the API infer content type."""
    if getattr(uploaded_file, "name", None) and "." in uploaded_file.name:
        return "." + uploaded_file.name.rsplit(".", 1)[-1]
    content_type = getattr(uploaded_file, "content_type", "")
    if content_type:
        mapping = {
            "audio/webm": ".webm",
            "audio/mp4": ".mp4",
            "audio/mpeg": ".mp3",
            "audio/ogg": ".ogg",
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
        }
        return mapping.get(content_type, ".webm")
    return ".webm"


def _save_uploaded_to_temp(uploaded_file) -> str:
    """
    Save Django UploadedFile to a NamedTemporaryFile and return its path.

    OpenAI Python v1 prefers a real file object (open(path, 'rb')),
    and sometimes doesn't like InMemoryUploadedFile directly.
    """

    suffix = _guess_suffix(uploaded_file)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)
        tmp.flush()
    finally:
        tmp.close()
    return tmp.name


def _cleanup_temp(path: Optional[str]) -> None:
    """Best-effort cleanup of temp files."""

    if not path:
        return
    try:
        os.unlink(path)
    except OSError:
        logger.debug("Temp file already removed: %s", path)


def transcribe_audio(audio_file) -> str:
    """
    Transcribe audio using latest OpenAI STT (gpt-4o-mini-transcribe).

    Args:
        audio_file: Django UploadedFile (in-memory or temp)

    Returns:
        str: transcription text

    Raises:
        TranscriptionError: if anything goes wrong
    """

    if client is None or not getattr(settings, "OPENAI_API_KEY", None):
        logger.error("❌ OPENAI_API_KEY missing in settings")
        raise TranscriptionError("OpenAI API key not configured")

    temp_path = None
    try:
        try:
            audio_file.seek(0)
        except Exception:
            logger.debug("Uploaded file does not support seek")

        temp_path = _save_uploaded_to_temp(audio_file)
        logger.info(
            "🎧 Saved uploaded audio to temp file: %s (name=%s, size=%s bytes)",
            temp_path,
            getattr(audio_file, "name", "<unknown>"),
            getattr(audio_file, "size", "<unknown>"),
        )

        with open(temp_path, "rb") as file_handle:
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=file_handle,
                language="en",
            )

        text = (
            getattr(response, "text", None)
            or getattr(response, "output_text", None)
            or ""
        ).strip()

        logger.info("🎤 Transcription result: %r", text)

        if not text:
            raise TranscriptionError("Transcription returned empty text")

        return text

    except TranscriptionError:
        raise
    except Exception as exc:
        logger.error("❌ Speech-to-text failed: %s", exc, exc_info=True)
        raise TranscriptionError(f"Audio transcription failed: {exc}")
    finally:
        _cleanup_temp(temp_path)
