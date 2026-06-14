"""
NLP & Analysis Engine package for the Thermoculture Research Assistant.

Exposes all analysis modules and their primary classes for convenient import::

    from nlp import (
        SentimentAnalyzer,
        ThemeExtractor,
        DiscourseClassifier,
        AnalysisEngine,
    )
"""

from nlp.sentiment import SentimentAnalyzer
from nlp.theme_extractor import ThemeExtractor
from nlp.classifier import DiscourseClassifier
from nlp.analyzer import AnalysisEngine

__all__ = [
    "SentimentAnalyzer",
    "ThemeExtractor",
    "DiscourseClassifier",
    "AnalysisEngine",
]
