from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.config import settings

# Pool tuning is meaningful for server DBs (Postgres) but invalid for SQLite,
# so we apply it only when the URL isn't sqlite. This keeps the app both
# production-correct and locally/testable.
_engine_kwargs = {"pool_pre_ping": True}  # Detects stale connections
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update({"pool_size": 5, "max_overflow": 10})

engine = create_engine(settings.database_url, **_engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()