from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
from datetime import datetime

# --- Initialize Flask app ---
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random key

# --- Register Blueprint (after app init) ---
from backend.admin_panel import admin_bp
app.register_blueprint(admin_bp)

# --- MySQL Database Connection ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="abc"  # Change if your database name is different
)
cursor = db.cursor(dictionary=True)

# ------------------- ROUTES -------------------

# ---------- Home/Login ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['email']
        password = request.form['password']

        if role == 'admin':
            cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
            admin = cursor.fetchone()
            if admin:
                session['admin'] = admin['id']
                return redirect('/admin')
            else:
                error = "Invalid admin credentials."

        elif role == 'student':
            cursor.execute("SELECT * FROM student WHERE student_name=%s AND enrollment_number=%s", (username, password))
            student = cursor.fetchone()
            if student:
                session['student'] = student['enrollment_number']
                return redirect('/student')
            else:
                error = "Invalid student credentials."

    return render_template('index.html', error=error)

# ---------- Student Dashboard ----------
@app.route('/student')
def student_dashboard():
    if 'student' not in session:
        return redirect('/')

    enrollment_number = session['student']
    cursor.execute("SELECT * FROM student WHERE enrollment_number = %s", (enrollment_number,))
    student = cursor.fetchone()

    cursor.execute("SELECT * FROM attendance WHERE enrollment_number = %s ORDER BY date DESC", (enrollment_number,))
    attendance = cursor.fetchall()

    return render_template('student.html', student=student, attendance=attendance)

# ---------- Admin Dashboard ----------
@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM student ORDER BY student_name")
    students = cursor.fetchall()

    return render_template('admin.html', students=students)

# ---------- Admin Search ----------
@app.route('/admin/search')
def admin_search():
    if 'admin' not in session:
        return redirect('/')

    query = request.args.get('query')
    cursor.execute("""
        SELECT * FROM student 
        WHERE student_name LIKE %s OR 
              enrollment_number LIKE %s OR 
              department LIKE %s
    """, (f'%{query}%', f'%{query}%', f'%{query}%'))
    students = cursor.fetchall()

    return render_template('admin.html', students=students)

# ---------- View Attendance for Specific Student ----------
@app.route('/admin/attendance/<enrollment>')
def view_student_attendance(enrollment):
    if 'admin' not in session:
        return redirect('/')

    cursor.execute("SELECT * FROM student WHERE enrollment_number = %s", (enrollment,))
    student = cursor.fetchone()

    cursor.execute("SELECT * FROM attendance WHERE enrollment_number = %s ORDER BY date DESC", (enrollment,))
    attendance = cursor.fetchall()

    return render_template('student.html', student=student, attendance=attendance)

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------- Run App ----------
if __name__ == '__main__':
    app.run(debug=True)
