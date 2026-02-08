"""Check recently collected BBC articles."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text

DATABASE_URL = "sqlite:///./thermoculture.db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check articles collected in last 10 minutes
    result = conn.execute(text("""
        SELECT COUNT(*) as count, MIN(collected_at) as first, MAX(collected_at) as last
        FROM discourse_samples
        WHERE source_id = (SELECT id FROM sources WHERE name = 'BBC News')
        AND collected_at > datetime('now', '-10 minutes')
    """))
    row = result.fetchone()

    print(f"BBC articles collected in last 10 minutes: {row[0]}")
    if row[0] > 0:
        print(f"  First collected: {row[1]}")
        print(f"  Last collected: {row[2]}")

    # Check total BBC articles
    result = conn.execute(text("""
        SELECT COUNT(*) as count
        FROM discourse_samples
        WHERE source_id = (SELECT id FROM sources WHERE name = 'BBC News')
    """))
    total = result.fetchone()[0]
    print(f"\nTotal BBC articles in database: {total}")
