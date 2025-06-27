import os
import cv2
import pickle
import face_recognition
import numpy as np
from datetime import datetime, date
import mysql.connector
from utils.email_notifications import send_sms_message  # ✅ SMS only, no email

ENCODINGS_FILE = "face_recognition/face_encodings.pkl"
if not os.path.exists(ENCODINGS_FILE):
    print("❌ Please run encode_faces.py to generate face encodings.")
    exit()

with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)

known_encodings = data["encodings"]
known_names = data["ids"]

marked_today = set()
recent_faces = {}
video = None
running = True  # flag to stop from Flask

def mark_attendance(enrollment_number):
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='abc'
    )
    cursor = connection.cursor()

    cursor.execute("SELECT student_name, parent_phone FROM student WHERE enrollment_number = %s", (enrollment_number,))
    result = cursor.fetchone()

    if not result:
        print(f"❌ Student not found for enrollment: {enrollment_number}")
        return

    student_name, parent_phone = result

    today = date.today().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM attendance WHERE enrollment_number = %s AND date = %s", (enrollment_number, today))
 
    already_marked = cursor.fetchone()

    if not already_marked:
        now = datetime.now()
        entry_time = now.strftime("%H:%M:%S")
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO attendance (enrollment_number, date, entry_time, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (enrollment_number, today, entry_time, timestamp))
        connection.commit()

        print(f"✅ Attendance marked for {student_name} ({enrollment_number}) at {entry_time}")

        try:
            send_sms_message(parent_phone, student_name, entry_time, today)
        except Exception as e:
            print(f"⚠ SMS failed to send: {e}")
    else:
        print(f"ℹ Attendance already marked today for: {student_name}")

    cursor.close()
    connection.close()

def is_fake_image(face_region):
    if face_region.size == 0:
        return True
    brightness = np.mean(face_region)
    return brightness > 210

def gen_frames():
    global video, running, marked_today, recent_faces
    video = cv2.VideoCapture(0)
    marked_today = set()
    recent_faces = {}
    running = True

    while running:
        success, frame = video.read()
        if not success:
            break

        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        for encoding, location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, encoding)
            face_distances = face_recognition.face_distance(known_encodings, encoding)

            if len(face_distances) == 0:
                continue

            best_match = np.argmin(face_distances)
            name = "Unknown"
            top, right, bottom, left = [v * 4 for v in location]
            face_region = frame[top:bottom, left:right]

            if is_fake_image(face_region):
                cv2.putText(frame, "Fake/Screen Detected", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                continue

            if matches[best_match]:
                name = known_names[best_match]
                if name not in marked_today:
                    mark_attendance(name)
                    marked_today.add(name)
                    recent_faces[name] = {
                        "image": cv2.resize(face_region, (60, 60)),
                        "timestamp": datetime.now()
                    }
            overlay = frame.copy()
            alpha = 0.4
            # Semi-transparent green overlay
            cv2.rectangle(overlay, (left, top), (right, bottom), (0, 255, 0), -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
             
             # Scan lines inside face box
            for i in range(top, bottom, 10):
             cv2.line(frame, (left, i), (right, i), (0, 255, 0), 1)

       ### # Futuristic corner lines
            corner_len = 20
            cv2.line(frame, (left, top), (left + corner_len, top), (0, 255, 0), 2)
            cv2.line(frame, (left, top), (left, top + corner_len), (0, 255, 0), 2)

            cv2.line(frame, (right, top), (right - corner_len, top), (0, 255, 0), 2)
            cv2.line(frame, (right, top), (right, top + corner_len), (0, 255, 0), 2)

            cv2.line(frame, (left, bottom), (left + corner_len, bottom), (0, 255, 0), 2)
            cv2.line(frame, (left, bottom), (left, bottom - corner_len), (0, 255, 0), 2)

            cv2.line(frame, (right, bottom), (right - corner_len, bottom), (0, 255, 0), 2)
            cv2.line(frame, (right, bottom), (right, bottom - corner_len), (0, 255, 0), 2)

            # Name tag in cool font
            cv2.putText(frame, name, (left, top - 15), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 255), 2)
             
        y_offset = 10
        for person, data in list(recent_faces.items()):
            if (datetime.now() - data["timestamp"]).total_seconds() > 3:
                del recent_faces[person]
                continue
            frame[10:70, y_offset:y_offset + 60] = data["image"]
            cv2.putText(frame, person, (y_offset, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 70

        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 2)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    video.release()
    cv2.destroyAllWindows()

def stop_recognition():
    global running
    running = False
