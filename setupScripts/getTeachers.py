import sqlite3 as sql

conn = sql.connect("database.db")

query = conn.execute("SELECT * FROM Teachers;")
fetchQuery = query.fetchall()

print(fetchQuery)