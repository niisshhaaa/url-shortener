import pytest
from fastapi import status
from backend.main import app
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
import os,dotenv

dotenv.load_dotenv()


UNAUTH_USER_BATCH = os.getenv("UNAUTH_USER_BATCH")
SUPER_USER_BATCH=os.getenv("SUPER_USER_BATCH")

# Sample payload items
def make_item(url: str, slug=None, exp_date=None, password=None):
    data = {"url_link": url, "custom_slug": slug, "exp_date": exp_date, "password": password}
    return data

@pytest.fixture
async def ac_client():
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

@pytest.mark.anyio
async def test_batch_shorten_success_all(ac_client):
    batch = [
        make_item("https://example.com/1"),
        make_item("https://example.com/2", slug="exampl"),
    ]
    resp = await ac_client.post('/shorten/batch', json=batch, headers={"Authorization": f"Bearer {SUPER_USER_BATCH}"})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "successes" in body and "failures" in body
    assert len(body["successes"]) == 2
    assert body["failures"] == []

@pytest.mark.anyio
async def test_batch_shorten_partial_failure_schema(ac_client):
    batch = [
        make_item("https://example.com/"),
        make_item("not-a-url"),
    ]
    resp = await ac_client.post('/shorten/batch', json=batch, headers={"Authorization": f"Bearer {SUPER_USER_BATCH}"})
    assert resp.status_code == status.HTTP_200_OK
    body = resp.json()
    assert "successes" in body and "failures" in body
    assert len(body["successes"]) == 1
    assert len(body["failures"]) == 1

@pytest.mark.anyio
async def test_batch_shorten_all_schema_failures(ac_client):
    batch = [make_item("ftp://bad-scheme.com")]
    resp = await ac_client.post('/shorten/batch', json=batch, headers={"Authorization": f"Bearer {SUPER_USER_BATCH}"})
    assert resp.status_code == 422
    

@pytest.mark.anyio
async def test_batch_shorten_expiry_in_past(ac_client):
    # Use a date in the past
    past_date = "2000-01-01"
    batch = [make_item("https://example.com/old", exp_date=past_date),
             make_item("https://example.com/1")]
    resp = await ac_client.post('/shorten/batch', json=batch, headers={"Authorization": f"Bearer {SUPER_USER_BATCH}"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["successes"]) == 1
    assert len(body["failures"]) == 1


@pytest.mark.anyio
async def test_batch_shorten_unauth_user(ac_client):
    batch = [make_item("https://example.com/1")]
    resp = await ac_client.post('/shorten/batch', json=batch, headers={"Authorization": f"Bearer {UNAUTH_USER_BATCH}"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid request for Hobby tier without pricing"}
