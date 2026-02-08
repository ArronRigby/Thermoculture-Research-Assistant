"""
Discourse classification module for the Thermoculture Research Assistant.

Classifies text into discourse categories relevant to climate change
conversation using weighted keyword scoring with normalisation.
"""

from __future__ import annotations

import re
from typing import List, Dict, Tuple


# ---------------------------------------------------------------------------
# Discourse categories and their weighted keyword sets
#
# Each keyword carries a weight.  Multi-word phrases are matched as
# sub-strings (case-insensitive); single words are matched on word
# boundaries.  Higher weight = stronger signal for that category.
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS: Dict[str, List[Tuple[str, float]]] = {
    "PRACTICAL_ADAPTATION": [
        ("installed", 1.2),
        ("switched to", 1.5),
        ("we now use", 1.5),
        ("heat pump", 1.4),
        ("heat pumps", 1.4),
        ("insulation", 1.2),
        ("solar panels", 1.4),
        ("solar panel", 1.4),
        ("changed habits", 1.3),
        ("adapted", 1.0),
        ("practical", 0.8),
        ("diy", 0.7),
        ("retrofit", 1.2),
        ("retrofitting", 1.2),
        ("double glazing", 1.2),
        ("loft insulation", 1.3),
        ("cavity wall", 1.2),
        ("draught proofing", 1.2),
        ("composting", 1.0),
        ("rainwater harvesting", 1.3),
        ("energy saving", 1.2),
        ("smart meter", 1.0),
        ("led bulbs", 1.0),
        ("electric vehicle", 1.2),
        ("cycling", 0.8),
        ("growing food", 1.1),
        ("allotment", 0.9),
        ("reduced", 0.6),
        ("cut down", 0.7),
        ("lowered", 0.6),
        ("upgraded", 0.9),
        ("implemented", 0.8),
        ("set up", 0.6),
        ("built", 0.5),
    ],
    "EMOTIONAL_RESPONSE": [
        ("worried", 1.2),
        ("scared", 1.3),
        ("anxious", 1.3),
        ("hopeful", 1.0),
        ("frustrated", 1.2),
        ("angry", 1.2),
        ("sad", 1.0),
        ("grief", 1.4),
        ("overwhelmed", 1.3),
        ("feel", 0.6),
        ("feeling", 0.7),
        ("terrified", 1.4),
        ("depressed", 1.3),
        ("despair", 1.4),
        ("helpless", 1.3),
        ("hopeless", 1.3),
        ("eco-anxiety", 1.6),
        ("eco anxiety", 1.6),
        ("climate grief", 1.6),
        ("panic", 1.1),
        ("dread", 1.2),
        ("upset", 1.0),
        ("rage", 1.2),
        ("fury", 1.2),
        ("heartbroken", 1.3),
        ("tearful", 1.1),
        ("sleepless", 1.0),
        ("nightmare", 1.0),
        ("stress", 1.0),
        ("stressed", 1.1),
        ("crying", 1.1),
        ("emotional", 0.8),
        ("mood", 0.6),
        ("mental health", 1.2),
    ],
    "POLICY_DISCUSSION": [
        ("government", 1.2),
        ("policy", 1.3),
        ("regulation", 1.3),
        ("regulations", 1.3),
        ("tax", 1.0),
        ("subsidy", 1.2),
        ("subsidies", 1.2),
        ("legislation", 1.4),
        ("parliament", 1.3),
        ("council", 1.0),
        ("mandate", 1.2),
        ("ban", 0.8),
        ("net zero", 1.3),
        ("carbon tax", 1.5),
        ("minister", 1.1),
        ("mp", 0.8),
        ("mps", 0.8),
        ("secretary of state", 1.2),
        ("green paper", 1.3),
        ("white paper", 1.3),
        ("consultation", 1.0),
        ("planning permission", 1.0),
        ("building regulations", 1.3),
        ("target", 0.7),
        ("targets", 0.7),
        ("strategy", 0.8),
        ("budget", 0.8),
        ("grant", 0.7),
        ("grants", 0.7),
        ("act", 0.5),
        ("law", 0.8),
        ("laws", 0.8),
        ("vote", 0.7),
        ("election", 0.7),
        ("manifesto", 1.0),
        ("devolution", 1.0),
    ],
    "COMMUNITY_ACTION": [
        ("community", 1.0),
        ("group", 0.6),
        ("volunteer", 1.2),
        ("volunteering", 1.3),
        ("volunteers", 1.2),
        ("protest", 1.3),
        ("protests", 1.3),
        ("campaign", 1.2),
        ("campaigning", 1.2),
        ("together", 0.7),
        ("neighbourhood", 1.0),
        ("local action", 1.5),
        ("collective", 1.0),
        ("grassroots", 1.4),
        ("petition", 1.3),
        ("march", 0.8),
        ("rally", 1.1),
        ("rally", 1.1),
        ("mutual aid", 1.4),
        ("cooperative", 1.1),
        ("co-op", 1.0),
        ("organising", 1.0),
        ("organizing", 1.0),
        ("fundraising", 1.0),
        ("charity", 0.8),
        ("parish", 0.8),
        ("town hall", 1.0),
        ("citizens assembly", 1.4),
        ("transition town", 1.5),
        ("litter pick", 1.1),
        ("tree planting", 1.2),
        ("community garden", 1.4),
        ("repair cafe", 1.4),
        ("sharing", 0.5),
        ("joining", 0.6),
    ],
    "DENIAL_DISMISSAL": [
        ("hoax", 1.8),
        ("natural cycle", 1.8),
        ("natural cycles", 1.8),
        ("not real", 1.6),
        ("exaggerated", 1.5),
        ("scam", 1.7),
        ("waste of money", 1.6),
        ("alarmist", 1.6),
        ("not proven", 1.5),
        ("hysteria", 1.5),
        ("conspiracy", 1.6),
        ("made up", 1.5),
        ("nonsense", 1.3),
        ("rubbish", 1.1),
        ("myth", 1.4),
        ("propaganda", 1.5),
        ("fear mongering", 1.5),
        ("fearmongering", 1.5),
        ("overblown", 1.4),
        ("nothing to worry", 1.4),
        ("always been changing", 1.5),
        ("sun", 0.3),
        ("solar activity", 1.3),
        ("fake", 1.4),
        ("fraud", 1.5),
        ("junk science", 1.7),
        ("no evidence", 1.4),
        ("don't believe", 1.2),
        ("scare tactics", 1.5),
        ("virtue signalling", 1.3),
        ("virtue signaling", 1.3),
        ("woke", 0.8),
        ("nanny state", 1.3),
    ],
}


class DiscourseClassifier:
    """
    Classify text into discourse categories using weighted keyword scoring.

    Categories
    ----------
    - PRACTICAL_ADAPTATION : Descriptions of practical steps taken or planned.
    - EMOTIONAL_RESPONSE   : Expressions of feelings about climate change.
    - POLICY_DISCUSSION    : Discussion of government policy, law, regulation.
    - COMMUNITY_ACTION     : References to collective / community efforts.
    - DENIAL_DISMISSAL     : Dismissal, denial, or scepticism of climate change.
    """

    CATEGORIES: List[str] = list(CATEGORY_KEYWORDS.keys())

    def __init__(self) -> None:
        # Pre-compile regex patterns for every keyword in every category
        self._patterns: Dict[str, List[Tuple[re.Pattern, float]]] = {}
        for category, keyword_weights in CATEGORY_KEYWORDS.items():
            patterns: List[Tuple[re.Pattern, float]] = []
            for keyword, weight in keyword_weights:
                if " " in keyword:
                    # Multi-word phrase -- match as substring
                    pat = re.compile(re.escape(keyword), re.IGNORECASE)
                else:
                    # Single word -- match on word boundaries
                    pat = re.compile(
                        r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE
                    )
                patterns.append((pat, weight))
            self._patterns[category] = patterns

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_text(self, text: str) -> Dict[str, float]:
        """
        Return raw weighted scores for each category.
        Each match of a keyword adds its weight to the category score.
        Multiple occurrences of the same keyword contribute additional
        score but with diminishing returns (sqrt scaling on count).
        """
        scores: Dict[str, float] = {cat: 0.0 for cat in self.CATEGORIES}

        for category, patterns in self._patterns.items():
            for pat, weight in patterns:
                matches = pat.findall(text)
                count = len(matches)
                if count > 0:
                    # Diminishing returns for repeated matches
                    scores[category] += weight * (count ** 0.5)

        return scores

    @staticmethod
    def _normalise(scores: Dict[str, float]) -> Dict[str, float]:
        """Normalise scores so they sum to 1.0.  If all scores are zero,
        distribute weight equally."""
        total = sum(scores.values())
        if total == 0:
            equal = 1.0 / len(scores)
            return {cat: round(equal, 4) for cat in scores}
        return {cat: round(val / total, 4) for cat, val in scores.items()}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, text: str) -> dict:
        """
        Classify a single piece of text.

        Returns
        -------
        dict
            ``classification_type`` : str   -- highest-scoring category
            ``confidence``          : float -- normalised score of the winner
            ``all_scores``          : dict  -- normalised scores for every category
        """
        if not text or not text.strip():
            normalised = self._normalise({cat: 0.0 for cat in self.CATEGORIES})
            return {
                "classification_type": self.CATEGORIES[0],
                "confidence": round(1.0 / len(self.CATEGORIES), 4),
                "all_scores": normalised,
            }

        raw_scores = self._score_text(text)
        normalised = self._normalise(raw_scores)

        # Pick the highest scoring category
        best_category = max(normalised, key=normalised.get)  # type: ignore[arg-type]
        confidence = normalised[best_category]

        return {
            "classification_type": best_category,
            "confidence": confidence,
            "all_scores": normalised,
        }

    def classify_batch(self, texts: List[str]) -> List[dict]:
        """Classify a list of texts and return a list of classification dicts."""
        return [self.classify(t) for t in texts]
