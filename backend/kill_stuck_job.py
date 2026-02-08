"""Kill the stuck BBC collection job."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# Database setup
DATABASE_URL = "sqlite:///./thermoculture.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()
try:
    # Update the stuck job to FAILED status
    result = db.execute(
        text("""
            UPDATE collection_jobs
            SET status = 'FAILED',
                completed_at = :now,
                error_message = 'Manually killed due to pagination bug - exceeded expected runtime'
            WHERE id = '20ac6787-98d1-45d7-a639-ea05c56fe7c9'
        """),
        {"now": datetime.now(timezone.utc)}
    )
    db.commit()
    print(f"Killed stuck job (rows affected: {result.rowcount})")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
