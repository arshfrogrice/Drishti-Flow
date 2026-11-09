# Drishti-Flow 🧠👁️

**A real-time, computer-vision-based habit awareness and pattern interruption system.**

Drishti-Flow is a Python desktop application designed to help users become more aware of repetitive, unconscious behaviors through real-time webcam monitoring and immediate visual feedback.

Using computer vision and facial/hand landmark detection, the application identifies potential habit-related gestures and temporarily blurs the live camera preview to interrupt the behavior and encourage conscious awareness.

> **Pause. Notice the moment.**

## ✨ Features

- **Real-Time Webcam Monitoring** — Uses OpenCV and MediaPipe to continuously track facial and hand landmarks.
- **Nose-Fingering Detection** — Detects fingertip proximity to the nose.
- **Face-Touch Detection** — Monitors hand proximity to facial regions such as the cheeks, forehead, and chin.
- **Possible Nail-Biting Detection** — Uses fingertip-to-mouth proximity and hand-position heuristics to identify potential nail-biting gestures.
- **Persistence-Based Detection** — Requires a gesture to remain detectable for a minimum duration before triggering an intervention.
- **Gaussian Blur Intervention** — Temporarily blurs the webcam preview when a potential habit is detected.
- **Interactive Desktop Dashboard** — Provides a graphical interface for monitoring and controlling detection.
- **Individual Habit Controls** — Allows users to enable or disable specific habit detectors.
- **Adjustable Sensitivity** — Provides a sensitivity slider for tuning detection thresholds.
- **Session Statistics** — Displays habit detection counts, session duration, detection status, and the most recent detection.
- **Local Processing** — Processes webcam frames locally without requiring cloud connectivity.

## 🎯 Project Goals

Drishti-Flow explores how computer vision and real-time visual interventions can improve awareness of repetitive physical habits.

The primary objectives are:

1. Identify potential unconscious habit-related gestures using facial and hand landmarks.
2. Provide immediate visual feedback through a non-auditory pattern interruption.
3. Allow users to customize which behaviors are monitored.
4. Maintain a modular architecture that supports additional detection algorithms.
5. Evaluate detection reliability and reduce false positives during ordinary movements.

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core application development |
| OpenCV | Webcam capture, frame processing, and Gaussian blur |
| MediaPipe | Hand and facial landmark detection |
| NumPy | Numerical computations and landmark distance calculations |
| CustomTkinter | Desktop graphical user interface |
| Pillow | Image conversion, resizing, and GUI display |
| Git & GitHub | Version control and collaboration |

## ⚙️ Current Implementation

The application currently supports three categories of habit-related gesture detection.

### 1. Nose-Fingering Detection

Tracks the distance between detected fingertips and selected nose landmarks.

When the hand remains sufficiently close to the nose for the configured duration, the system registers a potential nose-fingering event.

### 2. Face-Touch Detection

Monitors fingertip proximity to multiple facial regions, including the cheeks, forehead, and chin.

The system identifies potential face-touching behavior using normalized landmark distances and persistence thresholds.

### 3. Possible Nail-Biting Detection

Analyzes fingertip proximity to the mouth and relative finger positioning.

Because webcam-based proximity measurements cannot conclusively determine whether a person is biting their nails, this detector identifies **possible nail-biting gestures**, rather than confirmed nail-biting events.

### Detection Pipeline

1. Capture a frame from the webcam using OpenCV.
2. Detect facial and hand landmarks using MediaPipe.
3. Calculate normalized distances between fingertips and relevant facial landmarks.
4. Evaluate the selected habit-specific detection conditions.
5. Apply persistence checks to reduce brief, accidental triggers.
6. Register a detection event and update the session statistics.
7. Apply Gaussian blur to the live webcam preview as a visual interruption.
8. Resume normal monitoring when the intervention conditions are no longer active.

## 🖥️ Desktop Interface

Drishti-Flow includes a dark-themed desktop dashboard developed using CustomTkinter.

The interface provides:

- A live webcam preview.
- Start, Pause, and Stop controls.
- Individual toggles for the three habit detectors.
- An adjustable detection sensitivity slider.
- Habit-wise detection counters.
- A session timer.
- Current detection status.
- Most recent detection information.

The webcam preview uses aspect-ratio-preserving center cropping to fill the available display area without stretching the image.

## 📁 Project Structure

```text
Drishti-Flow/
├── main.py
├── interface.py
├── detector.py
├── intervention.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
└── tests/
    └── test_intervention.py
```

### Module Responsibilities

| File | Responsibility |
|---|---|
| `main.py` | Application entry point |
| `interface.py` | Desktop dashboard, webcam display, and user controls |
| `detector.py` | MediaPipe landmark processing and habit detection |
| `intervention.py` | Persistence tracking, event counting, and Gaussian blur |
| `config.py` | Application settings, labels, colors, and detection thresholds |
| `requirements.txt` | Python dependencies |
| `tests/test_intervention.py` | Tests for intervention-related logic |

This modular structure separates detection algorithms, intervention logic, and interface components to improve maintainability and extensibility.

## 🚀 Getting Started

### Prerequisites

- Python 3.12
- A functioning webcam
- Git
- Windows or macOS

### 1. Clone the Repository

```bash
git clone https://github.com/arshfrogrice/Drishti-Flow.git
cd Drishti-Flow
```

### 2. Create a Virtual Environment

**Windows:**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
```

**macOS:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The dependency file should include compatible versions of OpenCV, MediaPipe, NumPy, Pillow, and CustomTkinter.

### 4. Run the Application

```bash
python main.py
```

Allow webcam access if requested by your operating system.

### 5. Using the Dashboard

1. Launch the application.
2. Select the habits you want to monitor.
3. Adjust the sensitivity if required.
4. Click **Start** to begin webcam monitoring.
5. Observe the live preview and detection statistics.
6. Use **Pause** to temporarily suspend monitoring or **Stop** to end the session.

## 🔧 Configuration

Application settings and detection parameters are maintained in `config.py`.

The system includes configurable parameters for:

- Nose proximity detection.
- Face-touch proximity detection.
- Possible nail-biting detection.
- Gesture persistence duration.
- Detection sensitivity.
- Gaussian blur strength.
- Camera and interface settings.

The sensitivity slider provides an interface-level method for adjusting detection behavior.

Detection thresholds may require calibration depending on camera positioning, user distance, lighting, and landmark visibility.

## 🔒 Privacy

Drishti-Flow is designed around local webcam processing.

- Webcam frames are processed on the user's device.
- The current implementation does not require an internet connection for detection.
- The application does not intentionally upload webcam footage to a remote server.
- The current implementation does not include cloud-based image storage or remote monitoring.

Camera access permissions and security settings remain subject to the user's operating system.

## 🗺️ Roadmap

- [x] Webcam capture and landmark detection
- [x] Nose-fingering detection
- [x] Multi-region face-touch detection
- [x] Possible nail-biting detection
- [x] Persistence-based event tracking
- [x] Gaussian blur intervention
- [x] Modular Python architecture
- [x] CustomTkinter desktop dashboard
- [x] Start, Pause, and Stop controls
- [x] Individual habit selection
- [x] Adjustable detection sensitivity
- [x] Session statistics and detection counters
- [ ] Quantitative false-positive and false-negative evaluation
- [ ] Detection performance testing across multiple users
- [ ] Phone-reaching detection
- [ ] Improved nail-biting gesture classification
- [ ] Session analytics and historical trends
- [ ] Optional cloud integration for non-image session metrics
- [ ] Application packaging and distribution

## ⚠️ Limitations

Drishti-Flow is an experimental prototype and is not a clinically validated behavioral intervention system.

- Landmark proximity alone cannot conclusively establish that a particular habit is occurring.
- Possible nail-biting detection is heuristic-based and may confuse ordinary hand-to-mouth gestures with nail biting.
- Detection accuracy depends on lighting, webcam position, hand visibility, and facial landmark quality.
- Temporary occlusion and rapid movement can cause missed detections.
- False positives may occur during ordinary facial gestures.
- The effectiveness of Gaussian blur as a behavioral intervention has not yet been established through controlled user testing.
- Phone-reaching detection and cloud-based analytics have not yet been implemented.

## 🤝 Contributing

Contributions, ideas, and feedback are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Submit a pull request describing the modifications.

## 📄 License

No license has been specified yet. Until a license is added, permission to reuse, distribute, or modify the project should not be assumed.

---

**Drishti-Flow** — Building awareness, one moment at a time.
