"""Phase 1 Acceptance Tests: Configuration, Credential Vault Encryption & Logging (T1.3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.config import bootstrap_env_file, get_settings
from app.logging_config import setup_logging
from app.security import CredentialVault


def test_settings_bootstrap_and_safe_defaults(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    bootstrapped = bootstrap_env_file(env_file)
    assert bootstrapped.exists()

    cfg = get_settings(env_file)
    assert cfg.MM_ADMIN_TOKEN.startswith("mm_admin_")
    assert len(cfg.MM_VAULT_KEY) >= 32
    assert cfg.MM_ALLOW_PAID_LLM is False
    assert cfg.MM_MONTHLY_LLM_BUDGET_USD == 0.0


def test_credential_vault_encryption_and_tamper_detection(tmp_path: Path) -> None:
    key = Fernet.generate_key().decode("ascii")
    vault_file = tmp_path / "credentials.vault"
    vault = CredentialVault(key, vault_file)

    vault.set_secret("youtube_oauth_refresh_token", "yt_secret_token_12345")
    vault.set_secret("smtp_api_key", "smtp_key_67890")

    assert vault.get_secret("youtube_oauth_refresh_token") == "yt_secret_token_12345"
    assert vault.list_secret_names() == ["smtp_api_key", "youtube_oauth_refresh_token"]

    # Ensure raw file on disk does NOT contain plaintext
    raw_disk = vault_file.read_text(encoding="utf-8")
    assert "yt_secret_token_12345" not in raw_disk
    assert "youtube_oauth_refresh_token" not in raw_disk

    # Tamper with ciphertext and verify InvalidToken is raised
    vault_file.write_text(raw_disk[:-4] + "AAAA", encoding="utf-8")
    with pytest.raises(InvalidToken):
        vault.get_secret("youtube_oauth_refresh_token")


def test_structured_json_logging(tmp_path: Path) -> None:
    cfg = get_settings(tmp_path / ".env")
    cfg.MM_LOGS_DIR = tmp_path / "logs"
    logger = setup_logging(cfg, log_filename="test_audit.log")
    logger.info("Phase 1 test log entry")

    log_file = cfg.MM_LOGS_DIR / "test_audit.log"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    parsed = json.loads(lines[-1])
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Phase 1 test log entry"
