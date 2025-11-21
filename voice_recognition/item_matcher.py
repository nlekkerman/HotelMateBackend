"""Compatibility wrapper for the legacy item_matcher import path."""

from .fuzzy_matcher import (
    expand_search_tokens,
    find_best_match,
    find_best_match_in_stocktake,
    normalize_phrase,
    score_item,
)

__all__ = [
    "normalize_phrase",
    "expand_search_tokens",
    "score_item",
    "find_best_match",
    "find_best_match_in_stocktake",
]
