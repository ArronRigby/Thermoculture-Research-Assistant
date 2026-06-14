import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.models.models import User, ResearchNote, DiscourseSample, JobStatus, CollectionJob
from app.core.security import get_password_hash

pytestmark = pytest.mark.asyncio

class TestBatch7NegativePaths:
    # 1. filter combinations on /samples (date range + theme + search together)
    async def test_filter_combinations_samples(self, client: AsyncClient, auth_headers, db_session, test_source, test_location, test_theme):
        # Create a sample matching all filters
        now = datetime.now(timezone.utc)
        sample1 = DiscourseSample(
            id=str(uuid4()),
            title="Matching flooding sample",
            content="This is about flooding in London.",
            source_id=test_source.id,
            location_id=test_location.id,
            collected_at=now,
        )
        sample1.themes.append(test_theme)
        db_session.add(sample1)

        # Create a sample not matching theme
        sample2 = DiscourseSample(
            id=str(uuid4()),
            title="No theme flooding sample",
            content="This is about flooding in London.",
            source_id=test_source.id,
            location_id=test_location.id,
            collected_at=now,
        )
        db_session.add(sample2)

        # Create a sample not matching search
        sample3 = DiscourseSample(
            id=str(uuid4()),
            title="No search sample",
            content="This is about drought in London.",
            source_id=test_source.id,
            location_id=test_location.id,
            collected_at=now,
        )
        sample3.themes.append(test_theme)
        db_session.add(sample3)

        # Create a sample not matching date
        sample4 = DiscourseSample(
            id=str(uuid4()),
            title="Old flooding sample",
            content="This is about flooding in London.",
            source_id=test_source.id,
            location_id=test_location.id,
            collected_at=now - timedelta(days=10),
        )
        sample4.themes.append(test_theme)
        db_session.add(sample4)

        await db_session.commit()

        # Query with all filters combined (formatted to be URL-safe using 'Z')
        date_from = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        date_to = (now + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        response = await client.get(
            f"/api/v1/samples/?date_from={date_from}&date_to={date_to}&theme_ids={test_theme.id}&search_query=flooding",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(sample1.id)

    # 2. 409 on double job start
    async def test_double_job_start_409(self, client: AsyncClient, auth_headers, db_session, test_source):
        # Create a running/pending job first
        job1 = CollectionJob(
            id=str(uuid4()),
            source_id=test_source.id,
            status=JobStatus.RUNNING,
        )
        db_session.add(job1)
        await db_session.commit()

        # Try to start another job on the same source
        response = await client.post(
            "/api/v1/jobs/start",
            headers=auth_headers,
            json={"source_id": str(test_source.id)}
        )
        assert response.status_code == 409
        assert "already running" in response.json()["detail"]

    # 3. 404s with valid auth
    async def test_404_with_valid_auth(self, client: AsyncClient, auth_headers):
        non_existent_uuid = str(uuid4())
        
        # Source 404
        r1 = await client.get(f"/api/v1/sources/{non_existent_uuid}", headers=auth_headers)
        assert r1.status_code == 404
        
        # Sample 404
        r2 = await client.get(f"/api/v1/samples/{non_existent_uuid}", headers=auth_headers)
        assert r2.status_code == 404

        # Note 404
        r3 = await client.get(f"/api/v1/notes/{non_existent_uuid}", headers=auth_headers)
        assert r3.status_code == 404

    # 4. pagination bounds (page beyond total returns empty items, not error)
    async def test_pagination_bounds(self, client: AsyncClient, auth_headers, test_sample):
        # We have 1 sample in database (test_sample). Page size is 1. Page 2 is beyond total.
        response = await client.get(
            "/api/v1/samples/?page=2&page_size=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 1
        assert data["page"] == 2

    # 5. export with filters
    async def test_export_with_filters(self, client: AsyncClient, auth_headers, db_session, test_source, test_location, test_theme):
        # Create a sample matching all filters
        now = datetime.now(timezone.utc)
        sample1 = DiscourseSample(
            id=str(uuid4()),
            title="Export matching flooding",
            content="This is about flooding in London.",
            source_id=test_source.id,
            location_id=test_location.id,
            collected_at=now,
        )
        sample1.themes.append(test_theme)
        db_session.add(sample1)
        await db_session.commit()

        # JSON Export
        r_json = await client.get(
            f"/api/v1/export/samples?format=json&search_query=Export matching",
            headers=auth_headers
        )
        assert r_json.status_code == 200
        data = r_json.json()
        assert len(data) == 1
        assert data[0]["title"] == "Export matching flooding"

        # CSV Export
        r_csv = await client.get(
            f"/api/v1/export/samples?format=csv&search_query=Export matching",
            headers=auth_headers
        )
        assert r_csv.status_code == 200
        content = r_csv.text
        assert "Export matching flooding" in content

    # 6. notes user-isolation (user A cannot read/update/delete user B's note)
    async def test_notes_user_isolation(self, client: AsyncClient, db_session, test_user, test_sample):
        # Create User B and User B's note
        user_b = User(
            id=str(uuid4()),
            email="user_b@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="User B",
            is_active=True,
        )
        db_session.add(user_b)
        await db_session.commit()

        note_b = ResearchNote(
            id=str(uuid4()),
            title="User B Note",
            content="Confidential content of User B",
            user_id=user_b.id,
        )
        db_session.add(note_b)
        await db_session.commit()

        # Login as User A (test_user)
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"},
        )
        token_a = response.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User A tries to GET User B's note
        r_get = await client.get(f"/api/v1/notes/{note_b.id}", headers=headers_a)
        assert r_get.status_code == 404

        # User A tries to PUT (update) User B's note
        r_put = await client.put(
            f"/api/v1/notes/{note_b.id}",
            headers=headers_a,
            json={"title": "Hacked Title", "content": "Hacked Content"}
        )
        assert r_put.status_code == 404

        # User A tries to DELETE User B's note
        r_delete = await client.delete(f"/api/v1/notes/{note_b.id}", headers=headers_a)
        assert r_delete.status_code == 404

        # User A tries to link sample to User B's note
        r_link = await client.post(
            f"/api/v1/notes/{note_b.id}/link-sample/{test_sample.id}",
            headers=headers_a
        )
        assert r_link.status_code == 404

        # User A tries to unlink sample from User B's note
        r_unlink = await client.post(
            f"/api/v1/notes/{note_b.id}/unlink-sample/{test_sample.id}",
            headers=headers_a
        )
        assert r_unlink.status_code == 404
