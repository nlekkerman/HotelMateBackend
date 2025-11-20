"""
Unit Interpreter for Voice Commands
Handles complex unit parsing from messy speech patterns
"""
import re
import logging
from typing import Dict, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)


def interpret_units(text: str) -> Dict[str, Optional[float]]:
    """
    Interpret complex unit patterns from voice transcription
    
    Handles patterns like:
        - "one full and twenty three" → {full: 1, partial: 23, total: 24}
        - "two and a half" → {full: 2, partial: 0.5, total: 2.5}
        - "three point five" → {full: None, partial: None, total: 3.5}
        - "one keg twenty three pint" → {full: 1, partial: 23, total: 24}
        - "half keg and three pint" → {full: 0.5, partial: 3, total: 3.5}
        - "two full, one small" → {full: 2, partial: 1, total: 3}
    
    Args:
        text: Normalized text with numbers converted to digits
        
    Returns:
        dict: {
            'full_units': float or None,
            'partial_units': float or None,
            'total_value': float,
            'pattern': str  # Pattern type matched
        }
    """
    text = text.lower().strip()
    
    # Pattern 1: "X full and Y" or "X full Y"
    pattern1 = r'(\d+(?:\.\d+)?)\s*(?:full|keg|case|bottle|box)\s*(?:and|plus)?\s*(\d+(?:\.\d+)?)'
    match1 = re.search(pattern1, text)
    if match1:
        full = float(match1.group(1))
        partial = float(match1.group(2))
        return {
            'full_units': full,
            'partial_units': partial,
            'total_value': full + partial,
            'pattern': 'full_and_partial'
        }
    
    # Pattern 2: "X and a half" or "X and half"
    pattern2 = r'(\d+(?:\.\d+)?)\s*(?:and)?\s*(?:a\s+)?half'
    match2 = re.search(pattern2, text)
    if match2:
        full = float(match2.group(1))
        return {
            'full_units': full,
            'partial_units': 0.5,
            'total_value': full + 0.5,
            'pattern': 'and_a_half'
        }
    
    # Pattern 3: "X and a quarter" or "X and quarter"
    pattern3 = r'(\d+(?:\.\d+)?)\s*(?:and)?\s*(?:a\s+)?quarter'
    match3 = re.search(pattern3, text)
    if match3:
        full = float(match3.group(1))
        return {
            'full_units': full,
            'partial_units': 0.25,
            'total_value': full + 0.25,
            'pattern': 'and_a_quarter'
        }
    
    # Pattern 4: "X and three quarters"
    pattern4 = r'(\d+(?:\.\d+)?)\s*(?:and)?\s*(?:three\s+)?quarters?'
    match4 = re.search(pattern4, text)
    if match4:
        full = float(match4.group(1))
        return {
            'full_units': full,
            'partial_units': 0.75,
            'total_value': full + 0.75,
            'pattern': 'and_three_quarters'
        }
    
    # Pattern 5: "X and a bit" or "X-ish" (approximate)
    pattern5 = r'(\d+(?:\.\d+)?)\s*(?:and\s+a\s+bit|-ish|ish|or\s+so|about|around)'
    match5 = re.search(pattern5, text)
    if match5:
        full = float(match5.group(1))
        return {
            'full_units': full,
            'partial_units': 0.5,  # Assume roughly half more
            'total_value': full + 0.5,
            'pattern': 'approximate'
        }
    
    # Pattern 6: "X full, Y small" or "X full one small"
    pattern6 = r'(\d+(?:\.\d+)?)\s*(?:full|big|large)\s*,?\s*(?:and)?\s*(\d+(?:\.\d+)?)?(?:small|little|partial|bit)?'
    match6 = re.search(pattern6, text)
    if match6:
        full = float(match6.group(1))
        partial = float(match6.group(2)) if match6.group(2) else 1
        return {
            'full_units': full,
            'partial_units': partial,
            'total_value': full + partial,
            'pattern': 'full_small'
        }
    
    # Pattern 7: "half X" (half keg, half bottle, etc.)
    pattern7 = r'half\s+(?:of\s+)?(\d+(?:\.\d+)?)?'
    match7 = re.search(pattern7, text)
    if match7:
        if match7.group(1):
            value = float(match7.group(1)) * 0.5
        else:
            value = 0.5
        return {
            'full_units': None,
            'partial_units': value,
            'total_value': value,
            'pattern': 'half_unit'
        }
    
    # Pattern 8: "X point Y" (decimal format already handled by main parser)
    pattern8 = r'(\d+)\.(\d+)'
    match8 = re.search(pattern8, text)
    if match8:
        value = float(f"{match8.group(1)}.{match8.group(2)}")
        return {
            'full_units': None,
            'partial_units': None,
            'total_value': value,
            'pattern': 'decimal'
        }
    
    # Pattern 9: "one oh five" or "one dot five" (already converted by number words)
    # Just extract single number
    pattern9 = r'(\d+(?:\.\d+)?)'
    match9 = re.search(pattern9, text)
    if match9:
        value = float(match9.group(1))
        return {
            'full_units': None,
            'partial_units': None,
            'total_value': value,
            'pattern': 'single_value'
        }
    
    # No pattern matched
    return {
        'full_units': None,
        'partial_units': None,
        'total_value': 0,
        'pattern': 'no_match'
    }


def interpret_messy_unit_phrase(text: str) -> Dict:
    """
    Interpret really messy unit phrases common in Irish pub speech
    
    Examples:
        "one keg twenty three pint" → {full: 1, partial: 23, unit_type: 'keg'}
        "two bottles and six" → {full: 2, partial: 6, unit_type: 'bottle'}
        "three cases and five bottles" → {full: 3, partial: 5, unit_type: 'case'}
        "call it four" → {total: 4, approximation: True}
        "we'll say five" → {total: 5, approximation: True}
        "stick six there" → {total: 6, informal: True}
        "nearly full" → {estimation: 'nearly_full', approximate: 0.9}
        "half-ish" → {estimation: 'half_ish', approximate: 0.5}
    
    Args:
        text: Speech transcription text
        
    Returns:
        dict: Structured unit information
    """
    text = text.lower().strip()
    result = {
        'full_units': None,
        'partial_units': None,
        'total_value': None,
        'unit_type': None,
        'approximation': False,
        'informal': False,
        'estimation': None
    }
    
    # Detect unit types
    unit_types = {
        'keg': r'\b(keg|kegs)\b',
        'case': r'\b(case|cases|crate|crates)\b',
        'bottle': r'\b(bottle|bottles)\b',
        'pint': r'\b(pint|pints)\b',
        'litre': r'\b(litre|litres|liter|liters)\b'
    }
    
    for unit_name, pattern in unit_types.items():
        if re.search(pattern, text):
            result['unit_type'] = unit_name
            break
    
    # Check for approximation phrases
    approx_patterns = [
        r'\b(call it|we\'ll say|make it|about|around|roughly|approximately)\b',
        r'\b(or so|give or take|-ish|ish)\b'
    ]
    for pattern in approx_patterns:
        if re.search(pattern, text):
            result['approximation'] = True
            break
    
    # Check for informal phrases
    informal_patterns = [
        r'\b(stick|throw|put|chuck|mark|write)\b',
        r'\b(that|this|the|yoke|thing)\b'
    ]
    for pattern in informal_patterns:
        if re.search(pattern, text):
            result['informal'] = True
            break
    
    # Check for estimation phrases
    estimation_map = {
        r'\b(nearly|almost|close to)\s+full\b': ('nearly_full', 0.9),
        r'\b(nearly|almost|close to)\s+half\b': ('nearly_half', 0.45),
        r'\b(more or less|kinda|kind of)\s+full\b': ('kinda_full', 0.85),
        r'\b(more or less|kinda|kind of)\s+half\b': ('kinda_half', 0.5),
        r'\bhalf-?ish\b': ('half_ish', 0.5),
        r'\bfull-?ish\b': ('full_ish', 0.9),
        r'\bcouple\s+left\b': ('couple_left', 2),
        r'\bfew\s+left\b': ('few_left', 3),
        r'\bsmall\s+amount\b': ('small_amount', 1),
        r'\blittle\s+bit\b': ('little_bit', 0.5),
        r'\btiny\s+bit\b': ('tiny_bit', 0.25)
    }
    
    for pattern, (estimation, value) in estimation_map.items():
        if re.search(pattern, text):
            result['estimation'] = estimation
            result['total_value'] = value
            result['approximation'] = True
            break
    
    # If no estimation matched, try standard unit interpretation
    if result['total_value'] is None:
        units = interpret_units(text)
        result['full_units'] = units['full_units']
        result['partial_units'] = units['partial_units']
        result['total_value'] = units['total_value']
    
    return result


def extract_dozen_pattern(text: str) -> Optional[Tuple[int, int]]:
    """
    Extract dozen pattern from text
    
    Examples:
        "2 dozen 6" → (2, 6) = 30 total
        "3 dozen" → (3, 0) = 36 total
        "one dozen three" → (1, 3) = 15 total
    
    Args:
        text: Text with numbers already converted
        
    Returns:
        tuple: (full_dozens, partial_units) or None
    """
    # Pattern: X dozen Y
    pattern = r'(\d+)\s+dozen(?:\s+(\d+))?'
    match = re.search(pattern, text.lower())
    
    if match:
        dozens = int(match.group(1))
        partial = int(match.group(2)) if match.group(2) else 0
        return (dozens, partial)
    
    return None


def normalize_unit_text(text: str) -> str:
    """
    Normalize unit-related text for easier parsing
    
    Examples:
        "one full and twenty three" → "1 full and 23"
        "two and a half" → "2 and 0.5"
        "tree point five" → "3.5"
    
    Args:
        text: Raw transcription text
        
    Returns:
        str: Normalized text
    """
    from .command_parser import convert_number_words
    
    text = text.lower().strip()
    
    # Convert number words to digits
    text = convert_number_words(text)
    
    # Normalize "and a half" → "and 0.5"
    text = re.sub(r'\band\s+a\s+half\b', 'and 0.5', text)
    text = re.sub(r'\band\s+half\b', 'and 0.5', text)
    
    # Normalize "and a quarter" → "and 0.25"
    text = re.sub(r'\band\s+a\s+quarter\b', 'and 0.25', text)
    text = re.sub(r'\band\s+quarter\b', 'and 0.25', text)
    
    # Normalize "three quarters" → "0.75"
    text = re.sub(r'\bthree\s+quarters\b', '0.75', text)
    text = re.sub(r'\b3\s+quarters\b', '0.75', text)
    
    # Normalize unit variations
    text = re.sub(r'\bkegs?\b', 'keg', text)
    text = re.sub(r'\bcases?\b', 'case', text)
    text = re.sub(r'\bbottles?\b', 'bottle', text)
    text = re.sub(r'\bpints?\b', 'pint', text)
    text = re.sub(r'\bcrates?\b', 'crate', text)
    
    return text
