from flask import Blueprint, render_template, session, redirect, flash
from database.db_setup import create_connection

student_dashboard_bp = Blueprint('student_dashboard', __name__)

@student_dashboard_bp.route("/student/dashboard")
def student_dashboard():
    if "enrollment_number" not in session:
        return redirect("/")

    enrollment = session["enrollment_number"]
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM student WHERE enrollment_number = %s", (enrollment,))
    student = cursor.fetchone()

    if student is None:
        flash("Student not found!")
        return redirect("/")

    cursor.execute("SELECT * FROM attendance WHERE enrollment_number = %s ORDER BY date DESC", (enrollment,))
    attendance = cursor.fetchall()

    cursor.close()
    conn.close()

    # Set photo filename with fallback
    if student.get("enrollment_number"):
        student["photo"] = f"{student['enrollment_number']}.jpg"
    else:
        student["photo"] = "default.jpg"

    return render_template('student.html', student=student, attendance=attendance)
