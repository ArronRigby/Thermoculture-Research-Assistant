"""
NLP & Analysis Engine package for the Thermoculture Research Assistant.

Exposes all analysis modules and their primary classes for convenient import::

    from nlp import (
        SentimentAnalyzer,
        ThemeExtractor,
        DiscourseClassifier,
        GeoExtractor,
        AnalysisEngine,
        WordFrequencyAnalyzer,
    )
"""

from nlp.sentiment import SentimentAnalyzer
from nlp.theme_extractor import ThemeExtractor
from nlp.classifier import DiscourseClassifier
from nlp.geographic import GeoExtractor
from nlp.analyzer import AnalysisEngine
from nlp.wordcloud_data import WordFrequencyAnalyzer

__all__ = [
    "SentimentAnalyzer",
    "ThemeExtractor",
    "DiscourseClassifier",
    "GeoExtractor",
    "AnalysisEngine",
    "WordFrequencyAnalyzer",
]
