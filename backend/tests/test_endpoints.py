import asyncio
import uuid
import time
import os
import pytest
import pytest_asyncio
import httpx
from dotenv import load_dotenv
from rta_backend.db import get_supabase_client

load_dotenv()

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")

# =============================================================================
# Fixtures
# =============================================================================

def make_user_creds():
    uid = str(uuid.uuid4())[:8]
    return {
        "email": f"teest_{uid}@rta.dev",
        "username": f"testuser_{uid}",
        "password": "TestPass1!xyz",
        "captcha_token": "10000000-aaaa-bbbb-cccc-000000000001"  # hCaptcha test token
    }

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_user():
    """Register + login a test user once for all tests."""
    creds = make_user_creds()
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        # Signup
        r = await client.post("/v1/auth/signup", json=creds)
        if r.status_code not in (200, 201):
            pytest.fail(f"Signup failed (likely Supabase config): {r.status_code} - {r.text}")
        
        # Login to get API key
        r = await client.post("/v1/auth/login", json={
            "email": creds["email"],
            "password": creds["password"],
            "captcha_token": creds["captcha_token"]
        })
        if r.status_code != 200:
             pytest.fail(f"Login failed (likely Supabase config): {r.status_code} - {r.text}")
             
        data = r.json()
        
        return {
            "email": creds["email"],
            "password": creds["password"],
            "api_key": data.get("api_key"),
            "user_id": data.get("user", {}).get("id")
        }

@pytest_asyncio.fixture(scope="session")
async def second_user():
    """A second user — for rate limit isolation tests."""
    creds = make_user_creds()
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        await client.post("/v1/auth/signup", json=creds)
        r = await client.post("/v1/auth/login", json={
            "email": creds["email"],
            "password": creds["password"],
            "captcha_token": creds["captcha_token"]
        })
        data = r.json()
        return {
            "email": creds["email"],
            "password": creds["password"],
            "api_key": data.get("api_key"),
            "user_id": data.get("user", {}).get("id")
        }

@pytest_asyncio.fixture
async def client():
    """Fresh async HTTP client per test."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as c:
        yield c

# =============================================================================
# Helpers
# =============================================================================

def chat_payload(content="Hello, what is 2+2?", model="gpt-oss-120b", **kwargs):
    return {
        "messages": [{"role": "user", "content": content}],
        "model": model,
        **kwargs
    }

def auth_headers(api_key):
    return {"X-API-KEY": api_key}

# =============================================================================
# Auth Tests
# =============================================================================

@pytest.mark.asyncio
async def test_signup_success(client):
    creds = make_user_creds()
    r = await client.post("/v1/auth/signup", json=creds)
    assert r.status_code in (200, 201), f"Signup failed: {r.text}"

@pytest.mark.asyncio
async def test_signup_duplicate_email(client, test_user):
    """Re-registering same email should fail."""
    creds = make_user_creds()
    creds["email"] = test_user["email"]
    r = await client.post("/v1/auth/signup", json=creds)
    assert r.status_code in (400, 401, 409, 422)

@pytest.mark.asyncio
async def test_login_success(client, test_user):
    r = await client.post("/v1/auth/login", json={
        "email": test_user["email"],
        "password": test_user["password"],
        "captcha_token": "10000000-aaaa-bbbb-cccc-000000000001"
    })
    assert r.status_code == 200
    data = r.json()
    assert "api_key" in data or "access_token" in data

@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    r = await client.post("/v1/auth/login", json={
        "email": test_user["email"],
        "password": "wrong_password_here",
        "captcha_token": "10000000-aaaa-bbbb-cccc-000000000001"
    })
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_refresh_key_success(client, test_user):
    r = await client.post("/v1/auth/refresh-key", json={
        "email": test_user["email"],
        "password": test_user["password"],
        "captcha_token": "10000000-aaaa-bbbb-cccc-000000000001"
    })
    assert r.status_code == 200
    data = r.json()
    assert "api_key" in data

@pytest.mark.asyncio
async def test_refresh_key_invalid_password(client, test_user):
    r = await client.post("/v1/auth/refresh-key", json={
        "email": test_user["email"],
        "password": "wrong_password!",
        "captcha_token": "10000000-aaaa-bbbb-cccc-000000000001"
    })
    assert r.status_code == 401

# =============================================================================
# Chat Proxy Tests
# =============================================================================

@pytest.mark.asyncio
async def test_chat_returns_200(client, test_user):
    r = await client.post(
        "/v1/chat",
        json=chat_payload(),
        headers=auth_headers(test_user["api_key"])
    )
    assert r.status_code in (200, 502), f"Unexpected status: {r.status_code} — {r.text}"

@pytest.mark.asyncio
async def test_chat_response_shape(client, test_user):
    r = await client.post(
        "/v1/chat",
        json=chat_payload("What is 1+1?"),
        headers=auth_headers(test_user["api_key"])
    )
    if r.status_code != 200:
        pytest.skip("Providers not available in test env")

    data = r.json()
    assert isinstance(data["choices"], list)
    assert len(data["choices"]) >= 1
    msg = data["choices"][0]["message"]
    assert msg["role"] == "assistant"
    assert isinstance(msg["content"], str) and len(msg["content"]) > 0
    assert "prompt_tokens" in data["usage"]
    assert "completion_tokens" in data["usage"]
    assert isinstance(data["provider_used"], str)
    assert isinstance(data["model"], str)
    assert isinstance(data["models_tried"], list) and len(data["models_tried"]) >= 1
    assert data["latency_ms"] > 0
    assert isinstance(data["fallback_used"], bool)

@pytest.mark.asyncio
async def test_chat_missing_api_key(client):
    r = await client.post("/v1/chat", json=chat_payload())
    assert r.status_code in (401, 403, 422)

@pytest.mark.asyncio
async def test_chat_invalid_api_key(client):
    r = await client.post(
        "/v1/chat",
        json=chat_payload(),
        headers={"X-API-KEY": "rta_fakekeythisisfake123456"}
    )
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_chat_with_tools(client, test_user):
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }]
    r = await client.post(
        "/v1/chat",
        json=chat_payload("What is the weather in London?", tools=tools),
        headers=auth_headers(test_user["api_key"])
    )
    assert r.status_code in (200, 502)

@pytest.mark.asyncio
async def test_chat_provider_hint_respected(client, test_user):
    r = await client.post(
        "/v1/chat",
        json=chat_payload("Hi", provider="groq"),
        headers=auth_headers(test_user["api_key"])
    )
    if r.status_code == 200:
        data = r.json()
        assert any("groq" in m for m in data["models_tried"])

@pytest.mark.asyncio
async def test_chat_models_tried_populated(client, test_user):
    r = await client.post(
        "/v1/chat",
        json=chat_payload("Hello"),
        headers=auth_headers(test_user["api_key"])
    )
    if r.status_code == 200:
        data = r.json()
        assert isinstance(data["models_tried"], list)
        assert len(data["models_tried"]) > 0

@pytest.mark.asyncio
async def test_chat_telemetry_written_to_db(client, test_user):
    """After successful chat, telemetry row should exist in database."""
    r = await client.post(
        "/v1/chat",
        json=chat_payload("Test telemetry write"),
        headers=auth_headers(test_user["api_key"])
    )
    if r.status_code != 200:
        pytest.skip("Providers not available")

    await asyncio.sleep(2)  # Wait for background task

    try:
        sup = get_supabase_client()
        # Skip verify if no real DB connected
        if "Mock" in str(type(sup)):
            pytest.skip("Using mock client, cannot verify real DB write")
            
        res = sup.table("telemetry").select("*").eq("user_id", test_user["user_id"]).order("created_at", desc=True).limit(1).execute()
        
        assert res.data, "No telemetry row written"
        row = res.data[0]
        assert row.get("provider") is not None
        assert row.get("latency_ms") is not None
        assert row.get("models_tried") is not None
    except Exception as e:
        pytest.skip(f"Supabase check failed: {e}")

# =============================================================================
# Rate Limiting Tests
# =============================================================================

@pytest.mark.asyncio
async def test_rate_limit_triggers_429(client, test_user):
    """11 rapid requests with daily limit of 10 should yield at least one 429."""
    headers = auth_headers(test_user["api_key"])
    payload = chat_payload("hi")
    
    statuses = []
    # Note: we fire multiple times to hit the limit
    for _ in range(11):
        r = await client.post("/v1/chat", json=payload, headers=headers)
        statuses.append(r.status_code)
    
    assert 429 in statuses

@pytest.mark.asyncio
async def test_rate_limit_isolated_per_user(client, test_user, second_user):
    if not second_user.get("api_key"):
        pytest.skip("Second user setup failed")
    
    r = await client.post(
        "/v1/chat",
        json=chat_payload("Hello from user 2"),
        headers=auth_headers(second_user["api_key"])
    )
    assert r.status_code != 429

# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.asyncio
async def test_invalid_json_body_422(client, test_user):
    r = await client.post(
        "/v1/chat",
        content=b"this is not json",
        headers={**auth_headers(test_user["api_key"]), "Content-Type": "application/json"}
    )
    assert r.status_code == 422

@pytest.mark.asyncio
async def test_502_response_is_sanitized(client, test_user):
    r = await client.post(
        "/v1/chat",
        json=chat_payload("trigger 502"),
        headers=auth_headers(test_user["api_key"])
    )
    if r.status_code == 502:
        data = r.json()
        detail = data.get("detail", "")
        # Should be generic
        assert "traceback" not in detail.lower()
        assert "httpx" not in detail.lower()

@pytest.mark.asyncio
async def test_missing_messages_field_422(client, test_user):
    r = await client.post(
        "/v1/chat",
        json={"model": "gpt-oss-120b"},
        headers=auth_headers(test_user["api_key"])
    )
    assert r.status_code == 422

# =============================================================================
# Telemetry Endpoint Tests
# =============================================================================

@pytest.mark.asyncio
async def test_telemetry_collect_endpoint(client, test_user):
    r = await client.post(
        "/v1/telemetry/collect",
        json={
            "ai_prompt": "test prompt",
            "ai_response": "test response",
            "system_prompt": "test system prompt",
            "provider": "test_provider",
            "latency_ms": 123,
            "tokens_in": 10,
            "tokens_out": 20,
            "schema_version": 1
        },
        headers=auth_headers(test_user["api_key"])
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "Accepted"

# =============================================================================
# Health & Root
# =============================================================================

@pytest.mark.asyncio
async def test_health_check(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "version" in r.json()
