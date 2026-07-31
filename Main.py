import cv2
import mediapipe as mp
import numpy as np
import serial
import time

# -----------------------------
# Arduino Connection (FIXED)
# -----------------------------
arduino = serial.Serial('COM5', 9600, timeout=0)
time.sleep(1)

# -----------------------------
# MediaPipe Setup (OPTIMIZED)
# -----------------------------
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=False   # FIX: reduces lag + prevents freeze
)

# -----------------------------
# Eye Landmarks
# -----------------------------
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# -----------------------------
# Thresholds
# -----------------------------
EAR_THRESHOLD = 0.23
CLOSED_EYE_TIME = 2

# -----------------------------
# State Variables
# -----------------------------
sleep_start = None
alarm_sent = False

# -----------------------------
# Camera
# -----------------------------
cap = cv2.VideoCapture(0)

# -----------------------------
# Distance Function
# -----------------------------
def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

# -----------------------------
# EAR Calculation
# -----------------------------
def calculate_ear(points):
    A = distance(points[1], points[5])
    B = distance(points[2], points[4])
    C = distance(points[0], points[3])
    return (A + B) / (2.0 * C)

# -----------------------------
# Main Loop
# -----------------------------
while True:

    ret, frame = cap.read()
    if not ret:
        print("Camera Error")
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    h, w, _ = frame.shape
    status = "No Face Detected"

    if results.multi_face_landmarks:

        landmarks = results.multi_face_landmarks[0].landmark

        left_eye = [
            (int(landmarks[i].x * w), int(landmarks[i].y * h))
            for i in LEFT_EYE
        ]

        right_eye = [
            (int(landmarks[i].x * w), int(landmarks[i].y * h))
            for i in RIGHT_EYE
        ]

        # Draw points
        for point in left_eye + right_eye:
            cv2.circle(frame, point, 2, (255, 0, 0), -1)

        # EAR
        left_ear = calculate_ear(left_eye)
        right_ear = calculate_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0

        cv2.putText(frame, f"EAR: {avg_ear:.2f}",
                    (30, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2)

        # -----------------------------
        # EYES CLOSED
        # -----------------------------
        if avg_ear < EAR_THRESHOLD:

            status = "Eyes Closed"

            if sleep_start is None:
                sleep_start = time.time()

            elapsed = time.time() - sleep_start

            if elapsed >= CLOSED_EYE_TIME:
                status = "ALERT! DRIVER SLEEPING"

                if not alarm_sent:
                    print("Sending A -> Driver Sleeping")

                    try:
                        arduino.write(b'A')
                        arduino.flush()
                    except:
                        print("Serial write failed")

                    alarm_sent = True

        # -----------------------------
        # AWAKE
        # -----------------------------
        else:

            status = "Driver Awake"
            sleep_start = None

            if alarm_sent:
                print("Sending R -> Driver Awake")

                try:
                    arduino.write(b'R')
                    arduino.flush()
                except:
                    print("Serial write failed")

                alarm_sent = False

    # -----------------------------
    # Status Text
    # -----------------------------
    cv2.putText(frame, status,
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2)

    cv2.imshow("Anti-Sleep Project", frame)

    # Exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# -----------------------------
# SAFE EXIT
# -----------------------------
try:
    arduino.write(b'R')
except:
    pass

cap.release()
cv2.destroyAllWindows()
arduino.close()

print("Program Closed")