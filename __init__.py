from flask import Flask, render_template, request, redirect, url_for, session
import datetime
import sqlite3 as sql
import os
import re
from passlib.hash import pbkdf2_sha256
from createDB import createTables, populateDayTable

MAXSLOTS = 7
MAXDAYS = 7

app = Flask(__name__)
app.secret_key = "asdf987asdf;lk'sadf;lkjq46"

@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

def dbConnect():
    #Create and return a connection to the database file stored locally
    conn = sql.connect("database.db")
    return conn

def dbClose(conn):
    conn.close()

def createDatabase():
    #Creates and populate tables in database.db
    createTables()
    conn = dbConnect()
    getDayTable = conn.execute("SELECT * FROM Day;")
    if len(getDayTable.fetchall()) == 0:
        populateDayTable()

    conn.execute("INSERT INTO Admins(Username, Password) VALUES('admin', '$pbkdf2-sha256$29000$3Nt7L4UQAiBE6P2/l5ISQg$HENFx.IA43NYaygyQH4Ujl.ehegudlJ9akdrmVqtsu8');")
    dbClose(conn)

@app.route("/")
def index():
    #Handles the user connecting to website. All session variables are cleared. Returns the template login.html.
    session.clear()

    return render_template("login.html")

@app.route("/loginAuth", methods=["post"])
def loginAuth():
    #Checks the user's input for the login form with data from the Student or Tutor table.
    #If it is correct, return the main.html template, otherwise reload the login.html template.
    userName = request.form["userName"]
    passWord = request.form["passWord"]

    if len(userName) == 0 or len(passWord) == 0:
        return redirect(url_for("index"))

    conn = dbConnect()

    getStudents = conn.execute("Select StudentID, Username, Password FROM Students WHERE Username = ?;", (userName,))
    fetchStudents = getStudents.fetchone()
    getTutors = conn.execute("SELECT * FROM Teachers WHERE Username = ?;", (userName,))
    fetchTutors = getTutors.fetchone()
    getAdmins = conn.execute("Select * FROM Admins WHERE Username = ?;", (userName,))
    fetchAdmins = getAdmins.fetchone()

    if fetchStudents != None:
        if pbkdf2_sha256.verify(passWord, fetchStudents[2]) and fetchStudents[1] == userName:
            session["userName"] = userName
            session["accType"] = "student"
            session["studentID"] = fetchStudents[0]
            return redirect(url_for("main"))
        else:
            return redirect(url_for("index"))

    if fetchTutors != None:
        if pbkdf2_sha256.verify(passWord, fetchTutors[3]) and fetchTutors[1] == userName:
            session["userName"] = userName
            session["accType"] = "tutor"
            session["tutorName"] = fetchTutors[4] + " " + fetchTutors[5]
            session["tutorID"] = fetchTutors[0]
            return redirect(url_for("main"))
        else:
            return redirect(url_for("index"))

    if fetchAdmins != None:
        if pbkdf2_sha256.verify(passWord, fetchAdmins[2]) and fetchAdmins[1] == userName:
            session["userName"] = userName
            session["accType"] = "admin"
            session["adminID"] = fetchAdmins[0]
            return redirect(url_for("adminPage"))
        else:
            return redirect(url_for("index"))

    dbClose(conn)
    return redirect(url_for("index"))

@app.route("/signUp")
def signUp():
    #Handles users clicking signup hyperlink in login.html by returning the signup.html template
    return render_template("signup.html")

@app.route("/studentSignUpAuth", methods=["post"])
def studentSignUp():
    #Handles user input from the student signup form using the signUpAuth function
    authCheck = signUpAuth(request.form["userName"], request.form["firstName"], request.form["email"], request.form["passWord"], request.form["addressLn1"], request.form["addressLn2"], " ", " ", "student")
    if authCheck == True:
        return redirect(url_for("index"))
    else:
        session["signUpError"] = "Invalid inputs, please try again."
        return redirect(url_for("signUp"))

@app.route("/tutorSignUpAuth", methods=["post"])
def tutorSignUp():
    # Handles user input from the student signup form using the signUpAuth function
    authCheck = signUpAuth(request.form["userName"], "", request.form["email"], request.form["passWord"], " ", " ", request.form["fName"], request.form["lName"], "tutor")
    if authCheck == True:
        return redirect(url_for("adminPage"))
    else:
        session["signUpError"] = "Invalid inputs, please try again."
        return redirect(url_for("adminPage"))

def signUpAuth(userName, firstName, email, passWord, addressLn1, addressLn2, fName, lName, accType):
    #Determine if the user's input from the signup forms is a duplicate of a pre-existing account.
    #If it is, return the signup.html page, otherwise return the login.html page.
    if "signUpError" in session:
        session.pop("signUpError", None)
    if accType == "student":
        table = "Students"
    elif accType == "tutor":
        table = "Teachers"

    passHash = pbkdf2_sha256.hash(passWord, rounds=200000, salt_size=16)

    conn = dbConnect()
    fetchExisting = conn.execute("SELECT * FROM " + table + " WHERE Username = ?", (userName,))
    formatExisting = fetchExisting.fetchall()
    dbClose(conn)

    if len(formatExisting) > 0:
        return False
    else:
        conn = dbConnect()
        if table == "Students":
            conn.execute("INSERT INTO Students(Username, Email, Firstname, Password, AddressLine1, AddressLine2) Values(?, ?, ?, ?, ?, ?);", (userName, email, firstName, passHash, addressLn1, addressLn2,))
            return True

        if table == "Teachers":
            conn.execute("INSERT INTO Teachers(Username, Email, Password, FirstName, LastName) Values(?, ?, ?, ?, ?);", (userName, email, passHash, fName,  lName))
            return True

        conn.commit()
        dbClose(conn)

@app.route("/adminPage")
def adminPage():
    #Render the adminPage.html template when the user logs in as an admin
    conn = dbConnect()

    teacherBookingCount = []
    for i in getTeachers():
        count = conn.execute("SELECT count() FROM Bookings WHERE TeacherID = ?;", (i[2],))
        count = count.fetchall()
        teacherBookingCount.append(count[0][0])

    return render_template("adminPage.html", tutors=getTeachers(), bookingTotal = teacherBookingCount)

@app.route("/main")
def main():
    #Compile all the needed information to display bookings on the main.html template, then return the template.

    if "weekNum" not in session:
        session["weekNum"] = 0

    if "userName" in session and "accType" in session:
        userName = session["userName"]
        accType = session["accType"]

    times = getSlots() #Gets times for slots
    bookings = getBookings() #Gets bookings based on TutorID or StudentID
    availableSubjects = getAllSubjects() #Gets all subjects available from all tutors

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    weekBookings = []

    getDay = datetime.datetime.today() + datetime.timedelta(session["weekNum"] * 7)
    currentDay = getDay.weekday()
    currentDateStr = str(datetime.datetime.today())[:10]

    weekStart = datetime.date.today() + datetime.timedelta(session["weekNum"] * 7)
    for i in range(currentDay):
        weekStart = weekStart - datetime.timedelta(1)  #Decrement date until Monday's date is found

    weekEnd = datetime.date.today() + datetime.timedelta(session["weekNum"] * 7)
    for i in range(6 - currentDay):
        weekEnd = weekEnd + datetime.timedelta(1)  #Increment date until Sunday's date is found

    for i in bookings:
        returnValue = compileBookings(i, weekStart, weekEnd)
        if returnValue != None:
            weekBookings.append(returnValue)

    weekBookingsData = []

    for i in weekBookings:
        conn = dbConnect()
        getStudentName = conn.execute("SELECT Firstname FROM Students WHERE StudentID = ?", (i[1],))
        fetchStudentName = getStudentName.fetchone()

        getTutorName = conn.execute("SELECT Firstname, Lastname FROM Teachers WHERE TeacherID = ?", (i[0],))
        fetchTutorName = getTutorName.fetchone()

        tutorName = fetchTutorName[0] + " " + fetchTutorName[1]
        tutorName = tutorName.title()

        info = [fetchStudentName[0], tutorName, i[2], i[3], i[4], i[0], i[1]]
        weekBookingsData.append(info) #Change ID's to string values associated with them
        dbClose(conn)

    rowData = [] #Set up skeleton of rowData

    for i in range(len(times)):
        rowData.append(["", "", "", "", "", "", ""])

    for i in weekBookingsData: #Set specific items of rowData to hold data about sessions
        dateString = str(i)
        year = dateString[:4]
        month = dateString[5:7]
        day = dateString[8:10]
        weekDay = datetime.datetime(year, month, day, 12, 00, 000000).weekday()
        slot = i[4]
        for x in range(0, 8): #Row in the table
            for y in range(0, 8): #Column/day in the table
                if x == slot and y == weekDay:
                    rowData[x-1][y] = i[:3]

    users = []
    if session["accType"] == "student":
        users = getTeachers()
    elif session["accType"] == "tutor":
        users = getAllStudents()
        for i in range(len(users)):
            users[i] = [users[i][0], "", users[i][1], users[i][2], users[i][3]]

    return render_template("main.html", slotTimes = times, days = days, months = months, currentDay = currentDay, tableData = rowData, users = users, subjects = availableSubjects, subjectTeachers = getSubjectTeachers(), weekStartDate = str(weekStart), maxDays = MAXDAYS, maxSlots = MAXSLOTS)

@app.route("/resetSkip")
def resetSkip():
    #Pops "weekNum" from session dict. when the user clicks the link to reset the week view to the current week
    session.pop("weekNum", None)
    return redirect(url_for("main"))

@app.route("/skipLeft")
def skipLeft():
    #Decrements weekNum in session dict. when the user clicks the button to skip back a week
    session["weekNum"] -= 1
    return redirect(url_for("main"))

@app.route("/skipRight")
def skipRight():
    #Increments weekNum in session dict. when the user clicks the button to skip forward a week
    session["weekNum"] += 1
    return redirect(url_for("main"))

def compileBookings(bookingDetails, weekStart, weekEnd):
    #returns a list containing data about the booking passed to the function via the first parameter.
    #The date is converted to a number which denotes the day of the week the date appears on.
    conn = dbConnect()
    StudentID, TeacherID, Date, SlotNo, Subject = bookingDetails[1:]

    currentDay = datetime.datetime.today().weekday()

    dateIncrement = weekStart
    weekIncrement = True
    while weekIncrement == True:
        if Date == str(dateIncrement):
            weekIncrement = False
            dbClose(conn)
            return StudentID, TeacherID, Subject, Date, SlotNo #date is in weekday number format, 0 = Monday etc.
        else:
            if dateIncrement != weekEnd:
                dateIncrement += datetime.timedelta(1)
            else:
                weekIncrement = False
                dbClose(conn)
                return None

def getAllSubjects():
    #Returns a list of all subjects from the Subjects table
    conn = dbConnect()
    getSubjects = conn.execute("SELECT Subject FROM Subjects;")
    fetchSubjects = getSubjects.fetchall()

    subjects = []

    for i in fetchSubjects:
        if i[0] not in subjects:
            subjects.append(i[0])

    dbClose(conn)
    return subjects

def getSubjectTeachers():
    #Return a 2D list of all teachers organised by subject (one child list per subject)
    #Array format: TeacherID, Firstname, Lastname, Subject
    conn = dbConnect()

    getTeacherID = conn.execute("SELECT Teachers.TeacherID, Firstname, Lastname, Subjects.Subject FROM Teachers INNER JOIN Subjects ON Subjects.TeacherID == Teachers.TeacherID;")

    return getTeacherID.fetchall()

def getSlots():
    #Returns all slot times from the Day table.
    conn = dbConnect()
    fetchTimes = conn.execute("SELECT * FROM Day;")
    formatTimes = fetchTimes.fetchall()

    times = []

    for i in formatTimes:
        times.append(i[1])

    dbClose(conn)
    return times

def getAllBookings():
    #Return all bookings in the Bookings table
    conn = dbConnect()

    getBookings = conn.execute("SELECT * FROM Bookings;")
    fetchBookings = getBookings.fetchall()
    return fetchBookings

def getBookings():
    #Returns all bookings from Bookings table where username is the same as the user's
    conn = dbConnect()
    bookings = []

    if session["accType"] == "tutor":
        table = "Teachers"
        column = "TeacherID"
    elif session["accType"] == "student":
        table = "Students"
        column = "StudentID"

    getID = conn.execute("SELECT " + column + " FROM " + table + " WHERE Username = ?;", (session["userName"],)) #Get ID for user
    getIDFetch = getID.fetchone()

    getBookings = conn.execute("SELECT * FROM Bookings WHERE " + column + " = ?;", (getIDFetch[0],))
    getBookingsFetch = getBookings.fetchall()

    for i in getBookingsFetch:
        bookings.append(i)

    dbClose(conn)
    return bookings

def getTeachers():
    #Returns names of all teachers from Teachers table
    conn = dbConnect()
    teachers = []

    queryTeachers = conn.execute("SELECT Firstname, Lastname, TeacherID, Email FROM Teachers ORDER BY Lastname ASC;")
    fetchTeachers = queryTeachers.fetchall()

    for i in fetchTeachers:
        teachers.append([i[0], i[1], i[2], i[3]])

    dbClose(conn)
    return teachers

def getAllStudents():
    #Returns a list of student names from Students table
    conn = dbConnect()

    queryStudents = conn.execute("SELECT Firstname, Email, AddressLine1, AddressLine2 FROM Students;")
    fetchStudents = queryStudents.fetchall()

    return fetchStudents

@app.route("/createBooking", methods=["post"])
def createBooking():
    #Creates a record in the Bookings table using the user's input if the booking does not already exist
    #If the booking already exists, the user is returned to the main.html template
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    StudentID = int(request.form["studentID"])
    TeacherName = request.form["teacherName"] + " "
    SlotNo = int(request.form["slotNo"])

    month = request.form["date-month"]
    monthNum = ""
    dateNum = 0

    for i in range(len(months)):
        if months[i] == month:
            if i < 10:
                monthNum = "0" + str(i+1)
            else:
                monthNum = str(i+1)

    day = request.form["date-day"]
    if int(day) < 10:
        day = "0" + day

    Date = request.form["date-year"] + "-" + monthNum + "-" + day
    Subject = request.form["subject"]

    TeacherNameArray = []
    temp = ""

    for char in TeacherName:
        if char == " ":
            TeacherNameArray.append(temp)
            temp = ""
        else:
            temp = temp + char

    conn = dbConnect()

    getID = conn.execute("SELECT TeacherID FROM Teachers WHERE Firstname = ? AND Lastname = ?;", (TeacherNameArray[0], TeacherNameArray[1],))
    fetchID = getID.fetchone()

    dbClose(conn)

    TeacherID = fetchID[0]

    conn = dbConnect()

    getExistingBooking = conn.execute("SELECT * FROM Bookings WHERE TeacherID = ? AND Date = ? AND SlotNo = ?;", (TeacherID, Date, SlotNo,))
    fetchExistingBooking = getExistingBooking.fetchone()

    dbClose(conn)

    session.pop("bookingError", None)
    if fetchExistingBooking != None:
        dbClose(conn)
        session["bookingError"] = "Tutor already booked at selected time."
        return redirect(url_for("main"))
    else:
        session.pop("bookingError", None)
        dbClose(conn)
        conn = dbConnect()
        bookingsCreate = conn.execute("INSERT INTO Bookings(TeacherID, StudentID, Date, SlotNo, Subject) VALUES(?, ?, ?, ?, ?);", (TeacherID, StudentID, Date, SlotNo, Subject,))
        conn.commit()
        dbClose(conn)
        return redirect(url_for("main"))

@app.route("/addSubjectAuth", methods=["post"])
def addSubject():
    if "bookingError" in session:
        session.pop("bookingError", None)
    if "subjectError" in session:
        session.pop("subjectError", None)
    #Creates a record in the Subjects table using the user's input and tutorID from the session dictionary
    subject = request.form["subject"]
    conn = dbConnect()

    getSubjects = conn.execute("SELECT Subject FROM Subjects WHERE TeacherID = ?;", (session["tutorID"],))
    fetchSubjects = getSubjects.fetchall()

    if subject in fetchSubjects:
        session["subjectError"] = "Subject already assigned to tutor"
        return redirect(url_for("main"))

    if len(subject) < 2:
        session["subjectError"] = "Invalid subject"
        return redirect(url_for("main"))

    addQuery = conn.execute("INSERT INTO Subjects Values(?,?)", (session["tutorID"], subject,))

    conn.commit()
    dbClose(conn)

    return redirect(url_for("main"))

@app.route("/searchBookings", methods=["post"])
def searchBookings():
    session.pop("searchError", None)
    conn = dbConnect()

    searchTerm = request.form["searchTerm"]
    bookings = getBookings()
    searchResults = []

    yearFirst = re.findall("\d\d\d\d[-,/,.]\d\d[-,/,.]\d\d", searchTerm, flags=0)
    if len(yearFirst) == 0:
        dateFirst = re.findall("\d\d[-,/,.]\d\d[-,/,.]\d\d\d\d", searchTerm, flags=0)
        if len(dateFirst) == 0:
            session["searchError"] = "Error: Incorrect formatting"
            return redirect(url_for("main"))
        else:
            searchTerm = searchTerm[6:10] + "-" + searchTerm[3:5] + "-" + searchTerm[0:2]

    searchTermList = list(searchTerm)
    searchTerm = ""
    for char in range(len(searchTermList)):
        if searchTermList[char] == "/" or searchTermList[char] == ".":
            searchTermList[char] = "-"
    for i in searchTermList:
        searchTerm = searchTerm + i

    dates = {}

    for i in bookings:
        Date = i[3]
        SlotNo = i[4]
        dictKey = Date + ":" + str(SlotNo)
        dates[dictKey] = i

    sortedKeys = sort(list(dates.keys()))
    searchedKeys = binarySearch(searchTerm, sortedKeys, len(sortedKeys) // 2, "")

    if len(searchedKeys) != 0:
        searchLeft, searchRight = True, True
        count = 0
        countLeft, countRight = searchedKeys[0], searchedKeys[0]
        while searchLeft:
            if countLeft != 0:
                if sortedKeys[countLeft - 1][:-2] == searchTerm:
                    if countLeft - 1 not in searchedKeys:
                        searchedKeys.append(countLeft - 1)
                countLeft -= 1
            else:
                searchLeft = False

        while searchRight:
            if countRight != len(sortedKeys) - 1:
                if sortedKeys[countRight + 1][:-2] == searchTerm:
                    if countRight + 1 not in searchedKeys:
                        searchedKeys.append(countRight + 1)
                        print("appending " + str(countRight + 1))
                countRight += 1
            else:
                searchRight = False

    searchedKeys = sort(searchedKeys)

    searchResults = []

    for i in searchedKeys:
        key = sortedKeys[i]
        searchResults.append(dates[key])

    compiledResults = []
    for i in searchResults:
        getStudentDetails = conn.execute("SELECT Firstname, Email, AddressLine1, AddressLine2 FROM Students WHERE StudentID = ?;", (i[2],))
        fetchStudentDetails = getStudentDetails.fetchone()
        studentAddress = fetchStudentDetails[2] + ", " + fetchStudentDetails[3]

        getTeacherDetails = conn.execute("SELECT Firstname, Lastname, Email FROM Teachers WHERE TeacherID = ?;", (i[1],))
        fetchTeacherDetails = getTeacherDetails.fetchone()
        TeacherName = fetchTeacherDetails[0] + " " + fetchTeacherDetails[1]

        compiledResults.append([fetchStudentDetails[0], fetchStudentDetails[1], studentAddress, TeacherName, fetchTeacherDetails[2], i[3], i[4], i[5]])
        #[Student Name, Student Email, Student Address, Teacher Name, Teacher Email, Date, SlotNo, Subject]

    return render_template("results.html", results=compiledResults, searchTerm=searchTerm, timeSlots=getSlots())

def binarySearch(SearchTerm, data, total, side):
    resultIndex = []
    Mid = (len(data) // 2)
    if side == "less":
        total = total - Mid - 1
    elif side == "more":
        total = total + Mid
    if len(data) == 0:
        return []
    else:
        if data[Mid][:-2] == SearchTerm:
            resultIndex.append(total)
            return resultIndex
        else:
            if SearchTerm < str(data[Mid][:-2]):
                recursionType = "less"
                return binarySearch(SearchTerm, data[:Mid], total, recursionType)
            elif len(data) == 1:
                return []
            else:
                recursionType = "more"
                return binarySearch(SearchTerm, data[Mid:], total, recursionType)

if __name__ == "__main__":
    #Create database and populate Day table, then run the Flask app
    createDatabase()
    app.run()