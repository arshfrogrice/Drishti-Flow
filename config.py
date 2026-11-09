"""Single place for Drishti-Flow settings and human-readable labels."""

CAMERA_INDEX = 0
CAMERA_WIDTH = 960
CAMERA_HEIGHT = 540
FRAME_INTERVAL_MS = 30  # UI schedules the next frame after processing the last

NOSE_DISTANCE_THRESHOLD = 0.22
FACE_DISTANCE_THRESHOLD = 0.20
NAIL_DISTANCE_THRESHOLD = 0.16
NAIL_JOINT_TOLERANCE = 0.02

HOLD_SECONDS = 0.35
NAIL_HOLD_SECONDS = 0.65
BLUR_STRENGTH = 61  # Positive odd integer

NOSE = "Nose fingering"
FACE = "Face touching"
NAIL = "Possible nail biting"
HABITS = (NOSE, FACE, NAIL)

# UI preview is 16:9. Camera feeds are resized to fit without cropping.
PREVIEW_WIDTH = 800
PREVIEW_HEIGHT = 450

# Dark palette
BG = "#0B1120"
SURFACE = "#111C30"
PANEL = "#17253B"
BORDER = "#263851"
TEXT = "#EDF3FC"
MUTED = "#9BADBF"
ACCENT = "#4888F4"
SUCCESS = "#52D6A4"
WARNING = "#F5C06A"
DANGER = "#F3838F"
