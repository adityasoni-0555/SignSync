"""
STEP 5 — Live Prototype

Runs the full pipeline: webcam -> MediaPipe landmarks -> classifier ->
sentence buffer -> grammar -> on-screen text (+ optional TTS) -> optional
TouchDesigner visual layer over OSC.

Usage: python live_app.py
Requires: model.pkl (from train_model.py) and gloss_grammar.py in the same folder.

TOUCHDESIGNER (optional):
This app sends live data to TouchDesigner over OSC on 127.0.0.1:7000 if
python-osc is installed (pip install python-osc) and TouchDesigner is
running with a matching OSC In CHOP. If TouchDesigner isn't running, or
python-osc isn't installed, this is skipped automatically - the app still
works fully with just the OpenCV window. See touchdesigner_setup.md for
how to build the TouchDesigner side.

OSC messages sent:
  /sign/current      - the sign currently being recognized (string, per frame)
  /sign/confidence    - confidence of that recognition (0.0-1.0, per frame)
  /sign/buffer        - the sentence-in-progress word buffer (string)
  /sentence/final      - the completed, spoken sentence (string)

CONTROLS:
- Hold a gesture steady for ~0.5s to commit it to the sentence buffer.
- Show an open flat palm (held steady) to trigger "end of sentence":
  the buffer is converted to a sentence, shown on screen, and spoken (if TTS enabled).
- Press SPACE to manually complete the sentence and speak it.
- Press 'c' to clear the current buffer manually.
- Press 'q' to quit.
"""

import cv2
import pickle
import numpy as np
import hand_tracker
from collections import deque, Counter
from gloss_grammar import glosses_to_sentence

MODEL_PATH = "model.pkl"
STABLE_FRAMES = 15          # frames a prediction must hold to be "committed"
END_GESTURE_LABEL = "PAUSE" # add a "PAUSE" (flat open palm) gesture to your
                             # vocabulary in collect_data.py if you want this
CONFIDENCE_THRESHOLD = 0.6

# --- TouchDesigner connection (OSC) ---
# Sends live data to TouchDesigner for the visual layer. If TouchDesigner
# isn't running, or python-osc isn't installed, this is silently skipped -
# the app still works fully with just the OpenCV window either way.
OSC_ENABLED = True
OSC_IP = "127.0.0.1"   # "localhost" - TouchDesigner running on the SAME laptop
OSC_PORT = 7000        # must match the port TouchDesigner's OSC In CHOP listens on

try:
    from pythonosc import udp_client
    osc_client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT) if OSC_ENABLED else None
except Exception:
    osc_client = None
    print("python-osc not available — TouchDesigner visual layer will be skipped "
          "(the app still runs fully without it).")


def send_osc(address, value):
    """Sends one OSC message to TouchDesigner. Never crashes the app if it fails."""
    if osc_client is None:
        return
    try:
        osc_client.send_message(address, value)
    except Exception:
        pass  # TouchDesigner not listening - just skip silently, app keeps running

# Try to enable offline TTS; app still works without it.
try:
    import pyttsx3
    TTS_ENABLED = True
except Exception:
    TTS_ENABLED = False
    print("pyttsx3 not available — running without voice output (text only).")


def speak(text):
    """
    Speaks the given text aloud. Creates a FRESH pyttsx3 engine each call
    instead of reusing one - on Windows, reusing the same engine object
    across multiple runAndWait() calls often silently stops working after
    the first use. Creating a new one each time is slightly slower but
    reliable.
    """
    if not TTS_ENABLED or not text:
        return
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print("TTS error (continuing without voice for this sentence):", e)


def main():
    with open(MODEL_PATH, "rb") as f:
        clf = pickle.load(f)

    landmarker = hand_tracker.create_hand_landmarker()

    cap = cv2.VideoCapture(0)

    recent_predictions = deque(maxlen=STABLE_FRAMES)
    last_committed = None
    gloss_buffer = []
    current_sentence = ""

    print("Controls: hold a sign to commit it | c = clear buffer | q = quit")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        hand_landmarks, vec = hand_tracker.detect_landmarks(landmarker, frame)

        predicted_label = None

        if hand_landmarks is not None:
            hand_tracker.draw_landmarks(frame, hand_landmarks)

            vec = np.array(vec).reshape(1, -1)
            probs = clf.predict_proba(vec)[0]
            best_idx = np.argmax(probs)
            confidence = probs[best_idx]
            label = clf.classes_[best_idx]

            if confidence >= CONFIDENCE_THRESHOLD:
                predicted_label = label

        # Send live data to TouchDesigner every frame
        send_osc("/sign/current", predicted_label or "")
        send_osc("/sign/confidence", float(confidence) if hand_landmarks is not None else 0.0)

        recent_predictions.append(predicted_label)

        # Commit a gesture once it's stable across the recent window
        if len(recent_predictions) == STABLE_FRAMES:
            counts = Counter(recent_predictions)
            most_common, freq = counts.most_common(1)[0]
            if most_common is not None and freq == STABLE_FRAMES and most_common != last_committed:
                if most_common == END_GESTURE_LABEL:
                    if gloss_buffer:
                        current_sentence = glosses_to_sentence(gloss_buffer)
                        send_osc("/sentence/final", current_sentence)
                        speak(current_sentence)
                        gloss_buffer = []
                        send_osc("/sign/buffer", "")
                else:
                    gloss_buffer.append(most_common)
                    send_osc("/sign/buffer", " ".join(gloss_buffer))
                last_committed = most_common
            elif freq < STABLE_FRAMES:
                last_committed = None  # allow re-commit once hand changes

        # --- UI overlay ---
        cv2.putText(frame, f"Live sign: {predicted_label or '...'}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(frame, f"Buffer: {' '.join(gloss_buffer)}", (10, 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
        cv2.putText(frame, f"Sentence: {current_sentence}", (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, "SPACE=speak sentence  c=clear  q=quit", (10, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Sign to Speech Prototype", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            gloss_buffer = []
            current_sentence = ""
            send_osc("/sign/buffer", "")
            send_osc("/sentence/final", "")
        elif key == ord(' '):
            if gloss_buffer:
                current_sentence = glosses_to_sentence(gloss_buffer)
                print("Sentence:", current_sentence)
                send_osc("/sentence/final", current_sentence)
                speak(current_sentence)
                gloss_buffer = []
                send_osc("/sign/buffer", "")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
