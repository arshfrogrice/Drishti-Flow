import cv2
import mediapipe as mp
import math
import time
import tkinter as tk
from collections import deque
from PIL import Image, ImageTk


# ---------------- CONFIGURATION ----------------

# Normalized distances relative to the webcam frame diagonal.
# Tune these values for your camera position and distance from the screen.
FACE_TOUCH_DISTANCE = 0.035
PERSISTENCE_SECONDS = 0.5
COOLDOWN_SECONDS = 2.0
SMOOTHING_FRAMES = 5
RESET_DISTANCE = 0.045

PANEL_WIDTH = 400
PANEL_HEIGHT = 300

# MediaPipe Face Mesh landmark IDs representing broad facial regions.
# These are approximate anchor points, not precise face-region boundaries.
FACE_REGIONS = {
    "nose": 1,
    "mouth": 13,
    "chin": 152,
    "left cheek": 234,
    "right cheek": 454,
}

FINGERTIP_IDS = [4, 8, 12, 16, 20]


# ---------------- DISTANCE CALCULATION ----------------

def landmark_distance(point_a, point_b, frame_width, frame_height):
    """Calculate normalized 2D distance between two MediaPipe landmarks."""
    dx = (point_a.x - point_b.x) * frame_width
    dy = (point_a.y - point_b.y) * frame_height
    diagonal = math.sqrt(frame_width**2 + frame_height**2)
    return math.sqrt(dx**2 + dy**2) / diagonal


def closest_hand_to_face(hand_results, face_landmarks, frame_width, frame_height):
    """Return (minimum distance, region name) across fingertips and face anchors."""
    candidates = []
    face = face_landmarks.landmark

    for region_name, landmark_id in FACE_REGIONS.items():
        region_point = face[landmark_id]
        for hand in hand_results.multi_hand_landmarks or []:
            for fingertip_id in FINGERTIP_IDS:
                fingertip = hand.landmark[fingertip_id]
                distance = landmark_distance(
                    fingertip, region_point, frame_width, frame_height
                )
                candidates.append((distance, region_name))

    if not candidates:
        return None, None

    return min(candidates, key=lambda item: item[0])


# ---------------- SNAPSHOT SIDE PANEL ----------------

class SnapshotPanel:
    def __init__(self, root):
        self.root = root
        self.snapshot_window = None
        self.image_label = None
        self.photo = None

    def show(self, frame, region_name):
        """Display a temporary snapshot in memory; never save it to disk."""
        if self.snapshot_window is not None:
            try:
                if self.snapshot_window.winfo_exists():
                    return
            except tk.TclError:
                pass

        window = tk.Toplevel(self.root)
        self.snapshot_window = window
        window.title("Drishti-Flow | Pattern Interrupt")
        window.geometry("440x440")
        window.resizable(False, False)
        window.configure(bg="#171717")
        window.protocol("WM_DELETE_WINDOW", self.dismiss)

        tk.Label(
            window,
            text="PAUSE. NOTICE THE MOMENT.",
            font=("Arial", 15, "bold"),
            fg="white",
            bg="#171717",
        ).pack(pady=(15, 5))

        tk.Label(
            window,
            text=f"Possible hand-to-face movement: {region_name}.",
            font=("Arial", 10),
            fg="#cccccc",
            bg="#171717",
        ).pack(pady=(0, 12))

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        image.thumbnail((PANEL_WIDTH, PANEL_HEIGHT))
        self.photo = ImageTk.PhotoImage(image=image)

        self.image_label = tk.Label(window, image=self.photo, bg="#171717")
        self.image_label.pack(padx=10, pady=5)

        tk.Label(
            window,
            text="Take a breath. Then return to your task.",
            font=("Arial", 10),
            fg="#eeeeee",
            bg="#171717",
        ).pack(pady=8)

        tk.Button(
            window,
            text="Dismiss and continue",
            command=self.dismiss,
            font=("Arial", 10, "bold"),
            bg="#2d6a4f",
            fg="white",
            activebackground="#40916c",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=7,
        ).pack(pady=(0, 12))

    def dismiss(self):
        if self.snapshot_window is not None:
            try:
                if self.snapshot_window.winfo_exists():
                    self.snapshot_window.destroy()
            except tk.TclError:
                pass

        self.snapshot_window = None
        self.image_label = None
        self.photo = None

    def close(self):
        self.dismiss()


# ---------------- MAIN APPLICATION ----------------

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam. Check camera permissions.")
        return

    mp_face_mesh = mp.solutions.face_mesh
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    root = tk.Tk()
    root.withdraw()
    snapshot_panel = SnapshotPanel(root)

    distances = deque(maxlen=SMOOTHING_FRAMES)
    near_since = None
    last_alert_time = float("-inf")
    triggered_this_episode = False
    current_region = None
    status = "Waiting for face and hand"

    print("Drishti-Flow | Multi-region face-touch detection")
    print("Press Q in the webcam window to quit.")
    print("Snapshots are kept in memory only; they are not saved to disk.")

    try:
        while True:
            success, frame = cap.read()
            if not success:
                print("Error: Could not read webcam frame.")
                break

            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            face_results = face_mesh.process(rgb)
            hand_results = hands.process(rgb)
            rgb.flags.writeable = True

            face_detected = bool(face_results.multi_face_landmarks)
            hands_detected = bool(hand_results.multi_hand_landmarks)
            trigger_snapshot = False
            current_distance = None
            current_region = None

            if face_detected:
                for face_landmarks in face_results.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(
                            color=(0, 255, 0), thickness=1, circle_radius=1
                        ),
                    )

            if hands_detected:
                for hand in hand_results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, hand, mp_hands.HAND_CONNECTIONS
                    )

            if face_detected and hands_detected:
                current_distance, current_region = closest_hand_to_face(
                    hand_results,
                    face_results.multi_face_landmarks[0],
                    width,
                    height,
                )

            now = time.monotonic()

            if current_distance is None:
                distances.clear()
                near_since = None
                triggered_this_episode = False
                status = "Waiting for face and hand"
            else:
                distances.append(current_distance)
                smooth_distance = sum(distances) / len(distances)

                if smooth_distance <= FACE_TOUCH_DISTANCE:
                    if near_since is None:
                        near_since = now

                    duration = now - near_since
                    cooldown_finished = (
                        now - last_alert_time >= COOLDOWN_SECONDS
                    )

                    if (
                        duration >= PERSISTENCE_SECONDS
                        and cooldown_finished
                        and not triggered_this_episode
                    ):
                        trigger_snapshot = True
                        last_alert_time = now
                        triggered_this_episode = True
                        status = f"POSSIBLE FACE TOUCH: {current_region}"
                    elif triggered_this_episode:
                        status = f"Detected: {current_region}"
                    else:
                        status = f"Checking near {current_region}..."
                else:
                    # Reset the episode only after the hand moves clearly away.
                    if smooth_distance >= RESET_DISTANCE:
                        near_since = None
                        triggered_this_episode = False
                    else:
                        near_since = None

                    status = "Hand near face - checking" if smooth_distance < RESET_DISTANCE else "No face touch detected"

                cv2.putText(
                    frame,
                    f"Distance: {smooth_distance:.3f}",
                    (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2,
                )
                if current_region:
                    cv2.putText(
                        frame,
                        f"Closest region: {current_region}",
                        (20, 130),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 0),
                        2,
                    )

            if trigger_snapshot:
                snapshot_panel.show(frame.copy(), current_region or "face")

            try:
                root.update()
            except tk.TclError:
                pass

            cv2.putText(
                frame,
                f"Face: {'Yes' if face_detected else 'No'}",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0) if face_detected else (0, 0, 255),
                2,
            )
            cv2.putText(
                frame,
                f"Hands: {'Yes' if hands_detected else 'No'}",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0) if hands_detected else (0, 0, 255),
                2,
            )
            cv2.putText(
                frame,
                status[:55],
                (20, height - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 255) if status.startswith("POSSIBLE FACE TOUCH") else (255, 255, 255),
                2,
            )

            cv2.imshow("Drishti-Flow | Habit Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        snapshot_panel.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
        cap.release()
        face_mesh.close()
        hands.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()