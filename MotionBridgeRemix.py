# ==================================================
# ███╗░░░███╗██████╗░██████╗░
# ████╗░████║██╔══██╗██╔══██╗
# ██╔████╔██║██████╦╝██████╔╝
# ██║╚██╔╝██║██╔══██╗██╔══██╗
# ██║░╚═╝░██║██████╦╝██║░░██║
# ╚═╝░░░░░╚═╝╚═════╝░╚═╝░░╚═╝
#
# MotionBridgerRemix
# Version: 1.0
# By @ItsDoodyTime
# https://github.com/ItsDoodyTime/MotionBridgerRemix
# ==================================================


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
from PIL import Image, ImageTk
import threading

# ==================================================
# Paths & Constants
# ==================================================
APP_NAME = "MotionBridgerRemix"
APP_VERSION = "1.0.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

LOG_DIR = "logs"
LOG_PATH = os.path.join(LOG_DIR, "app.log")

MESH_STYLES = [ "TESS", "CONTOURS", "IRIS", "CONTOURS_IRIS" ]

# ==================================================
# Runtime Globals
# ==================================================
running = True
latest_frame = None
frame_lock = threading.Lock()
fps_value = 0.0

ws = None
ws_lock = threading.Lock()
ws_connected = False

mesh_style_index = 0
SHOW_CAMERA = False  # Always start with preview OFF for security
DRAW_FACE_MESH = False

# ==================================================
# Logging
# ==================================================
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("MotionBridgerRemix")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.info("Application starting")

# ==================================================
# Load config.json
# ==================================================
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except Exception as e:
    logger.critical(f"Failed to load config.json: {e}")
    messagebox.showerror(f"{APP_TITLE} - Crash", "Failed to load config.json.")
    sys.exit(1)

# ==================================================
# Configuration
# ==================================================

# --------------------------------------------------
# WebSocket Config
# --------------------------------------------------
WS_HOST = config["websocket"]["host"]
WS_PORT = config["websocket"]["port"]
RECONNECT_DELAY = config["websocket"]["reconnect_delay_seconds"]

# --------------------------------------------------
# Performance Config
# --------------------------------------------------
CAMERA_INDEX = config["performance"]["camera_index"]
MAX_FPS = max(1, config["performance"]["max_fps"])

# --------------------------------------------------
# Head Tracking config
# --------------------------------------------------
SMOOTHING = min(max(config["smoothing"]["head_rotation"], 0.0), 0.99)

YAW_DEAD = config["deadzone"]["y"]
PITCH_DEAD = config["deadzone"]["x"]
ROLL_DEAD = config["deadzone"]["z"]

# --------------------------------------------------
# Sprite Config (Fully Dynamic)
# --------------------------------------------------
SPRITES = config.get("sprites", {})

if not SPRITES:
    logger.warning("No sprites defined in config.json")

# ==================================================
# Tracker State (Dynamic, Config-Driven)
# ==================================================
tracker_state = {
    "HEAD": {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "rotation": 0.0
    }
    # Future expansion:
    # "MOUTH": {}
    # "EYE_BROW": {}
}

# ==================================================
# MediaPipe FaceMesh
# ==================================================
mp_face_mesh = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    refine_landmarks=True,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ==================================================
# Webcam
# ==================================================
cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    logger.critical("Failed to open webcam")
    messagebox.showerror(f"{APP_TITLE} - Crash", "Failed to open webcam.")
    sys.exit(1)

CAM_W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
CAM_H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
logger.info(f"Camera resolution: {CAM_W}x{CAM_H}")

# ==================================================
# WebSocket Connection
# ==================================================
def connect_ws():
    global ws, ws_connected

    while running:
        try:
            logger.info("Attempting WebSocket connection...")
            sock = websocket.create_connection(
                f"ws://{WS_HOST}:{WS_PORT}",
                timeout=5
            )
            with ws_lock:
                ws = sock
                ws_connected = True
            logger.info("WebSocket connected")
            return
        except Exception as e:
            with ws_lock:
                ws_connected = False
                ws = None
            logger.warning(f"WebSocket connect failed ({e}), retrying in {RECONNECT_DELAY}s")
            time.sleep(RECONNECT_DELAY)


threading.Thread(target=connect_ws, daemon=True).start()

# ==================================================
# Helpers
# ==================================================
prev_yaw = prev_pitch = prev_roll = 0.0

def smooth(prev, curr, factor):
    return prev * factor + curr * (1.0 - factor)

def deadzone(value, zone):
    return 0.0 if abs(value) < zone else value

def evaluate_condition(value, condition, threshold):
    if condition == ">": return value > threshold
    if condition == "<": return value < threshold
    if condition == "abs>": return abs(value) > threshold
    if condition == "abs<": return abs(value) < threshold
    return False

def update_camera_button():
    state_text = "ON" if SHOW_CAMERA else "OFF"
    state_color = "green" if SHOW_CAMERA else "red"
    btn_cam.config(
        text=f"Camera: {state_text}",
        fg=state_color
    )

def check_threshold(value, threshold):
    return abs(value) >= threshold

def scale_value(value, scale):
    return value * scale

def process_sprites():
    if not ws_connected:
        return

    for sprite_name, sprite_cfg in SPRITES.items():
        try:
            tracker_type = sprite_cfg["mediapipe_tracker"]
            tracker_vals = tracker_state.get(tracker_type)

            if not tracker_vals:
                continue

            thresholds = sprite_cfg.get("thresholds", {})
            output = {}

            for axis in ("x", "y", "z", "rotation"):
                if axis not in tracker_vals:
                    continue

                threshold = thresholds.get(axis, 0.0)
                value = tracker_vals[axis]

                if not check_threshold(value, threshold):
                    continue

                scale = sprite_cfg.get("pngtuberemix_values", {}).get(axis, 1.0)
                output[axis] = scale_value(value, scale)

            if output:
                ws.send(json.dumps({
                    "type": "action",
                    "data": {
                        "sprite": sprite_name,
                        "values": output
                    }
                }))

        except Exception as e:
            logger.warning(f"Sprite '{sprite_name}' failed: {e}")

def send_action(payload):
    global ws_connected, ws

    with ws_lock:
        sock = ws

    if not sock:
        return

    try:
        sock.send(json.dumps(payload))
    except Exception as e:
        logger.warning(f"WebSocket send failed: {e}")

        with ws_lock:
            try:
                sock.close()
            except Exception:
                pass
            ws = None
            ws_connected = False

        # Trigger reconnect in background
        threading.Thread(target=connect_ws, daemon=True).start()

# ==================================================
# Tkinter UI setup
# ==================================================
root = tk.Tk()
root.title(APP_TITLE)
root.resizable(False, False)

def on_close():
    global running
    if messagebox.askyesno("Exit Confirmation", "Are you sure you want to CLOSE MotionBridgerRemix?"):
        running = False
        try:
            cap.release()
        except:
            pass
        try:
            ws.close()
        except:
            pass
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# Toolbar frame
top = tk.Frame(root, bg="black")
top.pack(fill="x")

# WebSocket status
tk.Label(top, text="WS:", fg="white", bg="black").pack(side="left", padx=(5, 0))
lbl_ws_status = tk.Label(top, text="Disconnected", fg="red", bg="black")
lbl_ws_status.pack(side="left", padx=(0, 10))

# Buttons
def toggle_camera():
    global SHOW_CAMERA

    if not SHOW_CAMERA:
        # Confirm before enabling camera preview
        if not messagebox.askyesno(
            "Camera Security",
            "This will enable the camera preview.\n\n"
            "Your face may be visible on stream.\n\n"
            "Do you want to continue?"
        ):
            return  # User cancelled

    SHOW_CAMERA = not SHOW_CAMERA
    update_camera_button()

def toggle_mesh():
    global DRAW_FACE_MESH, DRAW_LANDMARKS
    DRAW_FACE_MESH = not DRAW_FACE_MESH
    DRAW_LANDMARKS = DRAW_FACE_MESH
    btn_mesh.config(
        text=f"Mesh: {'ON' if DRAW_FACE_MESH else 'OFF'}",
        fg="green" if DRAW_FACE_MESH else "red"
    )

def cycle_mesh_style():
    global mesh_style_index
    mesh_style_index = (mesh_style_index + 1) % len(MESH_STYLES)
    btn_style.config(text=f"Mesh Style: {MESH_STYLES[mesh_style_index]}")

btn_cam = tk.Button(
    top,
    text=f"Camera: {'ON' if SHOW_CAMERA else 'OFF'}",
    command=toggle_camera,
    fg="green" if SHOW_CAMERA else "red",
    bg="#222222",
    activebackground="#333333",
    bd=0
)
btn_cam.pack(side="left", padx=5)

btn_mesh = tk.Button(
    top,
    text=f"Mesh: {'ON' if DRAW_FACE_MESH else 'OFF'}",
    command=toggle_mesh,
    fg="green" if DRAW_FACE_MESH else "red",
    bg="#222222",
    activebackground="#333333",
    bd=0
)
btn_mesh.pack(side="left", padx=5)
update_camera_button()

btn_style = tk.Button(
    top,
    text=f"Mesh Style: {MESH_STYLES[mesh_style_index]}",
    command=cycle_mesh_style,
    fg="white",
    bg="#222222",
    activebackground="#333333",
    bd=0
)
btn_style.pack(side="left", padx=5)

# FPS counter
lbl_fps = tk.Label(top, text="FPS: 0.0", fg="green", bg="black")
lbl_fps.pack(side="right", padx=10)

# ==================================================
# Camera canvas (IMPORTANT FIX)
# ==================================================
CAM_W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
CAM_H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

canvas = tk.Canvas(
    root,
    width=CAM_W,
    height=CAM_H,
    bg="black",
    bd=0,
    highlightthickness=0
)
canvas.pack()

# Force window to correct size
root.geometry(f"{CAM_W}x{CAM_H + top.winfo_reqheight()}")

# ==================================================
# UI update loop
# ==================================================
def update_ui():
    if not running:
        return

    canvas.delete("all")

    with frame_lock:
        frame = latest_frame.copy() if latest_frame is not None else None

    if frame is not None and SHOW_CAMERA:
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(im)

        canvas.create_image(0, 0, anchor="nw", image=imgtk)
        canvas.image = imgtk  # prevent GC
    else:
        # Camera OFF screen
        canvas.create_text(
            CAM_W // 2,
            CAM_H // 2,
            text="Camera Preview is OFF",
            fill="white",
            font=("Arial", 20)
        )

    # Status updates
    lbl_ws_status.config(
        text="Connected" if ws_connected else "Disconnected",
        fg="green" if ws_connected else "red"
    )

    lbl_fps.config(text=f"FPS: {fps_value:.1f}")

    root.after(15, update_ui)

# ===================================================
# Camera/MediaPipe loop in a thread (Tracking only)
# ===================================================
def camera_loop():
    global latest_frame, prev_yaw, prev_pitch, prev_roll, fps_value, tracker_state

    last_time = time.time()

    while running:
        ret, frame = cap.read()
        if not ret:
            continue

        now = time.time()
        fps_value = 1.0 / (now - last_time)
        last_time = now

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            face = results.multi_face_landmarks[0]
            lm = face.landmark

            # --------------------------------------------------
            # Head pose calculations (normalized → scaled)
            # --------------------------------------------------
            nose = lm[1]
            left_eye = lm[33]
            right_eye = lm[263]
            forehead = lm[10]

            raw_yaw = right_eye.x - left_eye.x
            raw_pitch = forehead.y - nose.y
            raw_roll = right_eye.y - left_eye.y

            yaw = smooth(prev_yaw, deadzone(raw_yaw, YAW_DEAD), SMOOTHING)
            pitch = smooth(prev_pitch, deadzone(raw_pitch, PITCH_DEAD), SMOOTHING)
            roll = smooth(prev_roll, deadzone(raw_roll, ROLL_DEAD), SMOOTHING)

            prev_yaw, prev_pitch, prev_roll = yaw, pitch, roll

            # --------------------------------------------------
            # UPDATE TRACKER STATE (GLOBAL, CONFIG-DRIVEN)
            # --------------------------------------------------
            tracker_state["HEAD"]["x"] = pitch
            tracker_state["HEAD"]["y"] = yaw
            tracker_state["HEAD"]["z"] = roll
            tracker_state["HEAD"]["rotation"] = roll
            process_sprites()

            # --------------------------------------------------
            # Optional visual overlays
            # --------------------------------------------------
            if SHOW_CAMERA and DRAW_FACE_MESH:
                style = MESH_STYLES[mesh_style_index]
                if style == "TESS":
                    mp_draw.draw_landmarks(
                        frame,
                        face,
                        mp_face_mesh.FACEMESH_TESSELATION,
                        None,
                        mp_styles.get_default_face_mesh_tesselation_style()
                    )
                elif style == "CONTOURS":
                    mp_draw.draw_landmarks(
                        frame,
                        face,
                        mp_face_mesh.FACEMESH_CONTOURS,
                        None,
                        mp_styles.get_default_face_mesh_contours_style()
                    )
                elif style == "IRIS":
                    mp_draw.draw_landmarks(
                        frame,
                        face,
                        mp_face_mesh.FACEMESH_IRISES,
                        None,
                        mp_styles.get_default_face_mesh_iris_connections_style()
                    )
                elif style == "CONTOURS_IRIS":
                    mp_draw.draw_landmarks(
                        frame,
                        face,
                        mp_face_mesh.FACEMESH_CONTOURS,
                        None,
                        mp_styles.get_default_face_mesh_contours_style()
                    )
                    mp_draw.draw_landmarks(
                        frame,
                        face,
                        mp_face_mesh.FACEMESH_IRISES,
                        None,
                        mp_styles.get_default_face_mesh_iris_connections_style()
                    )

        with frame_lock:
            latest_frame = frame.copy()

# ==================================================
# Start threads and Tkinter loop
# ==================================================
threading.Thread(target=camera_loop, daemon=True).start()
root.after(0, update_ui)
root.mainloop()

# Cleanup
cap.release()
ws.close()
logger.info("Application closed")
