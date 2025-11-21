"""
Fuzzy Item Matching for Voice Commands
=====================================

Uses rapidfuzz for intelligent matching of partial/misspelled product names
from voice recognition (e.g. Whisper).

Key features:
- Brand synonyms (Bud → Budweiser, Smithix → Smithwicks, etc.)
- Multi-word synonym support (e.g. "west coast cooler")
- Normalisation of spoken numbers ("seven" -> "7", "half" -> "0.5")
- Fuzzy matching on SKU + item name
- Package awareness (bottle vs draught vs can)

Public API:
    find_best_match(search_phrase, items, min_score=0.55)
    find_best_match_in_stocktake(search_phrase, stocktake, min_score=0.55)
"""

import logging
from typing import List, Optional, Dict

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 1) CONFIG: synonyms & helpers
# ─────────────────────────────────────────────────────────────

# Brand synonyms for common misspellings/variations
# NOTE: Keep ONLY real brands / product-family words here.
BRAND_SYNONYMS = {
    # BEERS
    "budweiser": [
        "bud", "budwiser", "budweisser", "bude", "boodviser", "budwieser"
    ],
    "bulmers": [
        "bulmer", "bulmars", "bulmr", "bulmur", "boomer", "boomers",
        "boomer's", "bulmur's"
    ],
    "smithwicks": [
        "smithix", "smidix", "smithicks", "smithwix", "smiddicks"
    ],
    "heineken": [
        "heiny", "heinie", "heinikn", "heine", "heinkin", "hieneken"
    ],
    "peroni": ["perony", "perori", "perni", "perroni", "perrone"],

    # 🔥 COORS – with C/K variants
    "coors": [
        # correct
        "coors", "coors light", "coors beer",
        # classic STT / accent shit
        "course", "cores", "cooors", "cors", "core",
        # C↔K confusion
        "kors", "koors", "korse", "corse", "corz", "kors light"
    ],

    "guinness": ["guiness", "ginnes", "ginis", "guinnes", "guines"],
    "moretti": ["morety", "moreti", "moretty"],

    # C↔K for Corona
    "corona": [
        "corona", "carona", "coronna", "corono",
        "korona", "korona beer"
    ],

    "carlsberg": ["carlsbrg", "carlsburg"],
    "kbc": ["k b c", "killarney brewing", "kbc brewery"],

    # Cronins as its own brand + K variants
    "cronins": [
        "cronin", "cronins",
        "kronin", "kronins"  # C↔K at start
    ],

    "kronenbourg": ["kronenbourg", "kronen"],
    "kopparberg": ["copper", "copperberg", "kopper", "koppar"],
    "erdinger": ["airding"],
    "smirnoff ice": ["smirnoff", "smirnof", "smernoff", "smirnov"],
    "wkd": ["wicked", "w k d"],
    "west coast": ["westcoast", "west coast cooler"],
    "orchard thieves": ["orchard", "orchards"],
    "lagunitas": ["lagunita", "lagunitos"],
    "beamish": ["beemish"],
    "murphys": ["murphy", "murphies", "murfy"],
    "sol": ["sol beer", "sol bottle"],

    # SPIRITS - VODKA
    "absolut": ["absolute", "absoloot"],
    "smirnoff vodka": ["smirnof", "smernoff", "smirnov"],
    "grey goose": ["gray goose", "greygoose", "graygoose"],
    "belvedere": ["belvidere", "belvedeer"],
    "ketel one": ["kettle one", "kettle", "ketel"],
    "titos": ["tito", "teetos", "tito's"],
    "dingle vodka": ["dingle"],

    # SPIRITS - GIN
    "gordons": ["gordon", "gordans", "gordan", "gordon's"],
    "bombay": ["bombay sapphire", "bombay dry", "bumbay"],
    "tanqueray": ["tanquery", "tankery"],
    "hendricks": ["hendrick", "hendrix"],
    "beefeater": ["beefeeter", "beef eater", "beafeater"],
    "dingle gin": ["dingle"],
    "berthas revenge": ["bertha", "berthas", "bertha's revenge"],
    "boatyard": ["boat yard", "boatyard sloe"],
    "muckross": ["muckros", "muckross wild"],
    "ring of kerry": ["ring of carry"],
    "silver spear": ["silverspear"],
    "method and madness": ["method madness", "method & madness"],

    # SPIRITS - WHISKEY/WHISKY
    "jameson": ["jamesom", "jamison", "jameson's"],
    "bushmills": ["bushmils", "bush mills"],
    "powers": ["power", "powers whiskey"],
    "tullamore": ["tullamore dew"],
    "redbreast": ["red breast", "redbrest"],
    "green spot": ["greenspot"],
    "yellow spot": ["yellowspot"],
    "paddy": ["paddy whiskey", "paddys"],
    "killarney whiskey": ["killarney"],
    "dingle whiskey": ["dingle"],
    "skellig": ["skellig six18"],
    "roe and co": ["roe", "roe & co"],
    "west cork": ["westcork"],
    "jack daniels": ["jack daniel", "jack", "jd"],
    "johnnie walker": ["johnny walker", "jonny walker", "walker"],
    "famous grouse": ["grouse"],
    "glenfiddich": ["glenfidich", "glen fiddich"],
    "glenmorangie": ["glen morangie"],
    "laphroaig": ["lafroyg", "laphroig"],
    "talisker": ["taliska"],
    "black bush": ["blackbush"],
    "crested": ["crested ten", "crested 10"],
    "teachers": ["teacher"],

    # SPIRITS - RUM
    "bacardi": ["baccardi", "bakardi"],
    "havana": ["havana club", "havanna"],
    # captain – add kaptain / captn
    "captain morgan": [
        "captain", "captain morgans", "cap morgan",
        "captn morgan", "kaptain morgan"
    ],
    "malibu": ["maliboo"],
    "kraken": ["krackan", "cracken"],
    "matusalem": ["matuselem"],
    "sea dog": ["seadog"],

    # SPIRITS - TEQUILA
    "patron": ["patron silver"],
    "el jimador": ["jimador", "el jimador blanco"],
    "jose cuervo": ["cuervo", "j.c", "jc"],
    "olmeca": ["olmeca gold"],
    "corazon": ["corazon anejo"],
    "ghost": ["ghost tequila", "ghost spicy"],
    "tequila rose": ["tequila rosa"],
    "tequila bianca": ["bianca", "tequila blanco"],

    # SPIRITS - COGNAC/BRANDY
    "hennessy": ["hennesy", "henesy"],
    "courvoisier": [
        "cdc", "courvoisier", "couvoisier", "corvoisier",
        "courvosier", "cognac cdc"
    ],
    "remy martin": ["remy", "remy vsop"],
    "martell": ["martel", "martell vs"],
    # canadian – add kanadian
    "buffalo trace": ["buffalo", "trace"],
    "canadian club": ["canadian", "cc", "kanadian club"],

    # SPIRITS - LIQUEURS
    "baileys": ["bailey", "bailies"],
    "kahlua": ["kalua", "kahlúa"],
    "tia maria": ["tiamaria"],
    "disaronno": ["disarono", "amaretto"],
    "cointreau": ["cointrau"],
    "grand marnier": ["grandmarnier"],
    "drambuie": ["drambuey"],
    "southern comfort": ["southern"],
    "aperol": ["apparel"],
    "campari": ["campary"],
    "chambord": ["shambor"],
    "luxardo": ["luxardo limoncello"],
    "passoa": ["pasoa", "passion fruit"],
    "midori": ["midori green"],
    "galliano": ["galianos"],
    "sambuca": ["antica sambuca", "sambucca"],
    "pernod": ["perno"],
    "jagermeister": ["jager", "yager"],
    "irish mist": ["irishmist"],
    "benedictine": ["benidictine"],
    "pimms": ["pims", "pimm's"],

    # SPIRITS - SCHNAPPS/SYRUPS
    "peach schnapps": ["peach schnapps", "peach snaps"],
    "apple sourz": ["apple souz", "apple sours", "sourz"],

    # BOLS LIQUEURS
    "bols": ["bolls"],

    # VOLARE
    "volare": ["volari"],
    "triple sec": ["triple", "sec"],
    "limoncello": ["lemoncello", "limoncello"],
    "butterscotch": ["butter scotch", "butterscotch"],
    "passionfruit": ["passion fruit", "passion"],

    # PORTS & SHERRIES
    "osborne": ["osborne port"],
    "sandeman": ["sandeman port"],
    "tio pepe": ["tio pepe sherry"],
    "harveys": ["harveys bristol cream"],
    "bristol cream": ["bristol", "cream sherry"],
    "port": ["port wine", "porto"],
    "sherry": ["sherry wine"],
    "martini": ["martini vermouth", "vermouth"],

    # WINE BRANDS (Common foreign pronunciations)
    "chablis": ["shabli", "shably"],
    "merlot": ["merlo", "merloe"],
    "pinot": ["pino", "pinot grigio", "pinot gris"],
    "sauvignon": ["sovignon", "sauvignon blanc", "sauv blanc"],
    "chardonnay": ["chardonny", "chardonay", "shardonnay"],
    "cabernet": ["cab sauv", "cabernet sauvignon"],
    "rioja": ["ryoja", "rio ha"],
    "malbec": ["malbeck"],
    "prosecco": ["proseco"],
    "champagne": ["shampain"],
    "tempranillo": ["temp"],
    "primitivo": ["primativo"],
    "barbera": ["barberà"],
    "albarino": ["albariño"],
    "verdejo": ["verdejo", "verdayo"],

    # SPECIFIC WINE BRANDS
    "chateau": ["chateau", "chateaux", "shato"],
    "domaine": ["domaine", "domiane"],
    "marquess": ["marques", "marquess plata"],
    "santa ana": ["santa ana", "santana"],
    "jack rabbit": ["jackrabbit", "jack rabbit"],
    "sonnetti": ["sonnetti", "sonetti"],
    "pascaud": ["pacsaud", "pascaud bordeaux"],
    "pouilly": ["pouilly fume", "poilly", "pwilly"],
    "fleurie": ["fleurie", "fleuri"],
    "equino": ["equino malbec"],
    "roquende": ["roquende", "rokende"],
    "fuego": ["fuego blanco", "fuego"],
    "rialto": ["rialto prosecco"],
    "pannier": ["pannier champagne"],
    "collie": ["collie prosecco", "colli"],
    "reina": ["reina wine", "reyna"],
    "pazo": ["pazo albarino", "paso"],
    "tenuta": ["tenuta barbera"],
    "moilard": ["moilard macon", "macon village"],
    "chevaliere": ["chevalier", "chevaliere"],
    "jamelles": ["jamelles", "jamelle"],
    "giola": ["giola colle", "giola"],

    # MINERALS/SOFT DRINKS
    "coca cola": ["coke", "coca", "cola", "cocacola"],
    "seven up": ["7up", "7 up"],
    "sprite": ["sprit"],
    "fanta": ["fanter"],
    "lucozade": ["lucozaid"],
    "schweppes": ["schweps", "schwepps", "elderflower"],
    "fevertree": ["fever tree", "fever-tree"],
    "red bull": ["redbull"],
    "riverrock": ["river rock"],
    "appletiser": ["appletisier", "appletizer"],
    "three cents": ["3 cents"],
    "ginger beer": ["ginger"],
    "lemonade": ["lemonade nashs", "nashs"],
    "miwadi": ["miwadi cordial"],

    # SYRUPS
    "monin": ["monin syrup"],
    "grenadine": ["grenadene"],

    # JUICE BRANDS
    "kulana": ["kulana juice"],
    "splash": ["splash juice"],
    "britvic": ["britvick"],
}

# Modifiers / descriptors (NOT brands; not used in fuzzy match, but
# can be used later if you want to interpret style like zero/diet/white).
MODIFIER_SYNONYMS = {
    "zero": ["0", "zero alcohol", "non alcoholic", "alcohol free"],
    "diet": ["diet", "lite", "light"],
    "gluten free": ["gf", "gluten free", "celiac"],
    "free": ["free", "0.0", "zero percent"],
    "wild": ["wild berry", "wild fruit"],
    "blonde": ["blond", "blonde ale"],
    "red": ["red ale", "rouge"],
    "white": ["blanc", "blanco", "bianco"],
    "rose": ["rosé", "rosa", "rosato"],
    "sparkling": ["spark", "fizzy", "bubbles"],
    "still": ["still water", "flat"],
    "mini": ["miniature", "baby", "small"],
    "litre": ["ltr", "liter", "l"],
    "millilitre": ["ml", "milliliter"],
    "centilitre": ["cl"],
    "dozen": ["doz", "12"],
}

PACKAGE_SYNONYMS = {
    "bottle": ["bot", "botle", "botl", "bott", "btl", "bottl"],
    "draught": ["draft", "tap", "on tap", "keg", "kegs"],
    "pint": ["pt", "pnt", "pint bottle"],
    "can": ["cn", "tin"],
    "case": ["case", "box"],
    "split": ["split", "small bottle", "mini"],
}

# Number/Quantity words for voice recognition
QUANTITY_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "half": 0.5,
    "quarter": 0.25,
}

# Filler words we want to drop from STT text
FILLER_WORDS = {"please", "and", "eh", "uh", "um", "a", "the"}


# ─────────────────────────────────────────────────────────────
# 2) Normalisation helpers
# ─────────────────────────────────────────────────────────────

def normalize_phrase(raw: str) -> str:
    """
    Clean STT output:
    - lowercases
    - removes filler words
    - converts quantity words to digits ("seven" -> "7", "half" -> "0.5")
    """
    tokens = raw.lower().split()
    normalized: List[str] = []

    for t in tokens:
        if t in FILLER_WORDS:
            continue
        if t in QUANTITY_WORDS:
            normalized.append(str(QUANTITY_WORDS[t]))
        else:
            normalized.append(t)

    return " ".join(normalized)


def expand_search_tokens(phrase: str) -> List[str]:
    """
    Expand a search phrase with brand and package synonyms.

    Example:
        "bud botle" -> ["bud", "botle", "budweiser", "bottle", ...]
    """
    phrase_lower = phrase.lower()
    tokens = phrase_lower.split()
    expanded = set(tokens)

    # 1) Multi-word brand variants (e.g. "west coast cooler")
    for brand, variants in BRAND_SYNONYMS.items():
        for v in variants:
            if " " in v and v in phrase_lower:
                expanded.add(brand)
                expanded.update(v.split())

    # 2) Per-token brand + package expansion
    for token in tokens:
        # Brand synonyms
        for brand, variants in BRAND_SYNONYMS.items():
            if token == brand or token in variants:
                expanded.add(brand)
                expanded.update(variants)

        # Packaging synonyms
        for package, variants in PACKAGE_SYNONYMS.items():
            if token == package or token in variants:
                expanded.add(package)
                expanded.update(variants)

    return list(expanded)


# ─────────────────────────────────────────────────────────────
# 3) Scoring
# ─────────────────────────────────────────────────────────────

def score_item(item_name: str, sku: str, search_phrase: str) -> float:
    """
    Score how well an item matches a search phrase.

    Uses multiple fuzzy matching strategies:
    1. Token set ratio (ignores order, duplicates)
    2. Partial ratio (substring matching)
    3. Simple ratio (overall similarity)
    4. Synonym expansion
    5. Package type matching (draught vs bottle)

    Returns: Score from 0.0 to 1.0
    """
    phrase_lower = search_phrase.lower()
    full_label = f"{sku} {item_name}".strip().lower()

    # Get expanded tokens with synonyms
    search_tokens = expand_search_tokens(phrase_lower)

    scores: List[float] = []

    # 1. Direct fuzzy matching against full label (SKU + name)
    scores.append(fuzz.token_set_ratio(phrase_lower, full_label) / 100.0)
    scores.append(fuzz.partial_ratio(phrase_lower, full_label) / 100.0)
    scores.append(fuzz.ratio(phrase_lower, full_label) / 100.0)

    # 2. Match expanded tokens against full label
    for token in search_tokens:
        if len(token) >= 3:  # Skip very short tokens
            scores.append(fuzz.partial_ratio(token, full_label) / 100.0)

    # 3. Package type penalty/bonus
    draught_words = ["draught"] + PACKAGE_SYNONYMS["draught"]
    bottle_words = ["bottle"] + PACKAGE_SYNONYMS["bottle"]

    search_has_draught = any(word in phrase_lower for word in draught_words)
    search_has_bottle = any(word in phrase_lower for word in bottle_words)
    item_has_draught = any(word in full_label for word in draught_words)
    item_has_bottle = any(word in full_label for word in bottle_words)

    # Apply penalty/bonus
    if search_has_draught and item_has_bottle:
        # User said "draft" but item is "bottle" - heavy penalty
        scores = [s * 0.3 for s in scores]
    elif search_has_bottle and item_has_draught:
        scores = [s * 0.3 for s in scores]
    elif search_has_draught and item_has_draught:
        scores.append(0.98)
        scores.append(0.97)
    elif search_has_bottle and item_has_bottle:
        scores.append(0.98)
        scores.append(0.97)

    # Return weighted average of top 3 scores
    scores.sort(reverse=True)
    top_scores = scores[:3]

    return sum(top_scores) / len(top_scores) if top_scores else 0.0


# ─────────────────────────────────────────────────────────────
# 4) Public matching API
# ─────────────────────────────────────────────────────────────

def find_best_match(
    search_phrase: str,
    items: List,
    min_score: float = 0.55,
) -> Optional[Dict]:
    """
    Find the best matching item from a list.

    Args:
        search_phrase: The phrase to search for (e.g., "bud botle")
        items: List of StockItem objects (or queryset)
        min_score: Minimum confidence score (0.0-1.0)

    Returns:
        Dict with match info or None if no good match
    """
    if not search_phrase or not items:
        return None

    normalized = normalize_phrase(search_phrase)

    candidates = []
    for item in items:
        score = score_item(item.name, item.sku, normalized)
        candidates.append({
            "item": item,
            "score": score,
            "name": item.name,
            "sku": item.sku,
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    logger.info(
        f"Search: '{search_phrase}' (normalized: '{normalized}') - Top candidates:"
    )
    for i, candidate in enumerate(candidates[:5], 1):
        logger.info(
            f"  {i}. [{candidate['score']:.4f}] "
            f"{candidate['sku']}: {candidate['name']}"
        )

    best = candidates[0] if candidates else None
    if best and best["score"] >= min_score:
        logger.info(
            f"✓ SELECTED: '{search_phrase}' → '{best['name']}' "
            f"(SKU: {best['sku']}, confidence: {best['score']:.2f})"
        )
        return {
            "item": best["item"],
            "confidence": best["score"],
            "search_phrase": search_phrase,
        }

    logger.warning(
        f"✗ NO MATCH: '{search_phrase}' "
        f"(best: {best['name'] if best else 'none'}, "
        f"score: {best['score']:.2f if best else 0.0}, "
        f"threshold: {min_score})"
    )
    return None


def find_best_match_in_stocktake(
    search_phrase: str,
    stocktake,
    min_score: float = 0.55,
) -> Optional[Dict]:
    """
    Find best match among items in a specific stocktake.

    This limits the search to only items that are part of the stocktake,
    improving accuracy and speed.
    """
    from stock_tracker.models import StockItem

    stocktake_item_ids = stocktake.lines.values_list("item_id", flat=True)
    items = StockItem.objects.filter(
        id__in=stocktake_item_ids,
        active=True,
    )

    return find_best_match(search_phrase, list(items), min_score)
