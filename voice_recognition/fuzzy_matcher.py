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
    """Compute a fuzzy score between 0.0 and 1.0 for a stock item.
    
    Uses WHOLE SENTENCE analysis, not word-by-word matching.
    Prioritizes overall semantic similarity over exact token matches.
    """

    phrase_lower = search_phrase.lower()
    item_label = f"{sku} {item_name}".strip().lower()
    item_name_lower = item_name.lower()

    # PRIMARY: Whole-phrase fuzzy matching using multiple algorithms
    primary_scores: List[float] = []
    
    # Direct fuzzy matching against item name
    primary_scores.append(fuzz.token_set_ratio(phrase_lower, item_name_lower) / 100.0)
    primary_scores.append(fuzz.token_sort_ratio(phrase_lower, item_name_lower) / 100.0)
    primary_scores.append(fuzz.partial_ratio(phrase_lower, item_name_lower) / 100.0)
    primary_scores.append(fuzz.WRatio(phrase_lower, item_name_lower) / 100.0)

    # CRITICAL: Check for exact phrase matches ANYWHERE in sentence
    semantic_boost = 1.0
    exact_phrase_match = False
    best_match_length = 0
    
    phrase_tokens = phrase_lower.split()
    
    # Check ALL possible 2-word and 3-word combinations
    # This handles ANY word order: "arnie full circle" OR "full circle arnie"
    for i in range(len(phrase_tokens)):
        # Check 3-word phrases first (longer = better)
        if i + 2 < len(phrase_tokens):
            three_word = f"{phrase_tokens[i]} {phrase_tokens[i+1]} {phrase_tokens[i+2]}"
            if three_word in item_name_lower and len(three_word) > 8:
                semantic_boost = 5.0  # HUGE boost for 3-word match
                exact_phrase_match = True
                best_match_length = 3
                logger.info(
                    f"✅ 3-WORD MATCH: '{three_word}' in '{item_name}'"
                )
                break
        
        # Check 2-word phrases
        if i + 1 < len(phrase_tokens) and best_match_length < 2:
            two_word = f"{phrase_tokens[i]} {phrase_tokens[i+1]}"
            if two_word in item_name_lower and len(two_word) > 5:
                semantic_boost = 3.5  # BIG boost for 2-word match
                exact_phrase_match = True
                best_match_length = 2
                logger.info(
                    f"✅ 2-WORD MATCH: '{two_word}' in '{item_name}'"
                )
    
    # Modifier alignment (zero, blonde, etc.)
    modifier_factor = 1.0
    key_modifiers = ["zero", "diet", "light", "lite", "free", "blonde", "panther", "fuascal"]
    
    phrase_has_modifier = any(mod in phrase_lower for mod in key_modifiers)
    item_has_modifier = any(mod in item_name_lower for mod in key_modifiers)
    
    if phrase_has_modifier and item_has_modifier:
        # Check if SAME modifier
        for mod in key_modifiers:
            if mod in phrase_lower and mod in item_name_lower:
                modifier_factor = 1.3
                break
        # Different modifiers = penalty
        if modifier_factor == 1.0:
            modifier_factor = 0.15
    elif phrase_has_modifier and not item_has_modifier:
        modifier_factor = 0.15  # Said modifier but item doesn't have it
    elif not phrase_has_modifier and item_has_modifier:
        modifier_factor = 0.7  # Item has modifier but not mentioned

    # Package type alignment
    package_factor = _package_alignment_score(phrase_lower, item_label)

    # FINAL SCORE: Average of primary scores with boosts applied
    base_score = sum(primary_scores) / len(primary_scores)
    final_score = base_score * semantic_boost * modifier_factor * package_factor
    
    return min(final_score, 1.0)  # Cap at 1.0


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
        "🔍 Search '%s' -> TOP 5 candidates:\n"
        "  1. %s (SKU: %s) - Score: %.3f\n"
        "  2. %s (SKU: %s) - Score: %.3f\n"
        "  3. %s (SKU: %s) - Score: %.3f\n"
        "  4. %s (SKU: %s) - Score: %.3f\n"
        "  5. %s (SKU: %s) - Score: %.3f",
        search_phrase,
        candidates[0]["name"] if len(candidates) > 0 else "N/A",
        candidates[0]["sku"] if len(candidates) > 0 else "N/A",
        candidates[0]["score"] if len(candidates) > 0 else 0,
        candidates[1]["name"] if len(candidates) > 1 else "N/A",
        candidates[1]["sku"] if len(candidates) > 1 else "N/A",
        candidates[1]["score"] if len(candidates) > 1 else 0,
        candidates[2]["name"] if len(candidates) > 2 else "N/A",
        candidates[2]["sku"] if len(candidates) > 2 else "N/A",
        candidates[2]["score"] if len(candidates) > 2 else 0,
        candidates[3]["name"] if len(candidates) > 3 else "N/A",
        candidates[3]["sku"] if len(candidates) > 3 else "N/A",
        candidates[3]["score"] if len(candidates) > 3 else 0,
        candidates[4]["name"] if len(candidates) > 4 else "N/A",
        candidates[4]["sku"] if len(candidates) > 4 else "N/A",
        candidates[4]["score"] if len(candidates) > 4 else 0,
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
