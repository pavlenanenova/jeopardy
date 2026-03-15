"""
Tests for scripts/ingest_data.py main().

Only external I/O is mocked:
- requests.get — the HTTP download
- DATA_PATH — redirected to tmp_path so no real filesystem writes occur
- SessionLocal — replaced with a SQLite test session

All parsing, filtering, cleaning, and database logic runs for real.
"""
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.question import Question


CSV_WITH_VALID_AND_INVALID_ROWS = """\
Show Number, Air Date, Round, Category, Value, Question, Answer
4680,2004-12-31,Jeopardy!,HISTORY,$200,Galileo question,Copernicus
4680,2004-12-31,Double Jeopardy!,SCIENCE,$2000,Too expensive,Skipped
4680,2004-12-31,Final Jeopardy!,WORLD,None,Final question,Vatican City
"""

CSV_WITH_HTML = """\
Show Number, Air Date, Round, Category, Value, Question, Answer
4680,2004-12-31,Jeopardy!,HISTORY,$200,<a href="url">click here</a>,AT&amp;T
"""


@pytest.fixture
def sqlite_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def run_main(tmp_path, csv_content, session):
    csv_file = tmp_path / "JEOPARDY_CSV.csv"
    csv_file.write_text(csv_content, encoding="utf-8")
    mock_response = MagicMock()
    mock_response.text = csv_content
    with patch("scripts.ingest_data.DATA_PATH", csv_file), \
         patch("scripts.ingest_data.requests.get", return_value=mock_response), \
         patch("scripts.ingest_data.SessionLocal", return_value=session):
        from scripts.ingest_data import main
        main()


def test_main_ingests_valid_rows_only(tmp_path, sqlite_session):
    run_main(tmp_path, CSV_WITH_VALID_AND_INVALID_ROWS, sqlite_session)
    rows = sqlite_session.query(Question).all()
    assert len(rows) == 2
    assert all(r.value != "$2000" for r in rows)


def test_main_sets_final_jeopardy_value_to_null(tmp_path, sqlite_session):
    run_main(tmp_path, CSV_WITH_VALID_AND_INVALID_ROWS, sqlite_session)
    final = sqlite_session.query(Question).filter_by(round="Final Jeopardy!").first()
    assert final is not None
    assert final.value is None


def test_main_cleans_html_from_question_and_answer(tmp_path, sqlite_session):
    run_main(tmp_path, CSV_WITH_HTML, sqlite_session)
    row = sqlite_session.query(Question).first()
    assert row.question == "click here"
    assert row.answer == "AT&T"


def test_main_skips_download_if_csv_already_cached(tmp_path, sqlite_session):
    csv_file = tmp_path / "JEOPARDY_CSV.csv"
    csv_file.write_text(CSV_WITH_VALID_AND_INVALID_ROWS, encoding="utf-8")
    with patch("scripts.ingest_data.DATA_PATH", csv_file), \
         patch("scripts.ingest_data._create_session_with_retries") as mock_session, \
         patch("scripts.ingest_data.SessionLocal", return_value=sqlite_session):
        from scripts.ingest_data import main
        main()
    mock_session.assert_not_called()


def test_fetch_csv_uses_retry_session(tmp_path):
    """Test that fetch_csv uses the retry session."""
    csv_file = tmp_path / "JEOPARDY_CSV.csv"
    
    mock_response = MagicMock()
    mock_response.text = CSV_WITH_VALID_AND_INVALID_ROWS
    
    # Mock the session creation and get call
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    
    with patch("scripts.ingest_data.DATA_PATH", csv_file), \
         patch("scripts.ingest_data._create_session_with_retries", return_value=mock_session) as mock_create_session:
        from scripts.ingest_data import fetch_csv
        fetch_csv()
    
    # Verify session was created with retries
    mock_create_session.assert_called_once()
    # Verify session.get was called with the dataset URL
    mock_session.get.assert_called_once()
    # Verify file was created
    assert csv_file.exists()
    assert CSV_WITH_VALID_AND_INVALID_ROWS in csv_file.read_text()



def test_main_skips_ingestion_if_already_populated(tmp_path, sqlite_session):
    run_main(tmp_path, CSV_WITH_VALID_AND_INVALID_ROWS, sqlite_session)
    count_before = sqlite_session.query(Question).count()
    with patch("scripts.ingest_data.requests.get") as mock_get, \
         patch("scripts.ingest_data.SessionLocal", return_value=sqlite_session):
        csv_file = tmp_path / "JEOPARDY_CSV.csv"
        with patch("scripts.ingest_data.DATA_PATH", csv_file):
            from scripts.ingest_data import main
            main()
    mock_get.assert_not_called()
    assert sqlite_session.query(Question).count() == count_before