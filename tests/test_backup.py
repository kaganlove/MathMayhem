"""Phase 1 Acceptance Tests: Atomic Online SQLite Backup & Restore Verification (T1.8)."""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings
from app.database import create_db_engine, init_db, make_session_factory
from app.models import Episode
from app.security import get_vault
from scripts.backup import create_backup, restore_backup, verify_backup


def test_atomic_backup_verify_and_restore_parity(tmp_path: Path) -> None:
    cfg = get_settings(tmp_path / ".env")
    cfg.MM_DATA_DIR = tmp_path / "data"
    cfg.MM_BACKUPS_DIR = tmp_path / "backups"
    cfg.ensure_directories()

    engine = create_db_engine(cfg.database_url, cfg)
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        session.add(
            Episode(
                code="EP001",
                title="Never Divide by Zero",
                concept_summary="Pilot episode",
                aspect_ratio="9:16",
            )
        )
        session.commit()

    vault = get_vault(cfg)
    vault.set_secret("test_api_key", "secret_987654")
    engine.dispose()

    # 1. Create atomic backup archive
    archive = create_backup(cfg, label="test_phase1")
    assert archive.exists()

    # 2. Verify backup checksum and SQLite integrity
    v_res = verify_backup(archive)
    assert v_res["verified"] is True

    # 3. Restore to a clean directory and verify 100% row + secret parity
    restored_db = tmp_path / "restored" / "math_mayhem.db"
    restored_vault_file = tmp_path / "restored" / "credentials.vault"
    r_res = restore_backup(archive, restored_db, restored_vault_file)
    assert r_res["restored"] is True

    r_engine = create_db_engine(f"sqlite:///{restored_db.as_posix()}")
    r_session_factory = make_session_factory(r_engine)
    with r_session_factory() as r_session:
        ep = r_session.query(Episode).filter_by(code="EP001").first()
        assert ep is not None
        assert ep.title == "Never Divide by Zero"
    r_engine.dispose()
