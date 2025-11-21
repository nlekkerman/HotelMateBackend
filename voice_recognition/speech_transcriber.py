"""Convenience wrapper exposing the audio transcription helper."""

from .transcription import TranscriptionError, transcribe_audio

__all__ = ["transcribe_audio", "TranscriptionError"]
