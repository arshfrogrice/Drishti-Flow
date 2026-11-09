"""Persistence/counter logic and the established Gaussian-blur intervention."""

from dataclasses import dataclass
import cv2

from config import HABITS, NAIL, HOLD_SECONDS, NAIL_HOLD_SECONDS, BLUR_STRENGTH


@dataclass(frozen=True)
class DetectionState:
    candidate: str | None
    confirmed: bool
    new_event: bool


class EpisodeTracker:
    def __init__(self):
        self.counts = {label: 0 for label in HABITS}
        self.candidate = None
        self.since = None
        self._counted = False

    def reset_candidate(self):
        """Forget an unfinished gesture, e.g. when user pauses monitoring."""
        self.candidate = None
        self.since = None
        self._counted = False

    def reset_session(self):
        self.counts = {label: 0 for label in HABITS}
        self.reset_candidate()

    def update(self, candidate, now):
        if candidate != self.candidate:
            self.candidate = candidate
            self.since = now if candidate is not None else None
            self._counted = False

        hold = NAIL_HOLD_SECONDS if candidate == NAIL else HOLD_SECONDS
        confirmed = (
            candidate is not None
            and self.since is not None
            and now - self.since >= hold
        )
        new_event = bool(confirmed and not self._counted)
        if new_event:
            self.counts[candidate] += 1
            self._counted = True
        return DetectionState(candidate, confirmed, new_event)


def apply_blur(frame_bgr):
    """Only blurs the webcam feed shown in the app—not the whole desktop."""
    return cv2.GaussianBlur(frame_bgr, (BLUR_STRENGTH, BLUR_STRENGTH), 0)
