import os
from fastapi import FastAPI
from backend.main import create_app
import pytest
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
import dotenv
import fakeredis.aioredis
from middlewares import rate_limit_middleware

dotenv.load_dotenv()

url_prefix="/api/v2"

app_test=create_app(test=True)

FREE_TIER_POST=os.getenv("FREE_TIER_POST")
UNFAZE_API_KEY = os.getenv("UNFAZE_API_KEY")


@pytest.fixture
async def ac_client():
    async with LifespanManager(app_test):
        async with AsyncClient(transport=ASGITransport(app=app_test), base_url="http://test") as ac:
            yield ac

@pytest.fixture(autouse=True)
async def fake_redis(monkeypatch):
    # Create a new in‐memory FakeRedis for each test
    fake = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(rate_limit_middleware,"redis_client",fake)
    yield fake
    # flush so each test starts clean
    await fake.flushdb()

@pytest.mark.anyio
async def test_get_requests_within_limit(ac_client):

    short_code = "1e1052"
    input_url = "https://grafana.com/docs/k6/latest/extensions/"

    for i in range(4):
        response = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["Location"] == input_url

@pytest.mark.anyio
async def test_get_requests_beyond_limit(ac_client,fake_redis):

    short_code = "1e1052"
    input_url = "https://grafana.com/docs/k6/latest/extensions/"

    for i in range(5):
        response = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["Location"] == input_url

    response1 = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}", follow_redirects=False)
    assert response1.status_code == 429


@pytest.mark.anyio
async def test_post_shorten_beyond_limit_free_user(ac_client):
    for i in range(5):
        valid_url="https://www.youtube.com/watch?v=nb_fFj_0rq8"
        post_response = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": valid_url,"custom_slug":"freeavtr"}, headers={"Authorization": f"Bearer {FREE_TIER_POST}" })
        assert post_response.status_code == 200
        assert post_response.json() is not None

    response1 = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": valid_url,"custom_slug":"freeavtr"}, headers={"Authorization": f"Bearer {FREE_TIER_POST}" })
    assert response1.status_code == 429

@pytest.mark.anyio
async def test_post_shorten_beyond_limit_normal(ac_client):
    for i in range(3):
        valid_url="https://www.youtube.com/watch?v=nb_fFj_0rq8"
        post_response = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": valid_url,"custom_slug":"avtr"}, headers={"Authorization": f"Bearer {UNFAZE_API_KEY}" })
        assert post_response.status_code == 200
        assert post_response.json() is not None

    response1 = await ac_client.post(f'{url_prefix}/shorten', json={"url_link": valid_url,"custom_slug":"avtr"}, headers={"Authorization": f"Bearer {UNFAZE_API_KEY}" })
    assert response1.status_code == 429
