import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db
from app.main import app

# Smallest possible stand-ins for real image files: only the signature bytes matter.
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 16


@pytest.fixture
def session_factory():
    """Sessions for a throwaway in-memory database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client(tmp_path, session_factory):
    """A test client wired to the throwaway database and a temporary upload folder."""

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    def override_settings():
        return Settings(_env_file=None, extractor="mock", upload_dir=str(tmp_path), max_upload_mb=1)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = override_settings
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def scanned(client):
    """A receipt that has already been scanned and saved."""
    response = client.post(
        "/api/v1/receipts/scan",
        files={"file": ("receipt.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201
    return response.json()
