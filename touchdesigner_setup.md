# TouchDesigner Visual Layer — Setup Guide

Since you already know TouchDesigner, this is a straight node-graph spec,
not a beginner walkthrough. `live_app.py` sends live data over OSC to
`127.0.0.1:7000`. Build a network in TD to receive and display it.

## 1. Install python-osc (Python side, one-time)
```
py -3.11 -m pip install python-osc
```

## 2. OSC messages you'll receive in TD

| Address              | Type   | Sent when                                  |
|-----------------------|--------|---------------------------------------------|
| `/sign/current`        | string | every frame — the sign being recognized now |
| `/sign/confidence`      | float  | every frame — 0.0 to 1.0                     |
| `/sign/buffer`          | string | whenever a new word commits to the sentence  |
| `/sentence/final`        | string | when a sentence completes (SPACE or PAUSE)   |

## 3. TouchDesigner network to build

**Receiving the data:**
- Add an **OSC In CHOP**. Set `Network Port` to `7000` (must match `OSC_PORT`
  in `live_app.py`). Set `Local Address` to blank or `127.0.0.1`.
- OSC In CHOP gives you channels named after the OSC addresses (with `/`
  replaced by `:` or similar depending on TD version — check the CHOP's
  channel names in the viewer once data is flowing).
- Since these are mostly strings (sign name, sentence), you'll actually
  want an **OSC In DAT** instead of/alongside the CHOP for the string
  payloads — DAT gives you a table of incoming messages you can parse
  with a small Python **DAT Execute** or **CHOP Execute** callback to pull
  out the latest value per address into Table DATs or dedicated storage
  (e.g. `op('osc_in1')` rows filtered by address column).

**Suggested simple approach (robust, not overengineered):**
1. **OSC In DAT** — receives raw messages as a growing/rolling table (address, args).
2. A short **Text DAT (Python)** callback (`onReceive` or per-frame `Execute DAT`)
   that reads the latest row for each address and stores it in 4 small
   **Text DATs** or **Table DAT** cells: `current_sign`, `confidence`,
   `buffer_text`, `final_sentence`.
3. Bind those to **Text TOPs** for on-screen display:
   - `current_sign` → small text, top-left, shows what's being signed live
   - `buffer_text` → larger text, shows the sentence-in-progress
   - `final_sentence` → largest/centered text, appears + animates in when
     a sentence completes (trigger a **Fade TOP** or opacity animation off
     the `final_sentence` DAT changing)
4. Optional: drive a **Circle TOP** or glow/pulse effect off `confidence`
   value, so there's a live visual "recognition strength" indicator.
5. Optional: layer the actual webcam feed underneath using a **Video
   Device In TOP** (same webcam index as `cv2.VideoCapture(0)` in Python —
   note both Python and TD can't lock the SAME camera device at once on
   most systems, so either: (a) only Python opens the camera and TD only
   shows text/graphics without camera, which is simpler and avoids
   conflicts — recommended for the demo — or (b) use a virtual
   camera splitter tool if you want the feed in both places.

**Recommended for your timeline:** keep it to text + simple animated
graphics driven by the OSC data (steps 1-4), skip the dual-camera-feed
complexity (step 5) unless you have real time to spare — text/graphics
alone already looks far more "designed" than a command prompt or bare
OpenCV window, and it's the lower-risk way to hit a polished result.

## 4. Running both together for the demo
1. Open your TouchDesigner project first, make sure OSC In CHOP/DAT show
   "connected"/listening on port 7000.
2. Then run `py -3.11 live_app.py` — TD should start updating live as you sign.
3. Keep the OpenCV window (from live_app.py) either minimized or on a
   second monitor if you don't want judges seeing the raw debug view —
   TD window is your "front of house" display.

## 5. If OSC isn't arriving
- Confirm `OSC_PORT` in `live_app.py` (default 7000) matches TD's OSC In
  CHOP/DAT port exactly.
- Confirm `python-osc` installed under the SAME Python you're running
  live_app.py with (`py -3.11 -m pip install python-osc`).
- Firewall: Windows may prompt to allow Python network access the first
  time — allow it (this is local-only traffic, 127.0.0.1, not going out
  to the internet).
