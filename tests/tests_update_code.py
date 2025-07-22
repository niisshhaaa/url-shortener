import pytest
from datetime import date, timedelta
from backend.main import app
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
import os,dotenv

dotenv.load_dotenv()

EXPIRED_CODE_USER=os.getenv("EXPIRED_CODE_USER")
UNAUTH_USER_BATCH=os.getenv("UNAUTH_USER_BATCH")
FAZE_API_KEY=os.getenv("FAZE_API_KEY")
UPDATE_USER=os.getenv("UPDATE_USER")

@pytest.fixture
async def ac_client():
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

@pytest.mark.anyio
async def test_update_no_fields_provided(ac_client):
    # Create a new short URL first
    post = await ac_client.post('/shorten', json={"url_link": "https://example.com"}, headers={"Authorization": f"Bearer {UNAUTH_USER_BATCH}" })
    scode = post.json()["short_url"]
    # Now patch without any fields
    resp = await ac_client.patch(f'/shorten/{scode}', headers={"Authorization": f"Bearer {UNAUTH_USER_BATCH}" })
    assert resp.status_code == 422
    # assert resp.json() == {"message": "Please provide fields to update"}

@pytest.mark.anyio
async def test_update_not_found(ac_client):
    resp = await ac_client.patch('/shorten/nonexistent', json={"expiry_date": "2025-12-31"}, headers={"Authorization": f"Bearer {UNAUTH_USER_BATCH}" })
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Short code not found or deleted"

@pytest.mark.anyio
async def test_update_unauthorized(ac_client):
    # Create under valid user
    post = await ac_client.post('/shorten', json={"url_link": "https://example.com"}, headers={"Authorization": f"Bearer {UNAUTH_USER_BATCH}" })
    scode = post.json()["short_url"]
    # Attempt update with other user
    resp = await ac_client.patch(f'/shorten/{scode}', json={"password": "newpass123"}, headers={"Authorization": f"Bearer {FAZE_API_KEY}" })
    assert resp.status_code == 403
    assert resp.json()["detail"] == "Cannot update ,code belongs to another user"

@pytest.mark.anyio
async def test_update_expiry_only(ac_client):
    past_date="2024-05-05"
    post = await ac_client.post('/shorten', json={"url_link": "https://example3.com"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    scode = post.json()["short_url"]
    resp = await ac_client.patch(f'/shorten/{scode}', json={"expiry_date":past_date}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    assert resp.status_code == 200
    data = resp.json()
    assert data["expiry_date"] == past_date
    assert data["short_code"] == scode
    assert data["message"] == "updated short code!"

# @pytest.mark.anyio
# async def test_update_password_only(ac_client):
#     post = await ac_client.post('/shorten', json={"url_link": "https://example5.com"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
#     scode = post.json()["short_url"]
#     resp = await ac_client.patch(f'/shorten/{scode}', json={"new_password": "pass56789"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
#     assert resp.status_code == 200
#     # data = resp.json()
#     # assert data["password"] == "pass12345"
#     # assert data["short_code"] == scode

@pytest.mark.anyio
async def test_update_without_password(ac_client):
    post = await ac_client.post('/shorten', json={"url_link": "https://example5.com"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    scode = post.json()["short_url"]
    resp = await ac_client.patch(f'/shorten/{scode}', json={"new_password": "pass12345"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    assert resp.status_code == 403
    assert resp.json()=={"detail":"Invalid password as short code is protected"}

@pytest.mark.anyio
async def test_update_wrong_password(ac_client):
    post = await ac_client.post('/shorten', json={"url_link": "https://example5.com"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    scode = post.json()["short_url"]
    resp = await ac_client.patch(f'/shorten/{scode}', json={"password":"wrong","new_password": "pass12345"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    assert resp.status_code == 403
    assert resp.json()=={"detail":"Invalid password as short code is protected"}

# @pytest.mark.anyio
# async def test_update_both_fields(ac_client):
#     date="2027-05-05"
#     post = await ac_client.post('/shorten', json={"url_link": "https://example5.com"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
#     scode = post.json()["short_url"]
#     resp = await ac_client.patch(
#         f'/shorten/{scode}',
#         json={"expiry_date": date, "password": "pass56789","new_password":"pass56789"},
#         headers={"Authorization": f"Bearer {UPDATE_USER}" }
#     )
#     assert resp.status_code == 200
#     data = resp.json()
#     assert data["expiry_date"] == date
#     assert data["password"] == "pass56789"

@pytest.mark.anyio
async def test_update_invalid_date_format(ac_client):
    post = await ac_client.post('/shorten', json={"url_link": "https://example3.com"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    scode = post.json()["short_url"]
    resp = await ac_client.patch(f'/shorten/{scode}', json={"expiry_date": "31-12-2025"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    assert resp.status_code == 422

@pytest.mark.anyio
async def test_update_invalid_api_key(ac_client):
    correct_code="spf"
    resp = await ac_client.patch('/shorten/spf', json={"expiry_date": "2026-12-31"}, headers={"Authorization": f"Bearer wrong-key" })
    assert resp.status_code == 403
    assert resp.json() == {"detail": "Invalid API key"}

@pytest.mark.anyio
async def test_update_invalid_authorization(ac_client):
    correct_code="fpimidware"
    resp = await ac_client.patch(f'/shorten/{correct_code}', json={"expiry_date": "2026-12-31"}, headers={"Authorization": f"Bearer {UPDATE_USER}" })
    assert resp.status_code == 403
    assert resp.json() == {"detail": "Cannot update ,code belongs to another user"}
