import os
import cv2
import mysql.connector

def save_student_photo(enrollment_number):
    cap = cv2.VideoCapture(0)
    print("[INFO] Capturing photo... Press 's' to save.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Capture Photo", frame)

        key = cv2.waitKey(1)
        if key == ord('s'):
            # Save photo
            folder = 'static/photos'
            os.makedirs(folder, exist_ok=True)

            filename = f"{enrollment_number}.jpg"
            photo_path = os.path.join(folder, filename)
            cv2.imwrite(photo_path, frame)

            print(f"[INFO] Photo saved at: {photo_path}")
            break

    cap.release()
    cv2.destroyAllWindows()

    # Return path to save in DB (relative to 'static/')
    return f"photos/{enrollment_number}.jpg"

def register_student():
    # Step 1: Input details
    enrollment_number = input("Enrollment Number: ")
    student_name = input("Student Name: ")
    email = input("Email: ")
    parent_email = input("Parent Email: ")
    department = input("Department: ")
    branch = input("Branch: ")
    year = input("Year: ")
    section = input("Section: ")

    # Step 2: Capture photo and get path
    photo_path = f"photos/{enrollment_number}.jpg"


    # Step 3: Store in MySQL
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Put your XAMPP password if any
            database="abc"
        )
        cursor = conn.cursor()

        query = """
            INSERT INTO student (
                enrollment_number, student_name, email, parent_email,
                department, branch, year, section, photo_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            enrollment_number, student_name, email, parent_email,
            department, branch, year, section, photo_path
        )

        cursor.execute(query, values)
        conn.commit()

        print("[SUCCESS] Student registered successfully!")

    except mysql.connector.Error as err:
        print("Error:", err)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    register_student()
