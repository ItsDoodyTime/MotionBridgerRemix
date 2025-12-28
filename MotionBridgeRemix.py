import cv2
import json
import time
import os
import sys
import logging
import websocket
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox

# =========================
# Paths & Constants
# =========================
LOG_PATH = "logs/app.log"

# =========================
# Crash dialog
# =========================
def show_crash_dialog(message):
    try:
        root = tk.Tk()
        root.withdraw()

        def copy_log():
            try:
                with open(LOG_PATH, "r", encoding="utf-8") as f:
                    root.clipboard_clear()
                    root.clipboard_append(f.read())
                    root.update()
                messagebox.showinfo("Copied", "Error log copied to clipboard.")
            except Exception:
                messagebox.showerror("Error", "Failed to copy log.")

        if messagebox.askyesno(
            "PNGRemix Motion Tracker - Crash",
            f"{message}\n\nWould you like to copy the error log?"
        ):
            copy_log()

        root.destroy()
    except Exception:
        pass

# =========================
# Exit confirmation
# =========================
def confirm_exit():
    try:
        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno(
            "Exit",
            "Are you sure you want to close the motion tracker?"
        )
        root.destroy()
        return result
    except Exception:
        return True

# =========================
# Logging
# =========================
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("PNGRemixTracker")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info("Application starting")

# =========================
# Load config
# =========================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    logger.critical(f"Failed to load config.json: {e}")
    show_crash_dialog("Failed to load config.json.")
    sys.exit(1)

# =========================
# Config values
# =========================
WS_HOST = config["websocket"]["host"]
WS_PORT = config["websocket"]["port"]
RECONNECT_DELAY = config["websocket"]["reconnect_delay_seconds"]

SHOW_CAMERA = config["preview"]["show_camera"]
DRAW_FACE_MESH = config["preview"]["draw_face_mesh"]
DRAW_LANDMARKS = config["preview"]["draw_landmarks"]

CAMERA_INDEX = config["performance"]["camera_index"]
MAX_FPS = config["performance"]["max_fps"]

SMOOTHING = config["smoothing"]["head_rotation"]

YAW_MULT = config["head_rotation"]["yaw_multiplier"]
PITCH_MULT = config["head_rotation"]["pitch_multiplier"]
ROLL_MULT = config["head_rotation"]["roll_multiplier"]

YAW_DEAD = config["deadzone"]["yaw"]
PITCH_DEAD = config["deadzone"]["pitch"]
ROLL_DEAD = config["deadzone"]["roll"]

ACTIONS = config.get("actions", {})

# =========================
# MediaPipe
# =========================
mp_face_mesh = mp.tasks.face_mesh
mp_draw = mp.tasks.drawing_utils

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    refine_landmarks=True,
    max_num_faces=1
)

# =========================
# Webcam
# =========================
cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    logger.critical("Failed to open webcam")
    show_crash_dialog("Failed to open webcam.")
    sys.exit(1)

# =========================
# WebSocket
# =========================
def connect_ws():
    while True:
        try:
            ws = websocket.create_connection(
                f"ws://{WS_HOST}:{WS_PORT}", timeout=5
            )
            logger.info("Connected to PNGTubeRemix WebSocket")
            return ws
        except Exception as e:
            logger.warning(f"WebSocket failed ({e}), retrying...")
            time.sleep(RECONNECT_DELAY)

ws = connect_ws()

# =========================
# Helpers
# =========================
prev_yaw = prev_pitch = prev_roll = 0.0

def smooth(prev, curr, factor):
    return prev * factor + curr * (1 - factor)

def deadzone(value, zone):
    return 0.0 if abs(value) < zone else value

def evaluate_condition(value, condition, threshold):
    if condition == ">":
        return value > threshold
    if condition == "<":
        return value < threshold
    if condition == "abs>":
        return abs(value) > threshold
    if condition == "abs<":
        return abs(value) < threshold
    return False

def send_action(sprite, value):
    payload = {
        "type": "action",
        "data": {
            "sprite": sprite,
            "value": value
        }
    }
    ws.send(json.dumps(payload))

# =========================
# Main loop
# =========================
last_frame = time.time()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Lost webcam feed")

        now = time.time()
        if now - last_frame < 1 / MAX_FPS:
            continue
        last_frame = now

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            lm = face.landmark

            nose = lm[1]
            left_eye = lm[33]
            right_eye = lm[263]
            forehead = lm[10]

            yaw = (right_eye.x - left_eye.x)
            pitch = (forehead.y - nose.y)
            roll = (right_eye.y - left_eye.y)

            yaw = deadzone(yaw, YAW_DEAD) * YAW_MULT
            pitch = deadzone(pitch, PITCH_DEAD) * PITCH_MULT
            roll = deadzone(roll, ROLL_DEAD) * ROLL_MULT

            yaw = smooth(prev_yaw, yaw, SMOOTHING)
            pitch = smooth(prev_pitch, pitch, SMOOTHING)
            roll = smooth(prev_roll, roll, SMOOTHING)

            prev_yaw, prev_pitch, prev_roll = yaw, pitch, roll

            # Send transform
            ws.send(json.dumps({
                "type": "transform",
                "data": {
                    "rotation": {
                        "x": pitch,
                        "y": yaw,
                        "z": roll
                    }
                }
            }))

            # Action mapping
            motion_map = {
                "head_yaw": yaw,
                "head_pitch": pitch,
                "head_roll": roll
            }

            for motion, rules in ACTIONS.items():
                value = motion_map.get(motion)
                if value is None:
                    continue

                for rule in rules:
                    if evaluate_condition(
                        value,
                        rule["condition"],
                        rule["threshold"]
                    ):
                        send_action(
                            rule["sprite"],
                            rule.get("value", 1.0)
                        )

            # Draw preview
            if SHOW_CAMERA:
                if DRAW_FACE_MESH:
                    mp_draw.draw_landmarks(
                        frame, face, mp_face_mesh.FACEMESH_TESSELATION
                    )
                elif DRAW_LANDMARKS:
                    mp_draw.draw_landmarks(
                        frame, face, mp_face_mesh.FACEMESH_CONTOURS
                    )

        if SHOW_CAMERA:
            cv2.imshow("PNGRemix Motion Tracker", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                if confirm_exit():
                    break

except Exception as e:
    logger.critical(f"Unhandled exception: {e}")
    show_crash_dialog("An unexpected error occurred.")

# =========================
# Cleanup
# =========================
cap.release()
ws.close()
cv2.destroyAllWindows()
logger.info("Application closed")
