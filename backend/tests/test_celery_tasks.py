"""Tests for Celery task import integrity and basic execution."""
import pytest


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
