"""
Theme extraction module for the Thermoculture Research Assistant.

Uses TF-IDF vectorisation and Latent Dirichlet Allocation (LDA) to extract
topics from text, then maps them to a predefined set of UK-climate-relevant
themes via cosine similarity.
"""

from __future__ import annotations

import re
from typing import List, Dict, Optional

import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# Climate-specific stop words (high-frequency but uninformative for topics)
# ---------------------------------------------------------------------------
CLIMATE_STOP_WORDS: List[str] = [
    "climate", "change", "global", "warming", "carbon", "environment",
    "environmental", "weather", "temperature", "planet", "earth", "world",
    "uk", "united", "kingdom", "britain", "british", "england", "scotland",
    "wales", "northern", "ireland", "said", "also", "would", "could",
    "people", "think", "know", "just", "like", "get", "got", "going",
    "really", "things", "thing", "lot", "way", "time", "year", "years",
    "new", "one", "two", "much", "many", "make", "made", "need",
    "say", "says", "told", "will", "can", "may", "come", "even",
    "well", "back", "now", "see", "take", "still", "good", "first",
    "last", "long", "great", "little", "right", "old", "big", "use",
    "used", "using",
]


# ---------------------------------------------------------------------------
# Predefined climate themes with representative keywords
# ---------------------------------------------------------------------------
PREDEFINED_THEMES: Dict[str, List[str]] = {
    "Energy and Heating": [
        "energy", "bills", "bill", "electricity", "gas", "fuel",
        "insulation", "heat pump", "heat pumps", "boiler", "boilers",
        "heating", "solar", "panels", "power", "grid", "tariff",
        "meter", "smart meter", "fuel poverty", "efficiency", "draught",
        "cavity wall", "loft insulation", "radiator", "thermostat",
    ],
    "Extreme Weather": [
        "flooding", "flood", "floods", "storm", "storms", "heatwave",
        "heatwaves", "drought", "droughts", "rain", "rainfall", "snow",
        "ice", "wind", "gale", "lightning", "thunder", "cold snap",
        "freeze", "frost", "wildfire", "extreme", "hurricane", "tornado",
        "hot", "hotter", "record temperatures",
    ],
    "Transport": [
        "electric vehicle", "electric vehicles", "ev", "evs", "cycling",
        "bicycle", "bike", "public transport", "bus", "train", "rail",
        "flight", "flights", "flying", "aviation", "car", "cars",
        "driving", "petrol", "diesel", "emissions", "commute", "commuting",
        "walking", "e-bike", "charging", "charge point", "congestion",
    ],
    "Food and Agriculture": [
        "farming", "farm", "farmer", "farmers", "food", "food prices",
        "agriculture", "crop", "crops", "harvest", "growing season",
        "local food", "organic", "livestock", "meat", "dairy", "vegan",
        "vegetarian", "allotment", "garden", "soil", "fertiliser",
        "pesticide", "supply chain", "supermarket", "import",
    ],
    "Policy and Governance": [
        "net zero", "carbon tax", "regulation", "regulations", "government",
        "policy", "policies", "legislation", "parliament", "council",
        "local authority", "minister", "subsidy", "subsidies", "grant",
        "grants", "target", "targets", "mandate", "ban", "law", "act",
        "strategy", "consultation", "planning permission", "budget",
    ],
    "Mental Health and Anxiety": [
        "eco-anxiety", "eco anxiety", "climate grief", "worry", "worried",
        "anxious", "anxiety", "overwhelm", "overwhelmed", "stress",
        "stressed", "depression", "depressed", "hopeless", "hopelessness",
        "fear", "scared", "panic", "dread", "mental health", "wellbeing",
        "therapy", "cope", "coping", "burnout", "exhaustion",
    ],
    "Community Action": [
        "local group", "local groups", "volunteering", "volunteer",
        "volunteers", "protest", "protests", "activism", "activist",
        "campaign", "campaigning", "community", "neighbourhood",
        "collective", "grassroots", "petition", "march", "rally",
        "mutual aid", "cooperative", "co-op", "organising", "engagement",
        "town hall", "citizens assembly",
    ],
    "Biodiversity": [
        "wildlife", "nature", "species", "habitat", "habitats",
        "biodiversity", "ecosystem", "ecosystems", "bird", "birds",
        "insect", "insects", "bee", "bees", "pollinator", "pollinators",
        "tree", "trees", "woodland", "forest", "hedgehog", "fox",
        "river", "ocean", "marine", "coral", "rewilding", "conservation",
        "endangered", "protected",
    ],
    "Housing and Buildings": [
        "retrofit", "retrofitting", "insulation", "planning", "planning permission",
        "green home", "green homes", "epc", "energy performance",
        "new build", "new builds", "housing", "house", "flat",
        "apartment", "building", "buildings", "construction",
        "developer", "property", "rent", "mortgage", "landlord",
        "tenant", "damp", "mould", "ventilation", "double glazing",
    ],
    "Water": [
        "water", "water shortage", "reservoir", "reservoirs",
        "hosepipe ban", "hosepipe bans", "water quality", "sewage",
        "river", "rivers", "stream", "groundwater", "aquifer",
        "drinking water", "tap water", "water company", "water bill",
        "drought", "dry", "rainfall", "flooding", "surface water",
        "leak", "leaks", "pipe", "infrastructure", "treatment",
    ],
}


def _build_theme_vectors(vectorizer: TfidfVectorizer) -> np.ndarray:
    """
    Build TF-IDF vectors for each predefined theme using its keyword list
    as a pseudo-document.
    """
    theme_docs = [
        " ".join(keywords) for keywords in PREDEFINED_THEMES.values()
    ]
    return vectorizer.transform(theme_docs)


class ThemeExtractor:
    """
    Extract themes from text using TF-IDF + LDA, then map discovered
    topics to a set of predefined climate-relevant themes.
    """

    def __init__(self, max_features: int = 5000) -> None:
        self._max_features = max_features
        # Combine sklearn English stop words with our climate stop words
        self._tfidf = TfidfVectorizer(
            max_features=max_features,
            stop_words="english",
            min_df=1,
            max_df=0.95,
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z-]+\b",
        )
        # A secondary vectoriser fitted on theme keyword vocabulary
        # for cosine-similarity matching.
        self._theme_tfidf: Optional[TfidfVectorizer] = None
        self._theme_vectors: Optional[np.ndarray] = None
        self._theme_names: List[str] = list(PREDEFINED_THEMES.keys())
        self._prepare_theme_matcher()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prepare_theme_matcher(self) -> None:
        """Pre-fit a TF-IDF vectoriser on all theme keywords so that we can
        quickly compare any new text against the predefined themes."""
        all_keywords: List[str] = []
        for keywords in PREDEFINED_THEMES.values():
            all_keywords.extend(keywords)

        # Build a small vocabulary from theme keywords
        theme_docs = [
            " ".join(kws) for kws in PREDEFINED_THEMES.values()
        ]

        self._theme_tfidf = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z-]+\b",
        )
        self._theme_vectors = self._theme_tfidf.fit_transform(theme_docs)

    def _match_to_themes(self, text: str) -> List[Dict]:
        """
        Compare *text* against predefined themes using cosine similarity.
        Returns a list of ``{theme, relevance_score}`` dicts sorted by
        descending relevance, filtering out themes with negligible scores.
        """
        if self._theme_tfidf is None or self._theme_vectors is None:
            return []

        text_vec = self._theme_tfidf.transform([text])
        similarities = cosine_similarity(text_vec, self._theme_vectors).flatten()

        results: List[Dict] = []
        for idx, score in enumerate(similarities):
            if score > 0.01:
                results.append({
                    "theme": self._theme_names[idx],
                    "relevance_score": round(float(score), 4),
                })

        results.sort(key=lambda r: r["relevance_score"], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_themes(self, text: str) -> List[Dict]:
        """
        Extract themes from a single text.

        Returns a list of dicts each containing:
        - ``theme``: the predefined theme name
        - ``relevance_score``: cosine similarity in [0, 1]
        """
        if not text or not text.strip():
            return []
        return self._match_to_themes(text)

    def extract_themes_batch(
        self,
        texts: List[str],
        n_topics: int = 10,
    ) -> List[List[Dict]]:
        """
        Extract themes from a batch of texts.  In addition to per-text
        theme matching, an LDA model is fitted across the entire corpus
        to surface latent topics which are then mapped back to predefined
        themes.

        Parameters
        ----------
        texts : list[str]
            The texts to analyse.
        n_topics : int
            Number of latent topics for LDA to discover.

        Returns
        -------
        list[list[dict]]
            One list of theme dicts per input text.
        """
        if not texts:
            return []

        # Filter out empty texts but keep index mapping
        valid: List[tuple[int, str]] = [
            (i, t) for i, t in enumerate(texts) if t and t.strip()
        ]
        if not valid:
            return [[] for _ in texts]

        valid_indices, valid_texts = zip(*valid)

        # Fit TF-IDF + LDA on the corpus
        tfidf_matrix = self._tfidf.fit_transform(valid_texts)
        n_topics_actual = min(n_topics, len(valid_texts), tfidf_matrix.shape[1])
        if n_topics_actual < 1:
            n_topics_actual = 1

        lda = LatentDirichletAllocation(
            n_components=n_topics_actual,
            random_state=42,
            max_iter=20,
            learning_method="online",
        )
        doc_topic_matrix = lda.fit_transform(tfidf_matrix)

        # Build topic keyword strings to match against predefined themes
        feature_names = self._tfidf.get_feature_names_out()
        topic_keywords: List[str] = []
        for topic_weights in lda.components_:
            top_indices = topic_weights.argsort()[-15:][::-1]
            topic_keywords.append(
                " ".join(feature_names[i] for i in top_indices)
            )

        # Map each LDA topic to predefined themes
        topic_theme_map: List[List[Dict]] = []
        for kw_string in topic_keywords:
            topic_theme_map.append(self._match_to_themes(kw_string))

        # Assemble per-document results
        results: List[List[Dict]] = [[] for _ in texts]
        for doc_idx_in_valid, corpus_idx in enumerate(valid_indices):
            text = valid_texts[doc_idx_in_valid]

            # Direct cosine matching for the individual document
            direct_themes = self._match_to_themes(text)

            # Also consider themes from the document's dominant LDA topics
            topic_distribution = doc_topic_matrix[doc_idx_in_valid]
            top_topic_indices = topic_distribution.argsort()[-3:][::-1]

            # Merge LDA-derived themes with direct themes
            theme_scores: Dict[str, float] = {}
            for t in direct_themes:
                theme_scores[t["theme"]] = t["relevance_score"]

            for topic_idx in top_topic_indices:
                topic_weight = topic_distribution[topic_idx]
                if topic_weight < 0.05:
                    continue
                for t in topic_theme_map[topic_idx]:
                    blended = t["relevance_score"] * topic_weight
                    existing = theme_scores.get(t["theme"], 0.0)
                    theme_scores[t["theme"]] = max(existing, blended)

            merged = [
                {"theme": name, "relevance_score": round(score, 4)}
                for name, score in theme_scores.items()
                if score > 0.01
            ]
            merged.sort(key=lambda r: r["relevance_score"], reverse=True)
            results[corpus_idx] = merged

        return results

    def get_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract the most important keywords from *text* using TF-IDF
        scoring.

        Returns up to *top_n* keywords as plain strings.
        """
        if not text or not text.strip():
            return []

        # Fit a fresh single-document vectoriser (unigrams + bigrams)
        vec = TfidfVectorizer(
            stop_words="english",
            max_features=self._max_features,
            ngram_range=(1, 2),
            token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z-]+\b",
        )

        # TF-IDF needs at least one document; we split into sentences for richer scoring
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return []

        try:
            tfidf_matrix = vec.fit_transform(sentences)
        except ValueError:
            # All tokens were stop-words or empty
            return []

        feature_names = vec.get_feature_names_out()
        # Sum TF-IDF scores across all sentences
        summed_scores = tfidf_matrix.sum(axis=0).A1
        top_indices = summed_scores.argsort()[-top_n:][::-1]

        # Filter out climate stop words from results
        climate_stops = set(CLIMATE_STOP_WORDS)
        keywords: List[str] = []
        for idx in top_indices:
            word = feature_names[idx]
            if word.lower() not in climate_stops:
                keywords.append(word)
            if len(keywords) >= top_n:
                break

        return keywords
