import sqlite3
conn = sqlite3.connect('thermoculture.db')
cursor = conn.execute("DELETE FROM collection_jobs WHERE status = 'PENDING'")
conn.commit()
print(f"Deleted {cursor.rowcount} Pending job(s)")
cursor = conn.execute("SELECT id, status FROM collection_jobs")
print(f"Remaining jobs: {cursor.fetchall()}")
conn.close()
