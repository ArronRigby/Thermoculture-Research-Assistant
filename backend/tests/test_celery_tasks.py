"""Tests for Celery task import integrity and basic execution."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_celery_app_imports_without_error():
    """Importing celery_app must not raise ImportError."""
    from app.services import celery_app  # noqa: F401


def test_scheduled_collection_task_is_registered():
    """scheduled_collection must be registered in the Celery app."""
    from app.services.celery_app import celery_app as app
    registered = list(app.tasks.keys())
    assert "app.services.celery_app.scheduled_collection" in registered


def test_run_collection_task_is_registered():
    from app.services.celery_app import celery_app as app
    assert "app.services.celery_app.run_collection_task" in app.tasks


def test_analyze_sample_task_is_registered():
    from app.services.celery_app import celery_app as app
    assert "app.services.celery_app.analyze_sample_task" in app.tasks


def test_scheduled_collection_runs_with_no_active_sources():
    """scheduled_collection must complete without error when no active sources exist."""
    # Mock async_session_factory to return an empty result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_factory = MagicMock(return_value=mock_session)

    with patch("app.core.database.async_session_factory", mock_factory):
        from app.services.celery_app import scheduled_collection
        result = scheduled_collection()

    assert result["status"] == "completed"
    assert result["dispatched_count"] == 0
    assert result["dispatched"] == []
