from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
DATABASE = "database.db"


# -----------------------
# DATABASE INITIALIZATION
# -----------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Tasks table
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            status INTEGER DEFAULT 0,
            user_id INTEGER,
            due_date TEXT,
            priority TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# -----------------------
# HOME / DASHBOARD
# -----------------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM tasks WHERE user_id = ?", (session["user_id"],))
    tasks = c.fetchall()

    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == 1)
    pending = total - completed

    conn.close()

    return render_template("index.html",
                           tasks=tasks,
                           total=total,
                           completed=completed,
                           pending=pending)


# -----------------------
# ADD TASK
# -----------------------
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect(url_for("login"))

    task = request.form["task"]
    due_date = request.form.get("due_date")
    priority = request.form.get("priority")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
        INSERT INTO tasks (task, status, user_id, due_date, priority)
        VALUES (?, 0, ?, ?, ?)
    """, (task, session["user_id"], due_date, priority))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# -----------------------
# DELETE TASK
# -----------------------
@app.route("/delete/<int:task_id>")
def delete(task_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# -----------------------
# COMPLETE / TOGGLE TASK
# -----------------------
@app.route("/complete/<int:task_id>")
def complete(task_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
        UPDATE tasks
        SET status = CASE WHEN status = 0 THEN 1 ELSE 0 END
        WHERE id = ?
    """, (task_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# -----------------------
# EDIT TASK
# -----------------------
@app.route("/edit/<int:task_id>", methods=["POST"])
def edit(task_id):
    task = request.form["task"]
    due_date = request.form.get("due_date")
    priority = request.form.get("priority")

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("""
        UPDATE tasks
        SET task = ?, due_date = ?, priority = ?
        WHERE id = ?
    """, (task, due_date, priority, task_id))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))


# -----------------------
# REGISTER
# -----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists"

        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------
# LOGIN
# -----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


# -----------------------
# LOGOUT
# -----------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
