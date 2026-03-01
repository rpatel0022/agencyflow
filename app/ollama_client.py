"""Ollama LLM client — local, free alternative to Gemini.

Uses Ollama's REST API with structured JSON output via the `format` parameter.
Implements the same LLMClient Protocol so agents don't need to change.
"""

import json
import logging

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger("agencyflow.ollama")


class OllamaClient:
    """Async Ollama client that satisfies the LLMClient Protocol."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self._base_url = base_url or settings.ollama_base_url
        self._model = model or settings.ollama_model
        # Local models are slow — especially for large structured outputs.
        # The read timeout is the critical one: Ollama buffers the full response
        # before sending it back (stream=False), so we need to wait a long time.
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(connect=10.0, read=600.0, write=10.0, pool=10.0),
        )

    async def generate(self, prompt: str, response_schema: type[BaseModel]) -> dict:
        """Generate structured output from Ollama.

        Uses Ollama's `format` parameter with a JSON schema to get structured output,
        similar to how GeminiClient uses response_schema.
        """
        # Build the JSON schema from the Pydantic model
        schema = response_schema.model_json_schema()

        # Wrap the prompt with instructions for structured output
        system_prompt = (
            "You are a marketing agency AI assistant. "
            "Respond ONLY with valid JSON matching the provided schema. "
            "No markdown, no explanation — just the JSON object."
        )

        response = await self._http.post(
            "/api/chat",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "format": schema,
                "stream": False,
            },
        )
        response.raise_for_status()

        data = response.json()
        content = data["message"]["content"]
        return json.loads(content)

    async def close(self):
        await self._http.aclose()
