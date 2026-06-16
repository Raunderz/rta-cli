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
