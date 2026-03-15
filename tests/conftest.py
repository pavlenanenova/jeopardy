import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models.question import Question

# In-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables and seed test data before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add_all([
        Question(
            id=1,
            show_number=4680,
            air_date="2004-12-31",
            round="Jeopardy!",
            category="HISTORY",
            value="$200",
            question="For the last 8 years of his life, Galileo was under house arrest for espousing this man's theory",
            answer="Copernicus",
        ),
        Question(
            id=2,
            show_number=4680,
            air_date="2004-12-31",
            round="Double Jeopardy!",
            category="SCIENCE",
            value="$400",
            question="This element has the atomic number 1",
            answer="Hydrogen",
        ),
        Question(
            id=3,
            show_number=4680,
            air_date="2004-12-31",
            round="Final Jeopardy!",
            category="WORLD CAPITALS",
            value=None,
            question="This city is both the smallest and most densely populated country in the world",
            answer="Vatican City",
        ),
    ])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()