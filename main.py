import cv2
import mediapipe as mp
import numpy as np
import math
import time
import threading
import winsound
import subprocess
from collections import deque

# --- MULTITHREADED AUDIO & VOICE ENGINE ---
def play_snap_sound():
    def _sound():
        winsound.Beep(1200, 80)
        winsound.Beep(1800, 100)
    threading.Thread(target=_sound, daemon=True).start()

def speak_voice(text):
    def _speak():
        cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    threading.Thread(target=_speak, daemon=True).start()

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# --- 3D PROCEDURAL MODELS GENERATION ---
NUM_PARTICLES = 1000

# 1. Cyber Sphere
indices = np.arange(0, NUM_PARTICLES, dtype=float) + 0.5
phi = np.arccos(1 - 2 * indices / NUM_PARTICLES)
theta = np.pi * (1 + 5**0.5) * indices
s_x = np.cos(theta) * np.sin(phi) * 150
s_y = np.sin(theta) * np.sin(phi) * 150
s_z = np.cos(phi) * 150
sphere_model = np.stack([s_x, s_y, s_z], axis=1)

# 2. DNA Double Helix
t = np.linspace(-4 * np.pi, 4 * np.pi, NUM_PARTICLES // 2)
dna1_x = np.cos(t) * 75
dna1_y = t * 24
dna1_z = np.sin(t) * 75
dna2_x = np.cos(t + np.pi) * 75
dna2_y = t * 24
dna2_z = np.sin(t + np.pi) * 75
dna_model = np.vstack([
    np.stack([dna1_x, dna1_y, dna1_z], axis=1),
    np.stack([dna2_x, dna2_y, dna2_z], axis=1)
])

# 3. Planet Saturn
core_count = NUM_PARTICLES // 3
ring_count = NUM_PARTICLES - core_count
c_indices = np.arange(0, core_count, dtype=float) + 0.5
c_phi = np.arccos(1 - 2 * c_indices / core_count)
c_theta = np.pi * (1 + 5**0.5) * c_indices
core_x = np.cos(c_theta) * np.sin(c_phi) * 75
core_y = np.sin(c_theta) * np.sin(c_phi) * 75
core_z = np.cos(c_phi) * 75
saturn_core = np.stack([core_x, core_y, core_z], axis=1)

ring_radii = np.random.uniform(110, 210, ring_count)
ring_angles = np.random.uniform(0, 2 * np.pi, ring_count)
ring_x = np.cos(ring_angles) * ring_radii
ring_z = np.sin(ring_angles) * ring_radii
ring_y = np.random.uniform(-4, 4, ring_count)
saturn_rings = np.stack([ring_x, ring_y, ring_z], axis=1)

tilt_angle = np.radians(25)
tilt_matrix = np.array([
    [1, 0, 0],
    [0, np.cos(tilt_angle), -np.sin(tilt_angle)],
    [0, np.sin(tilt_angle), np.cos(tilt_angle)]
])
saturn_rings = np.dot(saturn_rings, tilt_matrix)
saturn_model = np.vstack([saturn_core, saturn_rings])

# 4. Human Heart
u = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
v = np.random.uniform(-np.pi / 2, np.pi / 2, NUM_PARTICLES)
h_x = 16 * (np.sin(u) ** 3) * np.cos(v) * 7.5
h_y = -(13 * np.cos(u) - 5 * np.cos(2*u) - 2 * np.cos(3*u) - np.cos(4*u)) * np.cos(v) * 7.5
h_z = 25 * np.sin(v) * 4.5
heart_base = np.stack([h_x, h_y, h_z], axis=1)

# 5. Cosmic Black Hole
bh_radii = np.random.uniform(45, 230, NUM_PARTICLES)
bh_base_angles = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
bh_speeds = 350.0 / (bh_radii ** 1.1)
bh_warp = np.where(np.sin(bh_base_angles) > 0, (bh_radii / 230.0) * 45, 0)
bh_y = np.random.uniform(-5, 5, NUM_PARTICLES) + bh_warp

bh_tilt = np.radians(35)
bh_rot_x = np.array([
    [1, 0, 0],
    [0, np.cos(bh_tilt), -np.sin(bh_tilt)],
    [0, np.sin(bh_tilt), np.cos(bh_tilt)]
])

# Models Catalogue
MODELS = [
    {
        "name": "COSMIC BLACK HOLE", 
        "data": None,
        "color": (0, 140, 255)  # Plasma Orange
    },
    {
        "name": "HUMAN HEART", 
        "data": heart_base.copy(), 
        "color": (40, 50, 255)  # Crimson Red
    },
    {
        "name": "DNA DOUBLE HELIX", 
        "data": dna_model, 
        "color": (255, 0, 255)  # Magenta
    },
    {
        "name": "PLANET SATURN", 
        "data": saturn_model, 
        "color": (0, 215, 255)  # Golden Orange
    },
    {
        "name": "CYBER SPHERE", 
        "data": sphere_model, 
        "color": (255, 255, 0)  # Cyan
    }
]

current_model_idx = 0
last_switch_time = 0
snap_ready = True  # Latch to prevent auto-switching

explode_points = np.random.uniform(-350, 350, (NUM_PARTICLES, 3))
current_particles = explode_points.copy()

# Hand Energy Trails Buffer
trail_points = deque(maxlen=24)

def get_distance(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def get_angle(p1, p2):
    rad = math.atan2(p2.y - p1.y, p2.x - p1.x)
    return math.degrees(rad)

current_scale = 1.0
current_rot_y = 0.0

prev_frame_time = time.time()
fps = 30.0

speak_voice("WonderSnap online. Loading Cosmic Black Hole.")

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    
    # Studio lighting
    display_frame = cv2.convertScaleAbs(img, alpha=1.1, beta=15)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    inference_start = time.time()
    results = hands.process(img_rgb)
    latency_ms = (time.time() - inference_start) * 1000

    active_name = MODELS[current_model_idx]["name"]

    # Dynamic target animations
    if active_name == "HUMAN HEART":
        beat_t = time.time() * 5.0
        pulse = 1.0 + 0.12 * (np.sin(beat_t) ** 8) + 0.05 * (np.sin(beat_t + 0.4) ** 8)
        active_target_data = heart_base * pulse
    elif active_name == "COSMIC BLACK HOLE":
        cur_t = time.time()
        cur_angles = bh_base_angles + (bh_speeds * cur_t * 0.08)
        bx = np.cos(cur_angles) * bh_radii
        bz = np.sin(cur_angles) * bh_radii
        raw_bh = np.stack([bx, bh_y, bz], axis=1)
        active_target_data = np.dot(raw_bh, bh_rot_x)
    else:
        active_target_data = MODELS[current_model_idx]["data"]

    target_shape = explode_points
    gesture_detected = "Floating Cloud"
    hand_centers = []

    if results.multi_hand_landmarks:
        num_hands = len(results.multi_hand_landmarks)

        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            lm = hand_landmarks.landmark
            wrist = lm[0]
            thumb_tip = lm[4]
            index_tip = lm[8]
            middle_tip = lm[12]

            hand_centers.append((int(wrist.x * w), int(wrist.y * h)))
            trail_points.append((int(index_tip.x * w), int(index_tip.y * h)))

            pinch_dist = get_distance(thumb_tip, index_tip)
            hand_open_dist = get_distance(wrist, middle_tip)
            wrist_angle = get_angle(wrist, lm[9])
            current_rot_y = np.radians(wrist_angle * 1.5)

            # --- GESTURE HIERARCHY (Fixed order to stop auto-switching) ---
            
            # 1. First priority: Fist (Assemble)
            if hand_open_dist < 0.22:
                gesture_detected = "Fist: Assembled"
                target_shape = active_target_data

            # 2. Second priority: Open Hand (Explode)
            elif hand_open_dist > 0.38:
                gesture_detected = "Open Hand: Explode"
                target_shape = explode_points

            # 3. Third priority: Snap / Pinch (Only if hand is NOT a fist)
            elif pinch_dist < 0.04:
                gesture_detected = "Snap: Model Switch!"
                target_shape = active_target_data
                
                # Triggers only ONCE per pinch (requires release)
                if snap_ready and (time.time() - last_switch_time > 1.5):
                    current_model_idx = (current_model_idx + 1) % len(MODELS)
                    new_model_name = MODELS[current_model_idx]["name"]
                    play_snap_sound()
                    speak_voice(f"Switching to {new_model_name}")
                    last_switch_time = time.time()
                    snap_ready = False
            else:
                gesture_detected = "Tracking Active"
                target_shape = active_target_data

            # Reset snap trigger only after user opens fingers apart
            if pinch_dist > 0.08:
                snap_ready = True

        # Two-Hand Zoom
        if num_hands == 2:
            p1, p2 = hand_centers[0], hand_centers[1]
            cv2.line(display_frame, p1, p2, (255, 0, 255), 2)
            dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            target_scale = np.clip(dist / 220.0, 0.5, 2.5)
            current_scale += (target_scale - current_scale) * 0.1

    # Hand Energy Aura Trails
    for idx, (tx, ty) in enumerate(trail_points):
        trail_rad = int(1 + (idx / len(trail_points)) * 5)
        trail_alpha = idx / len(trail_points)
        trail_color = (int(255 * trail_alpha), int(220 * trail_alpha), 50)
        cv2.circle(display_frame, (tx, ty), trail_rad, trail_color, -1)

    # Physics interpolation (LERP)
    current_particles += (target_shape - current_particles) * 0.14

    # 3D Rotation
    cos_a, sin_a = np.cos(current_rot_y), np.sin(current_rot_y)
    rot_matrix = np.array([
        [cos_a, 0, sin_a],
        [0,     1,     0],
        [-sin_a, 0, cos_a]
    ])
    rotated = np.dot(current_particles * current_scale, rot_matrix)

    # 3D to 2D Projection
    cx, cy = w // 2, h // 2
    fov = 500
    active_color = MODELS[current_model_idx]["color"]

    for x, y, z in rotated:
        depth = z + fov
        if depth > 10:
            px = int(cx + (x * fov) / depth)
            py = int(cy + (y * fov) / depth)

            if 0 <= px < w and 0 <= py < h:
                radius = 3 if depth > fov else 4
                cv2.circle(display_frame, (px, py), radius, active_color, -1)

    # Real-time FPS calculation
    curr_frame_time = time.time()
    fps = 0.9 * fps + 0.1 * (1.0 / (curr_frame_time - prev_frame_time))
    prev_frame_time = curr_frame_time

    # Telemetry HUD Overlays
    cv2.putText(display_frame, f"WONDERSNAP: {active_name}", (20, 40), 
                cv2.FONT_HERSHEY_DUPLEX, 0.8, active_color, 2)
    cv2.putText(display_frame, f"Status: {gesture_detected}", (20, 75), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
    
    hud_fps_text = f"FPS: {int(fps)} | LATENCY: {latency_ms:.1f}ms"
    cv2.putText(display_frame, hud_fps_text, (w - 320, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1)
    cv2.putText(display_frame, "ENGINE: NUMPY 3D PERSPECTIVE", (w - 320, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    cv2.putText(display_frame, "[Snap]: Switch Model | [Fist]: Assemble | [Open]: Explode | [Wrist]: Rotate", 
                (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.imshow("WonderSnap - Analysis Lab", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()