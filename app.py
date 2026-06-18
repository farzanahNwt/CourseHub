from flask import Flask, render_template, request, redirect, session, url_for, flash, Response
import xmlrpc.client
import mysql.connector
import hashlib
from datetime import datetime
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = 'dcrs_secure_secret_key_2024_ultra_secure'

# RPC Server Configuration
RPC_SERVER_URL = "http://localhost:8000/"

# Database Configuration
db_config = {
    'user': 'root',
    'password': '123456789',
    'host': '127.0.0.1',
    'database': 'coursehub_database'
}




def get_db_connection():
    return mysql.connector.connect(**db_config)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def safe_int(value):
    """Convert any value to int safely"""
    try:
        return int(value) if value is not None and value != '' else 0
    except (ValueError, TypeError):
        return 0

def safe_str(value):
    """Convert any value to string safely"""
    return str(value) if value is not None else ''

# ---------- RPC Proxy ----------
def get_rpc_proxy():
    try:
        return xmlrpc.client.ServerProxy(RPC_SERVER_URL, allow_none=True)
    except Exception as e:
        print(f"⚠️ RPC Connection Error: {e}")
        return None

# ---------- 1. Login ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Admin Login (Hardcoded)
        if username == 'admin' and password == 'admin123':
            session['user'] = 'admin'
            session['role'] = 'admin'
            session['name'] = 'System Administrator'
            session['id'] = 'admin'
            flash('Welcome back, Commander.', 'success')
            return redirect(url_for('admin_dashboard'))

        # Student Login (Database)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE username = %s AND password = %s", (username, password))
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        if student:
            session['user'] = student['username']
            session['id'] = student['student_id']
            session['role'] = 'student'
            session['name'] = student['name']
            flash(f'Welcome back, {student["name"]}!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')

# ---------- 2. Student Dashboard ----------
@app.route('/student')
def student_dashboard():

    if 'user' not in session or session.get('role') != 'student':
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))

    student_id = session['id']

    # Get data from RPC
    rpc = get_rpc_proxy()
    if rpc:
        try:
            all_courses = rpc.get_courses()
            # Ensure all numeric fields are ints
            for c in all_courses:
                if 'available_seats' in c:
                    c['available_seats'] = safe_int(c['available_seats'])
                if 'credits' in c:
                    c['credits'] = safe_int(c['credits'])

            my_courses = rpc.get_student_courses(student_id)
            for c in my_courses:
                if 'available_seats' in c:
                    c['available_seats'] = safe_int(c['available_seats'])
                if 'credits' in c:
                    c['credits'] = safe_int(c['credits'])
        except Exception as e:
            flash(f'RPC Error: {e}', 'danger')
            all_courses = []
            my_courses = []
    else:
        all_courses = []
        my_courses = []

    # Get profile data
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name, email FROM students WHERE student_id = %s", (student_id,))
    profile = cursor.fetchone()
    cursor.close()
    conn.close()

    # Calculate total hours safely
    total_hours = sum(safe_int(c.get('credits', 0)) for c in my_courses)

    max_credits = 21
    remaining_credits = max_credits - total_hours

    credit_warning = None

    if total_hours > max_credits:
        credit_warning = "Credit limit exceeded (Max 21 credits hour)"


    return render_template('student.html',
                           name=profile['name'] if profile else session['user'],
                           email=profile['email'] if profile else 'student@univ.edu',
                           courses=all_courses,
                           my_courses=my_courses,
                           total_hours=total_hours,
                           max_credits = max_credits,
                           remaining_credits = remaining_credits,
                           credit_warning = credit_warning)

# ---------- 3. Register Course ----------
@app.route('/register/<int:course_id>')
def register_course(course_id):
    if 'user' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))

    rpc = get_rpc_proxy()
    if rpc:
        try:
            result = rpc.register_course(session['id'], course_id)
            if result == "SUCCESS":
                flash(' Course enrolled successfully!', 'success')
            elif result == "FULL":
                flash('❌ No seats available for this course.', 'danger')
            elif result == "ALREADY":
                flash('⚠️ You are already enrolled in this course.', 'warning')
            else:
                flash(f'❌ Enrollment failed: {result}', 'danger')
        except Exception as e:
            flash(f'❌ RPC Error: {e}', 'danger')
    else:
        flash('❌ RPC Server unreachable.', 'danger')

    return redirect(url_for('student_dashboard'))

# ---------- 4. Drop Course ----------
@app.route('/drop/<int:course_id>')
def drop_course(course_id):
    if 'user' not in session:
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))

    rpc = get_rpc_proxy()
    if rpc:
        try:
            result = rpc.drop_course(session['id'], course_id)
            if result == "DROPPED":
                flash(' Course withdrawn successfully!', 'success')
            else:
                flash(f'⚠️ {result}', 'warning')
        except Exception as e:
            flash(f'❌ RPC Error: {e}', 'danger')
    else:
        flash('❌ RPC Server unreachable.', 'danger')

    return redirect(url_for('student_dashboard'))

# ---------- 5. Admin Dashboard ----------
@app.route('/admin')
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    rpc = get_rpc_proxy()
    if rpc:
        try:
            all_courses = rpc.get_courses()
            # Ensure all numeric fields are ints
            for c in all_courses:
                if 'available_seats' in c:
                    c['available_seats'] = safe_int(c['available_seats'])
                if 'credits' in c:
                    c['credits'] = safe_int(c['credits'])

            registrations = rpc.get_course_registrations()
            for r in registrations:
                for key in r:
                    r[key] = safe_str(r[key])
        except Exception as e:
            flash(f'RPC Error: {e}', 'danger')
            all_courses = []
            registrations = []
    else:
        all_courses = []
        registrations = []

    return render_template('admin.html', courses=all_courses, registrations=registrations)

# ---------- 6. Admin Add Course ----------
@app.route('/admin/add', methods=['POST'])
def admin_add_course():
    if 'user' not in session or session.get('role') != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    code = request.form['code']
    title = request.form['title']
    seats = safe_int(request.form['seats'])
    day = request.form['day']
    start = request.form['start']
    end = request.form['end']
    venue = request.form['venue']
    hours = safe_int(request.form['hours'])

    print(f" Adding course: {code}, {title}, {seats}, {day}, {start}, {end}, {venue}, {hours}")

    rpc = get_rpc_proxy()
    if rpc:
        try:
            result = rpc.add_course(code, title, seats, day, start, end, venue, hours)
            print(f" RPC Result: {result}")
            flash(f' Course {code} added successfully!', 'success')
        except Exception as e:
            print(f"❌ RPC Error: {e}")
            flash(f'❌ RPC Error: {e}', 'danger')
    else:
        flash('❌ RPC Server unreachable.', 'danger')

    return redirect(url_for('admin_dashboard'))

# ---------- 7. Admin Delete Course ----------
@app.route('/admin/delete/<int:course_id>')
def admin_delete_course(course_id):
    if 'user' not in session or session.get('role') != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    rpc = get_rpc_proxy()
    if rpc:
        try:
            rpc.delete_course(course_id)
            flash(' Course deleted successfully.', 'success')
        except Exception as e:
            flash(f'❌ RPC Error: {e}', 'danger')
    else:
        flash('❌ RPC Server unreachable.', 'danger')

    return redirect(url_for('admin_dashboard'))

# ---------- 8. Student Report ----------
@app.route('/student/report')
def student_report():
    if 'user' not in session or session.get('role') != 'student':
        flash('Please login first.', 'warning')
        return redirect(url_for('login'))

    student_id = session['id']

    # Get student info
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT student_id, name, username, email FROM students WHERE student_id = %s", (student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    # Get registered courses
    rpc = get_rpc_proxy()
    if rpc:
        try:
            my_courses = rpc.get_student_courses(student_id)
            for c in my_courses:
                c['credits'] = safe_int(c.get('credits', 0))
        except Exception as e:
            flash(f'RPC Error: {e}', 'danger')
            my_courses = []
    else:
        my_courses = []

    total_credits = sum(c.get('credits', 0) for c in my_courses)
    total_courses = len(my_courses)
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Export CSV
    if request.args.get('format') == 'csv':
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Course Code', 'Course Name', 'Credits', 'Day', 'Time', 'Status'])
        for c in my_courses:
            writer.writerow([
                c.get('course_code', ''),
                c.get('module_title', ''),
                c.get('credits', 0),
                c.get('day', ''),
                f"{c.get('start_time', '')} - {c.get('end_time', '')}",
                'Confirmed'
            ])
        output = si.getvalue()
        return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=registration_report.csv'})

    return render_template('student_report.html',
                           student=student,
                           courses=my_courses,
                           total_credits=total_credits,
                           total_courses=total_courses,
                           registration_date=registration_date)

# ---------- 9. Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)