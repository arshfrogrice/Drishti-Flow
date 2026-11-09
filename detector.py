"""Real-time webcam frame analysis; independent from the GUI.

A 'possible nail biting' result is a fingertip-at-mouth *gesture candidate*,
not verified biting. MediaPipe Hands/Face Mesh are used on-device.
"""

import math
import cv2
import mediapipe as mp

from config import (
    NOSE, FACE, NAIL,
    NOSE_DISTANCE_THRESHOLD, FACE_DISTANCE_THRESHOLD,
    NAIL_DISTANCE_THRESHOLD, NAIL_JOINT_TOLERANCE,
)

FINGER_JOINTS = {4: 3, 8: 6, 12: 10, 16: 14, 20: 18}
NOSE_POINTS = (1, 4)
FACE_POINTS = (205, 425, 234, 454, 10, 152)
MOUTH_POINTS = (0, 13, 14, 17, 61, 291)


def pixel_distance(a, b, width, height):
    return math.hypot((a.x - b.x) * width, (a.y - b.y) * height)


def nearest_normalized_distance(point, face, indices, width, height, face_width):
    return min(
        pixel_distance(point, face[index], width, height) / face_width
        for index in indices
    )


def classify_gesture(face, hand_landmarks, width, height, sensitivity=1.0,
                     enabled=None):
    """Return a candidate label or None. Priority: mouth > nose > other face.

    Sensitivity scales geometric proximity thresholds; it doesn't change hold times.
    """
    if enabled is None:
        enabled = {NOSE, FACE, NAIL}

    face_width = max(pixel_distance(face[234], face[454], width, height), 1.0)
    near_nose = near_face = near_mouth = False

    for hand in hand_landmarks:
        landmarks = hand.landmark
        for tip_index, joint_index in FINGER_JOINTS.items():
            tip = landmarks[tip_index]

            if NOSE in enabled:
                nose_d = nearest_normalized_distance(
                    tip, face, NOSE_POINTS, width, height, face_width
                )
                if nose_d < NOSE_DISTANCE_THRESHOLD * sensitivity:
                    near_nose = True

            if FACE in enabled:
                face_d = nearest_normalized_distance(
                    tip, face, FACE_POINTS, width, height, face_width
                )
                if face_d < FACE_DISTANCE_THRESHOLD * sensitivity:
                    near_face = True

            if NAIL in enabled:
                mouth_d = nearest_normalized_distance(
                    tip, face, MOUTH_POINTS, width, height, face_width
                )
                joint_d = nearest_normalized_distance(
                    landmarks[joint_index], face, MOUTH_POINTS,
                    width, height, face_width
                )
                if (
                    mouth_d < NAIL_DISTANCE_THRESHOLD * sensitivity
                    and mouth_d <= joint_d + NAIL_JOINT_TOLERANCE
                ):
                    near_mouth = True

    if near_mouth:
        return NAIL
    if near_nose:
        return NOSE
    if near_face:
        return FACE
    return None


class HabitDetector:
    """Owns MediaPipe model instances and provides a per-frame candidate."""

    def __init__(self):
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        try:
            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        except Exception:
            self._hands.close()
            raise

    def process(self, frame_bgr, sensitivity=1.0, enabled=None):
        height, width = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        hands_result = self._hands.process(rgb)
        face_result = self._face_mesh.process(rgb)

        if not (hands_result.multi_hand_landmarks and
                face_result.multi_face_landmarks):
            return None

        return classify_gesture(
            face_result.multi_face_landmarks[0].landmark,
            hands_result.multi_hand_landmarks,
            width, height,
            sensitivity=sensitivity,
            enabled=enabled,
        )

    def close(self):
        self._hands.close()
        self._face_mesh.close()
