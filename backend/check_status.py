import sqlite3
import pprint

def check_status():
    conn = sqlite3.connect('thermoculture.db')
    # ID, source_id, status, started_at, completed_at, items_collected, error_message
    cursor = conn.execute("SELECT * FROM collection_jobs")
    jobs = cursor.fetchall()
    conn.close()
    
    pprint.pprint(jobs)

if __name__ == "__main__":
    check_status()
