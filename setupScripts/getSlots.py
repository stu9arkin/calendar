import sqlite3 as sql

conn = sql.connect("database.db")

query = conn.execute("SELECT * FROM Day;")
fetchQuery = query.fetchall()

print(fetchQuery)