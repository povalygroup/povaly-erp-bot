"""Reset migration 006 so it can run again."""
import sqlite3

conn = sqlite3.connect('./data/povaly_bot.db')
cursor = conn.cursor()

# Delete the migration record
cursor.execute("DELETE FROM migrations WHERE name = 'migration_006_add_break_records'")
conn.commit()

print("✅ Migration 006 record deleted. Restart the bot to run it again.")

conn.close()
