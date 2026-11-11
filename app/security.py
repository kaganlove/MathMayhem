"""Encrypted credential vault and authentication guards for Math Mayhem."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings


class CredentialVault:
    """Encrypts and decrypts secrets at rest using Fernet (AES-128-CBC + HMAC-SHA256)."""

    def __init__(self, vault_key: str, vault_file: Path) -> None:
        if isinstance(vault_key, str):
            key_bytes = vault_key.encode("ascii")
        else:
            key_bytes = vault_key
        self._fernet = Fernet(key_bytes)
        self._vault_file = vault_file

    def encrypt_value(self, plaintext: str) -> str:
        """Encrypt a string and return URL-safe base64 ciphertext."""
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt_value(self, token: str) -> str:
        """Decrypt a ciphertext token or raise InvalidToken if tampered/corrupted."""
        return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")

    def _load_all(self) -> Dict[str, str]:
        if not self._vault_file.exists():
            return {}
        raw = self._vault_file.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        decrypted = self.decrypt_value(raw)
        data = json.loads(decrypted)
        if not isinstance(data, dict):
            raise ValueError("Vault file payload is not a JSON object")
        return {str(k): str(v) for k, v in data.items()}

    def _save_all(self, mapping: Dict[str, str]) -> None:
        self._vault_file.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(mapping, sort_keys=True)
        ciphertext = self.encrypt_value(serialized)
        self._vault_file.write_text(ciphertext, encoding="utf-8")

    def set_secret(self, name: str, value: str) -> None:
        """Store an encrypted secret by name."""
        if not name or not name.strip():
            raise ValueError("Secret name must not be empty")
        data = self._load_all()
        data[name] = value
        self._save_all(data)

    def get_secret(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve a decrypted secret by name."""
        data = self._load_all()
        return data.get(name, default)

    def delete_secret(self, name: str) -> bool:
        """Remove a secret from the encrypted store."""
        data = self._load_all()
        if name in data:
            del data[name]
            self._save_all(data)
            return True
        return False

    def list_secret_names(self) -> list[str]:
        """Return the names of stored secrets without exposing values."""
        return sorted(self._load_all().keys())


def get_vault(settings: Optional[Settings] = None) -> CredentialVault:
    cfg = settings or get_settings()
    vault_path = cfg.MM_DATA_DIR / "credentials.vault"
    return CredentialVault(cfg.MM_VAULT_KEY, vault_path)


_bearer_scheme = HTTPBearer(auto_error=False)


def verify_token_value(candidate: Optional[str], expected: str) -> bool:
    """Constant-time token comparison."""
    if not candidate or not expected:
        return False
    return secrets.compare_digest(candidate.strip(), expected.strip())


async def require_owner_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """FastAPI dependency enforcing owner authentication via Bearer header, X-MM-Token header, or session cookie."""
    settings: Settings = getattr(request.app.state, "settings", None) or get_settings()
    expected = settings.MM_ADMIN_TOKEN

    token: Optional[str] = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif "x-mm-token" in request.headers:
        token = request.headers.get("x-mm-token")
    elif "mm_session" in request.cookies:
        token = request.cookies.get("mm_session")

    if not verify_token_value(token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: valid owner token or session required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return settings.MM_OWNER_ID
