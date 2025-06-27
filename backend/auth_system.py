from database.config import get_connection

def authenticate_student(enrollment, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM student WHERE enrollment_number=%s AND password=%s", (enrollment, password))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    return student

def authenticate_admin(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()
    return admin
    session["enrollment_number"] = student_enrollment
