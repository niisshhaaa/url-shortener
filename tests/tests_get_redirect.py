import pytest
from backend.main import app
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
import os,dotenv

dotenv.load_dotenv()


@pytest.fixture
async def ac_client():
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

@pytest.mark.anyio
async def test_get_redirect_valid(ac_client):
    short_code = "1e1052"
    input_url = "https://grafana.com/docs/k6/latest/extensions/"
    response = await ac_client.get(f"/redirect?short_code={short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"] == input_url

@pytest.mark.anyio
async def test_get_redirect_not_found(ac_client):
    incorrect_scode = "nocode"
    response = await ac_client.get(f"/redirect?short_code={incorrect_scode}", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {"detail": "Code not found or deleted"}

@pytest.mark.anyio
async def test_get_redirect_expired(ac_client):
    expired_code = "e8b00d2e6"
    response = await ac_client.get(f"/redirect?short_code={expired_code}", follow_redirects=False)
    assert response.status_code == 410
    assert response.json() == {"detail": "Code already expired"} 

@pytest.mark.anyio
async def test_get_protected_correct_pass(ac_client):
    input_url="https://www.blackbox.ai/"
    short_code="boldai"
    response = await ac_client.get(f"/redirect?short_code={short_code}&password=boldai", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"] == input_url


@pytest.mark.anyio
async def test_get_protected_incorrect_pass(ac_client):
    input_url="https://www.blackbox.ai/"
    short_code="boldai"
    response = await ac_client.get(f"/redirect?short_code={short_code}&password=ai", follow_redirects=False)
    assert response.status_code == 403
    assert response.json()=={"detail":"Invalid password as short code is protected"}

@pytest.mark.anyio
async def test_get_protected_no_pass(ac_client):
    input_url="https://www.blackbox.ai/"
    short_code="boldai"
    response = await ac_client.get(f"/redirect?short_code={short_code}", follow_redirects=False)
    assert response.status_code == 403
    assert response.json()=={"detail":"Invalid password as short code is protected"}