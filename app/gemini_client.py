import asyncio
import json
import logging
import random
import time
from typing import Protocol, runtime_checkable

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger("agencyflow.gemini")


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM clients — enables swapping Gemini for mocks or other providers."""

    async def generate(self, prompt: str, response_schema: type[BaseModel]) -> dict: ...


class TokenBucketRateLimiter:
    """Token bucket rate limiter for Gemini API calls.

    Allows `rpm_limit` requests per 60-second window. Uses asyncio.Lock
    for thread safety and time.monotonic for clock reliability.
    """

    def __init__(self, rpm_limit: int):
        self._rpm_limit = rpm_limit
        self._tokens = float(rpm_limit)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a token is available."""
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                # Refill tokens based on elapsed time
                self._tokens = min(
                    self._rpm_limit,
                    self._tokens + elapsed * (self._rpm_limit / 60.0),
                )
                self._last_refill = now

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

            # No token available — wait before retrying
            await asyncio.sleep(60.0 / self._rpm_limit)


class GeminiClient:
    """Async Gemini API client with rate limiting and retry logic."""

    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 30.0  # seconds
    RETRYABLE_STATUS_CODES = {429, 503}

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        rpm_limit: int | None = None,
    ):
        self._api_key = api_key or settings.gemini_api_key
        self._model = model or settings.gemini_model
        self._rate_limiter = TokenBucketRateLimiter(rpm_limit or settings.gemini_rpm_limit)
        self._client = genai.Client(api_key=self._api_key)

    async def generate(self, prompt: str, response_schema: type[BaseModel]) -> dict:
        """Generate structured output from Gemini.

        Args:
            prompt: The prompt to send to Gemini.
            response_schema: Pydantic model class defining expected output structure.

        Returns:
            Parsed JSON dict matching the response_schema.

        Raises:
            RuntimeError: After exhausting retries on retryable errors.
            Exception: On non-retryable API errors.
        """
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            await self._rate_limiter.acquire()

            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                    ),
                )
                return json.loads(response.text)

            except Exception as exc:
                last_error = exc
                status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)

                if status_code in self.RETRYABLE_STATUS_CODES:
                    delay = self._backoff_delay(attempt)
                    logger.warning(
                        f"Gemini API returned {status_code}, retrying in {delay:.1f}s "
                        f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(delay)
                    continue

                # Non-retryable error — raise immediately
                raise

        raise RuntimeError(
            f"Gemini API failed after {self.MAX_RETRIES} retries: {last_error}"
        ) from last_error

    def _backoff_delay(self, attempt: int) -> float:
        """Exponential backoff with jitter."""
        delay = min(self.BASE_DELAY * (2 ** attempt), self.MAX_DELAY)
        jitter = random.uniform(0, delay * 0.5)
        return delay + jitter
