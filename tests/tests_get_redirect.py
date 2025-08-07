import json
import pytest
from backend.main import app
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
import dotenv
import fakeredis.aioredis
from backend.url_shortener import repository

dotenv.load_dotenv()

url_prefix="api/v2"


@pytest.fixture
async def ac_client():
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac

# @pytest.fixture(autouse=True)
# def clear_cache_between_tests():
#     cache_clear()
#     yield
#     cache_clear()

@pytest.fixture(autouse=True)
async def fake_redis(monkeypatch):
    # Create a new in‐memory FakeRedis for each test
    fake = fakeredis.aioredis.FakeRedis()
    monkeypatch.setattr(repository,"redis_client",fake)
    yield fake
    # flush so each test starts clean
    await fake.flushdb()


@pytest.mark.anyio
async def test_get_redirect_valid(ac_client):
    short_code = "1e1052"
    input_url = "https://grafana.com/docs/k6/latest/extensions/"
    response = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"] == input_url

@pytest.mark.anyio
async def test_get_redirect_not_found(ac_client):
    incorrect_scode = "nocode"
    response = await ac_client.get(f"{url_prefix}/redirect?short_code={incorrect_scode}", follow_redirects=False)
    assert response.status_code == 404
    assert response.json() == {"detail": "Code not found or deleted"}

@pytest.mark.anyio
async def test_get_redirect_expired(ac_client):
    expired_code = "e8b00d2e6"
    response = await ac_client.get(f"{url_prefix}/redirect?short_code={expired_code}", follow_redirects=False)
    assert response.status_code == 410
    assert response.json() == {"detail": "Code already expired"} 

@pytest.mark.anyio
async def test_get_protected_correct_pass(ac_client):
    input_url="https://www.blackbox.ai/"
    short_code="boldai"
    response = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}&password=boldai", follow_redirects=False)
    # assert response.status_code == 307
    assert response.headers["Location"] == input_url


@pytest.mark.anyio
async def test_get_protected_incorrect_pass(ac_client):
    input_url="https://www.blackbox.ai/"
    short_code="boldai"
    response = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}&password=ai", follow_redirects=False)
    assert response.status_code == 403
    assert response.json()=={"detail":"Invalid password as short code is protected"}

@pytest.mark.anyio
async def test_get_protected_no_pass(ac_client):
    input_url="https://www.blackbox.ai/"
    short_code="boldai"
    response = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}", follow_redirects=False)
    assert response.status_code == 403
    assert response.json()=={"detail":"Invalid password as short code is protected"}

@pytest.mark.anyio
async def test_redirect_uses_cache(ac_client,fake_redis):
    input_url="https://www.isavellatsoulias.com/understanding-phage-therapy"
    short_code="faze"
    redis_key = f"url:{short_code}"

    # Before we hit the endpoint, Redis should have no entry
    assert await fake_redis.get(redis_key) is None

    response = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"] == input_url

   # Now Redis should have a value
    raw = await fake_redis.get(redis_key)
    assert raw is not None

    data = json.loads(raw)
    assert data["original_url"] == input_url
    
    response2 = await ac_client.get(f"{url_prefix}/redirect?short_code={short_code}", follow_redirects=False)
    assert response2.status_code == 307
    assert response2.headers["Location"] == input_url
    assert response2.headers["Location"]==response.headers["Location"]
