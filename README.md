User registration and authentication are temporary and currently require manually creating users in the database until the authentication subsystem is completed
Steps to create test user
1. run Python app.py in the backend folder in a terminal and make sure the following prints
Verified database at ...
Running on http://127.0.0.1:5000
2. open a new terminal in the backend folder
3. open the terminal python interpreter using simply "python"
4. in the interpreter copy paste the command and replace username and password with whatever you want
import sqlite3

conn = sqlite3.connect("database/bucketlist.db")

conn.execute(
    "INSERT INTO users(username, password_hash) VALUES (?, ?)",
    ("username", "password")
)

conn.commit()

for row in conn.execute("SELECT * FROM users"):
    print(row)

conn.close()

this should print 
(1, username, password)
5. use the frontend as usual with the number in mind as that is the user id
