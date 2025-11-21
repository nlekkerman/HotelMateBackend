"""Optional GPT-based helpers for ambiguous voice commands."""

import logging
from typing import Iterable, Optional

from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

_client = None
if getattr(settings, "OPENAI_API_KEY", None):
    _client = OpenAI(api_key=settings.OPENAI_API_KEY)


class LLMUnavailable(Exception):
    """Raised when the LLM cannot be used."""


def _require_client() -> OpenAI:
    if _client is None:
        raise LLMUnavailable("OpenAI client not configured")
    return _client


def repair_transcription(
    raw_text: str,
    domain_hint: Optional[str] = None,
) -> str:
    """Use GPT to clean obvious transcription mistakes."""

    text = raw_text.strip()
    if not text:
        return text

    try:
        client = _require_client()
    except LLMUnavailable:
        return text

    system_prompt = (
        "You clean transcription text for bar stocktake voice commands. "
        "Return a concise corrected phrase without extra narration."
    )

    user_prompt = (
        "Please correct any obvious speech-to-text errors in: " + text
    )
    if domain_hint:
        user_prompt += f". Context: {domain_hint}"

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_output_tokens=64,
        )
        cleaned = (
            response.output_text.strip()
            if getattr(response, "output_text", None)
            else text
        )
        return cleaned or text
    except Exception as exc:
        logger.warning("LLM repair failed: %s", exc)
        return text


def pick_best_match(
    transcription: str,
    options: Iterable[str],
    domain_hint: Optional[str] = None,
) -> Optional[str]:
    """Ask GPT to pick the closest option from a list of item names."""

    options_list = list(options)
    if not options_list:
        return None

    try:
        client = _require_client()
    except LLMUnavailable:
        return None

    system_prompt = (
        "You are ranking stock items for a hospitality stocktake. "
        "Return only the best matching item name from the provided list."
    )
    user_prompt = (
        "Transcription: "
        f"'{transcription}'. Candidates: {options_list}. "
        "Answer with the exact item string or 'none'."
    )
    if domain_hint:
        user_prompt += f" Context: {domain_hint}."

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_output_tokens=16,
        )
        choice = (
            response.output_text.strip().strip('"')
            if getattr(response, "output_text", None)
            else ""
        )
        if not choice or choice.lower() == "none":
            return None
        if choice not in options_list:
            logger.info("LLM suggested '%s' not in candidates", choice)
            return None
        return choice
    except Exception as exc:
        logger.warning("LLM disambiguation failed: %s", exc)
        return None


__all__ = ["repair_transcription", "pick_best_match", "LLMUnavailable"]
