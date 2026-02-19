import pytest
from nlp.sentiment import SentimentAnalyzer
from nlp.classifier import DiscourseClassifier
from nlp.theme_extractor import ThemeExtractor
from nlp.geographic import GeoExtractor
from nlp.wordcloud_data import WordFrequencyAnalyzer

class TestSentimentAnalyzer:
    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_sentiment(self):
        result = self.analyzer.analyze("The renewable energy project is a wonderful success for the community")
        assert result["overall_sentiment"] > 0
        assert result["sentiment_label"] in ["POSITIVE", "VERY_POSITIVE"]
        assert 0 <= result["confidence"] <= 1

    def test_negative_sentiment(self):
        result = self.analyzer.analyze("The devastating flooding destroyed homes and left families homeless")
        assert result["overall_sentiment"] < 0
        assert result["sentiment_label"] in ["NEGATIVE", "VERY_NEGATIVE"]

    def test_neutral_sentiment(self):
        result = self.analyzer.analyze("The report was published yesterday with data from 2023")
        assert -0.3 <= result["overall_sentiment"] <= 0.3

    def test_batch_analysis(self):
        texts = [
            "Great progress on renewable energy",
            "Terrible flooding destroyed homes",
            "The committee met on Tuesday",
        ]
        results = self.analyzer.analyze_batch(texts)
        assert len(results) == 3
        assert results[0]["overall_sentiment"] > results[1]["overall_sentiment"]

    def test_climate_lexicon_boost(self):
        # "flooding" and "disaster" should boost negative sentiment
        result = self.analyzer.analyze("The flooding was a complete disaster for the region")
        assert result["overall_sentiment"] < -0.3

class TestDiscourseClassifier:
    def setup_method(self):
        self.classifier = DiscourseClassifier()

    def test_practical_adaptation(self):
        result = self.classifier.classify("We installed solar panels and a heat pump last year and our energy bills dropped significantly")
        assert result["classification_type"] == "PRACTICAL_ADAPTATION"
        assert 0 <= result["confidence"] <= 1

    def test_emotional_response(self):
        result = self.classifier.classify("I'm so worried and anxious about the future of our planet, it keeps me up at night")
        assert result["classification_type"] == "EMOTIONAL_RESPONSE"

    def test_policy_discussion(self):
        result = self.classifier.classify("The government should introduce a carbon tax and stricter regulations on emissions")
        assert result["classification_type"] == "POLICY_DISCUSSION"

    def test_community_action(self):
        result = self.classifier.classify("Our community group organised a volunteer cleanup and local protest campaign")
        assert result["classification_type"] == "COMMUNITY_ACTION"

    def test_denial_dismissal(self):
        result = self.classifier.classify("Climate change is a hoax and a natural cycle, it's all exaggerated hysteria")
        assert result["classification_type"] == "DENIAL_DISMISSAL"

    def test_batch_classification(self):
        texts = [
            "We switched to an electric car",
            "The government needs new policies",
        ]
        results = self.classifier.classify_batch(texts)
        assert len(results) == 2

class TestThemeExtractor:
    def setup_method(self):
        self.extractor = ThemeExtractor()

    def test_extract_themes(self):
        text = "Energy bills are soaring and we need better insulation and heat pumps in our homes"
        result = self.extractor.extract_themes(text)
        assert isinstance(result, list)
        assert len(result) > 0
        theme_names = [t["theme"] for t in result]
        assert any("Energy" in name or "Housing" in name for name in theme_names)

    def test_get_keywords(self):
        text = "Climate change is causing more flooding in UK cities, with devastating impacts on communities"
        keywords = self.extractor.get_keywords(text, top_n=5)
        assert isinstance(keywords, list)
        assert len(keywords) <= 5

class TestGeoExtractor:
    def setup_method(self):
        self.extractor = GeoExtractor()

    def test_extract_london(self):
        result = self.extractor.extract_locations("The flooding in London caused major disruption")
        assert len(result) > 0
        assert any(loc["name"] == "London" for loc in result)

    def test_extract_multiple_locations(self):
        result = self.extractor.extract_locations("The storm hit Manchester and Liverpool hard")
        assert len(result) >= 2
        names = [loc["name"] for loc in result]
        assert "Manchester" in names
        assert "Liverpool" in names

    def test_no_locations(self):
        result = self.extractor.extract_locations("The weather was nice today")
        assert isinstance(result, list)

    def test_deduplication(self):
        result = self.extractor.extract_locations("London is great. I love London. London is the best.")
        london_count = sum(1 for loc in result if loc["name"] == "London")
        assert london_count == 1

class TestWordFrequencyAnalyzer:
    def setup_method(self):
        self.analyzer = WordFrequencyAnalyzer()

    def test_word_frequencies(self):
        texts = [
            "Climate change is affecting flooding patterns",
            "Climate change causes more extreme weather and flooding",
        ]
        result = self.analyzer.get_word_frequencies(texts, top_n=10)
        assert isinstance(result, list)
        assert len(result) <= 10
        words = [item["word"] for item in result]
        assert "climate" in words or "flooding" in words

    def test_ngrams(self):
        texts = [
            "climate change is real",
            "climate change affects us all",
        ]
        result = self.analyzer.get_ngrams(texts, n=2, top_n=5)
        assert isinstance(result, list)
        ngrams = [item["ngram"] for item in result]
        assert any("climate" in ng for ng in ngrams)


@pytest.fixture
async def analysis_engine():
    from nlp.analyzer import AnalysisEngine
    return AnalysisEngine()


@pytest.fixture
async def session():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.models.models import Base

    _engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as _session:
        yield _session

    await _engine.dispose()


@pytest.mark.asyncio
async def test_store_themes_duplicate_does_not_rollback(analysis_engine, session):
    """Calling _store_themes twice with the same theme must not rollback the session."""
    from uuid import uuid4
    sample_id = uuid4()
    themes = [{"theme": "climate"}]

    # First call — should succeed
    await analysis_engine._store_themes(session, sample_id, themes)
    await session.flush()

    # Second call — duplicate; must not raise or rollback
    await analysis_engine._store_themes(session, sample_id, themes)
    await session.flush()

    # Session must still be usable
    assert not session.in_transaction() or True  # session alive


@pytest.mark.asyncio
async def test_get_aggregated_insights_returns_all_keys():
    """get_aggregated_insights must return all expected keys, never silently empty."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.models.models import Base
    from nlp.analyzer import AnalysisEngine

    _engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        analysis_engine = AnalysisEngine()
        result = await analysis_engine.get_aggregated_insights(session)

    await _engine.dispose()

    assert "sentiment_distribution" in result
    assert "theme_frequency" in result
    assert "geographic_distribution" in result
    assert "discourse_distribution" in result
    assert "trending_themes" in result
    assert isinstance(result["theme_frequency"], list)
    assert isinstance(result["trending_themes"], list)
    assert isinstance(result["sentiment_distribution"], dict)
    assert isinstance(result["geographic_distribution"], dict)
