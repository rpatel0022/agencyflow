from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Provider selection: "gemini" or "ollama"
    llm_provider: str = Field("ollama", description="LLM provider: 'gemini' or 'ollama'")

    # Gemini settings
    gemini_api_key: str = Field("", description="Google Gemini API key")
    gemini_model: str = Field("gemini-2.0-flash", description="Gemini model name")
    gemini_rpm_limit: int = Field(12, description="Requests per minute (20% safety margin from 15 RPM free tier)")

    # Ollama settings
    ollama_base_url: str = Field("http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field("gemma3n:e2b", description="Ollama model name")

    max_upload_size_bytes: int = Field(10 * 1024 * 1024, description="Max file upload size (10MB)")
    cors_origin: str = Field("http://localhost:5173", description="Allowed CORS origin")
    demo_mode: bool = Field(False, description="Use pre-computed demo outputs")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
