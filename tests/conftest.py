import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models.question import Question

# Use in-memory SQLite DB for tests to avoid file I/O issues in Docker
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

SEED_DATA = [
    Question(
        id=1,
        show_number=4680,
        air_date=date(2004, 12, 31),
        round="Jeopardy!",
        category="HISTORY",
        value="$200",
        question="For the last 8 years of his life, Galileo was under house arrest for espousing this man's theory",
        answer="Copernicus",
    ),
    Question(
        id=2,
        show_number=4680,
        air_date=date(2004, 12, 31),
        round="Double Jeopardy!",
        category="SCIENCE",
        value="$400",
        question="This element has the atomic number 1",
        answer="Hydrogen",
    ),
    Question(
        id=3,
        show_number=4680,
        air_date=date(2004, 12, 31),
        round="Final Jeopardy!",
        category="WORLD CAPITALS",
        value=None,
        question="This city is both the smallest and most densely populated country in the world",
        answer="Vatican City",
    ),
]


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    for item in SEED_DATA:
        db.merge(item)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Fresh empty SQLite session for ingest script tests."""
    from sqlalchemy import create_engine as ce
    test_engine = ce("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=test_engine)
    Session = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()