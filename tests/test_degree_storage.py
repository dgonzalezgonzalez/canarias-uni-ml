import sqlite3
from pathlib import Path

from src.canarias_uni_ml.degrees.catalog import write_degree_catalog


def test_write_degree_catalog_creates_separate_sqlite_db(tmp_path):
    fixture = Path("tests/fixtures/degrees_catalog_fixture.json")
    csv_path = tmp_path / "degrees.csv"
    db_path = tmp_path / "degrees.db"
    result = write_degree_catalog(str(csv_path), fixture_path=str(fixture), db_path=str(db_path))
    assert result == 0
    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("select count(*) from degrees_catalog").fetchone()[0]
        columns = [row[1] for row in conn.execute("pragma table_info(degrees_catalog)").fetchall()]
    finally:
        conn.close()
    assert count == 2
    assert "title_type" in columns
    assert "memory_resolution_status" in columns
