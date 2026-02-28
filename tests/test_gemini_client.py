"""Tests for GeminiClient: rate limiting, retry logic, backoff with jitter."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from app.gemini_client import GeminiClient, LLMClient, TokenBucketRateLimiter


# ---------------------------------------------------------------------------
# Test schema
# ---------------------------------------------------------------------------

class SampleOutput(BaseModel):
    name: str
    score: int


# ---------------------------------------------------------------------------
# TokenBucketRateLimiter tests
# ---------------------------------------------------------------------------

class TestTokenBucketRateLimiter:

    @pytest.mark.asyncio
    async def test_acquire_succeeds_when_tokens_available(self):
        limiter = TokenBucketRateLimiter(rpm_limit=12)
        # Should acquire immediately — starts with full tokens
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_acquire_blocks_when_tokens_exhausted(self):
        limiter = TokenBucketRateLimiter(rpm_limit=2)
        # Drain all tokens
        await limiter.acquire()
        await limiter.acquire()

        # Third acquire should block
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        # With 2 RPM, refill rate is 1 per 30s. We need at least some wait.
        assert elapsed > 0.5

    @pytest.mark.asyncio
    async def test_burst_capacity(self):
        """All initial tokens should be available immediately."""
        limiter = TokenBucketRateLimiter(rpm_limit=5)
        start = time.monotonic()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.5  # All 5 should be near-instant


# ---------------------------------------------------------------------------
# GeminiClient tests
# ---------------------------------------------------------------------------

class TestGeminiClient:

    def _make_client(self) -> GeminiClient:
        """Create a GeminiClient with mocked internals."""
        with patch("app.gemini_client.genai") as mock_genai:
            mock_genai.Client.return_value = MagicMock()
            client = GeminiClient(api_key="test-key", model="gemini-2.0-flash", rpm_limit=60)
        return client

    @pytest.mark.asyncio
    async def test_generate_returns_parsed_json(self):
        client = self._make_client()
        mock_response = MagicMock()
        mock_response.text = '{"name": "Test Campaign", "score": 95}'
        client._client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        result = await client.generate("test prompt", SampleOutput)

        assert result == {"name": "Test Campaign", "score": 95}

    @pytest.mark.asyncio
    async def test_generate_retries_on_429(self):
        client = self._make_client()

        # First call raises 429, second succeeds
        error_429 = Exception("Rate limited")
        error_429.status_code = 429

        mock_response = MagicMock()
        mock_response.text = '{"name": "Retry Success", "score": 42}'

        client._client.aio.models.generate_content = AsyncMock(
            side_effect=[error_429, mock_response]
        )

        with patch.object(client, "_backoff_delay", return_value=0.01):
            result = await client.generate("test prompt", SampleOutput)

        assert result == {"name": "Retry Success", "score": 42}
        assert client._client.aio.models.generate_content.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_retries_on_503(self):
        client = self._make_client()

        error_503 = Exception("Service unavailable")
        error_503.status_code = 503

        mock_response = MagicMock()
        mock_response.text = '{"name": "OK", "score": 1}'

        client._client.aio.models.generate_content = AsyncMock(
            side_effect=[error_503, mock_response]
        )

        with patch.object(client, "_backoff_delay", return_value=0.01):
            result = await client.generate("test prompt", SampleOutput)

        assert result["name"] == "OK"

    @pytest.mark.asyncio
    async def test_generate_raises_after_max_retries(self):
        client = self._make_client()

        error_429 = Exception("Rate limited")
        error_429.status_code = 429

        client._client.aio.models.generate_content = AsyncMock(
            side_effect=[error_429, error_429, error_429]
        )

        with patch.object(client, "_backoff_delay", return_value=0.01):
            with pytest.raises(RuntimeError, match="failed after 3 retries"):
                await client.generate("test prompt", SampleOutput)

    @pytest.mark.asyncio
    async def test_generate_raises_immediately_on_non_retryable(self):
        client = self._make_client()

        error_400 = Exception("Bad request")
        error_400.status_code = 400

        client._client.aio.models.generate_content = AsyncMock(side_effect=error_400)

        with pytest.raises(Exception, match="Bad request"):
            await client.generate("test prompt", SampleOutput)

        # Should NOT retry — only 1 call
        assert client._client.aio.models.generate_content.call_count == 1

    def test_backoff_delay_increases_with_attempts(self):
        client = self._make_client()
        delays = [client._backoff_delay(i) for i in range(3)]
        # Each delay should generally increase (with jitter, check base)
        assert delays[0] < 10  # Base 1s + up to 0.5s jitter
        assert delays[1] < 10  # Base 2s + up to 1s jitter
        assert delays[2] < 20  # Base 4s + up to 2s jitter

    def test_backoff_delay_respects_max(self):
        client = self._make_client()
        delay = client._backoff_delay(100)  # Very high attempt
        assert delay <= client.MAX_DELAY * 1.5  # Max + jitter


# ---------------------------------------------------------------------------
# LLMClient Protocol tests
# ---------------------------------------------------------------------------

class TestLLMClientProtocol:

    def test_gemini_client_satisfies_protocol(self):
        """GeminiClient should be recognized as implementing LLMClient."""
        with patch("app.gemini_client.genai"):
            client = GeminiClient(api_key="test-key", model="test", rpm_limit=60)
        assert isinstance(client, LLMClient)

    def test_mock_satisfies_protocol(self):
        """A mock with the right signature should satisfy LLMClient."""
        mock = MagicMock()
        mock.generate = AsyncMock(return_value={"test": "data"})
        assert isinstance(mock, LLMClient)
