# WonderSnap Analysis: Bare-Hand 3D Spatial Computing Engine

An interactive, touchless 3D spatial learning environment controlled entirely via standard webcam input and bare hands — no VR headsets, controllers, or specialized hardware required.

WonderSnap Analysis reconstructs 3D structural models (such as Biological DNA Helices and Planetary Systems) as dynamic, real-time particle simulations using pure NumPy projection mathematics and Google MediaPipe skeletal tracking.

---

## Key Features

- **Engine-Free 3D Particle Renderer:** Built without Three.js, Unity, or prebuilt graphics frameworks. Perspective transformations, depth scaling, and rotations are computed entirely in pure NumPy.
- **Natural Interaction Paradigm:** Full rotational and scale freedom mapped directly to human hand ergonomics.
- **Instantaneous Model Metamorphosis:** Smooth linear interpolation (LERP) particle morphing between distinct physical and biological systems.
- **Contextual Inspection HUD:** Integrated index-finger directional tracking that projects a target crosshair and analytical telemetry card.
- **Multithreaded Auditory Feedback:** Asynchronous audio signaling on gesture trigger states to preserve real-time visual pipeline throughput.

---

## Interaction Matrix

| Gesture | Physical Trigger | System Response |
| :--- | :--- | :--- |
| **Snap / Pinch** | Thumb tip to index tip | Cycles active model & plays audio cue |
| **Closed Fist** | Wrist to middle fingertip compression | Condenses particle cloud into target 3D model |
| **Open Hand** | Full knuckle and phalange extension | Triggers particle dispersal / explosion state |
| **Wrist Twist** | Dynamic angular deviation of wrist | Direct real-time Y-axis 3D model rotation |
| **Two-Hand Spread** | Distance between bilateral wrist coordinates | Continuous 3D scaling (Zoom In / Zoom Out) |
| **Point to Inspect**| Extended index finger with other digits clenched | Locks targeting reticle and renders telemetry card |

---

## Quickstart

### Prerequisites
- Python 3.9+
- Standard USB Webcam

### Installation & Run

```bash
# Clone the repository
git clone [https://github.com/dineshvarma8778706302-crypto/WONDER-ANALYSIS-TRACKING.git](https://github.com/dineshvarma8778706302-crypto/WONDER-ANALYSIS-TRACKING.git)
cd WONDER-ANALYSIS-TRACKING

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
