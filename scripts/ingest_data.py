"""
Download the Jeopardy dataset and load a filtered subset into PostgreSQL.
Only questions with values up to $1,200 are loaded.
The CSV is cached locally and reused on subsequent runs.
"""
import csv
import html
import logging
import os
import re
import sys
from datetime import date
from pathlib import Path

import requests
from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal
from app.models.question import Question

DATASET_URL = os.environ["DATASET_URL"]
DATA_PATH = Path("/app/data/JEOPARDY_CSV.csv")
MAX_VALUE = 1200
BATCH_SIZE = 500

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def fetch_csv() -> None:
    """Download the CSV to DATA_PATH, skipping if already present."""
    if DATA_PATH.exists():
        log.info("Dataset already present, skipping download")
        return
    log.info("Downloading dataset from %s", DATASET_URL)
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(DATASET_URL, timeout=60)
    response.raise_for_status()
    DATA_PATH.write_text(response.text, encoding="utf-8")
    log.info("Saved to %s", DATA_PATH)


def clean(text: str) -> str:
    """Strip HTML tags, unescape HTML entities, and remove escape characters."""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace('\"', '"').replace("\\''", "'")
    return text.strip()


VALID_ROUNDS = {"Jeopardy!", "Double Jeopardy!", "Final Jeopardy!"}


def is_valid_row(row: dict[str, str]) -> bool:
    """Return True if the row matches the expected dataset structure."""
    # All columns must be present and non-empty
    required = ["Show Number", "Air Date", "Round", "Category", "Question", "Answer"]
    if any(not row.get(col, "").strip() for col in required):
        return False

    # Round must be one of the three known values
    round_ = row["Round"].strip()
    if round_ not in VALID_ROUNDS:
        return False

    # Final Jeopardy! has no value — always include
    if round_ == "Final Jeopardy!":
        return True

    # Standard rounds must have a numeric value <= MAX_VALUE
    raw_value = row.get("Value", "").strip()
    try:
        return int(raw_value.replace("$", "").replace(",", "")) <= MAX_VALUE
    except ValueError:
        return False


def build_rows() -> list[dict[str, object]]:
    """Parse the CSV and return a list of row dicts ready for insertion."""
    rows = []
    with DATA_PATH.open(encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            raw = {k.strip(): v for k, v in raw.items()}

            if not is_valid_row(raw):
                continue

            try:
                air_date = date.fromisoformat(raw["Air Date"].strip())
            except ValueError:
                continue

            raw_value = raw.get("Value", "").strip()
            value = None if raw.get("Round", "").strip() == "Final Jeopardy!" else raw_value

            rows.append({
                "show_number": int(raw["Show Number"]),
                "air_date": air_date,
                "round": raw["Round"].strip(),
                "category": clean(raw.get("Category", "")),
                "value": value,
                "question": clean(raw.get("Question", "")),
                "answer": clean(raw.get("Answer", "")),
            })

    log.info("Rows accepted: %d", len(rows))
    return rows


def upsert_rows(rows: list[dict[str, object]]) -> None:
    """Insert rows into the database in batches, ignoring duplicates."""
    session = SessionLocal()
    try:
        for start in range(0, len(rows), BATCH_SIZE):
            batch = rows[start : start + BATCH_SIZE]
            session.execute(
                insert(Question).values(batch).on_conflict_do_nothing(constraint="uq_show_question")
            )
            session.commit()
            log.info("Progress: %d / %d rows committed", start + len(batch), len(rows))
        log.info("Done.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def already_ingested() -> bool:
    """Return True if the questions table already has data."""
    session = SessionLocal()
    try:
        return session.query(Question).first() is not None
    finally:
        session.close()


def main() -> None:
    if already_ingested():
        log.info("Database already populated, skipping ingestion")
        return
    fetch_csv()
    rows = build_rows()
    upsert_rows(rows)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("Ingestion failed: %s", e)
        sys.exit(1)