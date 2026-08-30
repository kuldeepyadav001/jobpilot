"""Pytest shared fixtures.

Sets env vars before importing the app (required by `core.config.Settings`),
then provides a throwaway SQLite engine + session for DB-backed tests.
"""
import os
import sys
from pathlib import Path

# --- Env must be set BEFORE any app module is imported ---
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("OLLAMA_BASE_URL", "http://127.0.0.1:1")  # unreachable fast for fallback tests

# Make the backend the import root
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from core.database import Base  # noqa: E402
import models  # noqa: E402,F401  — registers all tables on Base.metadata


@pytest.fixture
def engine():
    # Function-scoped so each test gets a fresh, empty DB (isolation).
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine)
    s = Session()
    try:
        yield s
    finally:
        s.rollback()
        s.close()
