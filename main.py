import cv2
import mediapipe as mp
import numpy as np
import math
import time
import threading
import winsound  # Windows built-in sound library

# Sound player (Threaded so FPS drops aagadhu)
def play_snap_sound():
    def _sound():
        winsound.Beep(1200, 100)
        winsound.Beep(1800, 120)
    threading.Thread(target=_sound, daemon=True).start()

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# --- 3D MODELS GENERATION ---
NUM_PARTICLES = 900

# 1. Sphere
indices = np.arange(0, NUM_PARTICLES, dtype=float) + 0.5
phi = np.arccos(1 - 2 * indices / NUM_PARTICLES)
theta = np.pi * (1 + 5**0.5) * indices
s_x = np.cos(theta) * np.sin(phi) * 150
s_y = np.sin(theta) * np.sin(phi) * 150
s_z = np.cos(phi) * 150
sphere_model = np.stack([s_x, s_y, s_z], axis=1)

# 2. DNA Helix
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

# 3. Saturn with Rings
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

# Models Metadata & Educational Database
MODELS = [
    {
        "name": "CYBER SPHERE", 
        "data": sphere_model, 
        "color": (255, 255, 0),
        "desc_1": "Core Type: Quantum Particle Singularity",
        "desc_2": "Nodes: 900 synced energy points"
    },
    {
        "name": "DNA DOUBLE HELIX", 
        "data": dna_model, 
        "color": (255, 0, 255),
        "desc_1": "Base Pairs: Adenine-Thymine | Guanine-Cytosine",
        "desc_2": "Structure: Right-handed antiparallel double helix"
    },
    {
        "name": "PLANET SATURN", 
        "data": saturn_model, 
        "color": (0, 215, 255),
        "desc_1": "Atmosphere: 96% Hydrogen | 3% Helium",
        "desc_2": "Rings: 99% Water ice particles & cosmic dust"
    }
]

current_model_idx = 0
last_switch_time = 0

explode_points = np.random.uniform(-350, 350, (NUM_PARTICLES, 3))
current_particles = explode_points.copy()

def get_distance(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y)

def get_angle(p1, p2):
    rad = math.atan2(p2.y - p1.y, p2.x - p1.x)
    return math.degrees(rad)

current_scale = 1.0
current_rot_y = 0.0

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    
    display_frame = cv2.addWeighted(img, 0.35, np.zeros_like(img), 0.65, 0)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    target_shape = explode_points
    gesture_detected = "Floating Cloud"
    hand_centers = []
    inspecting = False
    pointer_pos = None

    if results.multi_hand_landmarks:
        num_hands = len(results.multi_hand_landmarks)

        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_draw.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            lm = hand_landmarks.landmark
            wrist = lm[0]
            thumb_tip = lm[4]
            index_tip = lm[8]
            index_pip = lm[6]
            middle_tip = lm[12]
            middle_pip = lm[10]
            ring_tip = lm[16]
            ring_pip = lm[14]
            pinky_tip = lm[20]
            pinky_pip = lm[18]

            hand_centers.append((int(wrist.x * w), int(wrist.y * h)))

            # Gestures
            pinch_dist = get_distance(thumb_tip, index_tip)
            hand_open_dist = get_distance(wrist, middle_tip)
            wrist_angle = get_angle(wrist, lm[9])
            current_rot_y = np.radians(wrist_angle * 1.5)

            # Check if Index Finger is Pointing (Index up, other fingers folded)
            is_pointing = (index_tip.y < index_pip.y) and \
                          (middle_tip.y > middle_pip.y) and \
                          (ring_tip.y > ring_pip.y) and \
                          (pinky_tip.y > pinky_pip.y)

            if is_pointing:
                inspecting = True
                pointer_pos = (int(index_tip.x * w), int(index_tip.y * h))
                gesture_detected = "Pointing: Inspect Mode"
                target_shape = MODELS[current_model_idx]["data"]
            elif pinch_dist < 0.045:
                gesture_detected = "Snap: Model Switch!"
                target_shape = MODELS[current_model_idx]["data"]
                
                if time.time() - last_switch_time > 1.2:
                    current_model_idx = (current_model_idx + 1) % len(MODELS)
                    play_snap_sound()
                    last_switch_time = time.time()
            elif hand_open_dist < 0.2:
                gesture_detected = "Fist: Assembled"
                target_shape = MODELS[current_model_idx]["data"]
            elif hand_open_dist > 0.38:
                gesture_detected = "Open Hand: Explode"
                target_shape = explode_points

        # Two-Hand Zoom
        if num_hands == 2:
            p1, p2 = hand_centers[0], hand_centers[1]
            cv2.line(display_frame, p1, p2, (255, 0, 255), 2)
            dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            target_scale = np.clip(dist / 220.0, 0.5, 2.5)
            current_scale += (target_scale - current_scale) * 0.1

    # Physics interpolation
    current_particles += (target_shape - current_particles) * 0.14

    # 3D Rotation
    cos_a, sin_a = np.cos(current_rot_y), np.sin(current_rot_y)
    rot_matrix = np.array([
        [cos_a, 0, sin_a],
        [0,     1,     0],
        [-sin_a, 0, cos_a]
    ])
    rotated = np.dot(current_particles * current_scale, rot_matrix)

    # 3D Projection
    cx, cy = w // 2, h // 2
    fov = 500
    active_color = MODELS[current_model_idx]["color"]

    for x, y, z in rotated:
        depth = z + fov
        if depth > 10:
            px = int(cx + (x * fov) / depth)
            py = int(cy + (y * fov) / depth)

            if 0 <= px < w and 0 <= py < h:
                radius = 2 if depth > fov else 3
                cv2.circle(display_frame, (px, py), radius, active_color, -1)

    # INSPECTION CROSSHAIR & INFO CARD OVERLAY
    if inspecting and pointer_pos:
        px, py = pointer_pos
        # Target HUD Crosshair
        cv2.circle(display_frame, (px, py), 22, (0, 255, 255), 2)
        cv2.line(display_frame, (px - 30, py), (px + 30, py), (0, 255, 255), 1)
        cv2.line(display_frame, (px, py - 30), (px, py + 30), (0, 255, 255), 1)

        # Floating Educational Card
        card_x, card_y = min(px + 35, w - 380), max(py - 60, 40)
        # Background card glow
        cv2.rectangle(display_frame, (card_x, card_y), (card_x + 360, card_y + 90), (20, 20, 20), -1)
        cv2.rectangle(display_frame, (card_x, card_y), (card_x + 360, card_y + 90), (0, 255, 255), 2)
        
        # Details inside card
        model_info = MODELS[current_model_idx]
        cv2.putText(display_frame, f"INSPECTION: {model_info['name']}", (card_x + 10, card_y + 25), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 255, 255), 1)
        cv2.putText(display_frame, model_info["desc_1"], (card_x + 10, card_y + 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)
        cv2.putText(display_frame, model_info["desc_2"], (card_x + 10, card_y + 75), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 255, 180), 1)

    # General HUD Header
    active_name = MODELS[current_model_idx]["name"]
    cv2.putText(display_frame, f"WONDERSNAP: {active_name}", (20, 40), 
                cv2.FONT_HERSHEY_DUPLEX, 0.8, active_color, 2)
    cv2.putText(display_frame, f"Status: {gesture_detected}", (20, 75), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
    cv2.putText(display_frame, "[Snap]: Switch Model | [Point]: Inspect | [Fist]: Assemble | [Open]: Explode", 
                (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.imshow("WonderSnap - Analysis Lab", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()