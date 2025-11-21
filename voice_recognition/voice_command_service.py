"""High-level orchestration for voice command processing."""

import logging
from typing import Dict, Optional

from django.db.models import QuerySet

from .command_parser import parse_voice_command
from .fuzzy_matcher import find_best_match, find_best_match_in_stocktake
from .llm_reasoner import LLMUnavailable, pick_best_match, repair_transcription
from .transcription import TranscriptionError, transcribe_audio
from .unit_interpreter import interpret_messy_unit_phrase

logger = logging.getLogger(__name__)


class VoiceCommandError(Exception):
    """Raised when the voice command pipeline cannot produce a command."""


def _apply_unit_insights(parsed: Dict, unit_details: Dict) -> None:
    """Merge unit interpretation data into the parsed command."""

    if not parsed:
        return

    if "full_units" not in parsed or parsed.get("full_units") is None:
        if unit_details.get("full_units") is not None:
            parsed["full_units"] = unit_details["full_units"]
    if "partial_units" not in parsed or parsed.get("partial_units") is None:
        if unit_details.get("partial_units") is not None:
            parsed["partial_units"] = unit_details["partial_units"]
    if (
        parsed.get("value") is None
        and unit_details.get("total_value") is not None
    ):
        parsed["value"] = unit_details["total_value"]


def _match_items(
    item_identifier: str,
    *,
    stocktake=None,
    items: Optional[QuerySet] = None,
    min_score: float = 0.55,
    use_llm: bool = False,
    transcription: Optional[str] = None,
    domain_hint: Optional[str] = None,
) -> Optional[Dict]:
    """Match an item either within a stocktake or an arbitrary queryset."""

    match_result: Optional[Dict]
    if stocktake is not None:
        match_result = find_best_match_in_stocktake(
            item_identifier,
            stocktake,
            min_score=min_score,
        )
    elif items is not None:
        match_result = find_best_match(
            item_identifier,
            items,
            min_score=min_score,
        )
    else:
        match_result = None

    if match_result or not use_llm:
        return match_result

    if not transcription:
        return None

    candidate_names = [
        i.name for i in (items or [])
    ] if items is not None else []

    if stocktake is not None:
        stock_items = stocktake.lines.select_related("item").values_list(
            "item__name",
            flat=True,
        )
        candidate_names = list(stock_items)

    try:
        suggestion = pick_best_match(
            transcription,
            candidate_names,
            domain_hint=domain_hint,
        )
    except LLMUnavailable:
        suggestion = None

    if not suggestion:
        return None

    logger.info("LLM suggested fallback match '%s'", suggestion)

    if stocktake is not None:
        for line in stocktake.lines.select_related("item").all():
            if line.item.name == suggestion:
                return {
                    "item": line.item,
                    "confidence": 0.51,
                    "search_phrase": transcription,
                    "source": "llm",
                }
    elif items is not None:
        for item in items:
            if item.name == suggestion:
                return {
                    "item": item,
                    "confidence": 0.51,
                    "search_phrase": transcription,
                    "source": "llm",
                }
    return None


def process_audio_command(
    audio_file,
    *,
    stocktake=None,
    items: Optional[QuerySet] = None,
    min_match_score: float = 0.55,
    use_llm: bool = False,
    domain_hint: Optional[str] = None,
) -> Dict:
    """Run the full voice command pipeline and return structured output."""

    try:
        transcription = transcribe_audio(audio_file)
    except TranscriptionError as exc:
        raise VoiceCommandError(str(exc)) from exc

    cleaned_text = transcription
    if use_llm:
        try:
            cleaned_text = repair_transcription(
                transcription,
                domain_hint=domain_hint,
            )
        except LLMUnavailable:
            cleaned_text = transcription

    try:
        parsed_command = parse_voice_command(cleaned_text)
    except ValueError as exc:
        if use_llm and cleaned_text == transcription:
            try:
                repaired = repair_transcription(
                    cleaned_text,
                    domain_hint=domain_hint,
                )
            except LLMUnavailable:
                repaired = cleaned_text
            if repaired != cleaned_text:
                try:
                    parsed_command = parse_voice_command(repaired)
                    cleaned_text = repaired
                except ValueError as inner_exc:
                    raise VoiceCommandError(str(inner_exc)) from inner_exc
            else:
                raise VoiceCommandError(str(exc)) from exc
        else:
            raise VoiceCommandError(str(exc)) from exc

    unit_details = interpret_messy_unit_phrase(cleaned_text)
    _apply_unit_insights(parsed_command, unit_details)

    match_result = _match_items(
        parsed_command.get("item_identifier"),
        stocktake=stocktake,
        items=items,
        min_score=min_match_score,
        use_llm=use_llm,
        transcription=cleaned_text,
        domain_hint=domain_hint,
    )

    return {
        "transcription": transcription,
        "cleaned_transcription": cleaned_text,
        "command": parsed_command,
        "unit_details": unit_details,
        "match": match_result,
    }


__all__ = ["process_audio_command", "VoiceCommandError"]
