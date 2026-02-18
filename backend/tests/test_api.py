import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

class TestHealthCheck:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

class TestAuth:
    async def test_register(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Duplicate User",
            },
        )
        assert response.status_code == 400

    async def test_login(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "wrong@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

class TestSources:
    async def test_list_sources(self, client: AsyncClient, auth_headers, test_source):
        response = await client.get("/api/v1/sources/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_source(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/sources/",
            headers=auth_headers,
            json={
                "name": "New Source",
                "source_type": "NEWS",
                "url": "https://example.com",
                "description": "A new source",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Source"

    async def test_get_source(self, client: AsyncClient, auth_headers, test_source):
        response = await client.get(
            f"/api/v1/sources/{test_source.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_source.name

    async def test_delete_source(self, client: AsyncClient, auth_headers, test_source):
        response = await client.delete(
            f"/api/v1/sources/{test_source.id}", headers=auth_headers
        )
        assert response.status_code == 200

class TestSamples:
    async def test_list_samples(self, client: AsyncClient, auth_headers, test_sample):
        response = await client.get("/api/v1/samples/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_create_sample(self, client: AsyncClient, auth_headers, test_source):
        response = await client.post(
            "/api/v1/samples/",
            headers=auth_headers,
            json={
                "title": "Manual Entry Test",
                "content": "This is a manually entered discourse sample about climate change in the UK.",
                "source_id": str(test_source.id),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Manual Entry Test"

    async def test_get_sample(self, client: AsyncClient, auth_headers, test_sample):
        response = await client.get(
            f"/api/v1/samples/{test_sample.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_sample.title

    async def test_filter_samples_by_search(self, client: AsyncClient, auth_headers, test_sample):
        response = await client.get(
            "/api/v1/samples/?search_query=flooding", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_get_sample_not_found(self, client: AsyncClient, auth_headers):
        from uuid import uuid4
        response = await client.get(
            f"/api/v1/samples/{uuid4()}", headers=auth_headers
        )
        assert response.status_code == 404

class TestThemes:
    async def test_list_themes(self, client: AsyncClient, auth_headers, test_theme):
        response = await client.get("/api/v1/themes/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_theme(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/themes/",
            headers=auth_headers,
            json={
                "name": "New Test Theme",
                "description": "A theme for testing",
                "category": "Test",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Test Theme"

class TestLocations:
    async def test_list_locations(self, client: AsyncClient, auth_headers, test_location):
        response = await client.get("/api/v1/locations/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestAnalysis:
    async def test_sentiment_over_time(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/v1/analysis/sentiment-over-time", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_theme_frequency(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/v1/analysis/theme-frequency", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_geographic_distribution(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/v1/analysis/geographic-distribution", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_discourse_types(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/v1/analysis/discourse-types", headers=auth_headers
        )
        assert response.status_code == 200

class TestResearchNotes:
    async def test_create_note(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/notes/",
            headers=auth_headers,
            json={
                "title": "Test Research Note",
                "content": "# Test Note\n\nThis is a test research note with markdown content.",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Research Note"

    async def test_list_notes(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/notes/", headers=auth_headers)
        assert response.status_code == 200

class TestExport:
    async def test_export_samples_json(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/v1/export/samples?format=json", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_export_samples_csv(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/v1/export/samples?format=csv", headers=auth_headers
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_source_requires_auth(client: AsyncClient):
    response = await client.post("/api/v1/sources/", json={
        "name": "Test", "source_type": "NEWS", "is_active": True
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_source_requires_auth(client: AsyncClient):
    response = await client.delete("/api/v1/sources/nonexistent-id")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analysis_theme_frequency_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/analysis/theme-frequency")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_samples_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/export/samples")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_sample_requires_auth(client: AsyncClient):
    response = await client.post("/api/v1/samples/", json={
        "title": "Test", "content": "Test", "source_id": "fake-id"
    })
    assert response.status_code == 401
