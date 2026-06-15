from xmlrpc.server import SimpleXMLRPCServer
from database import get_connection

HOST = "127.0.0.1"
PORT = 8000
MAX_CREDITS = 21


def get_courses():
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            course_id,
            course_code,
            course_title,
            available_seats,
            credits,
            lecturer,
            day,
            TIME_FORMAT(start_time, '%H:%i') AS start_time,
            TIME_FORMAT(end_time, '%H:%i') AS end_time,
            venue
        FROM courses
        ORDER BY course_code
    """)

    courses = cursor.fetchall()

    cursor.close()
    db.close()

    return courses


def get_student_courses(student_id):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            c.course_id,
            c.course_code,
            c.course_title,
            c.available_seats,
            c.credits,
            c.lecturer,
            c.day,
            TIME_FORMAT(c.start_time, '%H:%i') AS start_time,
            TIME_FORMAT(c.end_time, '%H:%i') AS end_time,
            c.venue,
            DATE_FORMAT(r.registration_date, '%Y-%m-%d %H:%i') AS registration_date
        FROM registrations r
        JOIN courses c ON r.course_id = c.course_id
        WHERE r.student_id = %s
        ORDER BY c.day, c.start_time
    """, (student_id,))

    courses = cursor.fetchall()

    cursor.close()
    db.close()

    return courses


def get_total_credits(student_id):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT COALESCE(SUM(c.credits), 0) AS total_credits
        FROM registrations r
        JOIN courses c ON r.course_id = c.course_id
        WHERE r.student_id = %s
    """, (student_id,))

    result = cursor.fetchone()
    total = result["total_credits"]

    cursor.close()
    db.close()

    return total


def register_course(student_id, course_id):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    try:
        db.start_transaction()

        cursor.execute("""
            SELECT 
                course_id,
                course_code,
                course_title,
                available_seats,
                credits,
                lecturer,
                day,
                start_time,
                end_time,
                venue
            FROM courses
            WHERE course_id = %s
            FOR UPDATE
        """, (course_id,))

        new_course = cursor.fetchone()

        if not new_course:
            db.rollback()
            return "Course not found"

        if new_course["available_seats"] <= 0:
            db.rollback()
            return "Course is full"

        cursor.execute("""
            SELECT * 
            FROM registrations 
            WHERE student_id = %s AND course_id = %s
        """, (student_id, course_id))

        if cursor.fetchone():
            db.rollback()
            return "You already registered this course"

        cursor.execute("""
            SELECT COALESCE(SUM(c.credits), 0) AS total_credits
            FROM registrations r
            JOIN courses c ON r.course_id = c.course_id
            WHERE r.student_id = %s
        """, (student_id,))

        current_credits = cursor.fetchone()["total_credits"]

        if current_credits + new_course["credits"] > MAX_CREDITS:
            db.rollback()
            return f"Credit limit exceeded. Maximum credit allowed is {MAX_CREDITS}"

        cursor.execute("""
            SELECT 
                c.course_code,
                c.course_title,
                c.day,
                c.start_time,
                c.end_time
            FROM registrations r
            JOIN courses c ON r.course_id = c.course_id
            WHERE r.student_id = %s
        """, (student_id,))

        registered_courses = cursor.fetchall()

        for registered in registered_courses:
            same_day = registered["day"] == new_course["day"]

            time_overlap = (
                new_course["start_time"] < registered["end_time"]
                and new_course["end_time"] > registered["start_time"]
            )

            if same_day and time_overlap:
                db.rollback()
                return (
                    "Timetable clash detected with "
                    + registered["course_code"]
                    + " - "
                    + registered["course_title"]
                )

        cursor.execute("""
            INSERT INTO registrations (student_id, course_id)
            VALUES (%s, %s)
        """, (student_id, course_id))

        cursor.execute("""
            UPDATE courses
            SET available_seats = available_seats - 1
            WHERE course_id = %s
        """, (course_id,))

        db.commit()
        return "Course registered successfully"

    except Exception as e:
        db.rollback()
        return str(e)

    finally:
        cursor.close()
        db.close()


def drop_course(student_id, course_id):
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    try:
        db.start_transaction()

        cursor.execute("""
            SELECT * 
            FROM registrations 
            WHERE student_id = %s AND course_id = %s
        """, (student_id, course_id))

        registration = cursor.fetchone()

        if not registration:
            db.rollback()
            return "You are not registered for this course"

        cursor.execute("""
            DELETE FROM registrations 
            WHERE student_id = %s AND course_id = %s
        """, (student_id, course_id))

        cursor.execute("""
            UPDATE courses 
            SET available_seats = available_seats + 1 
            WHERE course_id = %s
        """, (course_id,))

        db.commit()
        return "Course dropped successfully"

    except Exception as e:
        db.rollback()
        return str(e)

    finally:
        cursor.close()
        db.close()


server = SimpleXMLRPCServer((HOST, PORT), allow_none=True)

server.register_function(get_courses, "get_courses")
server.register_function(register_course, "register_course")
server.register_function(get_student_courses, "get_student_courses")
server.register_function(drop_course, "drop_course")
server.register_function(get_total_credits, "get_total_credits")

print(f"RPC server running on http://{HOST}:{PORT}")
server.serve_forever()