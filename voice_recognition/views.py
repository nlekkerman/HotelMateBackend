"""Backwards-compatible import for voice command API views."""

from .views_voice import VoiceCommandConfirmView, VoiceCommandView

__all__ = ["VoiceCommandView", "VoiceCommandConfirmView"]
