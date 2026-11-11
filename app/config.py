"""Configuration settings for Math Mayhem."""

from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    MM_ENV: str = Field(default="development")
    MM_OWNER_ID: str = Field(default="owner_primary")
    MM_HOST: str = Field(default="127.0.0.1")
    MM_PORT: int = Field(default=8000)

    # Paths
    MM_DATA_DIR: Path = Field(default=BASE_DIR / "data")
    MM_ASSETS_DIR: Path = Field(default=BASE_DIR / "assets")
    MM_RENDERS_DIR: Path = Field(default=BASE_DIR / "renders")
    MM_BACKUPS_DIR: Path = Field(default=BASE_DIR / "backups")
    MM_LOGS_DIR: Path = Field(default=BASE_DIR / "logs")
    MM_DATABASE_URL: Optional[str] = Field(default=None)

    # Security
    MM_ADMIN_TOKEN: str = Field(default="")
    MM_VAULT_KEY: str = Field(default="")
    MM_SESSION_SECRET: str = Field(default="")

    # Rendering & GPU
    MM_FFMPEG_PATH: Optional[str] = Field(default=None)
    MM_FFPROBE_PATH: Optional[str] = Field(default=None)
    MM_PREFER_NVENC: bool = Field(default=True)

    # Cost & API Guardrails (Disabled by default; never auto-incur charges)
    MM_ALLOW_PAID_LLM: bool = Field(default=False)
    MM_MONTHLY_LLM_BUDGET_USD: float = Field(default=0.0)

    @property
    def database_url(self) -> str:
        if self.MM_DATABASE_URL:
            return self.MM_DATABASE_URL
        db_path = (self.MM_DATA_DIR / "math_mayhem.db").resolve()
        return f"sqlite:///{db_path.as_posix()}"

    @property
    def sqlite_path(self) -> Path:
        if self.MM_DATABASE_URL and self.MM_DATABASE_URL.startswith("sqlite:///"):
            raw = self.MM_DATABASE_URL.replace("sqlite:///", "", 1)
            return Path(raw)
        return (self.MM_DATA_DIR / "math_mayhem.db").resolve()

    def ensure_directories(self) -> None:
        """Ensure all runtime directories exist."""
        for directory in (
            self.MM_DATA_DIR,
            self.MM_ASSETS_DIR,
            self.MM_ASSETS_DIR / "character",
            self.MM_ASSETS_DIR / "audio",
            self.MM_ASSETS_DIR / "props",
            self.MM_RENDERS_DIR,
            self.MM_RENDERS_DIR / "previews",
            self.MM_RENDERS_DIR / "masters",
            self.MM_BACKUPS_DIR,
            self.MM_LOGS_DIR,
        ):
            directory.mkdir(parents=True, exist_ok=True)


def bootstrap_env_file(env_path: Optional[Path] = None) -> Path:
    """Create a secure default .env file if one does not already exist."""
    target = env_path or (BASE_DIR / ".env")
    if target.exists():
        return target

    admin_token = f"mm_admin_{secrets.token_urlsafe(24)}"
    vault_key = Fernet.generate_key().decode("ascii")
    session_secret = secrets.token_hex(32)

    content = (
        "# Math Mayhem Local Configuration (Auto-Generated)\n"
        "# DO NOT COMMIT THIS FILE TO VERSION CONTROL\n"
        "MM_ENV=development\n"
        "MM_OWNER_ID=owner_primary\n"
        "MM_HOST=127.0.0.1\n"
        "MM_PORT=8000\n"
        f"MM_ADMIN_TOKEN={admin_token}\n"
        f"MM_VAULT_KEY={vault_key}\n"
        f"MM_SESSION_SECRET={session_secret}\n"
        "MM_PREFER_NVENC=true\n"
        "MM_ALLOW_PAID_LLM=false\n"
        "MM_MONTHLY_LLM_BUDGET_USD=0.0\n"
    )
    target.write_text(content, encoding="utf-8")
    return target


def get_settings(env_path: Optional[Path] = None) -> Settings:
    """Return initialized Settings, ensuring .env and directories exist."""
    bootstrap_env_file(env_path)
    if env_path is not None:
        settings = Settings(_env_file=str(env_path))
    else:
        settings = Settings()

    if not settings.MM_VAULT_KEY:
        settings.MM_VAULT_KEY = Fernet.generate_key().decode("ascii")
    if not settings.MM_ADMIN_TOKEN:
        settings.MM_ADMIN_TOKEN = f"mm_admin_{secrets.token_urlsafe(24)}"
    if not settings.MM_SESSION_SECRET:
        settings.MM_SESSION_SECRET = secrets.token_hex(32)

    settings.ensure_directories()
    return settings
