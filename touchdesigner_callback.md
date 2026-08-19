# TouchDesigner OSC Callback — Final Working Version

This is the Python code that goes inside the `oscin1_callbacks` Text DAT
node in your TouchDesigner project (NOT a file you run separately — copy
this INTO that node's text editor in TouchDesigner).

It receives live data from live_app.py (sign recognition, sentence
buffer, completed sentences) and writes it into three Text TOP nodes so
they display live on screen.

## Setup this depends on:
- An "OSC In DAT" node named `oscin1`, listening on port 7000
  (Protocol: Messaging (UDP), matches OSC_PORT in live_app.py)
- Three Text TOP nodes in your network, named EXACTLY:
  - `current_sign`
  - `buffer_text`
  - `final_sentence`
  (Names must match exactly — this was the bug we hit: a node named
  `buffer_txt` instead of `buffer_text` silently didn't update.)

## The code (paste into oscin1_callbacks):

```python
def onReceiveOSC(dat, rowIndex, message, bytes, timeStamp, address, args, peer):
	val = str(args[0]) if args else ''
	targets = {'/sign/current': 'current_sign', '/sign/buffer': 'buffer_text', '/sentence/final': 'final_sentence'}
	if address in targets:
		op(targets[address]).par.text = val
	return
```

## Notes on what each part does:
- `onReceiveOSC(...)` — this exact function name and signature is what
  TouchDesigner's OSC In DAT automatically calls whenever a new OSC
  message arrives. Don't rename it.
- `val = str(args[0]) if args else ''` — pulls out the actual data sent
  (e.g. "WATER" or "I need water.") from the incoming message.
- `targets = {...}` — maps each OSC address (matches what live_app.py
  sends) to the TouchDesigner node that should display it.
- `op(targets[address]).par.text = val` — writes the value into that
  node's Text parameter. Note: `.par.text` (not just `.text`) is
  required specifically because these are Text TOP nodes — Text DAT
  nodes would use `.text` directly instead.

## Common issues we hit while setting this up (for reference):
1. **"Input DAT must be text only"** — happened when a manually-created
   DAT Execute node was pointed at the OSC In DAT's raw output. Fixed by
   using the OSC In DAT's own auto-generated `oscin1_callbacks` node
   instead, with the `onReceiveOSC` signature above.
2. **SyntaxError from code on one line** — happened when pasting
   collapsed all the code onto a single line, losing line breaks/
   indentation. Fixed by typing the code manually with real Enter presses
   between lines and consistent Tab indentation.
3. **AttributeError: 'td.textTOP' object has no attribute 'text'** —
   happened because Text TOPs need `.par.text`, not `.text` directly
   (that's for Text DATs). Fixed by adding `.par`.
4. **One field silently not updating (no error)** — happened because the
   actual TouchDesigner node name (`buffer_txt`) didn't exactly match the
   name used in the `targets` dict (`buffer_text`). Node names must match
   EXACTLY, character for character.
