"""CLI entry points for Math Mayhem setup and operations."""

from __future__ import annotations

import sys

from app.config import bootstrap_env_file, get_settings
from app.database import create_db_engine, init_db


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "init-env":
        path = bootstrap_env_file()
        print(f"Environment initialized at: {path}")
        return 0
    if cmd == "init-db":
        cfg = get_settings()
        engine = create_db_engine(cfg.database_url, cfg)
        init_db(engine)
        engine.dispose()
        print(f"Database initialized at: {cfg.sqlite_path}")
        return 0
    print("Usage: python -m app.cli [init-env|init-db]")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
