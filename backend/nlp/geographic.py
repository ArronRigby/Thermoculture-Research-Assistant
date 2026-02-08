"""
Geographic entity recognition module for UK locations.

Extracts UK city, town, and region names from free text using a reference
gazetteer of 60+ locations with approximate coordinates and region labels.
Applies context-aware heuristics to filter common false positives.
"""

from __future__ import annotations

import re
from typing import List, Dict, Set, Tuple


# ---------------------------------------------------------------------------
# UK Gazetteer -- name -> (latitude, longitude, region)
# ---------------------------------------------------------------------------
UK_LOCATIONS: Dict[str, Tuple[float, float, str]] = {
    # England -- Major cities
    "London":           (51.5074, -0.1278,  "London"),
    "Manchester":       (53.4808, -2.2426,  "North West"),
    "Birmingham":       (52.4862, -1.8904,  "West Midlands"),
    "Liverpool":        (53.4084, -2.9916,  "North West"),
    "Leeds":            (53.8008, -1.5491,  "Yorkshire and the Humber"),
    "Sheffield":        (53.3811, -1.4701,  "Yorkshire and the Humber"),
    "Bristol":          (51.4545, -2.5879,  "South West"),
    "Newcastle":        (54.9783, -1.6178,  "North East"),
    "Nottingham":       (52.9548, -1.1581,  "East Midlands"),
    "Leicester":        (52.6369, -1.1398,  "East Midlands"),
    "Coventry":         (52.4068, -1.5197,  "West Midlands"),
    "Bradford":         (53.7960, -1.7594,  "Yorkshire and the Humber"),
    "Plymouth":         (50.3755, -4.1427,  "South West"),
    "Wolverhampton":    (52.5870, -2.1270,  "West Midlands"),
    "Southampton":      (50.9097, -1.4044,  "South East"),
    "Portsmouth":       (50.8198, -1.0880,  "South East"),
    "Brighton":         (50.8225, -0.1372,  "South East"),
    "Oxford":           (51.7520, -1.2577,  "South East"),
    "Cambridge":        (52.2053,  0.1218,  "East of England"),
    "Norwich":          (52.6309,  1.2974,  "East of England"),
    "York":             (53.9591, -1.0815,  "Yorkshire and the Humber"),
    "Bath":             (51.3811, -2.3590,  "South West"),
    "Exeter":           (50.7184, -3.5339,  "South West"),
    "Sunderland":       (54.9069, -1.3838,  "North East"),
    "Derby":            (52.9225, -1.4746,  "East Midlands"),
    "Stoke-on-Trent":   (53.0027, -2.1794,  "West Midlands"),
    "Hull":             (53.7676, -0.3274,  "Yorkshire and the Humber"),
    "Middlesbrough":    (54.5742, -1.2350,  "North East"),
    "Blackpool":        (53.8175, -3.0357,  "North West"),
    "Bolton":           (53.5785, -2.4299,  "North West"),
    "Ipswich":          (52.0567,  1.1482,  "East of England"),
    "Peterborough":     (52.5695, -0.2405,  "East of England"),
    "Luton":            (51.8787, -0.4200,  "East of England"),
    "Milton Keynes":    (52.0406, -0.7594,  "South East"),
    "Swindon":          (51.5558, -1.7797,  "South West"),
    "Cheltenham":       (51.8994, -2.0783,  "South West"),
    "Gloucester":       (51.8642, -2.2382,  "South West"),
    "Bournemouth":      (50.7192, -1.8808,  "South West"),
    "Northampton":      (52.2405, -0.9027,  "East Midlands"),
    "Reading":          (51.4543, -0.9781,  "South East"),
    "Canterbury":       (51.2802,  1.0789,  "South East"),
    "Chester":          (53.1930, -2.8931,  "North West"),
    "Lincoln":          (53.2307, -0.5406,  "East Midlands"),
    "Carlisle":         (54.8925, -2.9329,  "North West"),
    "Durham":           (54.7761, -1.5733,  "North East"),
    "Lancaster":        (54.0466, -2.8007,  "North West"),
    "Worcester":        (52.1936, -2.2216,  "West Midlands"),
    "Hereford":         (52.0565, -2.7160,  "West Midlands"),
    "Salisbury":        (51.0688, -1.7945,  "South West"),
    "Truro":            (50.2632, -5.0510,  "South West"),
    "Colchester":       (51.8959,  0.8919,  "East of England"),
    "Wakefield":        (53.6833, -1.4977,  "Yorkshire and the Humber"),
    "Doncaster":        (53.5228, -1.1285,  "Yorkshire and the Humber"),
    "Barnsley":         (53.5529, -1.4793,  "Yorkshire and the Humber"),
    # Scotland
    "Edinburgh":        (55.9533, -3.1883,  "Scotland"),
    "Glasgow":          (55.8642, -4.2518,  "Scotland"),
    "Aberdeen":         (57.1497, -2.0943,  "Scotland"),
    "Dundee":           (56.4620, -2.9707,  "Scotland"),
    "Inverness":        (57.4778, -4.2247,  "Scotland"),
    "Stirling":         (56.1166, -3.9369,  "Scotland"),
    "Perth":            (56.3950, -3.4308,  "Scotland"),
    "St Andrews":       (56.3398, -2.7967,  "Scotland"),
    "Fort William":     (56.8198, -5.1052,  "Scotland"),
    # Wales
    "Cardiff":          (51.4816, -3.1791,  "Wales"),
    "Swansea":          (51.6214, -3.9436,  "Wales"),
    "Newport":          (51.5842, -2.9977,  "Wales"),
    "Wrexham":          (53.0469, -2.9925,  "Wales"),
    "Bangor":           (53.2274, -4.1293,  "Wales"),
    "Aberystwyth":      (52.4153, -4.0829,  "Wales"),
    "Carmarthen":       (51.8576, -4.3121,  "Wales"),
    "Llanelli":         (51.6840, -4.1629,  "Wales"),
    # Northern Ireland
    "Belfast":          (54.5973, -5.9301,  "Northern Ireland"),
    "Derry":            (54.9966, -7.3086,  "Northern Ireland"),
    "Londonderry":      (54.9966, -7.3086,  "Northern Ireland"),
    "Lisburn":          (54.5162, -6.0580,  "Northern Ireland"),
    "Newry":            (54.1751, -6.3402,  "Northern Ireland"),
    "Armagh":           (54.3503, -6.6528,  "Northern Ireland"),
    "Enniskillen":      (54.3448, -7.6326,  "Northern Ireland"),
}


# ---------------------------------------------------------------------------
# Ambiguous names that are common English words.
# These require extra contextual evidence before being accepted as locations.
# ---------------------------------------------------------------------------
AMBIGUOUS_NAMES: Set[str] = {
    "Reading", "Bath", "Deal", "Hull", "March", "Wells", "Ware",
    "Chester", "Lancaster", "Derby", "Durham", "Lincoln", "York",
    "Bolton", "Newport", "Bangor", "Perth", "Armagh",
}


# Preposition / context patterns that strongly indicate a place-name usage
_LOCATION_CONTEXT_RE = re.compile(
    r"""
    (?:
        \b(?:in|from|across|around|near|outside|leaving|visiting|of|to|at|towards|via)\s+
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Pattern to detect verb-form usage of "Reading" (e.g. "reading a book")
_READING_VERB_RE = re.compile(
    r"\breading\s+(?:a|the|this|that|my|his|her|their|some|about|up|through)\b",
    re.IGNORECASE,
)


class GeoExtractor:
    """
    Extract UK geographic entities from free text.

    Uses a gazetteer of 60+ UK cities and towns with coordinates
    and applies context-aware heuristics to reduce false positives.
    """

    def __init__(self) -> None:
        # Build lookup structures
        self._locations = UK_LOCATIONS

        # Pre-compile a regex for each location name
        self._patterns: Dict[str, re.Pattern] = {}
        for name in self._locations:
            if " " in name:
                # Multi-word: match as-is (case-insensitive)
                self._patterns[name] = re.compile(
                    re.escape(name), re.IGNORECASE
                )
            else:
                # Single word: word-boundary matching
                self._patterns[name] = re.compile(
                    r"\b" + re.escape(name) + r"\b", re.IGNORECASE
                )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_false_positive(self, name: str, text: str, match: re.Match) -> bool:
        """
        Return True if *match* of *name* in *text* is likely a false positive
        (i.e. the word is being used in its non-geographic sense).
        """
        # Special handling for "Reading"
        if name == "Reading":
            # Check if it's used as a verb anywhere nearby
            start = max(0, match.start() - 5)
            end = min(len(text), match.end() + 40)
            surrounding = text[start:end]
            if _READING_VERB_RE.search(surrounding):
                return True
            # If first letter is lowercase, likely a verb
            matched_text = text[match.start():match.end()]
            if matched_text[0].islower():
                return True

        # For other ambiguous names, require geographic context
        if name in AMBIGUOUS_NAMES:
            # Look for a preposition immediately before the match
            preceding_start = max(0, match.start() - 20)
            preceding_text = text[preceding_start:match.start()]
            if not _LOCATION_CONTEXT_RE.search(preceding_text):
                # Also accept if the word is capitalised and not at sentence start
                matched_text = text[match.start():match.end()]
                if match.start() == 0:
                    return True
                # Check if at sentence start (preceded by '. ' or start)
                pre_char_idx = match.start() - 1
                while pre_char_idx >= 0 and text[pre_char_idx] == " ":
                    pre_char_idx -= 1
                if pre_char_idx >= 0 and text[pre_char_idx] in ".!?":
                    return True
                # If the matched text is lowercase, reject
                if matched_text[0].islower():
                    return True
                # Capitalised mid-sentence without preposition --
                # accept but with less certainty (we still include it)
                return False
            return False

        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_locations(self, text: str) -> List[Dict]:
        """
        Extract UK locations from *text*.

        Returns a deduplicated list of dicts, each containing:
        - ``name``      : str   -- the canonical location name
        - ``region``    : str   -- the UK region
        - ``latitude``  : float -- approximate latitude
        - ``longitude`` : float -- approximate longitude
        """
        if not text or not text.strip():
            return []

        found: Dict[str, Dict] = {}  # keyed by canonical name for dedup

        for name, pattern in self._patterns.items():
            for match in pattern.finditer(text):
                if self._is_false_positive(name, text, match):
                    continue

                if name not in found:
                    lat, lon, region = self._locations[name]
                    found[name] = {
                        "name": name,
                        "region": region,
                        "latitude": lat,
                        "longitude": lon,
                    }

        # Return a stable list sorted alphabetically by name
        return sorted(found.values(), key=lambda d: d["name"])
