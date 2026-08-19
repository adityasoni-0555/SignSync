"""
hand_tracker.py — shared hand-tracking helper.

MediaPipe changed how hand tracking works in newer versions (the old
`mp.solutions.hands` method was retired). This file uses the current,
correct method (called the "Tasks API") and gives collect_data.py and
live_app.py a simple function to call, so neither of those files needs
to deal with MediaPipe's setup details directly.

On first run, this automatically downloads a small model file
(hand_landmarker.task, a few MB) from Google — this needs internet
ONE TIME only; after that it's saved locally and reused.
"""

import os
import urllib.request
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

MODEL_PATH = "hand_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

# 21 hand landmark connections, for drawing the skeleton overlay on screen.
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index finger
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle finger
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring finger
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky finger
    (0, 17),                                 # palm base
]


def _ensure_model_downloaded():
    if not os.path.isfile(MODEL_PATH):
        print("Downloading hand-tracking model (one-time, needs internet)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded.")


def create_hand_landmarker():
    """Creates and returns a ready-to-use hand landmark detector."""
    _ensure_model_downloaded()
    base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
    options = mp_vision.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
        min_tracking_confidence=0.6,
    )
    return mp_vision.HandLandmarker.create_from_options(options)


def detect_landmarks(landmarker, frame_bgr):
    """
    Runs hand detection on one BGR OpenCV frame.
    Returns (landmarks_list_or_None, flat_63_value_vector_or_None).
    landmarks_list is the raw list of 21 (x, y, z) points, useful for drawing.
    flat vector is what the classifier model expects as input.
    """
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect(mp_image)

    if not result.hand_landmarks:
        return None, None

    hand = result.hand_landmarks[0]  # first detected hand
    flat_vector = []
    for lm in hand:
        flat_vector.extend([lm.x, lm.y, lm.z])

    return hand, flat_vector


def draw_landmarks(frame_bgr, hand_landmarks):
    """Draws the hand skeleton onto the frame for the on-screen preview."""
    if hand_landmarks is None:
        return
    h, w, _ = frame_bgr.shape
    points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]

    for start_idx, end_idx in HAND_CONNECTIONS:
        cv2.line(frame_bgr, points[start_idx], points[end_idx], (0, 255, 0), 2)
    for x, y in points:
        cv2.circle(frame_bgr, (x, y), 4, (0, 200, 255), -1)
