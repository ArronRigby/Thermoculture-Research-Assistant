import sqlite3
import os

def cleanup():
    db_path = os.path.join('backend', 'thermoculture.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Identify BBC articles (based on BBC URLs) that are assigned to non-BBC sources
    # We look for source_url containing 'bbc.co.uk' but source_id not matching 'BBC News' source
    
    # First, get the BBC News source id
    cursor.execute("SELECT id FROM sources WHERE name = 'BBC News'")
    bbc_source_row = cursor.fetchone()
    if not bbc_source_row:
        print("BBC News source not found in database.")
        conn.close()
        return
    
    bbc_source_id = bbc_source_row[0]
    
    # Count leaked articles
    cursor.execute("""
        SELECT COUNT(*) FROM discourse_samples 
        WHERE source_url LIKE '%bbc.co.uk%' 
        AND source_id != ?
    """, (bbc_source_id,))
    leaked_count = cursor.fetchone()[0]
    
    print(f"Found {leaked_count} articles from BBC assigned to other sources.")
    
    if leaked_count > 0:
        # Delete leaked articles
        cursor.execute("""
            DELETE FROM discourse_samples 
            WHERE source_url LIKE '%bbc.co.uk%' 
            AND source_id != ?
        """, (bbc_source_id,))
        conn.commit()
        print(f"Successfully deleted {leaked_count} leaked articles.")
    
    # Also reset collection_jobs counts for consistency (optional but helpful)
    cursor.execute("UPDATE collection_jobs SET items_collected = 0 WHERE items_collected > 0 AND source_id != ?", (bbc_source_id,))
    conn.commit()

    conn.close()
    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
