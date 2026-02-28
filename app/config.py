from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field("gemini-2.0-flash", description="Gemini model name")
    gemini_rpm_limit: int = Field(12, description="Requests per minute (20% safety margin from 15 RPM free tier)")
    max_upload_size_bytes: int = Field(10 * 1024 * 1024, description="Max file upload size (10MB)")
    cors_origin: str = Field("http://localhost:5173", description="Allowed CORS origin")
    demo_mode: bool = Field(False, description="Use pre-computed demo outputs")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
