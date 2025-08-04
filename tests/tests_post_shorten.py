import pytest
from backend.main import app
from fastapi import status
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
from config.config import configSettgs
import os,dotenv

dotenv.load_dotenv()
url_prefix="api/v2"

valid_url="https://www.isavellatsoulias.com/understanding-phage-therapy"


FAZE_API_KEY = os.getenv("FAZE_API_KEY")
UNFAZE_API_KEY = os.getenv("UNFAZE_API_KEY")

@pytest.fixture
async def ac_client():
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

@pytest.mark.anyio
async def test_post_shorten_valid(ac_client):
    post_response = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": valid_url}, headers={"Authorization": f"Bearer {FAZE_API_KEY}" })
    assert post_response.status_code == status.HTTP_200_OK
    assert post_response.json() is not None

@pytest.mark.anyio
async def test_post_shorten_invalid_api_key(ac_client):
    response = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": valid_url}, headers={"Authorization": "apikeyapikeyapikey"})
    assert response.status_code == status.HTTP_403_FORBIDDEN or status.HTTP_401_UNAUTHORIZED

@pytest.mark.anyio
async def test_post_shorten_invalid_url(ac_client):
    response = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": ""}, headers={"Authorization": f"Bearer {FAZE_API_KEY}"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.anyio
async def test_post_shorten_with_expiry(ac_client):
    response = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": "https://example.com/1", "exp_date": "2045-08-01"}, headers={"Authorization": f"Bearer {FAZE_API_KEY}" })
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is not None

@pytest.mark.anyio
async def test_post_shorten_slug(ac_client):
    response = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": valid_url, "custom_slug":"faze"}, headers = {"Authorization": f"Bearer {FAZE_API_KEY}"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is not None

@pytest.mark.anyio
async def test_post_shorten_slug_not_unq_newuser(ac_client):
    response = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": valid_url, "custom_slug": "faze"}, headers={"Authorization": f"Bearer {UNFAZE_API_KEY}"})
    assert response.status_code == status.HTTP_409_CONFLICT