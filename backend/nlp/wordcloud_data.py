"""
Word frequency analysis module for the Thermoculture Research Assistant.

Provides word and n-gram frequency counts suitable for word cloud generation,
with climate-specific stop word filtering and lemmatisation.
"""

from __future__ import annotations

import re
import string
from collections import Counter
from typing import List, Dict

from sklearn.feature_extraction.text import CountVectorizer


# ---------------------------------------------------------------------------
# Extended stop words
# Standard English stop words plus climate domain words that appear so
# frequently in the corpus that they add noise rather than insight.
# ---------------------------------------------------------------------------
ENGLISH_STOP_WORDS: set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "can't", "cannot", "could", "couldn't", "d", "did", "didn't", "do",
    "does", "doesn't", "doing", "don", "don't", "down", "during", "each",
    "few", "for", "from", "further", "get", "got", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's",
    "her", "here", "here's", "hers", "herself", "him", "himself", "his",
    "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "just", "let's", "ll",
    "m", "me", "might", "mightn't", "more", "most", "mustn't", "my",
    "myself", "needn't", "no", "nor", "not", "now", "o", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
    "out", "over", "own", "re", "s", "same", "shan't", "she", "she'd",
    "she'll", "she's", "should", "shouldn't", "so", "some", "such", "t",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "us", "ve", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when",
    "when's", "where", "where's", "which", "while", "who", "who's", "whom",
    "why", "why's", "will", "with", "won't", "would", "wouldn't", "you",
    "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves",
}

CLIMATE_STOP_WORDS: set[str] = {
    "climate", "change", "global", "warming", "carbon", "environment",
    "environmental", "weather", "temperature", "planet", "earth", "world",
    "uk", "united", "kingdom", "britain", "british", "england", "scotland",
    "wales", "northern", "ireland", "said", "also", "would", "could",
    "people", "think", "know", "like", "get", "going", "really", "things",
    "thing", "lot", "way", "time", "year", "years", "new", "one", "two",
    "much", "many", "make", "made", "need", "say", "says", "told", "come",
    "even", "well", "back", "see", "take", "still", "good", "first",
    "last", "long", "great", "little", "right", "old", "big", "use",
    "used", "using",
}

ALL_STOP_WORDS: set[str] = ENGLISH_STOP_WORDS | CLIMATE_STOP_WORDS


# ---------------------------------------------------------------------------
# Simple rule-based lemmatiser
# Avoids the heavy NLTK/spaCy download for deployment simplicity.
# ---------------------------------------------------------------------------

# Common suffix rules (applied in order; first match wins)
_SUFFIX_RULES: List[tuple[str, str]] = [
    ("ies", "y"),       # communities -> community
    ("ves", "f"),       # lives -> life
    ("ses", "s"),       # analyses -> analysis (approximate)
    ("ches", "ch"),     # beaches -> beach
    ("shes", "sh"),     # crashes -> crash
    ("xes", "x"),       # boxes -> box
    ("zes", "z"),       # buzzes -> buzz
    ("ness", ""),       # happiness -> happi  (rough but groups well)
    ("ment", ""),       # government -> govern
    ("ing", ""),        # flooding -> flood  (will also catch gerunds)
    ("tion", ""),       # adaptation -> adapta
    ("sion", ""),       # emission -> emis
    ("ed", ""),         # flooded -> flood
    ("ly", ""),         # extremely -> extreme
    ("er", ""),         # warmer -> warm
    ("est", ""),        # warmest -> warm
    ("s", ""),          # floods -> flood
]

# Irregular mappings for words we care about
_IRREGULAR: Dict[str, str] = {
    "communities": "community",
    "policies": "policy",
    "families": "family",
    "cities": "city",
    "countries": "country",
    "energies": "energy",
    "batteries": "battery",
    "activities": "activity",
    "strategies": "strategy",
    "stories": "story",
    "children": "child",
    "women": "woman",
    "men": "man",
    "people": "person",
    "lives": "life",
    "leaves": "leaf",
    "wolves": "wolf",
    "crises": "crisis",
    "analyses": "analysis",
    "flooding": "flood",
    "flooded": "flood",
    "floods": "flood",
    "heated": "heat",
    "heating": "heat",
    "heats": "heat",
    "insulating": "insulation",
    "insulated": "insulation",
    "recycled": "recycle",
    "recycling": "recycle",
    "renewable": "renewable",
    "renewables": "renewable",
    "emissions": "emission",
    "polluting": "pollution",
    "polluted": "pollution",
    "protesting": "protest",
    "protested": "protest",
    "protests": "protest",
    "volunteering": "volunteer",
    "volunteered": "volunteer",
    "volunteers": "volunteer",
    "worried": "worry",
    "worrying": "worry",
    "worries": "worry",
    "anxious": "anxiety",
    "farming": "farm",
    "farmed": "farm",
    "farmers": "farmer",
    "growing": "grow",
    "grown": "grow",
    "drought": "drought",
    "droughts": "drought",
    "heatwave": "heatwave",
    "heatwaves": "heatwave",
    "storms": "storm",
    "stormy": "storm",
}


def _lemmatize(word: str) -> str:
    """Simple rule-based lemmatisation."""
    lower = word.lower()

    # Check irregulars first
    if lower in _IRREGULAR:
        return _IRREGULAR[lower]

    # Apply suffix rules
    if len(lower) > 4:
        for suffix, replacement in _SUFFIX_RULES:
            if lower.endswith(suffix):
                candidate = lower[: -len(suffix)] + replacement
                # Only accept if the stem is at least 3 chars
                if len(candidate) >= 3:
                    return candidate

    return lower


def _clean_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    # Remove URLs
    text = re.sub(r"https?://\S+", " ", text)
    # Remove punctuation except hyphens inside words
    text = re.sub(r"[^\w\s-]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


class WordFrequencyAnalyzer:
    """
    Analyse word and n-gram frequencies across a corpus of texts,
    with stop word removal and lemmatisation.
    """

    def __init__(self) -> None:
        self._stop_words = ALL_STOP_WORDS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_word_frequencies(
        self,
        texts: List[str],
        top_n: int = 100,
    ) -> List[Dict]:
        """
        Compute word frequencies across all *texts*.

        Returns up to *top_n* entries, each a dict with:
        - ``word``      : the lemmatised word
        - ``count``     : absolute count across all texts
        - ``frequency`` : relative frequency (count / total_words)
        """
        if not texts:
            return []

        counter: Counter = Counter()
        total_words = 0

        for text in texts:
            cleaned = _clean_text(text)
            tokens = cleaned.split()
            for token in tokens:
                # Strip leading/trailing hyphens
                token = token.strip("-")
                if not token or len(token) < 2:
                    continue
                lemma = _lemmatize(token)
                if lemma in self._stop_words or len(lemma) < 2:
                    continue
                # Skip tokens that are purely numeric
                if lemma.isdigit():
                    continue
                counter[lemma] += 1
                total_words += 1

        if total_words == 0:
            return []

        most_common = counter.most_common(top_n)
        return [
            {
                "word": word,
                "count": count,
                "frequency": round(count / total_words, 6),
            }
            for word, count in most_common
        ]

    def get_ngrams(
        self,
        texts: List[str],
        n: int = 2,
        top_n: int = 50,
    ) -> List[Dict]:
        """
        Compute n-gram frequencies across all *texts*.

        Parameters
        ----------
        texts : list[str]
            Input texts.
        n : int
            Size of the n-gram (2 = bigram, 3 = trigram, etc.).
        top_n : int
            Maximum number of n-grams to return.

        Returns
        -------
        list[dict]
            Each dict has keys ``ngram`` (str) and ``count`` (int).
        """
        if not texts or n < 1:
            return []

        # Pre-process: clean, tokenize, lemmatize, remove stop words
        processed_docs: List[str] = []
        for text in texts:
            cleaned = _clean_text(text)
            tokens = cleaned.split()
            kept: List[str] = []
            for token in tokens:
                token = token.strip("-")
                if not token or len(token) < 2:
                    continue
                lemma = _lemmatize(token)
                if lemma in self._stop_words or len(lemma) < 2:
                    continue
                if lemma.isdigit():
                    continue
                kept.append(lemma)
            processed_docs.append(" ".join(kept))

        # Filter out empty docs
        processed_docs = [d for d in processed_docs if d.strip()]
        if not processed_docs:
            return []

        try:
            vectorizer = CountVectorizer(
                ngram_range=(n, n),
                min_df=1,
                token_pattern=r"(?u)\b\w[\w-]+\b",
            )
            ngram_matrix = vectorizer.fit_transform(processed_docs)
        except ValueError:
            return []

        feature_names = vectorizer.get_feature_names_out()
        counts = ngram_matrix.sum(axis=0).A1

        # Sort by count descending
        top_indices = counts.argsort()[::-1][:top_n]

        return [
            {
                "ngram": feature_names[idx],
                "count": int(counts[idx]),
            }
            for idx in top_indices
            if counts[idx] > 0
        ]
