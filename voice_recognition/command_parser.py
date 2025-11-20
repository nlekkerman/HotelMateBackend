"""
Voice Command Parser
Parses transcribed text into structured stocktake commands using regex
"""
import re
import logging
from typing import Dict, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)

# Action keywords (case-insensitive)
ACTION_KEYWORDS = {
    'count': ['count', 'counted', 'counting', 'total', 'have', 'got', 'stock', 'there are', 'there is'],
    'purchase': ['purchase', 'purchased', 'buy', 'bought', 'received', 'delivery', 'delivered'],
    'waste': ['waste', 'wasted', 'broken', 'spoiled', 'spilled', 'breakage', 'damaged']
}

# Number word conversions
NUMBER_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
    'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
    'eighty': 80, 'ninety': 90, 'hundred': 100
}


def convert_number_words(text):
    """
    Convert number words to digits in text
    
    Examples:
        "five point five" -> "5.5"
        "twenty three" -> "23"
        "three cases" -> "3 cases"
    """
    result = text.lower()
    
    # Handle decimal points (e.g., "five point five")
    decimal_pattern = r'(\w+)\s+point\s+(\w+)'
    def replace_decimal(match):
        whole = NUMBER_WORDS.get(match.group(1), match.group(1))
        decimal = NUMBER_WORDS.get(match.group(2), match.group(2))
        return f"{whole}.{decimal}"
    result = re.sub(decimal_pattern, replace_decimal, result)
    
    # Handle compound numbers (e.g., "twenty four" -> "24")
    # Match patterns like "twenty three", "thirty five", etc.
    compound_pattern = r'\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\s+(one|two|three|four|five|six|seven|eight|nine)\b'
    def replace_compound(match):
        tens = NUMBER_WORDS.get(match.group(1), 0)
        ones = NUMBER_WORDS.get(match.group(2), 0)
        return str(tens + ones)
    result = re.sub(compound_pattern, replace_compound, result)
    
    # Replace individual number words
    for word, num in NUMBER_WORDS.items():
        result = re.sub(rf'\b{word}\b', str(num), result)
    
    return result


def parse_voice_command(transcription: str) -> Dict:
    """
    Parse transcribed text into structured command
    
    Args:
        transcription: Raw text from speech-to-text service
        
    Returns:
        dict: {
            'action': str,              # 'count', 'purchase', or 'waste'
            'item_identifier': str,     # Product name or SKU
            'value': float,             # Combined quantity (for compatibility)
            'full_units': int,          # Optional: full units (kegs, cases, bottles)
            'partial_units': float,     # Optional: partial units (pints, bottles, fraction)
            'transcription': str        # Original transcription for debugging
        }
        
    Raises:
        ValueError: If command cannot be parsed
        
    Examples:
        "count guinness 5.5"
            -> {action: 'count', item_identifier: 'guinness', value: 5.5, ...}
        
        "purchase jack daniels 2 bottles"
            -> {action: 'purchase', item_identifier: 'jack daniels', value: 2, ...}
        
        "count heineken 3 cases 6 bottles"
            -> {action: 'count', item_identifier: 'heineken', 
                full_units: 3, partial_units: 6, value: 3.5, ...}
        
        "waste budweiser one point five"
            -> {action: 'waste', item_identifier: 'budweiser', value: 1.5, ...}
    """
    
    # Convert number words to digits
    text = convert_number_words(transcription.lower().strip())
    
    logger.info(f"🔍 Parsing: '{text}' (from '{transcription}')")
    
    # 1. Detect action
    action = None
    action_word = None
    for action_type, keywords in ACTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                action = action_type
                action_word = keyword
                break
        if action:
            break
    
    if not action:
        raise ValueError(f"No action keyword found in '{transcription}'")
    
    logger.info(f"✓ Action: {action} (matched: {action_word})")
    
    # 2. Extract numeric values
    # Pattern 1: Dozen format "3 dozen 6", "2 dozen"
    dozen_pattern = r'(\d+)\s+dozen(?:\s+(\d+))?'
    
    # Pattern 2: Full + partial units "3 cases 6 bottles", "2 kegs 12 pints"
    full_partial_pattern = r'(\d+(?:\.\d+)?)\s*(?:cases?|kegs?|boxes?)\s+(?:and\s+)?(\d+(?:\.\d+)?)\s*(?:bottles?|pints?|cans?|ml)?'
    
    # Pattern 3: Single value with optional unit "5.5", "10 bottles", "3 kegs"
    single_value_pattern = r'(\d+(?:\.\d+)?)\s*(?:cases?|kegs?|boxes?|bottles?|pints?|cans?|liters?|ml)?(?:\s|$)'
    
    full_units = None
    partial_units = None
    value = None
    
    # Try dozen pattern first (most specific)
    dozen_match = re.search(dozen_pattern, text)
    if dozen_match:
        full_units = int(dozen_match.group(1))
        partial_units = int(dozen_match.group(2)) if dozen_match.group(2) else 0
        value = (full_units * 12) + partial_units
        logger.info(f"✓ Parsed dozen: {full_units} dozen + {partial_units} = {value}")
    else:
        # Try full + partial pattern
        full_partial_match = re.search(full_partial_pattern, text)
        if full_partial_match:
            full_units = int(float(full_partial_match.group(1)))
            partial_units = float(full_partial_match.group(2))
            value = float(full_units) + partial_units
            logger.info(f"✓ Parsed full+partial: {full_units} full, {partial_units} partial (combined: {value})")
        else:
            # Try single value pattern
            # Find all matches and take the last one (closest to end, likely the quantity)
            single_matches = list(re.finditer(single_value_pattern, text))
            if single_matches:
                last_match = single_matches[-1]
                value = float(last_match.group(1))
                logger.info(f"✓ Parsed single value: {value}")
            else:
                raise ValueError(f"No numeric value found in '{transcription}'")
    
    # 3. Extract item identifier (everything between action and numbers)
    # Remove the action keyword from beginning
    item_text = text
    if action_word:
        # Find where action word ends
        action_pos = item_text.find(action_word)
        if action_pos != -1:
            item_text = item_text[action_pos + len(action_word):].strip()
    
    # Remove the numeric part at the end
    if dozen_match:
        item_text = item_text[:dozen_match.start()].strip()
    elif full_partial_match:
        item_text = item_text[:full_partial_match.start()].strip()
    elif single_matches:
        item_text = item_text[:single_matches[-1].start()].strip()
    
    # Remove any trailing numbers or dozen patterns that might have been left
    item_text = re.sub(r'\s+\d+\s+dozen\s*$', '', item_text)
    item_text = re.sub(r'\s+\d+(?:\.\d+)?\s*$', '', item_text)
    
    item_identifier = item_text.strip()
    
    if not item_identifier:
        raise ValueError(f"No item identifier found in '{transcription}'")
    
    logger.info(f"✓ Item identifier: '{item_identifier}'")
    
    # Build result
    result = {
        'action': action,
        'item_identifier': item_identifier,
        'value': value,
        'transcription': transcription
    }
    
    # Add full/partial if detected
    if full_units is not None:
        result['full_units'] = full_units
        result['partial_units'] = partial_units
    
    logger.info(f"✅ Parsed command: {result}")
    
    return result
