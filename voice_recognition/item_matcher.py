"""
Fuzzy Item Matching for Voice Commands
Uses rapidfuzz for intelligent matching of partial/misspelled product names
"""
from rapidfuzz import fuzz, process
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


# Brand synonyms for common misspellings/variations
BRAND_SYNONYMS = {
    "budweiser": ["bud", "budwiser", "budweisser", "bude", "boodviser", "budwieser"],
    "bulmers": ["bulmer", "bulmars", "bulmr"],
    "smithwicks": ["smithix", "smidix", "smithicks", "smithwix", "smiddicks"],
    "heineken": ["heiny", "heinie", "heinikn", "heine", "heinkin"],
    "peroni": ["perony", "perori", "perni", "peroni"],
    "coors": ["course", "cores", "cooors", "cors"],
    "guinness": ["guiness", "ginnes", "ginis", "guinnes"],
    "moretti": ["morety", "moreti", "moretti"],
    "corona": ["carona", "coronna"],
    "carlsberg": ["carlsbrg", "carlsburg"],
    "kbc": ["k b c", "killarney brewing", "kbc brewery"],
}

# Packaging type synonyms
PACKAGE_SYNONYMS = {
    "bottle": ["bot", "botle", "botl", "bott", "btl", "bottl"],
    "draught": ["draft", "tap", "on tap", "keg", "kegs"],
    "pint": ["pt", "pnt"],
    "can": ["cn", "tin"],
}


def expand_search_tokens(phrase: str) -> List[str]:
    """
    Expand a search phrase with synonyms
    
    Example:
        "bud botle" -> ["bud", "budweiser", "botle", "bottle"]
    """
    tokens = phrase.lower().split()
    expanded = set(tokens)
    
    for token in tokens:
        # Add brand synonyms
        for brand, variants in BRAND_SYNONYMS.items():
            if token in variants or token == brand:
                expanded.add(brand)
                expanded.update(variants)
        
        # Add package synonyms
        for package, variants in PACKAGE_SYNONYMS.items():
            if token in variants or token == package:
                expanded.add(package)
                expanded.update(variants)
    
    return list(expanded)


def score_item(item_name: str, search_phrase: str) -> float:
    """
    Score how well an item matches a search phrase
    
    Uses multiple fuzzy matching strategies:
    1. Token set ratio (ignores order, duplicates)
    2. Partial ratio (substring matching)
    3. Simple ratio (overall similarity)
    4. Synonym expansion
    5. Package type matching (draught vs bottle)
    
    Returns: Score from 0.0 to 1.0
    """
    item_lower = item_name.lower()
    phrase_lower = search_phrase.lower()
    
    # Get expanded tokens with synonyms
    search_tokens = expand_search_tokens(phrase_lower)
    
    scores = []
    
    # 1. Direct fuzzy matching
    scores.append(fuzz.token_set_ratio(phrase_lower, item_lower) / 100.0)
    scores.append(fuzz.partial_ratio(phrase_lower, item_lower) / 100.0)
    scores.append(fuzz.ratio(phrase_lower, item_lower) / 100.0)
    
    # 2. Match expanded tokens against item name
    for token in search_tokens:
        if len(token) >= 3:  # Skip very short tokens
            scores.append(fuzz.partial_ratio(token, item_lower) / 100.0)
    
    # 3. SKU partial match bonus (if phrase looks like SKU)
    if any(c.isdigit() for c in phrase_lower):
        # Phrase contains numbers, might be SKU
        scores.append(fuzz.partial_ratio(phrase_lower, item_lower) / 100.0)
    
    # 4. Package type penalty/bonus
    # If search mentions "draught/draft/keg" but item has "bottle", penalize
    # If search mentions "bottle" but item has "draught/keg", penalize
    # Use all synonyms from PACKAGE_SYNONYMS
    draught_words = ["draught"] + PACKAGE_SYNONYMS["draught"]
    bottle_words = ["bottle"] + PACKAGE_SYNONYMS["bottle"]
    
    search_has_draught = any(word in phrase_lower for word in draught_words)
    search_has_bottle = any(word in phrase_lower for word in bottle_words)
    item_has_draught = any(word in item_lower for word in draught_words)
    item_has_bottle = any(word in item_lower for word in bottle_words)
    
    # Apply penalty if package types conflict
    if search_has_draught and item_has_bottle:
        # User said "draft" but item is "bottle" - penalize heavily
        scores = [s * 0.3 for s in scores]
    elif search_has_bottle and item_has_draught:
        # User said "bottle" but item is "draught" - penalize heavily
        scores = [s * 0.3 for s in scores]
    elif search_has_draught and item_has_draught:
        # Both mention draught - boost score
        scores.append(0.95)
    elif search_has_bottle and item_has_bottle:
        # Both mention bottle - boost score
        scores.append(0.95)
    
    # Return weighted average of top 3 scores
    scores.sort(reverse=True)
    top_scores = scores[:3]
    
    return sum(top_scores) / len(top_scores) if top_scores else 0.0


def find_best_match(
    search_phrase: str,
    items: List,
    min_score: float = 0.55
) -> Optional[Dict]:
    """
    Find the best matching item from a list
    
    Args:
        search_phrase: The phrase to search for (e.g., "bud botle")
        items: List of StockItem objects
        min_score: Minimum confidence score (0.0-1.0)
    
    Returns:
        Dict with match info or None if no good match
    """
    if not search_phrase or not items:
        return None
    
    best_item = None
    best_score = 0.0
    
    for item in items:
        score = score_item(item.name, search_phrase)
        
        # Bonus for SKU match
        if item.sku.lower() in search_phrase.lower():
            score = max(score, 0.9)
        
        if score > best_score:
            best_score = score
            best_item = item
    
    if best_item and best_score >= min_score:
        logger.info(
            f"✓ Matched '{search_phrase}' to '{best_item.name}' "
            f"(SKU: {best_item.sku}, confidence: {best_score:.2f})"
        )
        return {
            'item': best_item,
            'confidence': best_score,
            'search_phrase': search_phrase
        }
    
    logger.warning(
        f"✗ No match for '{search_phrase}' "
        f"(best: {best_item.name if best_item else 'none'}, "
        f"score: {best_score:.2f}, threshold: {min_score})"
    )
    return None


def find_best_match_in_stocktake(
    search_phrase: str,
    stocktake,
    min_score: float = 0.55
) -> Optional[Dict]:
    """
    Find best match among items in a specific stocktake
    
    This limits the search to only items that are part of the stocktake,
    improving accuracy and speed.
    """
    # Get all items in this stocktake
    from stock_tracker.models import StockItem
    
    stocktake_item_ids = stocktake.lines.values_list('item_id', flat=True)
    items = StockItem.objects.filter(
        id__in=stocktake_item_ids,
        active=True
    )
    
    return find_best_match(search_phrase, items, min_score)
