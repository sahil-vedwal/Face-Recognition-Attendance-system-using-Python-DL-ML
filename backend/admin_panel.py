from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import mysql.connector
import os

admin_bp = Blueprint('admin_bp', __name__)
UPLOAD_FOLDER = "static/photos"

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'abc'
}

# ---------- Admin Dashboard ----------
@admin_bp.route("/admin/dashboard", endpoint="admin_dashboard")
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student")
    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin.html", students=students)


# ---------- Register Student ----------
@admin_bp.route("/admin/register", methods=["GET", "POST"], endpoint="register_student")
def register_student():
    if 'admin' not in session:
        return redirect('/')

    if request.method == "POST":
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

            insert_query = """
                INSERT INTO student (
                    enrollment_number, student_name, email, department,
                    branch, year, section, photo,
                    parent_phone, password
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            data = (
                enrollment_number, student_name, email, department,
                branch, year, section, photo_filename,
                parent_phone, password
            )

            cursor.execute(insert_query, data)
            conn.commit()
            cursor.close()
            conn.close()

            flash("Student registered successfully!", "success")
            return redirect(url_for("admin_bp.register_student"))

        except Exception as e:
            print("Error:", e)
            flash("Something went wrong during registration.", "danger")

    return render_template("register_student.html")


# ---------- Update Student ----------
@admin_bp.route('/admin/update/<enrollment_number>', methods=['GET', 'POST'], endpoint='update_student')
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

            update_query = """
                UPDATE student
                SET student_name=%s, email=%s, department=%s,
                    branch=%s, year=%s, section=%s,
                    password=%s, parent_phone=%s
                WHERE enrollment_number=%s
            """
            cursor.execute(update_query, (
                student_name, email, department, branch,
                year, section, password, parent_phone,
                enrollment_number
            ))
            conn.commit()

            flash('Student details updated successfully!', 'success')
            return redirect(url_for('admin_bp.admin_dashboard'))

        except Exception as e:
            print("Update Error:", e)
            flash('Error updating student.', 'danger')

    cursor.execute("SELECT * FROM student WHERE enrollment_number = %s", (enrollment_number,))
    student = cursor.fetchone()

    cursor.close()
    conn.close()

    if student:
        return render_template('update_student.html', student=student)
    else:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin_bp.admin_dashboard'))


# ---------- Delete Student ----------
@admin_bp.route('/admin/delete/<enrollment_number>', methods=['GET'], endpoint='delete_student')
def delete_student(enrollment_number):
    if 'admin' not in session:
        return redirect('/')

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM student WHERE enrollment_number = %s", (enrollment_number,))
        conn.commit()

        # Also delete the student photo
        photo_path = os.path.join(UPLOAD_FOLDER, f"{enrollment_number}.jpg")
        if os.path.exists(photo_path):
            os.remove(photo_path)

        cursor.close()
        conn.close()

        flash("Student deleted successfully!", "success")
    except Exception as e:
        print("Delete Error:", e)
        flash("Error deleting student.", "danger")

    return redirect(url_for('admin_bp.admin_dashboard'))


# ---------- Search Students ----------
@admin_bp.route('/admin/search')
def admin_search():
    if 'admin' not in session:
        return redirect('/')

    query = request.args.get('query')
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM student 
        WHERE student_name LIKE %s OR enrollment_number LIKE %s OR department LIKE %s
    """, (f"%{query}%", f"%{query}%", f"%{query}%"))

    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin.html', students=students)


# ---------- All Attendance ----------
@admin_bp.route('/admin/attendance', methods=['GET'], endpoint='admin_attendance_all')
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


# ---------- Attendance for Specific Student ----------
@admin_bp.route('/admin/attendance/<enrollment_number>', methods=['GET'], endpoint='admin_attendance_student')
def admin_attendance_student(enrollment_number):
    if 'admin' not in session:
        return redirect('/')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Fetch student info
    cursor.execute("SELECT * FROM student WHERE enrollment_number = %s", (enrollment_number,))
    student = cursor.fetchone()

    # Fetch attendance
    cursor.execute("""
        SELECT * FROM attendance 
        WHERE enrollment_number = %s 
        ORDER BY date DESC
    """, (enrollment_number,))
    attendance_records = cursor.fetchall()

    cursor.close()
    conn.close()

    if student:
       return render_template("admin_attendance.html", student=student, records=attendance_records)
    else:
        flash("Student not found.", "danger")
        return redirect(url_for('admin_bp.admin_dashboard'))
