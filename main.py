
import cv2
import mediapipe as mp
import math
import time
import tkinter as tk

from collections import deque
from PIL import Image, ImageTk


# ---------------- CONFIGURATION ----------------

NEAR_DISTANCE = 0.02
APPROACH_DISTANCE = 0.30

PERSISTENCE_SECONDS = 0.5
APPROACH_DELTA = 0.015

COOLDOWN_SECONDS = 2.0
SMOOTHING_FRAMES = 5

PANEL_WIDTH = 400
PANEL_HEIGHT = 300


# ---------------- DISTANCE CALCULATION ----------------

def landmark_distance(point_a, point_b, frame_width, frame_height):
    """Calculate normalized 2D distance between landmarks."""
    dx = (point_a.x - point_b.x) * frame_width
    dy = (point_a.y - point_b.y) * frame_height

    diagonal = math.sqrt(frame_width**2 + frame_height**2)

    return math.sqrt(dx**2 + dy**2) / diagonal


# ---------------- SNAPSHOT SIDE PANEL ----------------

class SnapshotPanel:
    def __init__(self, root):
        self.root = root
        self.snapshot_window = None
        self.image_label = None
        self.photo = None
        self.status_label = None

    def show(self, frame):
        """Display a temporary snapshot without saving it to disk."""

        # Avoid replacing a snapshot that is already visible.
        if (
            self.snapshot_window is not None
            and self.snapshot_window.winfo_exists()
        ):
            return

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
            font=("Segoe UI", 15, "bold"),
            fg="white",
            bg="#171717",
        ).pack(pady=(15, 5))

        tk.Label(
            window,
            text="A possible hand-to-face habit was detected.",
            font=("Segoe UI", 10),
            fg="#cccccc",
            bg="#171717",
        ).pack(pady=(0, 12))

        # Keep the snapshot in memory only.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        image.thumbnail((PANEL_WIDTH, PANEL_HEIGHT))

        self.photo = ImageTk.PhotoImage(image=image)

        self.image_label = tk.Label(
            window,
            image=self.photo,
            bg="#171717",
        )
        self.image_label.pack(padx=10, pady=5)

        self.status_label = tk.Label(
            window,
            text="Take a breath. Then return to your task.",
            font=("Segoe UI", 10),
            fg="#eeeeee",
            bg="#171717",
        )
        self.status_label.pack(pady=8)

        tk.Button(
            window,
            text="Dismiss and continue",
            command=self.dismiss,
            font=("Segoe UI", 10, "bold"),
            bg="#2d6a4f",
            fg="white",
            activebackground="#40916c",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=7,
        ).pack(pady=(0, 12))

    def dismiss(self):
        """Close the panel and release the temporary snapshot."""

        if self.snapshot_window is not None:
            try:
                if self.snapshot_window.winfo_exists():
                    self.snapshot_window.destroy()
            except tk.TclError:
                pass

        self.snapshot_window = None
        self.image_label = None
        self.status_label = None
        self.photo = None

    def close(self):
        self.dismiss()


# ---------------- MAIN APPLICATION ----------------

def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
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

    # Tkinter side panel
    root = tk.Tk()
    root.withdraw()

    snapshot_panel = SnapshotPanel(root)

    distances = deque(maxlen=SMOOTHING_FRAMES)

    near_since = None
    last_alert_time = float("-inf")
    previous_distance = None

    # Only one snapshot per continuous near-face episode.
    triggered_this_episode = False

    status = "Waiting for face and hand"

    print("Drishti-Flow | Milestone 3")
    print("Press Q in the webcam window to quit.")

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

            current_distance = None

            # -------- DRAW FACE LANDMARKS --------

            if face_detected:
                for face_landmarks in face_results.multi_face_landmarks:
                    mp_drawing.draw_landmarks(
                        image=frame,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing.DrawingSpec(
                            color=(0, 255, 0),
                            thickness=1,
                            circle_radius=1,
                        ),
                    )

            # -------- HAND DETECTION --------

            if face_detected and hands_detected:
                face = face_results.multi_face_landmarks[0].landmark
                nose = face[1]

                fingertip_ids = [4, 8, 12, 16, 20]
                candidate_distances = []

                for hand in hand_results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand,
                        mp_hands.HAND_CONNECTIONS,
                    )

                    for idx in fingertip_ids:
                        tip = hand.landmark[idx]

                        distance = landmark_distance(
                            tip, nose, width, height
                        )
                        candidate_distances.append(distance)

                if candidate_distances:
                    current_distance = min(candidate_distances)

            elif hands_detected:
                for hand in hand_results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame,
                        hand,
                        mp_hands.HAND_CONNECTIONS,
                    )

            # -------- HABIT DETECTION --------

            now = time.monotonic()
            trigger_snapshot = False

            if current_distance is None:
                distances.clear()
                near_since = None
                previous_distance = None
                triggered_this_episode = False

                status = "Waiting for face and hand"

            else:
                distances.append(current_distance)
                smooth_distance = sum(distances) / len(distances)

                approaching = (
                    previous_distance is not None
                    and smooth_distance
                    < previous_distance - APPROACH_DELTA
                )

                if smooth_distance <= NEAR_DISTANCE:

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
                        # Capture the frame at the detection moment.
                        trigger_snapshot = True

                        last_alert_time = now
                        triggered_this_episode = True

                        status = "POSSIBLE HABIT DETECTED"

                    elif triggered_this_episode:
                        status = "Snapshot triggered"

                    elif duration >= PERSISTENCE_SECONDS:
                        status = "Near face - cooldown"

                    else:
                        status = "Hand near face - checking"

                else:
                    near_since = None
                    triggered_this_episode = False

                    if (
                        smooth_distance <= APPROACH_DISTANCE
                        and approaching
                    ):
                        status = "Hand approaching face"
                    else:
                        status = "No trigger"

                previous_distance = smooth_distance

                cv2.putText(
                    frame,
                    f"Distance: {smooth_distance:.3f}",
                    (20, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 0),
                    2,
                )

            # -------- CAPTURE AND DISPLAY SNAPSHOT --------

            if trigger_snapshot:
                # This is a copy of the current annotated webcam frame.
                # It is displayed from memory and never written to disk.
                snapshot = frame.copy()
                snapshot_panel.show(snapshot)

            # Process popup events without blocking webcam processing.
            try:
                root.update()
            except tk.TclError:
                pass

            # -------- STATUS DISPLAY --------

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
                f"Hand: {'Yes' if hands_detected else 'No'}",
                (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0) if hands_detected else (0, 0, 255),
                2,
            )

            cv2.putText(
                frame,
                status,
                (20, height - 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 0, 255)
                if status == "POSSIBLE HABIT DETECTED"
                else (255, 255, 255),
                2,
            )

            cv2.imshow("Drishti-Flow | Habit Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        snapshot_panel.close()
        root.destroy()

        cap.release()
        face_mesh.close()
        hands.close()

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
