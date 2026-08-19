# SignSync — Real-Time Sign Language to Speech/Text Translator

**Team VAIRABA** (a fearless mind) — Aarambh Hackathon
Problem Statement ID: AA004 | Theme: Open Innovation | Category: Software

A prototype system that recognizes hand signs in real time via webcam,
assembles them into natural English sentences, and converts them to
speech — built to demonstrate real-time sign-to-speech translation for
deaf/mute individuals.

## How it works

```
Webcam → MediaPipe hand tracking → ML classifier (per-sign recognition)
       → sentence buffer → grammar engine → text-to-speech
       → (optional) live visual layer in TouchDesigner via OSC
```

1. **Hand tracking** (`hand_tracker.py`) — uses MediaPipe's HandLandmarker
   (Tasks API) to extract 21 hand landmarks per frame from the webcam feed.
2. **Sign recognition** (`train_model.py` / `collect_data.py`) — a
   RandomForest classifier trained on landmark coordinates, mapping hand
   shapes to a custom 15-word gesture vocabulary. 99.33% test accuracy.
3. **Sentence generation** (`gloss_grammar.py`) — converts a sequence of
   recognized signs (gloss) into a natural English sentence. Tries an AI
   model (Claude) first for fully general grammar handling; falls back to
   a hand-written rule engine (handles tense, prepositions, and
   single-word inputs) if no internet/API credit is available.
4. **Speech output** — `pyttsx3` (offline text-to-speech).
5. **Visual layer** (optional) — `live_app.py` sends live recognition
   data to TouchDesigner over OSC for a polished on-screen display.

## Gesture vocabulary

`I, YOU, WANT, HAVE, GO, HELP, WATER, COLLEGE, CLASS, TOMORROW, TODAY,
HELLO, THANK_YOU, YES, NO`

Custom gestures were used (rather than real ISL) for the prototype phase,
chosen for maximum visual distinctness for reliable recognition. Real ISL
vocabulary is the scaling roadmap.

## Tech stack

- **Input / hand tracking:** OpenCV, MediaPipe
- **Gesture classification:** Python, scikit-learn
- **Grammar processing:** rule-based engine + optional LLM (Anthropic API)
- **Text-to-speech:** pyttsx3
- **Visual layer:** TouchDesigner (via OSC / python-osc)

## Setup

```bash
pip install -r requirements.txt
```

### 1. Record training data
```bash
python collect_data.py
```
Perform each gesture ~50 times when prompted (press SPACE to capture,
`n` for next gesture). Produces `gesture_data.csv`.

### 2. Train the classifier
```bash
python train_model.py
```
Produces `model.pkl`. Prints test accuracy.

### 3. (Optional) Enable AI-powered grammar
```bash
set ANTHROPIC_API_KEY=your-key-here      # Windows cmd
$env:ANTHROPIC_API_KEY="your-key-here"   # PowerShell
```
Requires `pip install anthropic` and API credit. Without this, the app
automatically uses the offline rule-based grammar engine instead — no
functionality is lost, just less general sentence coverage.

### 4. Run the live app
```bash
python live_app.py
```
Sign words one at a time (hold ~0.5s to commit). Press **SPACE** to
complete and speak the sentence, `c` to clear the buffer, `q` to quit.

### 5. (Optional) TouchDesigner visual layer
See `touchdesigner_setup.md` and `touchdesigner_callback.md` for the
TouchDesigner-side node graph and OSC receiver code.

## Project files

| File | Purpose |
|---|---|
| `hand_tracker.py` | MediaPipe hand-landmark detection helper |
| `collect_data.py` | Records labeled training samples from webcam |
| `train_model.py` | Trains the RandomForest sign classifier |
| `gloss_grammar.py` | Converts recognized sign sequences to natural sentences |
| `live_app.py` | Main live application (recognition + sentence + speech + OSC) |
| `touchdesigner_setup.md` | TouchDesigner node graph setup guide |
| `touchdesigner_callback.md` | OSC receiver Python code for TouchDesigner |

## Roadmap

- Expand from custom gestures to real ISL vocabulary
- Two-way communication (speech/text → sign)
- Multilingual output support
- Per-user calibration for individual signing styles
