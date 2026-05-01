"""Find all views in the database."""

import sqlite3

conn = sqlite3.connect("./data/povaly_bot.db")
cursor = conn.cursor()

# Get all views
cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
views = cursor.fetchall()

print("Views in database:")
for view in views:
    print(f"  - {view[0]}")

conn.close()
