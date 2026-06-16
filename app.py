from flask import Flask, render_template, request, redirect, session, flash
import xmlrpc.client
from database import get_connection

app = Flask(__name__)
app.secret_key = "coursehub_secret_key"

rpc_server = xmlrpc.client.ServerProxy("http://192.168.56.1:8000/", allow_none=True)


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM students WHERE username=%s AND password=%s",
            (username, password)
        )
        student = cursor.fetchone()

        cursor.close()
        db.close()

        if student:
            session["student_id"] = student["student_id"]
            session["name"] = student["name"]
            session["email"] = student["email"]
            return redirect("/dashboard")
        else:
            flash("Invalid username or password")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "student_id" not in session:
        return redirect("/")

    courses = rpc_server.get_courses()
    my_courses = rpc_server.get_student_courses(session["student_id"])

    return render_template(
        "dashboard.html",
        page="dashboard",
        courses=courses,
        my_courses=my_courses
    )


@app.route("/browse")
def browse():
    if "student_id" not in session:
        return redirect("/")

    courses = rpc_server.get_courses()
    return render_template("dashboard.html", page="browse", courses=courses, my_courses=[])


@app.route("/registrations")
def registrations():
    if "student_id" not in session:
        return redirect("/")

    my_courses = rpc_server.get_student_courses(session["student_id"])
    return render_template("dashboard.html", page="registrations", courses=[], my_courses=my_courses)


@app.route("/schedule")
def schedule():
    if "student_id" not in session:
        return redirect("/")

    my_courses = rpc_server.get_student_courses(session["student_id"])
    return render_template("dashboard.html", page="schedule", courses=[], my_courses=my_courses)


@app.route("/notifications")
def notifications():
    if "student_id" not in session:
        return redirect("/")

    return render_template("dashboard.html", page="notifications", courses=[], my_courses=[])


@app.route("/profile")
def profile():
    if "student_id" not in session:
        return redirect("/")

    return render_template("dashboard.html", page="profile", courses=[], my_courses=[])


@app.route("/register/<int:course_id>")
def register(course_id):
    if "student_id" not in session:
        return redirect("/")

    message = rpc_server.register_course(session["student_id"], course_id)
    flash(message)
    return redirect("/browse")


@app.route("/drop/<int:course_id>")
def drop(course_id):
    if "student_id" not in session:
        return redirect("/")

    message = rpc_server.drop_course(session["student_id"], course_id)
    flash(message)
    return redirect("/registrations")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=5000)