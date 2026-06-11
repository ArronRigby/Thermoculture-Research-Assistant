import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import SavedQuote, DiscourseSample, ResearchNote


@pytest.mark.asyncio
async def test_quotes_endpoints_require_auth(client: AsyncClient, test_sample: DiscourseSample):
    # GET /quotes/ requires auth
    res = await client.get("/api/v1/quotes/")
    assert res.status_code == 401

    # POST /quotes/ requires auth
    res = await client.post("/api/v1/quotes/", json={"sample_id": test_sample.id, "text": "Some text"})
    assert res.status_code == 401

    # DELETE /quotes/{id} requires auth
    res = await client.delete("/api/v1/quotes/some-id")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_create_and_get_quote(client: AsyncClient, auth_headers: dict, test_sample: DiscourseSample):
    # Save a quote
    payload = {
        "sample_id": test_sample.id,
        "text": "This is a saved quote snippet."
    }
    response = await client.post("/api/v1/quotes/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["sample_id"] == test_sample.id
    assert data["text"] == payload["text"]
    assert "source_name" in data
    assert "citation" in data
    assert "saved_at" in data
    quote_id = data["id"]

    # Get quotes list
    response = await client.get("/api/v1/quotes/", headers=auth_headers)
    assert response.status_code == 200
    quotes = response.json()
    assert len(quotes) == 1
    assert quotes[0]["id"] == quote_id
    assert quotes[0]["text"] == payload["text"]


@pytest.mark.asyncio
async def test_delete_quote(client: AsyncClient, auth_headers: dict, test_sample: DiscourseSample, db_session: AsyncSession):
    # First save a quote
    payload = {
        "sample_id": test_sample.id,
        "text": "Quote to be deleted."
    }
    response = await client.post("/api/v1/quotes/", json=payload, headers=auth_headers)
    quote_id = response.json()["id"]

    # Delete quote
    response = await client.delete(f"/api/v1/quotes/{quote_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify deleted
    response = await client.get("/api/v1/quotes/", headers=auth_headers)
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_delete_quote_owner_only(client: AsyncClient, auth_headers: dict, test_sample: DiscourseSample, db_session: AsyncSession):
    # Create another user and get auth headers
    from uuid import uuid4
    from app.models.models import User
    from app.core.security import get_password_hash
    
    other_user = User(
        id=str(uuid4()),
        email="other@example.com",
        hashed_password=get_password_hash("otherpassword123"),
        full_name="Other User",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.commit()
    
    # Login as other user
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "other@example.com", "password": "otherpassword123"},
    )
    other_token = response.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Save quote as original test_user
    payload = {
        "sample_id": test_sample.id,
        "text": "Owner-only test quote."
    }
    response = await client.post("/api/v1/quotes/", json=payload, headers=auth_headers)
    quote_id = response.json()["id"]

    # Try to delete quote as other user
    response = await client.delete(f"/api/v1/quotes/{quote_id}", headers=other_headers)
    assert response.status_code == 403

    # Delete as owner succeeds
    response = await client.delete(f"/api/v1/quotes/{quote_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_note_creation_empty_content(client: AsyncClient, auth_headers: dict):
    # Creating a note with empty content should be allowed now
    payload = {
        "title": "A note with empty content",
        "content": ""
    }
    response = await client.post("/api/v1/notes/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["content"] == ""
