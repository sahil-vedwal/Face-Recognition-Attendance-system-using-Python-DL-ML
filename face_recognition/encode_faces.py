import os
import cv2
import face_recognition
import pickle

# ✅ Path to the student photos folder (after registration)
IMAGE_DIR = "static/photos"

# ✅ Path to save the face encodings
ENCODINGS_PATH = "face_recognition/face_encodings.pkl"

known_encodings = []
known_ids = []

for filename in os.listdir(IMAGE_DIR):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        path = os.path.join(IMAGE_DIR, filename)
        img = cv2.imread(path)
        if img is None:
            print(f"⚠️ Failed to load {filename}")
            continue

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)

        if len(boxes) == 0:
            print(f"⚠️ No face found in {filename}")
            continue

        encodings = face_recognition.face_encodings(rgb, boxes)
        if len(encodings) == 0:
            print(f"⚠️ Face encoding failed for {filename}")
            continue

        enrollment_number = filename.split('.')[0]
        known_encodings.append(encodings[0])
        known_ids.append(enrollment_number)
        print(f"✅ Encoded {enrollment_number}")

# ✅ Save encodings
data = {"encodings": known_encodings, "ids": known_ids}
with open(ENCODINGS_PATH, "wb") as f:
    pickle.dump(data, f)

print("✅ All face encodings saved successfully.")
