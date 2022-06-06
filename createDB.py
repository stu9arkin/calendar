import sqlite3 as sql

def createTables():
    times = ["8:00-9:00", "9:30-10:30", "11:00-12:00", "12:30-13:30", "14:00-15:00", "15:30-16:30", "17:00-18:00"]

    conn = sql.connect("database.db") 
    c = conn.cursor()

    c.execute("PRAGMA foreign_keys = ON;")

    c.execute("""CREATE TABLE IF NOT EXISTS Students(
        StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username varchar(50) NOT NULL,
        Email varchar(100) NOT NULL,
        Firstname varchar(50) NOT NULL,
        Password varchar(255) NOT NULL,
        AddressLine1 varchar(255) NOT NULL,
        AddressLine2 varchar(255) NOT NULL);""")

    c.execute("""CREATE TABLE IF NOT EXISTS Teachers(
        TeacherID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username varchar(50) NOT NULL,
        Email varchar(100) NOT NULL,
        Password varchar(255) NOT NULL,
        FirstName varchar(100),
        Lastname varchar(100) NOT NULL);""")

    c.execute("""CREATE TABLE IF NOT EXISTS Admins(
        AdminID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username varchar(50) NOT NULL,
        Password varchar(255) NOT NULL);""")

    c.execute("""CREATE TABLE IF NOT EXISTS Day(
        SlotNo INTEGER PRIMARY KEY AUTOINCREMENT,
        Time varchar(11) NOT NULL);""")

    c.execute("""CREATE TABLE IF NOT EXISTS Bookings(
        BookingID INTEGER PRIMARY KEY AUTOINCREMENT,
        TeacherID INTEGER,
        StudentID INTEGER,
        Date varchar(10) NOT NULL,
        SlotNo INTEGER NOT NULL,
        Subject varchar(50) NOT NULL,
        FOREIGN KEY(TeacherID) REFERENCES Teachers(TeacherID),
        FOREIGN KEY(StudentID) REFERENCES Students(StudentID));""")

    c.execute("""CREATE TABLE IF NOT EXISTS Subjects(
        TeacherID INTEGER,
        Subject varchar(50) NOT NULL,
        FOREIGN KEY(TeacherID) REFERENCES Teachers(TeacherID));""")

    for i in times:
        c.execute("INSERT INTO Day(Time) Values(?)", (i,))
    
    conn.commit()
    conn.close()

def populateDayTable():
    conn = sql.connect("database.db") 
    c = conn.cursor()
    times = ["8:00-9:00", "9:30-10:30", "11:00-12:00", "12:30-13:30", "14:00-15:00", "15:30-16:30", "17:00-18:00"]

    for i in times:
        c.execute("INSERT INTO Day(Time) Values(?)", (i,))
        conn.commit()

    conn.close()
