"""
UK location reference data and fuzzy-matching utilities.

Provides a dictionary of ~50+ UK locations mapped to Region enum values, plus
a :func:`find_locations` function that scans free text for location mentions
while trying to avoid false positives.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Import the canonical Region enum from the models layer.  The string
# values here must match the enum members exactly so that they can be
# passed straight into SQLAlchemy queries.
# ---------------------------------------------------------------------------
from app.models.models import Region

# ---------------------------------------------------------------------------
# UK Locations Database
# ---------------------------------------------------------------------------
# Each entry maps a location name to its Region enum value.
# We store the *canonical* casing for display, but all matching is
# case-insensitive.
# ---------------------------------------------------------------------------

UK_LOCATIONS: dict[str, Region] = {
    # London
    "London": Region.LONDON,
    "Westminster": Region.LONDON,
    "Camden": Region.LONDON,
    "Greenwich": Region.LONDON,
    "Hackney": Region.LONDON,
    "Islington": Region.LONDON,
    "Tower Hamlets": Region.LONDON,
    "Croydon": Region.LONDON,
    # South East
    "Brighton": Region.SOUTH_EAST,
    "Oxford": Region.SOUTH_EAST,
    "Canterbury": Region.SOUTH_EAST,
    "Southampton": Region.SOUTH_EAST,
    "Portsmouth": Region.SOUTH_EAST,
    "Reading": Region.SOUTH_EAST,
    "Guildford": Region.SOUTH_EAST,
    "Milton Keynes": Region.SOUTH_EAST,
    "Luton": Region.SOUTH_EAST,
    "Slough": Region.SOUTH_EAST,
    "Maidstone": Region.SOUTH_EAST,
    "Hastings": Region.SOUTH_EAST,
    # South West
    "Bristol": Region.SOUTH_WEST,
    "Bath": Region.SOUTH_WEST,
    "Plymouth": Region.SOUTH_WEST,
    "Exeter": Region.SOUTH_WEST,
    "Gloucester": Region.SOUTH_WEST,
    "Bournemouth": Region.SOUTH_WEST,
    "Swindon": Region.SOUTH_WEST,
    "Cheltenham": Region.SOUTH_WEST,
    "Taunton": Region.SOUTH_WEST,
    "Torquay": Region.SOUTH_WEST,
    # East of England
    "Cambridge": Region.EAST,
    "Norwich": Region.EAST,
    "Ipswich": Region.EAST,
    "Colchester": Region.EAST,
    "Peterborough": Region.EAST,
    "Chelmsford": Region.EAST,
    "Southend-on-Sea": Region.EAST,
    # West Midlands
    "Birmingham": Region.WEST_MIDLANDS,
    "Coventry": Region.WEST_MIDLANDS,
    "Wolverhampton": Region.WEST_MIDLANDS,
    "Stoke-on-Trent": Region.WEST_MIDLANDS,
    "Worcester": Region.WEST_MIDLANDS,
    "Hereford": Region.WEST_MIDLANDS,
    "Shrewsbury": Region.WEST_MIDLANDS,
    "Walsall": Region.WEST_MIDLANDS,
    "Dudley": Region.WEST_MIDLANDS,
    # East Midlands
    "Nottingham": Region.EAST_MIDLANDS,
    "Leicester": Region.EAST_MIDLANDS,
    "Derby": Region.EAST_MIDLANDS,
    "Lincoln": Region.EAST_MIDLANDS,
    "Northampton": Region.EAST_MIDLANDS,
    "Mansfield": Region.EAST_MIDLANDS,
    # North West
    "Manchester": Region.NORTH_WEST,
    "Liverpool": Region.NORTH_WEST,
    "Chester": Region.NORTH_WEST,
    "Preston": Region.NORTH_WEST,
    "Blackpool": Region.NORTH_WEST,
    "Bolton": Region.NORTH_WEST,
    "Carlisle": Region.NORTH_WEST,
    "Lancaster": Region.NORTH_WEST,
    "Warrington": Region.NORTH_WEST,
    "Wigan": Region.NORTH_WEST,
    "Stockport": Region.NORTH_WEST,
    "Burnley": Region.NORTH_WEST,
    # North East
    "Newcastle": Region.NORTH_EAST,
    "Sunderland": Region.NORTH_EAST,
    "Durham": Region.NORTH_EAST,
    "Middlesbrough": Region.NORTH_EAST,
    "Darlington": Region.NORTH_EAST,
    "Hartlepool": Region.NORTH_EAST,
    "Gateshead": Region.NORTH_EAST,
    # Yorkshire and the Humber
    "Leeds": Region.YORKSHIRE,
    "Sheffield": Region.YORKSHIRE,
    "York": Region.YORKSHIRE,
    "Bradford": Region.YORKSHIRE,
    "Hull": Region.YORKSHIRE,
    "Huddersfield": Region.YORKSHIRE,
    "Doncaster": Region.YORKSHIRE,
    "Wakefield": Region.YORKSHIRE,
    "Harrogate": Region.YORKSHIRE,
    "Scarborough": Region.YORKSHIRE,
    # Scotland
    "Edinburgh": Region.SCOTLAND,
    "Glasgow": Region.SCOTLAND,
    "Aberdeen": Region.SCOTLAND,
    "Dundee": Region.SCOTLAND,
    "Inverness": Region.SCOTLAND,
    "Stirling": Region.SCOTLAND,
    "Perth": Region.SCOTLAND,
    "St Andrews": Region.SCOTLAND,
    "Fort William": Region.SCOTLAND,
    "Dumfries": Region.SCOTLAND,
    # Wales
    "Cardiff": Region.WALES,
    "Swansea": Region.WALES,
    "Newport": Region.WALES,
    "Bangor": Region.WALES,
    "Aberystwyth": Region.WALES,
    "Wrexham": Region.WALES,
    "Llanelli": Region.WALES,
    "Carmarthen": Region.WALES,
    # Northern Ireland
    "Belfast": Region.NORTHERN_IRELAND,
    "Derry": Region.NORTHERN_IRELAND,
    "Londonderry": Region.NORTHERN_IRELAND,
    "Lisburn": Region.NORTHERN_IRELAND,
    "Newry": Region.NORTHERN_IRELAND,
    "Armagh": Region.NORTHERN_IRELAND,
    "Banbridge": Region.NORTHERN_IRELAND,
}

# ---------------------------------------------------------------------------
# Ambiguous words that are also common English words.
# For these, we require the word to appear in a geographic context to count
# as a location match.
# ---------------------------------------------------------------------------

_AMBIGUOUS_NAMES: set[str] = {
    "reading",    # verb / city
    "bath",       # noun / city
    "derby",      # event / city
    "hull",       # noun / city
    "chester",    # first name / city
    "lancaster",  # surname / city
    "durham",     # surname / city
    "lincoln",    # surname / city
    "bolton",     # surname / city
    "york",       # surname / city (New York false-positive too)
    "preston",    # surname / city
    "newport",    # generic / city
    "bangor",     # shared name (Wales / NI)
    "perth",      # Australia / Scotland
    "stirling",   # adjective / city
    "shrewsbury", # could be Shrewsbury Town FC context but is mostly fine
    "wigan",      # surname / city
}

#: Geographic context words that disambiguate an ambiguous location.
_GEO_CONTEXT_WORDS: set[str] = {
    "city", "town", "council", "borough", "county", "area", "region",
    "resident", "residents", "constituency", "mp", "mps", "mayor",
    "station", "airport", "university", "hospital", "school",
    "flooding", "flood", "climate",
    "road", "street", "high street", "centre", "center",
    "north", "south", "east", "west", "near", "based in", "living in",
}

# Pre-compile patterns for performance.
# We build one big alternation so we only scan the text once for location
# candidates.
_LOCATION_NAMES_LOWER: dict[str, str] = {
    name.lower(): name for name in UK_LOCATIONS
}

# Sort by length descending so longer names match first (e.g.
# "Stoke-on-Trent" before "Stoke").
_SORTED_NAMES: list[str] = sorted(
    _LOCATION_NAMES_LOWER.keys(), key=len, reverse=True
)

# Build a compiled regex that matches any known location name as a whole word.
_LOCATION_PATTERN: re.Pattern[str] = re.compile(
    r"\b(" + "|".join(re.escape(name) for name in _SORTED_NAMES) + r")\b",
    re.IGNORECASE,
)

# A small window (chars) around a match to check for geographic context.
_CONTEXT_WINDOW = 80


def _has_geo_context(text: str, match_start: int, match_end: int) -> bool:
    """
    Check whether geographic context words appear near the matched span.

    We look in a window of ``_CONTEXT_WINDOW`` characters before and after
    the match.
    """
    window_start = max(0, match_start - _CONTEXT_WINDOW)
    window_end = min(len(text), match_end + _CONTEXT_WINDOW)
    window = text[window_start:window_end].lower()

    for ctx in _GEO_CONTEXT_WORDS:
        if ctx in window:
            return True
    return False


def _is_new_york(text: str, match_start: int, match_end: int) -> bool:
    """Return True if 'York' is actually part of 'New York'."""
    prefix_start = max(0, match_start - 4)
    prefix = text[prefix_start:match_start].lower().rstrip()
    return prefix.endswith("new")


def find_locations(text: str) -> list[dict[str, Any]]:
    """
    Scan *text* for mentions of known UK locations.

    Returns a list of dicts, each with:

    - ``name`` -- canonical location name (e.g. ``"Manchester"``)
    - ``region`` -- :class:`Region` enum value as a string (e.g. ``"NORTH_WEST"``)

    The function is case-insensitive and tries to avoid common false
    positives for ambiguous words like "Reading" (the verb) or "Bath"
    (the noun).

    Parameters
    ----------
    text:
        Free-form text to search.

    Returns
    -------
    list[dict[str, str]]:
        De-duplicated list of location matches.
    """
    if not text:
        return []

    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for match in _LOCATION_PATTERN.finditer(text):
        matched_lower = match.group(0).lower()

        # Skip duplicates.
        if matched_lower in seen:
            continue

        # Avoid "New York" being detected as "York".
        if matched_lower == "york" and _is_new_york(text, match.start(), match.end()):
            continue

        canonical_name = _LOCATION_NAMES_LOWER[matched_lower]

        # For ambiguous names, require nearby geographic context.
        if matched_lower in _AMBIGUOUS_NAMES:
            if not _has_geo_context(text, match.start(), match.end()):
                continue

        region = UK_LOCATIONS[canonical_name]

        seen.add(matched_lower)
        results.append({
            "name": canonical_name,
            "region": region.value,
        })

    return results
