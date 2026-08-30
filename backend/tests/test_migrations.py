"""Migration-content test.

Runs `alembic upgrade head` against a fresh temp SQLite DB (in a subprocess so
`core.config` reads the injected env), then asserts the expected final schema.
This guards against migration drift — the repo must always tell the DB's true history.
"""
import os
import subprocess
import sqlite3
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _run_alembic(db_path: Path) -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["SECRET_KEY"] = "migration-test-secret"
    env["ENVIRONMENT"] = "development"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic failed:\n{result.stdout}\n{result.stderr}"


def test_upgrade_head_creates_expected_schema(tmp_path):
    db_path = tmp_path / "mig.db"
    _run_alembic(db_path)

    conn = sqlite3.connect(db_path)
    try:
        # All 8 core tables present
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"jobs", "applications", "resumes", "responses", "companies",
                "status_history", "analytics_snapshot", "apply_log"}.issubset(tables)

        # The new message_id dedupe column must exist on responses
        resp_cols = {r[1] for r in conn.execute("PRAGMA table_info(responses)")}
        assert "message_id" in resp_cols

        # Alembic version recorded at head
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        assert version == "a2b3c4d5e6f7"
    finally:
        conn.close()
