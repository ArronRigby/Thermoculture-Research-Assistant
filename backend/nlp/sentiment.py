"""
Sentiment analysis module for the Thermoculture Research Assistant.

Provides climate-aware sentiment analysis combining VADER with a custom
climate-specific lexicon for more accurate scoring of environmental discourse.
"""

from __future__ import annotations

import re
from typing import List, Dict

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# ---------------------------------------------------------------------------
# Climate-specific lexicon adjustments
# Each value is an additive modifier applied to the compound score.
# Negative values push sentiment toward negative; positive toward positive.
# ---------------------------------------------------------------------------
CLIMATE_NEGATIVE_LEXICON: Dict[str, float] = {
    # Extreme weather / disaster language
    "flooding": -0.15,
    "flood": -0.15,
    "floods": -0.15,
    "disaster": -0.20,
    "disasters": -0.20,
    "crisis": -0.15,
    "crises": -0.15,
    "catastrophe": -0.20,
    "catastrophic": -0.20,
    "devastation": -0.20,
    "devastated": -0.18,
    "heatwave": -0.12,
    "heatwaves": -0.12,
    "drought": -0.15,
    "droughts": -0.15,
    "wildfire": -0.15,
    "wildfires": -0.15,
    "extinction": -0.20,
    "collapse": -0.18,
    "irreversible": -0.15,
    "tipping point": -0.15,
    "sea level rise": -0.12,
    "toxic": -0.12,
    "pollution": -0.12,
    "polluted": -0.12,
    "contaminated": -0.14,
    "deforestation": -0.14,
    "emission": -0.08,
    "emissions": -0.08,
    "carbon footprint": -0.06,
    "ocean acidification": -0.14,
    "melting": -0.10,
    "eroding": -0.10,
    "erosion": -0.10,
    "displacement": -0.12,
    "famine": -0.18,
    "starvation": -0.18,
    "uninhabitable": -0.18,
}

CLIMATE_POSITIVE_LEXICON: Dict[str, float] = {
    # Solutions / hope language
    "renewable": 0.12,
    "renewables": 0.12,
    "solution": 0.12,
    "solutions": 0.12,
    "community action": 0.15,
    "sustainability": 0.12,
    "sustainable": 0.12,
    "green energy": 0.14,
    "clean energy": 0.14,
    "solar power": 0.12,
    "solar panels": 0.12,
    "wind power": 0.12,
    "wind farm": 0.12,
    "heat pump": 0.10,
    "heat pumps": 0.10,
    "insulation": 0.08,
    "retrofit": 0.08,
    "electric vehicle": 0.10,
    "electric vehicles": 0.10,
    "net zero": 0.10,
    "carbon neutral": 0.12,
    "biodiversity": 0.08,
    "rewilding": 0.12,
    "reforestation": 0.14,
    "restoration": 0.10,
    "adaptation": 0.08,
    "resilience": 0.10,
    "resilient": 0.10,
    "regenerative": 0.12,
    "recycling": 0.08,
    "composting": 0.08,
    "conservation": 0.10,
    "transition": 0.06,
    "innovation": 0.10,
    "breakthrough": 0.12,
    "progress": 0.10,
    "community energy": 0.14,
    "local food": 0.08,
    "volunteering": 0.10,
    "collective action": 0.14,
    "activism": 0.06,
    "empowered": 0.10,
    "hopeful": 0.10,
}


def _label_from_score(score: float) -> str:
    """Map a sentiment score in [-1, 1] to a human-readable label."""
    if score < -0.6:
        return "VERY_NEGATIVE"
    elif score < -0.2:
        return "NEGATIVE"
    elif score <= 0.2:
        return "NEUTRAL"
    elif score <= 0.6:
        return "POSITIVE"
    else:
        return "VERY_POSITIVE"


class SentimentAnalyzer:
    """Climate-aware sentiment analyzer combining VADER with a custom lexicon."""

    def __init__(self) -> None:
        self._vader = SentimentIntensityAnalyzer()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_climate_adjustment(self, text: str) -> float:
        """
        Scan *text* for climate-specific terms and return an aggregate
        adjustment value.  Multi-word phrases are checked first so that
        they are not double-counted via their individual words.
        """
        text_lower = text.lower()
        adjustment = 0.0
        matched_spans: list[tuple[int, int]] = []

        # Helper to avoid overlapping matches
        def _overlaps(start: int, end: int) -> bool:
            for s, e in matched_spans:
                if start < e and end > s:
                    return True
            return False

        # Process multi-word phrases first (sorted longest first)
        all_terms = list(CLIMATE_NEGATIVE_LEXICON.items()) + list(
            CLIMATE_POSITIVE_LEXICON.items()
        )
        all_terms.sort(key=lambda t: len(t[0]), reverse=True)

        for term, modifier in all_terms:
            # Use word-boundary matching for single words, substring for phrases
            if " " in term:
                pattern = re.escape(term)
            else:
                pattern = r"\b" + re.escape(term) + r"\b"

            for match in re.finditer(pattern, text_lower):
                if not _overlaps(match.start(), match.end()):
                    adjustment += modifier
                    matched_spans.append((match.start(), match.end()))

        # Clamp total adjustment so it doesn't overwhelm VADER
        return max(-0.5, min(0.5, adjustment))

    def _compute_confidence(self, vader_scores: dict, adjustment: float) -> float:
        """
        Derive a 0-1 confidence value.  When VADER is very certain (high
        absolute compound) and the climate adjustment agrees in sign, we
        are most confident.
        """
        compound = vader_scores["compound"]
        pos = vader_scores["pos"]
        neg = vader_scores["neg"]
        neu = vader_scores["neu"]

        # Base confidence from how polarised the text is
        polarity_strength = abs(compound)

        # Agreement between VADER direction and climate adjustment direction
        if compound != 0 and adjustment != 0:
            agreement = 1.0 if (compound > 0) == (adjustment > 0) else 0.8
        else:
            agreement = 0.9

        # Reduce confidence when the text is very neutral
        neutral_penalty = 1.0 - (neu * 0.3)

        # Combine into a single confidence in [0, 1]
        raw_confidence = polarity_strength * agreement * neutral_penalty

        # Ensure minimum confidence of 0.3 (we always have *some* signal)
        confidence = max(0.3, min(1.0, raw_confidence + 0.3))
        return round(confidence, 4)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> dict:
        """
        Analyse a single piece of text and return sentiment information.

        Returns
        -------
        dict
            ``overall_sentiment`` : float in [-1, 1]
            ``sentiment_label``  : str  one of VERY_NEGATIVE .. VERY_POSITIVE
            ``confidence``       : float in [0, 1]
        """
        if not text or not text.strip():
            return {
                "overall_sentiment": 0.0,
                "sentiment_label": "NEUTRAL",
                "confidence": 0.3,
            }

        vader_scores = self._vader.polarity_scores(text)
        compound = vader_scores["compound"]

        climate_adj = self._compute_climate_adjustment(text)

        # Blend VADER compound with climate adjustment
        adjusted = compound + climate_adj
        # Clamp to [-1, 1]
        adjusted = max(-1.0, min(1.0, adjusted))
        adjusted = round(adjusted, 4)

        label = _label_from_score(adjusted)
        confidence = self._compute_confidence(vader_scores, climate_adj)

        return {
            "overall_sentiment": adjusted,
            "sentiment_label": label,
            "confidence": confidence,
        }

    def analyze_batch(self, texts: List[str]) -> List[dict]:
        """Analyse a list of texts and return a list of sentiment dicts."""
        return [self.analyze(t) for t in texts]
