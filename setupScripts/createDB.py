import sqlite3 as sql

conn = sql.connect("database.db")
c = conn.cursor()

c.execute("PRAGMA foreign_keys = ON;")

c.execute("""CREATE TABLE Students(
    StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username varchar(50) NOT NULL,
    Password varchar(255) NOT NULL,
    AddressLine1 varchar(255) NOT NULL,
    AddressLine2 varchar(255));""")
print("Created table: Students")

c.execute("""CREATE TABLE Teachers(
    TeacherID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username varchar(50) NOT NULL,
    Password varchar(255) NOT NULL,
    FirstName varchar(100),
    Lastname varchar(100) NOT NULL);""")
print("Created table: Teachers")

c.execute("""CREATE TABLE Day(
    SlotNo INTEGER PRIMARY KEY,
    Time varchar(11));""")
print("Created table: Day")

c.execute("""CREATE TABLE Slots(
    SlotID INTEGER PRIMARY KEY AUTOINCREMENT,
    Date varchar(10) NOT NULL,
    SlotNo INTEGER,
    FOREIGN KEY(SlotNo) REFERENCES Day(SlotNo));""")
print("Created table: Slots")

c.execute("""CREATE TABLE Bookings(
    BookingID INTEGER PRIMARY KEY AUTOINCREMENT,
    TeacherID INTEGER,
    StudentID INTEGER NOT NULL,
    SlotID INTEGER,
    Subject varchar(50) NOT NULL,
    FOREIGN KEY(TeacherID) REFERENCES Teachers(TeacherID),
    FOREIGN KEY(SlotID) REFERENCES Slots(SlotID),
    FOREIGN KEY(StudentID) REFERENCES Students(StudentID))""")
print("Created table: Bookings")

c.execute("""CREATE TABLE Subjects(
    TeacherID INTEGER PRIMARY KEY,
    Subject varchar(50) NOT NULL,
    FOREIGN KEY(TeacherID) REFERENCES Teachers(TeacherID));""")
print("Created table: Subjects")

conn.commit()

conn.close()
