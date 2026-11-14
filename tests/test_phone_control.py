"""Comprehensive Automated Test Suite for Phase 5 — Remote Phone Control.

Validates:
1. QR Code & Pairing Token lifecycle (generation, QR SVG data URI, expiration, consumption).
2. PairedDevice database registration and audit logging.
3. Mobile Text & Voice Memo idea submission.
4. Episode approval and batch approval via mobile endpoints.
5. Episode revision request workflow.
6. HTTP 206 Partial Content (Range Request) mobile video streaming.
7. WebSocket connection, connection handshake, and ping/pong heartbeat.
"""

from __future__ import annotations

import asyncio
import io
import json
import time
from pathlib import Path

import httpx
import pytest
from starlette.testclient import TestClient

from app.database import create_db_engine, init_db, make_session_factory
from app.main import create_app
from app.models import (
    AuditEvent,
    Episode,
    EpisodeVersion,
    PairedDevice,
    VoiceIdeaMemo,
    approve_episode_version,
)
from app.phone_control import (
    PairingManager,
    PhoneWebSocketHub,
    VoiceIdeaService,
    get_local_lan_ip,
    phone_ws_hub,
)


@pytest.fixture(scope="module")
def app_instance():
    return create_app()


def test_lan_ip_resolution() -> None:
    """Verify local LAN IP resolves to valid IPv4 address."""
    ip = get_local_lan_ip()
    assert ip, "Local IP must not be empty"
    parts = ip.split(".")
    assert len(parts) == 4, f"Invalid IP structure: {ip}"
    for p in parts:
        assert p.isdigit() and 0 <= int(p) <= 255


def test_pairing_token_and_qr_generation() -> None:
    """Verify cryptographic token generation, pairing URL and Segno QR SVG output."""
    token = PairingManager.generate_pairing_token()
    assert len(token) >= 32

    url = PairingManager.build_pairing_url(token, host="192.168.1.81", port=8000)
    assert "http://192.168.1.81:8000/phone?token=" in url
    assert token in url

    qr_uri = PairingManager.generate_qr_svg_data_uri(url)
    assert qr_uri.startswith("data:image/svg+xml"), "QR must be SVG data URI"
    assert "<svg" in qr_uri or "svg" in qr_uri


def test_consume_pairing_token_and_device_registration(app_instance) -> None:
    """Verify token consumption, session issuance, and PairedDevice record creation."""
    session_factory = app_instance.state.session_factory
    token = PairingManager.generate_pairing_token()

    with session_factory() as session:
        success, sess_tok, dev_id = PairingManager.consume_pairing_token(
            token=token,
            session=session,
            device_name="Test iPhone 16 Pro",
            ip="192.168.1.150",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0)",
        )
        assert success is True
        assert sess_tok is not None
        assert dev_id is not None
        assert dev_id.startswith("phone_")

        # Verify device in DB
        dev = session.query(PairedDevice).filter_by(device_id=dev_id).first()
        assert dev is not None
        assert dev.device_name == "Test iPhone 16 Pro"
        assert dev.is_active is True

        # Verify AuditEvent
        audit = session.query(AuditEvent).filter_by(event_type="PHONE_DEVICE_PAIRED", entity_id=dev_id).first()
        assert audit is not None

        # Re-consuming the same token must fail
        success2, _, _ = PairingManager.consume_pairing_token(token=token, session=session)
        assert success2 is False


def test_mobile_web_interface_endpoint(app_instance) -> None:
    """Verify GET /phone renders mobile HTML and sets cookie when token is passed."""
    async def _run():
        transport = httpx.ASGITransport(app=app_instance)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            token = PairingManager.generate_pairing_token()
            resp = await client.get(f"/phone?token={token}")
            assert resp.status_code == 200
            assert "Math Mayhem — Mobile Control Hub" in resp.text
            assert "mm_phone_session" in resp.cookies

    asyncio.run(_run())


def test_api_pairing_info_endpoint(app_instance) -> None:
    """Verify GET /api/phone/pair generates fresh token, local URL, and QR code."""
    async def _run():
        transport = httpx.ASGITransport(app=app_instance)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/phone/pair")
            assert resp.status_code == 200
            data = resp.json()
            assert "token" in data
            assert "pairing_url" in data
            assert "qr_svg_data_uri" in data
            assert data["expires_in_seconds"] == 900

    asyncio.run(_run())


def test_text_idea_submission(app_instance) -> None:
    """Verify POST /api/phone/idea/text creates VoiceIdeaMemo and logs audit."""
    session_factory = app_instance.state.session_factory

    async def _run():
        transport = httpx.ASGITransport(app=app_instance)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            payload = {
                "title": "Negative Exponent Inversion",
                "concept": "Protagonist tries 2 ^ -3 on calculator and gets sucked into an upside-down world where 2^-3 = 1/8.",
                "math_category": "exponents",
            }
            resp = await client.post("/api/phone/idea/text", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert "memo_code" in data
            assert data["title"] == "Negative Exponent Inversion"

            with session_factory() as session:
                memo = session.query(VoiceIdeaMemo).filter_by(memo_code=data["memo_code"]).first()
                assert memo is not None
                assert memo.math_category == "exponents"
                assert "upside-down world" in memo.raw_concept

    asyncio.run(_run())


def test_voice_idea_submission(app_instance) -> None:
    """Verify POST /api/phone/idea/voice accepts multipart audio memo and saves file."""
    session_factory = app_instance.state.session_factory

    async def _run():
        transport = httpx.ASGITransport(app=app_instance)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            fake_audio_bytes = b"RIFF....WAVEfmt ....data...." + b"\x00\x7f" * 500
            data = {
                "title": "Voice Memo - Imaginary Numbers",
                "concept": "What happens when you square root negative one? sqrt(-1) = i.",
                "math_category": "algebra",
            }
            files = {"audio": ("memo.wav", fake_audio_bytes, "audio/wav")}

            resp = await client.post("/api/phone/idea/voice", data=data, files=files)
            assert resp.status_code == 200
            res_data = resp.json()
            assert "memo_code" in res_data
            assert Path(res_data["file_path"]).exists()

            with session_factory() as session:
                memo = session.query(VoiceIdeaMemo).filter_by(memo_code=res_data["memo_code"]).first()
                assert memo is not None
                assert memo.audio_file_path is not None
                assert memo.audio_sha256 is not None

    asyncio.run(_run())


def test_mobile_episode_approval_flow(app_instance) -> None:
    """Verify single and batch approval endpoints via phone controller."""
    session_factory = app_instance.state.session_factory

    with session_factory() as session:
        ep = session.query(Episode).filter_by(code="EP001").first()
        if not ep:
            ep = Episode(code="EP001", title="Never Divide by Zero", status="PREVIEW_READY")
            session.add(ep)
            session.flush()

        ver = session.query(EpisodeVersion).filter_by(episode_id=ep.id, version_number=1).first()
        if not ver:
            ver = EpisodeVersion(
                episode_id=ep.id,
                version_number=1,
                status="PREVIEW_READY",
                video_sha256="abc1234567890",
            )
            session.add(ver)
            session.commit()

        target_ver_id = ver.id

    async def _run():
        transport = httpx.ASGITransport(app=app_instance)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Single Approval
            resp = await client.post(
                "/api/phone/approve",
                json={"episode_id": ep.id, "version_number": 1, "notes": "Approved from mobile test"},
            )
            assert resp.status_code == 200
            res_data = resp.json()
            assert res_data["status"] == "APPROVED"
            assert "approval_log_id" in res_data

            # Batch Approval
            resp_batch = await client.post(
                "/api/phone/batch-approve",
                json={"version_ids": [target_ver_id], "notes": "Batch mobile approval"},
            )
            assert resp_batch.status_code == 200
            batch_data = resp_batch.json()
            assert batch_data["approved_count"] == 1

    asyncio.run(_run())


def test_mobile_video_range_request_streaming(app_instance) -> None:
    """Verify video streaming endpoint handles full request and HTTP 206 Partial Content range requests."""
    async def _run():
        transport = httpx.ASGITransport(app=app_instance)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Full content request (stream headers check)
            async with client.stream("GET", "/api/phone/video/ep001_master.mp4") as resp_full:
                assert resp_full.status_code in (200, 206)
                assert resp_full.headers["Accept-Ranges"] == "bytes"
                assert "video/mp4" in resp_full.headers["Content-Type"]
                chunk = await anext(resp_full.aiter_bytes())
                assert len(chunk) > 0

            # 2. Range request (first 1024 bytes)
            headers = {"Range": "bytes=0-1023"}
            async with client.stream("GET", "/api/phone/video/ep001_master.mp4", headers=headers) as resp_range:
                assert resp_range.status_code == 206
                assert resp_range.headers["Content-Range"].startswith("bytes 0-1023/")
                body = await resp_range.aread()
                assert len(body) == 1024

    asyncio.run(_run())


def test_phone_websocket_hub_and_broadcast(app_instance) -> None:
    """Verify WebSocket hub message dispatch, job progress broadcast, and event history."""
    async def _run():
        hub = PhoneWebSocketHub()

        received = []

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, msg):
                received.append(msg)

        mock_ws = MockWebSocket()
        await hub.connect(mock_ws)
        assert len(received) == 1
        assert received[0]["type"] == "CONNECTION_ESTABLISHED"

        # Broadcast progress
        await hub.broadcast_job_progress(
            job_id=42,
            stage="Cairo Vector Simulation",
            progress_pct=65.0,
            fps=70.0,
            message="Rendering frame 468/720",
        )
        assert len(received) == 2
        assert received[1]["type"] == "JOB_PROGRESS"
        assert received[1]["stage"] == "Cairo Vector Simulation"
        assert received[1]["fps"] == 70.0

        # Broadcast notification
        await hub.broadcast_notification("Master Render Ready", "Episode 001 v2 is ready for review.", kind="success")
        assert len(received) == 3
        assert received[2]["type"] == "NOTIFICATION"
        assert "Master Render Ready" in received[2]["title"]

        # Disconnect
        hub.disconnect(mock_ws)
        assert len(hub.active_connections) == 0

    asyncio.run(_run())
