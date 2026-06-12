"""
AI Resume Analyzer — API Integration Tests

Tests for auth, candidate, job, scoring, and email endpoints
using FastAPI TestClient.
"""

import os
import pytest
import pytest_asyncio
from pathlib import Path

# Force test database
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_resume_analyzer.db"

from httpx import ASGITransport, AsyncClient
from backend.main import app
from backend.database import engine, Base


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient):
    """Register an admin user and return JWT token."""
    await client.post("/api/auth/register", json={
        "username": "testadmin",
        "email": "admin@test.com",
        "password": "admin123",
        "role": "admin",
        "full_name": "Test Admin",
    })
    resp = await client.post("/api/auth/login", json={
        "username": "testadmin",
        "password": "admin123",
    })
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def candidate_token(client: AsyncClient):
    """Register a candidate user and return JWT token."""
    await client.post("/api/auth/register", json={
        "username": "testcandidate",
        "email": "candidate@test.com",
        "password": "cand123",
        "role": "candidate",
        "full_name": "Test Candidate",
    })
    resp = await client.post("/api/auth/login", json={
        "username": "testcandidate",
        "password": "cand123",
    })
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════
# Auth Tests
# ═══════════════════════════════════════════

@pytest.mark.asyncio
class TestAuth:

    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "pass123",
            "role": "candidate",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["role"] == "candidate"

    async def test_register_duplicate(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "dup",
            "email": "dup@test.com",
            "password": "pass123",
            "role": "candidate",
        })
        resp = await client.post("/api/auth/register", json={
            "username": "dup",
            "email": "dup@test.com",
            "password": "pass123",
            "role": "candidate",
        })
        assert resp.status_code == 400

    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "loginuser",
            "email": "login@test.com",
            "password": "pass123",
            "role": "candidate",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "loginuser",
            "password": "pass123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "wrongpw",
            "email": "wrongpw@test.com",
            "password": "pass123",
            "role": "candidate",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "wrongpw",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    async def test_me_endpoint(self, client: AsyncClient, candidate_token):
        resp = await client.get("/api/auth/me", headers=auth_headers(candidate_token))
        assert resp.status_code == 200
        assert resp.json()["username"] == "testcandidate"


# ═══════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════

@pytest.mark.asyncio
class TestHealth:

    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


# ═══════════════════════════════════════════
# Jobs Tests
# ═══════════════════════════════════════════

@pytest.mark.asyncio
class TestJobs:

    async def test_create_job_admin(self, client: AsyncClient, admin_token):
        resp = await client.post("/api/jobs/", json={
            "title": "Python Dev",
            "description": "Looking for a Python developer with experience.",
            "required_skills": ["Python", "SQL"],
            "preferred_skills": ["Docker"],
            "experience_level": "mid",
        }, headers=auth_headers(admin_token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Python Dev"
        assert data["status"] == "active"

    async def test_create_job_candidate_forbidden(self, client: AsyncClient, candidate_token):
        resp = await client.post("/api/jobs/", json={
            "title": "Test Job",
            "description": "Should fail because candidate is not admin.",
        }, headers=auth_headers(candidate_token))
        assert resp.status_code == 403

    async def test_list_jobs(self, client: AsyncClient, admin_token):
        # Create a job first
        await client.post("/api/jobs/", json={
            "title": "Test Job",
            "description": "Test description for listing.",
        }, headers=auth_headers(admin_token))

        resp = await client.get("/api/jobs/", headers=auth_headers(admin_token))
        assert resp.status_code == 200
        jobs = resp.json()
        assert len(jobs) >= 1

    async def test_close_job(self, client: AsyncClient, admin_token):
        # Create job
        create_resp = await client.post("/api/jobs/", json={
            "title": "To Close",
            "description": "This job will be closed.",
        }, headers=auth_headers(admin_token))
        job_id = create_resp.json()["id"]

        # Close it
        resp = await client.delete(f"/api/jobs/{job_id}", headers=auth_headers(admin_token))
        assert resp.status_code == 200

        # Verify it's closed
        get_resp = await client.get(f"/api/jobs/{job_id}", headers=auth_headers(admin_token))
        assert get_resp.json()["status"] == "closed"


# ═══════════════════════════════════════════
# Candidates Tests
# ═══════════════════════════════════════════

@pytest.mark.asyncio
class TestCandidates:

    async def test_list_candidates_admin_only(self, client: AsyncClient, admin_token, candidate_token):
        # Admin can list
        resp = await client.get("/api/candidates/", headers=auth_headers(admin_token))
        assert resp.status_code == 200

        # Candidate cannot
        resp = await client.get("/api/candidates/", headers=auth_headers(candidate_token))
        assert resp.status_code == 403

    async def test_my_profile(self, client: AsyncClient, candidate_token):
        resp = await client.get("/api/candidates/me", headers=auth_headers(candidate_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "Test Candidate"


# ═══════════════════════════════════════════
# Email Tests
# ═══════════════════════════════════════════

@pytest.mark.asyncio
class TestEmails:

    async def test_send_and_get_logs(self, client: AsyncClient, admin_token):
        # 1. Create a job
        job_resp = await client.post("/api/jobs/", json={
            "title": "Email Test Job",
            "description": "This is a test job description for checking email send flows.",
        }, headers=auth_headers(admin_token))
        assert job_resp.status_code == 201
        job_id = job_resp.json()["id"]

        # 2. Create candidate profile (via registration)
        await client.post("/api/auth/register", json={
            "username": "mailcandidate",
            "email": "mailcandidate@test.com",
            "password": "pass123",
            "role": "candidate",
            "full_name": "Mail Candidate",
        })
        
        # Candidate log in to auto-initialize candidate entry
        c_login = await client.post("/api/auth/login", json={
            "username": "mailcandidate",
            "password": "pass123",
        })
        c_token = c_login.json()["access_token"]
        c_profile_resp = await client.get("/api/candidates/me", headers=auth_headers(c_token))
        candidate_id = c_profile_resp.json()["id"]

        # 3. Send email via Admin
        send_resp = await client.post("/api/emails/send", json={
            "candidate_ids": [candidate_id],
            "job_id": job_id,
            "template": "shortlist",
            "custom_message": "Hello from tests",
        }, headers=auth_headers(admin_token))
        assert send_resp.status_code == 200
        send_data = send_resp.json()
        assert send_data["total"] == 1
        # Since SMTP is offline in test environment, it should fail but log to file
        assert send_data["failed"] == 1
        assert "SMTP failed" in send_data["details"][0]["error_message"]

        # 4. Fetch logs and verify log entry is saved
        logs_resp = await client.get("/api/emails/logs", headers=auth_headers(admin_token))
        assert logs_resp.status_code == 200
        logs = logs_resp.json()
        assert len(logs) >= 1
        assert logs[0]["recipient_email"] == "mailcandidate@test.com"
        assert logs[0]["template_name"] == "shortlist"
        assert logs[0]["status"] == "failed"

