import cv2
import mediapipe as mp
import numpy as np
import time

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Eye landmark indices
LEFT_EYE = [159, 145]
RIGHT_EYE = [386, 374]
NOSE_TIP = 1

def eye_aspect_ratio(landmarks, eye_indices):
    p1 = np.array([landmarks[eye_indices[0]].x, landmarks[eye_indices[0]].y])
    p2 = np.array([landmarks[eye_indices[1]].x, landmarks[eye_indices[1]].y])
    return np.linalg.norm(p1 - p2)

def main():
    cap = cv2.VideoCapture(0)
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    last_blink = time.time()
    blink_duration = 0.0
    distracted = False

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

                if ear_avg < 0.003:  # eyes closed
                    blink_duration = time.time() - last_blink
                    if blink_duration > 1.5:
                        status = "Eyes closed - Distracted"
                        distracted = True
                else:
                    last_blink = time.time()
                    blink_duration = 0

                nose_x = landmarks[NOSE_TIP].x
                if nose_x < 0.3 or nose_x > 0.7:
                    status = "Looking away - Distracted"
                    distracted = True

        else:
            status = "No face detected - Distracted"
            distracted = True

        color = (0, 0, 255) if distracted else (0, 255, 0)
        cv2.putText(frame, status, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
        cv2.imshow('Focus Detector', frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
