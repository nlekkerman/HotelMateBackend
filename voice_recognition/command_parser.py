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
    'count': ['count', 'count this', 'count that', 'counted', 'counting', 'update count', 
              'set count', 'add count', 'write count', 'record count', 'log count', 'mark count',
              'total', 'have', 'got', 'stock', 'there are', 'there is', 'we have', 'i see',
              'put here', 'add here', 'enter count', 'correct count', 'fix count',
              'put five', 'put four', 'put three', 'make five', 'make three', 'stick five',
              'stick three', 'throw five', 'put down', 'write five'],
    'purchase': ['purchase', 'purchases', 'purchased', 'buy', 'bought', 'received', 'delivery', 
                 'delivered', 'deliveries', 'add purchase', 'add delivery', 'incoming',
                 'incoming stock', 'incoming delivery', 'new stock', 'restock', 'top up',
                 'add new', 'add more', 'supplier delivered', 'we received', 'we got stock in',
                 'stock arrived', 'delivery came', 'add three', 'add four', 'add six',
                 'add two kegs', 'add two bottles', 'record delivery'],
    'waste': ['waste', 'wasted', 'broken', 'spoiled', 'spilled', 'breakage', 'damaged',
              'spill', 'spillage', 'dump', 'dumped', 'loss', 'lost', 'broke', 'smashed',
              'minus', 'minus one', 'subtract one', 'remove one', 'take off', 'minus bottle',
              'minus pint', 'bottle broke', 'one smashed', 'that\'s gone', 'that one\'s gone',
              'one fell', 'that bottle\'s finished', 'throw away', 'bin that', 'waste pint',
              'waste bottle']
}

# Number word conversions (including common STT misrecognitions)
NUMBER_WORDS = {
    # 0
    'zero': 0, 'zerro': 0, 'zaro': 0, 'zeroo': 0, 'oh': 0, 'o': 0, 'oo': 0, 
    'none': 0, 'null': 0,
    # 1
    'one': 1, 'won': 1, 'wan': 1, 'wun': 1, 'on': 1, 'uhn': 1,
    # 2
    'two': 2, 'too': 2, 'tu': 2, 'to': 2, 'tew': 2,
    # 3
    'three': 3, 'tree': 3, 'thre': 3, 'tri': 3, 'tre': 3,
    # 4
    'four': 4, 'for': 4, 'foor': 4, 'foe': 4,
    # 5
    'five': 5, 'fife': 5, 'faiv': 5, 'fyve': 5, 'fiv': 5,
    # 6
    'six': 6, 'sex': 6, 'siks': 6, 'sixs': 6, 'sicks': 6,
    # 7
    'seven': 7, 'sevn': 7, 'sevan': 7, 'sevenn': 7,
    # 8
    'eight': 8, 'ate': 8, 'eit': 8, 'eete': 8, 'ayt': 8,
    # 9
    'nine': 9, 'nain': 9, 'nayn': 9, 'ninee': 9,
    # 10
    'ten': 10, 'tenn': 10, 'tan': 10,
    # 11-19
    'eleven': 11, 'elefen': 11, 'eleffin': 11, 'elevn': 11,
    'twelve': 12, 'twelv': 12, 'twelf': 12,
    'thirteen': 13, 'tirteen': 13, 'thurteen': 13, 'thirteee': 13,
    'fourteen': 14, 'forteen': 14, 'fourtin': 14,
    'fifteen': 15, 'fiffteen': 15, 'fiftean': 15,
    'sixteen': 16, 'sixtin': 16, 'sextin': 16,
    'seventeen': 17, 'sevnteen': 17, 'sevntean': 17,
    'eighteen': 18, 'ateen': 18, 'eitin': 18,
    'nineteen': 19, 'nainteen': 19, 'naintean': 19,
    # Tens
    'twenty': 20, 'twenny': 20, 'tweni': 20, 'twentie': 20,
    'thirty': 30, 'tirty': 30, 'dirty': 30, 'thurty': 30,
    'forty': 40, 'fourty': 40, 'fortee': 40,
    'fifty': 50, 'fiftee': 50, 'fiftyy': 50,
    'sixty': 60, 'sixti': 60, 'sixtie': 60,
    'seventy': 70, 'sevnty': 70, 'seventee': 70,
    'eighty': 80, 'eitee': 80, 'atey': 80,
    'ninety': 90, 'ninetee': 90, 'ninty': 90,
    # Large numbers
    'hundred': 100, 'hunderd': 100, 'hunnert': 100,
    'thousand': 1000, 'tausand': 1000, 'tausen': 1000,
    # Fractions and partials
    'half': 0.5, 'quarter': 0.25, 'three quarters': 0.75,
    'point five': 0.5, 'point two': 0.2, 'point three': 0.3,
    'dot five': 0.5, 'dot two': 0.2, 'dot three': 0.3
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
    
    # 1. Detect action (can be at beginning OR end)
    action = None
    action_word = None
    action_position = -1
    
    for action_type, keywords in ACTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                action = action_type
                action_word = keyword
                # Find position of action word
                action_position = text.find(keyword)
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
            
            # CRITICAL: Purchases can ONLY be full units (no partial)
            # "purchase 3 cases 5 bottles" is INVALID
            # "count 3 cases 5 bottles" is VALID
            if action == 'purchase':
                raise ValueError(
                    f"Purchase command cannot have partial units. "
                    f"Use 'purchase {full_units}' for full units only. "
                    f"Partial units should be recorded as waste."
                )
            
            # For COUNT action, full_units and partial_units are passed
            # separately to the backend. The backend calculates:
            # counted_qty = (full_units × uom) + partial_units
            # 
            # Example: "5 cases 5 bottles" with uom=12
            # Backend calculates: (5 × 12) + 5 = 65 bottles
            value = float(full_units)  # Store full units in value
            
            logger.info(f"✓ Parsed full+partial: {full_units} full, {partial_units} partial")
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
    
    # 3. Extract item identifier (remove action words and numbers)
    item_text = text
    
    # Remove the action keyword from anywhere in the text
    if action_word:
        item_text = item_text.replace(action_word, ' ')
    
    # Remove common filler/question words
    filler_pattern = (r'\b(i|we|the|a|an|this|that|but|why|is|it|what|how|'
                      r'where|when|who|umm|uh|ok|so|many|think)\b')
    item_text = re.sub(filler_pattern, ' ', item_text)
    
    # Remove question marks and other punctuation (keep letters/spaces only)
    item_text = re.sub(r'[?!.,;:]', ' ', item_text)
    
    # Remove numbers and units
    item_text = re.sub(r'\d+(?:\.\d+)?', ' ', item_text)
    item_text = re.sub(r'\b(cases?|bottles?|kegs?|pints?|cans?|dozen|boxes?|liters?|ml)\b', ' ', item_text)
    
    # Collapse multiple spaces
    item_text = re.sub(r'\s+', ' ', item_text)
    
    # Split into tokens and keep only meaningful words (3+ chars or known brands)
    tokens = item_text.strip().split()
    known_short_words = ['bud', 'kbc', 'sol', 'wkd', 'ice']
    meaningful_tokens = [
        t for t in tokens 
        if len(t) >= 3 or t in known_short_words
    ]
    
    item_identifier = ' '.join(meaningful_tokens).strip()
    
    if not item_identifier or len(item_identifier) < 2:
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
