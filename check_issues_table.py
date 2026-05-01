"""Check issues table structure."""

import sqlite3

conn = sqlite3.connect("./data/povaly_bot.db")
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(issues)")
columns = cursor.fetchall()

print("Issues table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
