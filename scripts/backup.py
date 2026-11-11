"""Atomic online SQLite backup and restore verification utility for Math Mayhem."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings, get_settings


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_backup(settings: Optional[Settings] = None, label: str = "snapshot") -> Path:
    """Perform an atomic online SQLite backup and package it with a checksum manifest."""
    cfg = settings or get_settings()
    cfg.MM_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    db_path = cfg.sqlite_path

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    archive_path = cfg.MM_BACKUPS_DIR / f"backup_{timestamp}_{label}.zip"

    with tempfile.TemporaryDirectory(prefix="mm_bak_") as tmp_str:
        tmp_dir = Path(tmp_str)
        snapshot_db = tmp_dir / "math_mayhem.db"

        if db_path.exists():
            src_conn = sqlite3.connect(str(db_path))
            dst_conn = sqlite3.connect(str(snapshot_db))
            with dst_conn:
                src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()
        else:
            # Create empty valid sqlite file if db hasn't been touched yet
            conn = sqlite3.connect(str(snapshot_db))
            conn.close()

        db_hash = _sha256_file(snapshot_db)
        manifest: Dict[str, Any] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "label": label,
            "database_filename": "math_mayhem.db",
            "database_sha256": db_hash,
            "database_size_bytes": snapshot_db.stat().st_size,
        }

        vault_path = cfg.MM_DATA_DIR / "credentials.vault"
        if vault_path.exists():
            manifest["vault_filename"] = "credentials.vault"
            manifest["vault_sha256"] = _sha256_file(vault_path)

        manifest_file = tmp_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(snapshot_db, arcname="math_mayhem.db")
            zf.write(manifest_file, arcname="manifest.json")
            if vault_path.exists():
                zf.write(vault_path, arcname="credentials.vault")

    return archive_path


def verify_backup(archive_path: Path) -> Dict[str, Any]:
    """Verify the checksum and SQLite integrity of a backup zip archive."""
    if not archive_path.exists():
        raise FileNotFoundError(f"Backup archive not found: {archive_path}")

    with tempfile.TemporaryDirectory(prefix="mm_verify_") as tmp_str:
        tmp_dir = Path(tmp_str)
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(tmp_dir)

        manifest_path = tmp_dir / "manifest.json"
        if not manifest_path.exists():
            raise ValueError("Backup archive missing manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        db_file = tmp_dir / manifest["database_filename"]
        actual_hash = _sha256_file(db_file)
        if actual_hash != manifest["database_sha256"]:
            raise ValueError(
                f"Database SHA256 mismatch: expected {manifest['database_sha256']}, got {actual_hash}"
            )

        conn = sqlite3.connect(str(db_file))
        integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        conn.close()
        if integrity.lower() != "ok":
            raise ValueError(f"SQLite integrity check failed: {integrity}")

        return {"verified": True, "archive": str(archive_path), "manifest": manifest}


def restore_backup(archive_path: Path, target_db_path: Path, target_vault_path: Optional[Path] = None) -> Dict[str, Any]:
    """Verify and restore a backup archive to target_db_path."""
    verification = verify_backup(archive_path)
    with tempfile.TemporaryDirectory(prefix="mm_restore_") as tmp_str:
        tmp_dir = Path(tmp_str)
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(tmp_dir)

        src_db = tmp_dir / "math_mayhem.db"
        target_db_path.parent.mkdir(parents=True, exist_ok=True)
        src_conn = sqlite3.connect(str(src_db))
        dst_conn = sqlite3.connect(str(target_db_path))
        with dst_conn:
            src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()

        src_vault = tmp_dir / "credentials.vault"
        if target_vault_path and src_vault.exists():
            target_vault_path.parent.mkdir(parents=True, exist_ok=True)
            target_vault_path.write_bytes(src_vault.read_bytes())

    return {"restored": True, "target_db_path": str(target_db_path), "manifest": verification["manifest"]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Math Mayhem Backup & Restore Utility")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("create")
    ver_p = sub.add_parser("verify")
    ver_p.add_argument("--latest", action="store_true")
    ver_p.add_argument("--archive", type=str, default=None)
    res_p = sub.add_parser("restore")
    res_p.add_argument("--archive", type=str, required=True)

    args = parser.parse_args()
    cfg = get_settings()

    if args.command == "create":
        out = create_backup(cfg)
        print(f"Created backup: {out}")
        return 0
    if args.command == "verify":
        if args.latest:
            archives = sorted(cfg.MM_BACKUPS_DIR.glob("backup_*.zip"))
            if not archives:
                raise FileNotFoundError("No backup archives found")
            target = archives[-1]
        else:
            target = Path(args.archive)
        res = verify_backup(target)
        print(json.dumps(res, indent=2))
        return 0
    if args.command == "restore":
        res = restore_backup(
            Path(args.archive),
            cfg.sqlite_path,
            cfg.MM_DATA_DIR / "credentials.vault",
        )
        print(json.dumps(res, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
