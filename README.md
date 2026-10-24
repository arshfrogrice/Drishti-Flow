# Drishti-Flow
# Drishti-Flow 🧠👁️

**A computer-vision-based habit awareness and pattern interruption system.**

Drishti-Flow is a Python-based application designed to help users become more aware of repetitive, unconscious behaviors through real-time webcam monitoring and gentle visual interruptions.

Rather than simply tracking habits after they happen, Drishti-Flow aims to recognize potential habit patterns as they occur and encourage a moment of conscious awareness.

> **Pause. Notice the moment.**

## ✨ Features

- **Real-Time Webcam Monitoring** — Processes webcam frames to detect facial and hand landmarks.
- **Face-Touch Detection** — Monitors hand proximity to multiple facial regions, including the nose, mouth, cheeks, and chin.
- **Movement Tracking** — Uses landmark distances, temporal smoothing, and approach detection to analyze hand movements.
- **Persistence-Based Detection** — Requires a potential behavior to persist for a configurable duration before triggering an interruption.
- **Cooldown Mechanism** — Helps prevent repeated alerts during a single detection episode.
- **Snapshot-Based Awareness** — Displays a temporary snapshot when a potential habit is detected, encouraging the user to pause and notice their behavior.
- **Privacy-Conscious Processing** — Snapshots are held in memory and are not intentionally saved to disk by the application.

## 🎯 Project Goals

Drishti-Flow aims to explore how computer vision can support habit awareness through:

- Real-time detection of repetitive physical behaviors.
- Immediate, non-intrusive visual feedback.
- Configurable detection thresholds and interruption timing.
- A modular architecture that can support additional habit detectors.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| OpenCV | Webcam capture and frame processing |
| MediaPipe | Face mesh and hand landmark detection |
| Tkinter | Snapshot awareness window |
| Pillow | Image conversion and display |

## ⚙️ Current Implementation

The current prototype focuses on **hand-to-face behavior detection**.

It detects facial and hand landmarks, calculates normalized distances between fingertips and selected facial regions, smooths measurements over consecutive frames, and triggers an awareness panel when the configured proximity and persistence conditions are satisfied.

### Detection Pipeline

1. Capture a frame from the webcam.
2. Detect face and hand landmarks.
3. Calculate distances between fingertips and facial regions.
4. Smooth distance measurements over recent frames.
5. Evaluate proximity, persistence, and cooldown conditions.
6. Capture the current frame in memory.
7. Display the awareness panel.

## 🚀 Getting Started

### Prerequisites

- Python 3.12 recommended for the current MediaPipe-based implementation.
- A working webcam.
- Git.
- macOS or Windows.

### 1. Clone the repository

```bash
git clone https://github.com/arshfrogrice/Drishti-Flow.git
cd Drishti-Flow
```

### 2. Create a virtual environment

**macOS:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install opencv-python mediapipe==0.10.21 Pillow
```

### 4. Run the application

```bash
python main.py
```

Allow camera access if your operating system requests permission.

To quit, focus the webcam window and press **Q**, or interrupt the running process with `Ctrl+C` in the terminal.

## 🔧 Configuration

Detection behavior can be adjusted through configuration constants in `main.py`, including:

- `NEAR_DISTANCE` — Proximity threshold for the original nose-touch detector.
- `PERSISTENCE_SECONDS` — Minimum duration before an interruption.
- `APPROACH_DELTA` — Distance change used to identify an approaching hand.
- `COOLDOWN_SECONDS` — Minimum interval between eligible interruptions.
- `SMOOTHING_FRAMES` — Number of recent distance measurements used for smoothing.

Thresholds may require calibration for different camera positions, distances, and lighting conditions.

## 🔒 Privacy

Privacy is an important design consideration for Drishti-Flow.

- Webcam processing is performed locally by the application.
- Captured snapshots are displayed from memory rather than intentionally written to disk.
- The current prototype does not implement cloud-based image uploads or remote monitoring.

Operating-system camera permissions and other applications accessing the webcam remain outside the application's control.

## 🗺️ Roadmap

- [x] Webcam capture and landmark detection
- [x] Hand-to-nose proximity detection
- [x] Persistence and cooldown logic
- [x] Snapshot-based awareness interruption
- [ ] Expand and validate multi-region face-touch detection
- [ ] Add phone-reaching detection
- [ ] Reduce false positives during ordinary gestures
- [ ] Build a desktop control panel with Start, Pause, and Stop
- [ ] Add configurable sensitivity and habit preferences
- [ ] Evaluate detection reliability across different users and environments
- [ ] Improve documentation and prepare a stable release

## ⚠️ Limitations

Drishti-Flow is an experimental prototype, not a clinically validated behavioral intervention system.

- Proximity-based detection cannot reliably distinguish intentional habits from ordinary gestures in every situation.
- Detection performance depends on lighting, camera angle, landmark visibility, and threshold calibration.
- Phone-reaching detection has not yet been implemented in the current prototype.
- The system may generate false positives or miss genuine behaviors.

## 🤝 Contributing

Contributions, ideas, and feedback are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Submit a pull request describing the changes.

## 📄 License

No license has been specified yet. Until a license is added to the repository, permission to reuse, distribute, or modify this project should not be assumed.

---

**Drishti-Flow** — Building awareness, one moment at a time.
