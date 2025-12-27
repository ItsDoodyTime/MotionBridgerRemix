import cv2
import mediapipe as mp
import numpy as np
import json
import time
import websocket
import math

# =============================
# PNGTubeRemix WebSocket Config
# =============================
# Change the numbers after ":" to the port you have set in PNGTubeRemix's Websocket Tab.
WS_URL = "ws://localhost:9321"
# The name of your sprite. (THIS IS CASE-SENSITIVE!)
HEAD_SPRITE_NAME = "Head"
# (IMPORTANT!) This is how frequent you send udpates to PNGTubeRemix. Thing of it as the frame rate of the program.
# Default Value = 0.05 MILLISECONDS which is 20 updates/sec. (20 FPS)
# If it's laggy, You can INCREASE the number, to DECREASE the number of updates per 1 second.
# Just be aware that the animation will look very choppy and snappy. (you are lowering the FPS!)
SEND_INTERVAL = 0.05

# =============================
# Motion Mapping Settings
# =============================


# Unit: degrees
MAX_HEAD_ROTATION = 20.0
# Unit: pixels
MAX_HEAD_Y_OFFSET = 15.0

# =============================
# WebSocket Setup
# =============================
ws = websocket.WebSocket()
ws.connect(WS_URL)
print("Connected to PNGTubeRemix")

# =============================
# MediaPipe Setup
# =============================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

last_send_time = 0

# =============================
# Utility Functions
# =============================
def clamp(value, min_val, max_val):
    return max(min(value, max_val), min_val)

def send_animate(rotation):
    payload = {
        "event": "animate_sprite",
        "sprite_name": HEAD_SPRITE_NAME,
        "rotation": rotation,
        "duration": SEND_INTERVAL
    }
    ws.send(json.dumps(payload))

def send_move(y_offset):
    payload = {
        "event": "move_sprite",
        "sprite_name": HEAD_SPRITE_NAME,
        "x": 0,
        "y": y_offset,
        "duration": SEND_INTERVAL
    }
    ws.send(json.dumps(payload))

# =============================
# Head Pose Estimation
# =============================
def estimate_head_pose(landmarks, image_w, image_h):
    # Key points (MediaPipe indices)
    nose_tip = landmarks[1]
    left_eye = landmarks[33]
    right_eye = landmarks[263]
    chin = landmarks[199]

    # Convert to pixel space
    nose = np.array([nose_tip.x * image_w, nose_tip.y * image_h])
    left = np.array([left_eye.x * image_w, left_eye.y * image_h])
    right = np.array([right_eye.x * image_w, right_eye.y * image_h])
    chin = np.array([chin.x * image_w, chin.y * image_h])

    # Yaw (left/right)
    eye_center = (left + right) / 2
    yaw = (nose[0] - eye_center[0]) / image_w * 60

    # Pitch (up/down)
    pitch = (nose[1] - eye_center[1]) / image_h * 60

    return yaw, pitch

# =============================
# Main Loop
# =============================
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        yaw, pitch = estimate_head_pose(landmarks, w, h)

        # Clamp & scale
        yaw = clamp(yaw, -MAX_HEAD_ROTATION, MAX_HEAD_ROTATION)
        pitch = clamp(pitch, -MAX_HEAD_ROTATION, MAX_HEAD_ROTATION)

        y_offset = clamp(-pitch, -MAX_HEAD_Y_OFFSET, MAX_HEAD_Y_OFFSET)

        now = time.time()
        if now - last_send_time >= SEND_INTERVAL:
            send_animate(rotation=yaw)
            send_move(y_offset=y_offset)
            last_send_time = now

    cv2.imshow("Tracking", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
ws.close()
