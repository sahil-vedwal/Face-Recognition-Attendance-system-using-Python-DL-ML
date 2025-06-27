from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
import mysql.connector
import sys
import os

# Create Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # for sessions and flashing

# Add root directory to sys.path to import from parent folders
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'face_recognition')))

from face_recognition_system import gen_frames, stop_recognition
import cv2
import pickle
import face_recognition
import numpy as np
from datetime import datetime, date
from utils.email_notifications import send_sms_message



app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = "static/photos"

# -------------------- DATABASE CONFIG --------------------
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'abc'
}

# -------------------- ROUTES --------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def handle_login():
    role = request.form['role']
    email = request.form['email']
    password = request.form['password']

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if role == 'admin':
        if email == 'admin' and password == 'admin123':
            session['admin'] = True
            return redirect('/admin/dashboard')
        else:
            flash("Invalid admin credentials", "danger")

    elif role == 'student':
        cursor.execute("SELECT * FROM student WHERE student_name=%s AND password=%s", (email, password))
        student = cursor.fetchone()
        if student:
            session['student'] = student['enrollment_number']
            return redirect('/student/dashboard')
        else:
            flash("Invalid student credentials", "danger")

    cursor.close()
    conn.close()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------- FACE RECOGNITION --------------------
@app.route('/start_face_recognition')
def start_face_recognition():
    return render_template('face_recognition_live.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop-face-recognition')
def stop_face_recognition():
    try:
        stop_recognition()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# -------------------- STUDENT DASHBOARD --------------------
@app.route('/student/dashboard')
def student_dashboard():
    if 'student' not in session:
        return redirect('/')

    enrollment = session['student']
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student WHERE enrollment_number = %s", (enrollment,))
    student = cursor.fetchone()

    cursor.execute("""
        SELECT DATE(date) as date, TIME(entry_time) as entry_time, TIME(exit_time) as exit_time
        FROM attendance WHERE enrollment_number = %s ORDER BY date DESC
    """, (enrollment,))
    attendance = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('student.html', student=student, attendance=attendance)

# -------------------- ADMIN DASHBOARD --------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin.html', students=students)

@app.route('/admin/search')
def admin_search():
    if 'admin' not in session:
        return redirect('/')

    query = request.args.get('query', '')
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM student 
        WHERE student_name LIKE %s OR enrollment_number LIKE %s
    """, (f"%{query}%", f"%{query}%"))
    students = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('admin.html', students=students)

@app.route('/admin/attendance')
def admin_attendance():
    if 'admin' not in session:
        return redirect('/')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM attendance ORDER BY date DESC")
    attendance_data = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_attendance.html', attendance=attendance_data)

@app.route('/admin/attendance/<enrollment_number>')
def admin_view_student_attendance(enrollment_number):
    if 'admin' not in session:
        return redirect('/')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student WHERE enrollment_number = %s", (enrollment_number,))
    student = cursor.fetchone()

    cursor.execute("""
        SELECT DATE(date) as date, TIME(entry_time) as entry_time, TIME(exit_time) as exit_time
        FROM attendance WHERE enrollment_number = %s ORDER BY date DESC
    """, (enrollment_number,))
    attendance = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('student.html', student=student, attendance=attendance)

# -------------------- REGISTER STUDENT --------------------
@app.route('/admin/register', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        try:
            enrollment_number = request.form["enrollment_number"]
            student_name = request.form["student_name"]
            email = request.form["email"]
            department = request.form["department"]
            branch = request.form["branch"]
            year = request.form["year"]
            section = request.form["section"]
            parent_phone = request.form["parent_phone"]
            password = request.form["password"]

            photo = request.files["photo"]
            photo_filename = f"{enrollment_number}.jpg"
            photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)
            photo.save(photo_path)

            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO student (
                    enrollment_number, student_name, email, department,
                    branch, year, section, photo, parent_phone, password
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (enrollment_number, student_name, email, department,
                  branch, year, section, photo_filename, parent_phone, password))
            conn.commit()
            cursor.close()
            conn.close()

            flash("Student registered successfully!", "success")
            return redirect(url_for("register_student"))
        except Exception as e:
            print("Error:", e)
            flash("Something went wrong during registration.", "danger")

    return render_template("register_student.html")

# -------------------- UPDATE STUDENT --------------------
@app.route('/admin/update/<enrollment_number>', methods=['GET', 'POST'])
def update_student(enrollment_number):
    if 'admin' not in session:
        return redirect('/')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            student_name = request.form['student_name']
            email = request.form['email']
            department = request.form['department']
            branch = request.form['branch']
            year = request.form['year']
            section = request.form['section']
            password = request.form['password']
            parent_phone = request.form['parent_phone']

            cursor.execute("""
                UPDATE student SET student_name=%s, email=%s, department=%s,
                branch=%s, year=%s, section=%s, password=%s, parent_phone=%s
                WHERE enrollment_number=%s
            """, (student_name, email, department, branch, year, section, password, parent_phone, enrollment_number))
            conn.commit()
            flash("Student updated successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            print("Update Error:", e)
            flash("Error updating student.", "danger")

    cursor.execute("SELECT * FROM student WHERE enrollment_number = %s", (enrollment_number,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('update_student.html', student=student)

# -------------------- DELETE STUDENT --------------------
@app.route('/admin/delete/<enrollment_number>')
def delete_student(enrollment_number):
    if 'admin' not in session:
        return redirect('/')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student WHERE enrollment_number = %s", (enrollment_number,))
        conn.commit()

        photo_path = os.path.join(UPLOAD_FOLDER, f"{enrollment_number}.jpg")
        if os.path.exists(photo_path):
            os.remove(photo_path)

        cursor.close()
        conn.close()
        flash("Student deleted successfully!", "success")
    except Exception as e:
        print("Delete Error:", e)
        flash("Error deleting student.", "danger")

    return redirect(url_for('admin_dashboard'))

# -------------------- MAIN --------------------
if __name__ == '__main__':
    app.run(debug=True)
