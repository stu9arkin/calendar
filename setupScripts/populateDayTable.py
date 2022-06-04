import sqlite3 as sql

times = ["8:00-9:00","9:30-10:30", "11:00-12:00", "12:30-13:30", "14:00-15:00", "15:30-16:30", "17:00-8:00"]

conn = sql.connect("database.db")

for i in times:
    conn.execute("INSERT INTO Day(Time) Values(?)", (i,))

conn.commit()
conn.close()
