"""Fuzzy item matching utilities for voice commands."""

import logging
from typing import Dict, Iterable, List, Optional

from rapidfuzz import fuzz

from .brand_synonyms import (
    BRAND_SYNONYMS,
    FILLER_WORDS,
    PACKAGE_SYNONYMS,
    QUANTITY_WORDS,
)

logger = logging.getLogger(__name__)


def normalize_phrase(raw: str) -> str:
    """Lowercase, drop filler words, and normalise quantity words."""

    tokens = raw.lower().split()
    normalized: List[str] = []

    for token in tokens:
        if token in FILLER_WORDS:
            continue
        if token in QUANTITY_WORDS:
            normalized.append(str(QUANTITY_WORDS[token]))
        else:
            normalized.append(token)

    return " ".join(normalized)


def expand_search_tokens(phrase: str) -> List[str]:
    """Expand a phrase with brand and packaging synonyms."""

    phrase_lower = phrase.lower()
    tokens = phrase_lower.split()
    expanded = set(tokens)

    for brand, variants in BRAND_SYNONYMS.items():
        if brand in phrase_lower:
            expanded.add(brand)
        for variant in variants:
            if variant in phrase_lower:
                expanded.add(brand)
                expanded.update(variant.split())

    for token in tokens:
        for brand, variants in BRAND_SYNONYMS.items():
            if token == brand or token in variants:
                expanded.add(brand)
                expanded.update(variants)
        for package, variants in PACKAGE_SYNONYMS.items():
            if token == package or token in variants:
                expanded.add(package)
                expanded.update(variants)

    return list(expanded)


def _package_alignment_score(phrase_lower: str, item_label: str) -> float:
    """Return a boost or penalty based on draught/bottle hints."""

    draught_words = ["draught"] + PACKAGE_SYNONYMS.get("draught", [])
    bottle_words = ["bottle"] + PACKAGE_SYNONYMS.get("bottle", [])

    search_has_draught = any(word in phrase_lower for word in draught_words)
    search_has_bottle = any(word in phrase_lower for word in bottle_words)
    item_has_draught = any(word in item_label for word in draught_words)
    item_has_bottle = any(word in item_label for word in bottle_words)

    # Strong penalty for package type mismatch
    if search_has_draught and item_has_bottle:
        return 0.1
    if search_has_bottle and item_has_draught:
        return 0.1
    # Strong boost for package type match
    if search_has_draught and item_has_draught:
        return 1.2
    if search_has_bottle and item_has_bottle:
        return 1.2
    return 1.0


def score_item(item_name: str, sku: str, search_phrase: str) -> float:
    """Compute a fuzzy score between 0.0 and 1.0 for a stock item."""

    phrase_lower = search_phrase.lower()
    item_label = f"{sku} {item_name}".strip().lower()

    scores: List[float] = []
    scores.append(fuzz.token_set_ratio(phrase_lower, item_label) / 100.0)
    scores.append(fuzz.partial_ratio(phrase_lower, item_label) / 100.0)
    scores.append(fuzz.ratio(phrase_lower, item_label) / 100.0)

    for token in expand_search_tokens(phrase_lower):
        if len(token) >= 3:
            scores.append(fuzz.partial_ratio(token, item_label) / 100.0)

    # Check for modifier matches (zero, diet, etc.)
    modifier_boost = 1.0
    for modifier in ["zero", "diet", "light", "lite", "free"]:
        if modifier in phrase_lower and modifier in item_label:
            modifier_boost = 1.3
            break
        elif modifier in phrase_lower and modifier not in item_label:
            # Strong penalty if modifier is said but item doesn't have it
            modifier_boost = 0.2
            break
        elif modifier not in phrase_lower and modifier in item_label:
            # Slight penalty if item has modifier but user didn't say it
            modifier_boost = 0.8
            break

    package_factor = _package_alignment_score(phrase_lower, item_label)
    scores = [score * package_factor * modifier_boost for score in scores]

    scores.sort(reverse=True)
    top_scores = scores[:3]
    return sum(top_scores) / len(top_scores) if top_scores else 0.0


def find_best_match(
    search_phrase: str,
    items: Iterable,
    min_score: float = 0.55,
) -> Optional[Dict]:
    """Find the highest scoring item from an iterable of StockItem objects."""

    if not search_phrase:
        return None

    items_list = list(items)
    if not items_list:
        return None

    normalized = normalize_phrase(search_phrase)
    candidates: List[Dict] = []

    for item in items_list:
        score = score_item(item.name, item.sku, normalized)
        candidates.append(
            {
                "item": item,
                "score": score,
                "name": item.name,
                "sku": item.sku,
            }
        )

    candidates.sort(key=lambda candidate: candidate["score"], reverse=True)

    logger.info(
        "Search '%s' -> top candidates: %s",
        search_phrase,
        candidates[:3],
    )

    best = candidates[0] if candidates else None
    if best and best["score"] >= min_score:
        logger.info(
            "Selected '%s' → '%s' (%s) with score %.2f",
            search_phrase,
            best["name"],
            best["sku"],
            best["score"],
        )
        return {
            "item": best["item"],
            "confidence": best["score"],
            "search_phrase": search_phrase,
        }

    if best:
        logger.warning(
            "No confident match for '%s' (best %.2f < %.2f)",
            search_phrase,
            best["score"],
            min_score,
        )
    else:
        logger.warning("No candidates produced for '%s'", search_phrase)
    return None


def find_best_match_in_stocktake(
    search_phrase: str,
    stocktake,
    min_score: float = 0.55,
) -> Optional[Dict]:
    """Search within the items that belong to a stocktake."""

    from stock_tracker.models import StockItem

    item_ids = stocktake.lines.values_list("item_id", flat=True)
    items = StockItem.objects.filter(id__in=item_ids, active=True)
    return find_best_match(search_phrase, items, min_score=min_score)


__all__ = [
    "normalize_phrase",
    "expand_search_tokens",
    "score_item",
    "find_best_match",
    "find_best_match_in_stocktake",
]
