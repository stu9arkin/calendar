import sqlite3 as sql

conn = sql.connect("database.db")

getBookings = conn.execute("SELECT * FROM Bookings;")
fetchBookings = getBookings.fetchall()

getSlots = conn.execute("SELECT * FROM Slots;")
fetchSlots = getSlots.fetchall()

for i in fetchBookings:
    print(i)

for i in fetchSlots:
    print(i)