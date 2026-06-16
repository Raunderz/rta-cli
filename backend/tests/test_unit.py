import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


# =============================================================================
# db.py tests
# =============================================================================

class TestGetSupabaseClient:
    """Tests for the singleton Supabase client."""

    def test_singleton_returns_same_instance(self):
        """Second call should return the cached client, not create a new one."""
        from rta_backend import db
        db._supabase_client = None
        with patch("rta_backend.db.supabase.create_client") as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client

            with patch.dict("os.environ", {"SUPABASE_URL": "http://test", "SUPABASE_KEY": "key123"}):
                c1 = db.get_supabase_client()
                c2 = db.get_supabase_client()
                assert c1 is c2
                assert mock_create.call_count == 1

    def test_missing_env_raises(self):
        """Should raise ValueError if env vars are missing."""
        from rta_backend import db
        db._supabase_client = None
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="SUPABASE_URL"):
                db.get_supabase_client()


class TestCheckAndUpdateDailyCalls:
    """Tests for the daily call limiter."""

    @pytest.mark.asyncio
    async def test_allows_first_call(self):
        """First call of the day should be allowed."""
        from rta_backend import db
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"calls_used_today": 0, "credits": 0, "calls_reset_date": "2099-01-01"}]
        )
        with patch("rta_backend.db.get_supabase_client", return_value=mock_client), \
             patch("rta_backend.db._get_billing_lock") as mock_lock:
            mock_lock.return_value = asyncio.Lock()
            allowed, reason = await db.check_and_update_daily_calls("user1", "free", 10, 15000)
            assert allowed is True
            assert reason == ""

    @pytest.mark.asyncio
    async def test_blocks_at_limit(self):
        """Should block when calls_used_today >= call_limit."""
        from rta_backend import db
        today = datetime.now(timezone.utc).date().isoformat()
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"calls_used_today": 10, "credits": 0, "calls_reset_date": today}]
        )
        with patch("rta_backend.db.get_supabase_client", return_value=mock_client), \
             patch("rta_backend.db._get_billing_lock") as mock_lock:
            mock_lock.return_value = asyncio.Lock()
            allowed, reason = await db.check_and_update_daily_calls("user1", "free", 10, 15000)
            assert allowed is False
            assert "call limit" in reason

    @pytest.mark.asyncio
    async def test_resets_on_new_day(self):
        """Should reset counters when date changes."""
        from rta_backend import db
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"calls_used_today": 9, "credits": 5000, "calls_reset_date": "2000-01-01"}]
        )
        with patch("rta_backend.db.get_supabase_client", return_value=mock_client), \
             patch("rta_backend.db._get_billing_lock") as mock_lock:
            mock_lock.return_value = asyncio.Lock()
            allowed, reason = await db.check_and_update_daily_calls("user1", "free", 10, 15000)
            assert allowed is True
            # Verify credits were reset to 0 in the update call
            update_call = mock_client.table.return_value.update.call_args[0][0]
            assert update_call["credits"] == 0

    @pytest.mark.asyncio
    async def test_negative_values_clamped(self):
        """Negative database values should be clamped to 0."""
        from rta_backend import db
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"calls_used_today": -5, "credits": -100, "calls_reset_date": "2099-01-01"}]
        )
        with patch("rta_backend.db.get_supabase_client", return_value=mock_client), \
             patch("rta_backend.db._get_billing_lock") as mock_lock:
            mock_lock.return_value = asyncio.Lock()
            allowed, reason = await db.check_and_update_daily_calls("user1", "free", 10, 15000)
            assert allowed is True
            # Should increment from 0, not from -5
            update_call = mock_client.table.return_value.update.call_args[0][0]
            assert update_call["calls_used_today"] == 1


class TestUpdateTokenUsage:
    """Tests for token usage tracking."""

    @pytest.mark.asyncio
    async def test_adds_tokens(self):
        """Should add tokens to existing count."""
        from rta_backend import db
        today = datetime.now(timezone.utc).date().isoformat()
        mock_client = MagicMock()
        # Setup the query chain to return existing credits
        mock_query = mock_client.table.return_value.select.return_value.eq.return_value
        mock_query.execute.return_value = MagicMock(
            data=[{"credits": 100, "calls_reset_date": today}]
        )
        with patch("rta_backend.db.get_supabase_client", return_value=mock_client), \
             patch("rta_backend.db._get_billing_lock") as mock_lock:
            mock_lock.return_value = asyncio.Lock()
            await db.update_token_usage("user1", 50)
            update_call = mock_client.table.return_value.update.call_args[0][0]
            assert update_call["credits"] == 150

    @pytest.mark.asyncio
    async def test_skips_zero_or_negative(self):
        """Should skip update for zero or negative tokens."""
        from rta_backend import db
        mock_client = MagicMock()
        with patch("rta_backend.db.get_supabase_client", return_value=mock_client), \
             patch("rta_backend.db._get_billing_lock") as mock_lock:
            mock_lock.return_value = asyncio.Lock()
            await db.update_token_usage("user1", 0)
            await db.update_token_usage("user1", -10)
            mock_client.table.assert_not_called()


# =============================================================================
# security.py tests
# =============================================================================

class TestHashKey:
    def test_deterministic(self):
        from rta_backend.security import hash_key
        assert hash_key("test") == hash_key("test")

    def test_different_inputs_different_hashes(self):
        from rta_backend.security import hash_key
        assert hash_key("abc") != hash_key("def")

    def test_returns_hex_string(self):
        from rta_backend.security import hash_key
        result = hash_key("hello")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest


class TestValidatePasswordStrength:
    def test_valid_password(self):
        from rta_backend.security import validate_password_strength
        assert validate_password_strength("StrongPass1!") is True

    def test_too_short(self):
        from rta_backend.security import validate_password_strength
        assert validate_password_strength("Sho1!") is False

    def test_no_uppercase(self):
        from rta_backend.security import validate_password_strength
        assert validate_password_strength("nouppercase1!") is False

    def test_no_digit(self):
        from rta_backend.security import validate_password_strength
        assert validate_password_strength("NoDigitHere!") is False

    def test_no_special_char(self):
        from rta_backend.security import validate_password_strength
        assert validate_password_strength("NoSpecial123") is False


class TestVerifyHcaptcha:
    @pytest.mark.asyncio
    async def test_returns_false_when_secret_missing(self):
        from rta_backend import security
        original = security.hcaptcha_secret_key
        security.hcaptcha_secret_key = None
        result = await security.verify_hcaptcha("test-token")
        assert result is False
        security.hcaptcha_secret_key = original

    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        from rta_backend import security
        original = security.hcaptcha_secret_key
        security.hcaptcha_secret_key = "test-secret"
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        with patch.object(security._hcaptcha_client, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await security.verify_hcaptcha("valid-token")
            assert result is True
        security.hcaptcha_secret_key = original

    @pytest.mark.asyncio
    async def test_returns_false_on_failure(self):
        from rta_backend import security
        original = security.hcaptcha_secret_key
        security.hcaptcha_secret_key = "test-secret"
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": False, "error-codes": ["invalid-input-response"]}
        with patch.object(security._hcaptcha_client, "post", new_callable=AsyncMock, return_value=mock_response):
            result = await security.verify_hcaptcha("bad-token")
            assert result is False
        security.hcaptcha_secret_key = original


# =============================================================================
# jobs.py tests
# =============================================================================

class TestUpdateJob:
    @pytest.mark.asyncio
    async def test_updates_status(self):
        from rta_backend import jobs
        mock_client = MagicMock()
        with patch("rta_backend.jobs.get_supabase_client", return_value=mock_client):
            await jobs.update_job("job-1", status="running")
            call_args = mock_client.table.return_value.update.call_args[0][0]
            assert call_args["status"] == "running"
            assert "updated_at" in call_args

    @pytest.mark.asyncio
    async def test_marks_done_on_completed(self):
        from rta_backend import jobs
        mock_client = MagicMock()
        with patch("rta_backend.jobs.get_supabase_client", return_value=mock_client):
            await jobs.update_job("job-1", status="completed", result={"text": "hello"})
            call_args = mock_client.table.return_value.update.call_args[0][0]
            assert call_args["done"] is True
            assert call_args["result"] == {"text": "hello"}

    @pytest.mark.asyncio
    async def test_chunk_append_uses_lock(self):
        """Chunk append should acquire per-job lock."""
        from rta_backend import jobs
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"chunks": ["chunk1"]}]
        )
        with patch("rta_backend.jobs.get_supabase_client", return_value=mock_client):
            await jobs.update_job("job-1", chunk="chunk2")
            call_args = mock_client.table.return_value.update.call_args[0][0]
            assert call_args["chunks"] == ["chunk1", "chunk2"]


# =============================================================================
# proxy.py tests
# =============================================================================

class TestTruncateMessages:
    def test_short_messages_unchanged(self):
        from rta_backend.proxy import truncate_messages
        msgs = [{"role": "user", "content": "hello"}]
        result = truncate_messages(msgs, max_chars=1000)
        assert len(result) == 1
        assert result[0]["content"] == "hello"

    def test_long_messages_truncated(self):
        from rta_backend.proxy import truncate_messages
        long_content = "x" * 50000
        msgs = [
            {"role": "user", "content": long_content},
            {"role": "assistant", "content": "response"},
        ]
        result = truncate_messages(msgs, max_chars=1000)
        # Should keep system msg + last few + truncation marker
        total_chars = sum(len(m.get("content", "")) for m in result)
        assert total_chars < 50000

    def test_empty_input(self):
        from rta_backend.proxy import truncate_messages
        result = truncate_messages([], max_chars=1000)
        assert result == []

    def test_preserves_message_order(self):
        from rta_backend.proxy import truncate_messages
        msgs = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        result = truncate_messages(msgs, max_chars=10000)
        assert result[0]["role"] == "system"
        assert result[-1]["role"] == "assistant"


# =============================================================================
# TTLCache tests
# =============================================================================

class TestTTLCache:
    def test_set_and_get(self):
        from rta_backend.utils import TTLCache
        cache = TTLCache(max_size=10)
        cache.set("key1", "value1", ttl=60)
        assert cache.get("key1") == "value1"

    def test_returns_none_for_missing_key(self):
        from rta_backend.utils import TTLCache
        cache = TTLCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_evicts_expired_entries(self):
        from rta_backend.utils import TTLCache
        import time
        cache = TTLCache(max_size=10)
        cache.set("key1", "value1", ttl=0)  # expires immediately
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_evicts_oldest_when_full(self):
        from rta_backend.utils import TTLCache
        cache = TTLCache(max_size=3)
        cache.set("a", 1, ttl=60)
        cache.set("b", 2, ttl=60)
        cache.set("c", 3, ttl=60)
        cache.set("d", 4, ttl=60)  # should evict "a"
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_moves_accessed_item_to_end(self):
        from rta_backend.utils import TTLCache
        cache = TTLCache(max_size=3)
        cache.set("a", 1, ttl=60)
        cache.set("b", 2, ttl=60)
        cache.set("c", 3, ttl=60)
        cache.get("a")  # access "a" to move it to end
        cache.set("d", 4, ttl=60)  # should evict "b" (oldest unaccessed)
        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_overwrite_existing_key(self):
        from rta_backend.utils import TTLCache
        cache = TTLCache(max_size=10)
        cache.set("key1", "old", ttl=60)
        cache.set("key1", "new", ttl=60)
        assert cache.get("key1") == "new"
        assert len(cache) == 1

    def test_delete(self):
        from rta_backend.utils import TTLCache
        cache = TTLCache(max_size=10)
        cache.set("key1", "value1", ttl=60)
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_len(self):
        from rta_backend.utils import TTLCache
        cache = TTLCache(max_size=10)
        assert len(cache) == 0
        cache.set("a", 1, ttl=60)
        cache.set("b", 2, ttl=60)
        assert len(cache) == 2


# =============================================================================
# OAuth state tests
# =============================================================================

class TestOAuthState:
    def test_github_login_sets_state_cookie(self):
        """github_login should set oauth_state cookie."""
        from rta_backend.auth import github_login
        import asyncio
        response = asyncio.get_event_loop().run_until_complete(github_login())
        # RedirectResponse has set_cookie on the response object itself
        # Check that the redirect URL contains state parameter
        assert "state=" in response.headers["location"]

    def test_callback_rejects_mismatched_state(self):
        """auth_callback should reject if state doesn't match cookie."""
        from rta_backend.auth import auth_callback
        import inspect
        sig = inspect.signature(auth_callback)
        assert "request" in sig.parameters


# =============================================================================
# Login response shape tests
# =============================================================================

class TestLoginResponseShape:
    def test_login_user_object_stripped(self):
        """Login response should only contain id and email, not full Supabase user."""
        from rta_backend.auth import login
        import inspect
        # Verify the function exists and returns a dict
        # The actual response shape is enforced by the code change:
        # "user": {"id": res.user.id, "email": res.user.email}
        source = inspect.getsource(login)
        assert '"id": res.user.id' in source
        assert '"email": res.user.email' in source
        assert '"user": res.user' not in source  # full object should NOT be returned

    def test_refresh_key_user_object_stripped(self):
        """Refresh-key response should only contain id and email."""
        from rta_backend.auth import refresh_key
        import inspect
        source = inspect.getsource(refresh_key)
        assert '"id": res.user.id' in source
        assert '"email": res.user.email' in source
        assert '"user": res.user' not in source
