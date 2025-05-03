import cv2
import mediapipe as mp
import numpy as np
import time
import csv
from datetime import datetime

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

LEFT_EYE = [159, 145]
RIGHT_EYE = [386, 374]
NOSE_TIP = 1

log_file = "distraction_log.csv"

def log_distraction(reason):
    now = datetime.now().strftime("%H:%M:%S")
    with open(log_file, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([now, reason])

def eye_aspect_ratio(landmarks, eye_indices):
    p1 = np.array([landmarks[eye_indices[0]].x, landmarks[eye_indices[0]].y])
    p2 = np.array([landmarks[eye_indices[1]].x, landmarks[eye_indices[1]].y])
    return np.linalg.norm(p1 - p2)

def main():
    with open(log_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "Distraction Reason"])

    cap = cv2.VideoCapture(0)
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    last_blink = time.time()
    blink_duration = 0.0
    prev_status = "Focused"

    focus_time = 0.0
    distraction_time = 0.0
    session_start = time.time()
    last_switch = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        status = "Focused"
        distracted = False

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    frame, face_landmarks, mp_face_mesh.FACEMESH_TESSELATION)

                landmarks = face_landmarks.landmark
                left_ear = eye_aspect_ratio(landmarks, LEFT_EYE)
                right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE)
                ear_avg = (left_ear + right_ear) / 2

                if ear_avg < 0.003:
                    blink_duration = time.time() - last_blink
                    if blink_duration > 1.5:
                        status = "Eyes closed"
                        distracted = True
                else:
                    last_blink = time.time()
                    blink_duration = 0

                nose_x = landmarks[NOSE_TIP].x
                if nose_x < 0.3 or nose_x > 0.7:
                    status = "Looking away"
                    distracted = True
        else:
            status = "No face"
            distracted = True

        if status != prev_status:
            now = time.time()
            duration = now - last_switch
            if prev_status == "Focused":
                focus_time += duration
            else:
                distraction_time += duration

            if status != "Focused":
                log_distraction(status)

            prev_status = status
            last_switch = now

        color = (0, 0, 255) if distracted else (0, 255, 0)
        cv2.putText(frame, f"Status: {status}", (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
        cv2.imshow('Focus', frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC 
            now = time.time()
            if prev_status == "Focused":
                focus_time += now - last_switch
            else:
                distraction_time += now - last_switch
            break

    cap.release()
    cv2.destroyAllWindows()

    total_time = time.time() - session_start
    print("\n====== Focus Session Summary ======")
    print(f"Total Time      : {int(total_time)} seconds")
    print(f"Focused         : {int(focus_time)} seconds")
    print(f"Distracted      : {int(distraction_time)} seconds")
    print(f"Log saved to    : {log_file}")
    print("========================================")

if __name__ == "__main__":
    main()
