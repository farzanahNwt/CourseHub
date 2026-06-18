from xmlrpc.server import SimpleXMLRPCServer
import mysql.connector

server = SimpleXMLRPCServer(("0.0.0.0", 8000), allow_none=True)
print("🌌 DCRS RPC Server initialized on port 8000...")
print("📡 Waiting for incoming requests...\n")

# ---------- Database Connection ----------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="coursehub_database"
    )

# ---------- Safe Converter ----------
def safe(row):
    if not row:
        return {}
    clean = {}
    for k, v in row.items():
        clean[k] = str(v) if v is not None else ""
    return clean

# ---------- 1. Get All Courses ----------
def get_courses():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
                SELECT course_id, course_code, module_title, credits, day, start_time, end_time, venue, available_seats
                FROM courses
                ORDER BY course_code
                """)
    data = [safe(row) for row in cur.fetchall()]
    cur.close()
    db.close()

    print(f"📊 get_courses() returned {len(data)} courses")
    return data

# ---------- 2. Get Student Courses ----------
def get_student_courses(student_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
                SELECT c.course_id, c.course_code, c.module_title, c.credits, c.day, c.start_time, c.end_time, c.venue, c.available_seats
                FROM courses c
                         JOIN registrations r ON c.course_id = r.course_id
                WHERE r.student_id = %s
                """, (student_id,))
    data = [safe(row) for row in cur.fetchall()]
    cur.close()
    db.close()
    return data

# ---------- 3. Register Course ----------
def register_course(student_id, course_id):
    db = get_db()
    cur = db.cursor()

    # Check if course exists and has seats
    cur.execute("SELECT available_seats FROM courses WHERE course_id = %s", (course_id,))
    seat = cur.fetchone()
    if not seat or seat[0] <= 0:
        cur.close()
        db.close()
        return "FULL"

    # Check if already registered
    cur.execute("SELECT * FROM registrations WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    if cur.fetchone():
        cur.close()
        db.close()
        return "ALREADY"

    # Register and decrease seats
    cur.execute("UPDATE courses SET available_seats = available_seats - 1 WHERE course_id = %s", (course_id,))
    cur.execute("INSERT INTO registrations(student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
    db.commit()
    cur.close()
    db.close()
    return "SUCCESS"

# ---------- 4. Drop Course ----------
def drop_course(student_id, course_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("DELETE FROM registrations WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    cur.execute("UPDATE courses SET available_seats = available_seats + 1 WHERE course_id = %s", (course_id,))
    db.commit()
    cur.close()
    db.close()
    return "DROPPED"

# ---------- 5. Admin: Add Course ----------
def add_course(code, title, seats, day, start, end, venue, hours):
    db = get_db()
    cur = db.cursor()
    cur.execute("""
                INSERT INTO courses(course_code, module_title, available_seats, day, start_time, end_time, venue, credits)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (code, title, seats, day, start, end, venue, hours))
    db.commit()
    cur.close()
    db.close()

    print(f"✅ Course {code} added to database!")
    return "ADDED"

# ---------- 6. Admin: Delete Course ----------
def delete_course(course_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM registrations WHERE course_id = %s", (course_id,))
    cur.execute("DELETE FROM courses WHERE course_id = %s", (course_id,))
    db.commit()
    cur.close()
    db.close()
    return "DELETED"

# ---------- 7. Admin: Get All Students ----------
def get_students():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT student_id, name, username, email FROM students")
    data = [safe(r) for r in cur.fetchall()]
    cur.close()
    db.close()
    return data

# ---------- 8. Admin: Get Registrations ----------
def get_course_registrations():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
                SELECT c.course_code, c.module_title, s.name as student_name, s.username
                FROM registrations r
                         JOIN courses c ON r.course_id = c.course_id
                         JOIN students s ON r.student_id = s.student_id
                ORDER BY c.course_code
                """)
    data = [safe(row) for row in cur.fetchall()]
    cur.close()
    db.close()
    return data

# ---------- 9. Get Course Stats ----------
def get_course_stats():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
                SELECT
                    c.course_code,
                    c.module_title,
                    c.available_seats,
                    COUNT(r.student_id) as registered_count,
                    c.available_seats - COUNT(r.student_id) as seats_remaining
                FROM courses c
                         LEFT JOIN registrations r ON c.course_id = r.course_id
                GROUP BY c.course_id
                """)
    data = [safe(row) for row in cur.fetchall()]
    cur.close()
    db.close()
    return data

# ---------- 10. Get Student Registrations ----------
def get_student_registrations(student_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
                SELECT c.course_code, c.module_title, c.day, c.start_time, c.end_time, c.venue
                FROM registrations r
                         JOIN courses c ON r.course_id = c.course_id
                WHERE r.student_id = %s
                """, (student_id,))
    data = [safe(row) for row in cur.fetchall()]
    cur.close()
    db.close()
    return data

# ---------- Register All Functions ----------
server.register_function(get_courses)
server.register_function(get_student_courses)
server.register_function(register_course)
server.register_function(drop_course)
server.register_function(add_course)
server.register_function(delete_course)
server.register_function(get_students)
server.register_function(get_course_registrations)
server.register_function(get_course_stats)
server.register_function(get_student_registrations)

print("✅ All RPC functions registered successfully!")
print("📋 Available functions:")
print("   - get_courses()")
print("   - get_student_courses(student_id)")
print("   - register_course(student_id, course_id)")
print("   - drop_course(student_id, course_id)")
print("   - add_course(code, title, seats, day, start, end, venue, hours)")
print("   - delete_course(course_id)")
print("   - get_students()")
print("   - get_course_registrations()")
print("   - get_course_stats()")
print("   - get_student_registrations(student_id)")
print("\n🚀 Server is ready and listening...")

server.serve_forever()