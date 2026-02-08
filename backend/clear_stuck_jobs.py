import sqlite3
conn = sqlite3.connect('thermoculture.db')
cursor = conn.execute("DELETE FROM collection_jobs WHERE status != 'COMPLETED'")
conn.commit()
print(f"Cleared {cursor.rowcount} non-completed jobs.")
conn.close()
