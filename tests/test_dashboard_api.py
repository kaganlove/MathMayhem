"""Phase 1 Acceptance Tests: Local Mobile-Responsive Dashboard Shell & Auth (T1.7)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from app.config import get_settings
from app.main import create_app


def test_dashboard_auth_and_endpoints(tmp_path: Path) -> None:
    cfg = get_settings(tmp_path / ".env")
    cfg.MM_DATA_DIR = tmp_path / "data"
    cfg.MM_RENDERS_DIR = tmp_path / "renders"
    cfg.MM_LOGS_DIR = tmp_path / "logs"
    cfg.MM_BACKUPS_DIR = tmp_path / "backups"
    cfg.ensure_directories()

    app = create_app(cfg)

    async def _run_checks() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Unauthenticated requests must be rejected with 401
            unauth_home = await client.get("/")
            assert unauth_home.status_code == 401
            unauth_health = await client.get("/api/health")
            assert unauth_health.status_code == 401

            # 2. Invalid login token rejected
            bad_login = await client.post("/api/auth/login", json={"token": "wrong_token"})
            assert bad_login.status_code == 401

            # 3. Valid owner login sets session cookie and unlocks dashboard
            login_res = await client.post("/api/auth/login", json={"token": cfg.MM_ADMIN_TOKEN})
            assert login_res.status_code == 200
            assert login_res.json()["authenticated"] is True

            # 4. Authenticated dashboard shell renders mobile viewport & GPU info
            home_res = await client.get("/")
            assert home_res.status_code == 200
            assert 'name="viewport" content="width=device-width, initial-scale=1.0"' in home_res.text
            assert "Math Mayhem" in home_res.text
            assert "RTX 5080" in home_res.text

            # 5. Create Episode 001 record via API
            ep_res = await client.post(
                "/api/episodes",
                json={
                    "code": "EP001",
                    "title": "Never Divide by Zero",
                    "concept_summary": "10 / 0 is undefined",
                    "aspect_ratio": "9:16",
                },
            )
            assert ep_res.status_code == 201
            assert ep_res.json()["code"] == "EP001"

            # 6. Health endpoint returns telemetry
            health_res = await client.get("/api/health")
            assert health_res.status_code == 200
            h_data = health_res.json()
            assert h_data["status"] == "ok"
            assert h_data["database_ok"] is True
            assert h_data["gpu"]["available"] is True

    asyncio.run(_run_checks())
    app.state.engine.dispose()
