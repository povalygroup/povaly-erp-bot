import sqlite3

db_path = r'd:\Povaly Group\Applications\pova-bot\data\povaly_erp_bot.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table schema
cursor.execute("PRAGMA table_info(tasks)")
columns = cursor.fetchall()

print('Current database schema for tasks table:')
print('Column # | Name                  | Type    | NotNull | Default | PK')
print('-' * 75)
for col in columns:
    cid, name, type_, notnull, dflt_value, pk = col
    print(f'{cid:<8} | {name:<21} | {type_:<7} | {notnull:<7} | {str(dflt_value):<7} | {pk}')

print(f'\nTotal columns: {len(columns)}')

# Get the CREATE TABLE statement
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
create_stmt = cursor.fetchone()
if create_stmt:
    print('\nCREATE TABLE statement:')
    print(create_stmt[0])

conn.close()
