from flask import Flask, render_template, request, redirect, session, url_for, flash
import xmlrpc.client
import mysql.connector
import hashlib

app = Flask(__name__)
app.secret_key = 'dcrs_secure_secret_key_2024_ultra_secure'

# RPC Server Configuration
RPC_SERVER_URL = "http://localhost:8000/"

# Database Configuration
db_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'coursehub_database',
    'port': 3307

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
    global credit_warning
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
                if 'credit_hours' in c:
                    c['credit_hours'] = safe_int(c['credit_hours'])

            my_courses = rpc.get_student_courses(student_id)
            for c in my_courses:
                if 'available_seats' in c:
                    c['available_seats'] = safe_int(c['available_seats'])
                if 'credit_hours' in c:
                    c['credit_hours'] = safe_int(c['credit_hours'])
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
    total_hours = sum(safe_int(c.get('credit_hours', 0)) for c in my_courses)

    max_credits = 21
    remaining_credits = max_credits - total_hours
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
                flash('✅ Course registered successfully!', 'success')
            elif result == "FULL":
                flash('❌ No seats available for this course.', 'danger')
            elif result == "ALREADY":
                flash('⚠️ You are already registered for this course.', 'warning')
            else:
                flash(f'❌ Registration failed: {result}', 'danger')
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
                flash('✅ Course dropped successfully!', 'success')
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
                if 'credit_hours' in c:
                    c['credit_hours'] = safe_int(c['credit_hours'])

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

    rpc = get_rpc_proxy()
    if rpc:
        try:
            rpc.add_course(code, title, seats, day, start, end, venue, hours)
            flash(f'✅ Course {code} deployed successfully!', 'success')
        except Exception as e:
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
            flash('✅ Course purged successfully.', 'success')
        except Exception as e:
            flash(f'❌ RPC Error: {e}', 'danger')
    else:
        flash('❌ RPC Server unreachable.', 'danger')

    return redirect(url_for('admin_dashboard'))

# ---------- 8. Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been disconnected.', 'info')
    return redirect(url_for('login'))

# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)