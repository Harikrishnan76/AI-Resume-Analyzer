"""
AI Resume Analyzer — Application Configuration

Loads settings from environment variables / .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the project root (parent of backend/) to find .env reliably
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ──
    app_name: str = "AI Resume Analyzer"
    debug: bool = True
    secret_key: str = "change-me-to-a-random-secret-string"

    # ── Database ──
    database_url: str = "sqlite+aiosqlite:///./data/resume_analyzer.db"

    # ── File Storage ──
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 10

    # ── Auth ──
    access_token_expire_minutes: int = 1440  # 24 hours
    algorithm: str = "HS256"

    # ── SMTP ──
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@resumeanalyzer.local"
    smtp_use_tls: bool = False

    # ── Email APIs (Optional — highly recommended fallback for 100% deliverability) ──
    resend_api_key: str = ""
    sendgrid_api_key: str = ""

    # ── OpenAI (optional) ──
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # ── Scoring ──
    score_weight_keyword: float = 0.40
    score_weight_embedding: float = 0.40
    score_weight_rules: float = 0.20
    embedding_model: str = "all-MiniLM-L6-v2"
    shortlist_threshold: float = 0.65

    @property
    def upload_path(self) -> Path:
        """Resolved upload directory path."""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def llm_enabled(self) -> bool:
        """Whether LLM-assisted extraction is available."""
        return bool(self.openai_api_key and self.openai_api_key.strip())

    @property
    def email_dev_mode(self) -> bool:
        """
        In dev mode (debug=True + default SMTP), emails are saved to files
        and reported as successful instead of failing on SMTP connection.
        """
        return self.debug and self.smtp_host == "localhost" and self.smtp_port == 1025

    @property
    def project_root(self) -> Path:
        """Project root directory."""
        return _PROJECT_ROOT


# Singleton settings instance
settings = Settings()
