"""Pytest configuration and fixtures."""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
# Import all models to ensure they're registered with Base.metadata
from app.models import (
    Tenant,
    Vendor,
    Invoice,
    BankTransaction,
    Match,
    IdempotencyKey,
)
from decimal import Decimal
from datetime import datetime, timedelta


# Use file-based SQLite for tests to avoid connection issues with :memory:
_test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
_test_db_path = _test_db_file.name
_test_db_file.close()

SQLALCHEMY_DATABASE_URL = f"sqlite:///{_test_db_path}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    # Ensure all models are imported before creating tables
    from app.models import (
        Tenant,
        Vendor,
        Invoice,
        BankTransaction,
        Match,
        IdempotencyKey,
    )
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Create a session
    db = TestingSessionLocal()
    try:
        yield db
        db.rollback()  # Rollback any uncommitted changes
    finally:
        db.close()
        # Clean up tables for next test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        # Return the same test database session
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    tenant = Tenant(name="Test Tenant")
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def vendor(db, tenant):
    """Create a test vendor."""
    vendor = Vendor(tenant_id=tenant.id, name="Test Vendor")
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def pytest_sessionfinish(session, exitstatus):
    """Clean up test database file after all tests."""
    if os.path.exists(_test_db_path):
        os.unlink(_test_db_path)
