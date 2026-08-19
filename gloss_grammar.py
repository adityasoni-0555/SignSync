"""
STEP 4 — Gloss-to-Sentence Grammar

This is your "NLP/semantics" layer. It has TWO modes:

1. ONLINE mode (preferred): sends the recognized words to an AI model which
   understands real English grammar - correctly handles tenses, articles,
   word order, and questions, even for combinations we never planned for.
   e.g. [I, TOMORROW, COLLEGE, GO] -> "I will go to college tomorrow."

2. OFFLINE fallback: if there's no internet, or the AI call fails or times
   out, it automatically falls back to simple hand-written rules below.
   These are more limited (fixed patterns only) but need zero internet.

You don't need to choose - the code tries mode 1 first, and only uses
mode 2 if mode 1 isn't available. This means your live demo never just
freezes or crashes if the venue wifi drops.

SETUP FOR ONLINE MODE:
1. Get a free API key from https://console.anthropic.com (takes ~5 min)
2. Install the SDK once: pip install anthropic
3. Set your key as an environment variable before running live_app.py:
   Windows (Command Prompt):  set ANTHROPIC_API_KEY=your-key-here
   Windows (PowerShell):      $env:ANTHROPIC_API_KEY="your-key-here"
   If you skip this setup entirely, the app still works - it just always
   uses offline mode.

EDIT THIS FILE to match your final gesture set from collect_data.py.
"""

import os

ONLINE_TIMEOUT_SECONDS = 3  # how long to wait for the AI before giving up

def _try_ai_sentence(glosses):
    """
    Attempt to build a natural sentence using the AI. Returns None if
    anything goes wrong (no internet, no API key, timeout, etc) so the
    caller can fall back to offline rules.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None  # no key set up - skip straight to offline mode

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key, timeout=ONLINE_TIMEOUT_SECONDS)
        word_list = ", ".join(glosses)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=60,
            messages=[{
                "role": "user",
                "content": (
                    f"These are sign-language gloss words in the order signed: {word_list}. "
                    "Sign language glosses drop small grammar words (like 'will', 'to', 'a', "
                    "'the', 'is', 'am') that a natural English sentence needs. Convert the "
                    "glosses into ONE short, fully natural, grammatically correct English "
                    "sentence - ADD any missing helper verbs, articles, and prepositions "
                    "needed, and fix tense based on time words (e.g. TOMORROW/TODAY). "
                    "Example: glosses 'I TOMORROW COLLEGE GO' -> \"I will go to college "
                    "tomorrow.\" Example: glosses 'I HAVE CLASS TODAY' -> \"I have class "
                    "today.\" Reply with ONLY the final sentence, nothing else - no quotes, "
                    "no explanation."
                )
            }]
        )
        text = response.content[0].text.strip()
        return text if text else None
    except Exception as e:
        # Any failure (no internet, timeout, bad key, etc) - fall back,
        # but print what went wrong so it's not a silent mystery.
        print(f"[AI mode unavailable, using offline fallback: {e}]")
        return None

# Map each gesture to a grammatical role. This offline engine now handles
# tense (TOMORROW -> "will ...") and prepositions (GO -> "to ...")
# specifically for your fixed 15-word vocabulary, so it produces correct
# sentences even without internet/AI.
ROLES = {
    "I": "SUBJECT",
    "YOU": "SUBJECT",
    "WANT": "VERB",
    "HAVE": "VERB",
    "HELP": "VERB",
    "GO": "VERB",
    "WATER": "OBJECT",
    "COLLEGE": "OBJECT",
    "CLASS": "OBJECT",
    "TOMORROW": "TIME",
    "TODAY": "TIME",
    "YES": "AFFIRM",
    "NO": "NEGATE",
    "THANK_YOU": "PHRASE",
    "HELLO": "PHRASE",
}

# Fixed phrases that don't need reordering.
PHRASES = {
    "THANK_YOU": "Thank you.",
    "HELLO": "Hello.",
    "YES": "Yes.",
    "NO": "No.",
}

# Base (dictionary) form of each verb, used in both present and future tense.
VERB_BASE = {
    "WANT": "want",
    "HAVE": "have",
    "HELP": "help",
    "GO": "go",
}
# Verbs that need a preposition before their object (GO -> "to college").
VERB_PREPOSITIONS = {
    "GO": "to",
}

# Some verbs don't sound natural as "VERB + object" (e.g. "I help water"
# makes no sense) - override the whole verb phrase for these instead.
VERB_OBJECT_OVERRIDE = {
    "HELP": "need help with",
}

# When ONLY one of these verbs is signed by itself (no subject, no object),
# a bare verb alone isn't a natural sentence, so use a natural full phrase.
SOLO_VERB_PHRASES = {
    "HELP": "I need help.",
    "GO": "I want to go.",
    "WANT": "I want something.",
    "HAVE": "I have something.",
}

# When a SUBJECT or TIME word is signed completely alone, with nothing else.
SOLO_SUBJECT_PHRASES = {
    "I": "That's me.",
    "YOU": "That's you.",
}
SOLO_TIME_PHRASES = {
    "TOMORROW": "See you tomorrow.",
    "TODAY": "I am here today.",
}


def glosses_to_sentence(glosses):
    """
    Convert a list of recognized gloss labels (in the order signed)
    into a natural-language sentence string.

    Tries the AI (online) first for proper grammar handling. If that's
    not available for any reason (no internet, no credit, etc), falls
    back to the offline rule-based engine below, which is written
    specifically for this project's 15-word vocabulary and handles
    tense (TOMORROW/TODAY), prepositions, and single-word signs (assumes
    "I" as the signer and "need" as an implied verb when only a thing is
    signed, e.g. WATER alone -> "I need water.").
    """
    if not glosses:
        return ""

    ai_result = _try_ai_sentence(glosses)
    if ai_result:
        return ai_result

    # --- OFFLINE FALLBACK below (used whenever AI mode is unavailable) ---

    # Single-word special cases (fixed phrases, solo verbs, solo objects,
    # solo subjects, solo time words) — every one of the 15 words now
    # produces a real sentence even when signed completely alone.
    if len(glosses) == 1:
        word = glosses[0]
        if word in PHRASES:
            return PHRASES[word]
        if word in SOLO_VERB_PHRASES:
            return SOLO_VERB_PHRASES[word]
        if word in SOLO_SUBJECT_PHRASES:
            return SOLO_SUBJECT_PHRASES[word]
        if word in SOLO_TIME_PHRASES:
            return SOLO_TIME_PHRASES[word]
        if ROLES.get(word) == "OBJECT":
            return f"I need {word.lower()}."

    subject = next((g for g in glosses if ROLES.get(g) == "SUBJECT"), None)
    verb = next((g for g in glosses if ROLES.get(g) == "VERB"), None)
    obj = next((g for g in glosses if ROLES.get(g) == "OBJECT"), None)
    time_word = next((g for g in glosses if ROLES.get(g) == "TIME"), None)

    # Default to "I" as the signer whenever no subject was explicitly signed
    # (this is what lets things like WANT+WATER, without I/YOU, still form
    # a complete sentence).
    subject = subject or "I"

    # If there's an object but no verb was signed, imply "need"
    # (e.g. just WATER, or WATER+TODAY -> "I need water today.").
    if not verb and obj:
        verb_base = "need"
        prep = None
    elif verb and obj and verb in VERB_OBJECT_OVERRIDE:
        verb_base = VERB_OBJECT_OVERRIDE[verb]
        prep = None  # the phrase above already includes its own preposition
    elif verb:
        verb_base = VERB_BASE.get(verb, verb.lower())
        prep = VERB_PREPOSITIONS.get(verb)
    else:
        verb_base = None
        prep = None

    if verb_base:
        subj_word = "I" if subject == "I" else "You"

        # TOMORROW -> future tense ("will go"); TODAY or no time word -> present tense.
        if time_word == "TOMORROW":
            verb_phrase = f"will {verb_base}"
        else:
            verb_phrase = verb_base

        obj_phrase = ""
        if obj:
            obj_phrase = f" {prep} {obj.lower()}" if prep else f" {obj.lower()}"

        time_phrase = f" {time_word.lower()}" if time_word else ""

        return f"{subj_word} {verb_phrase}{obj_phrase}{time_phrase}."

    # Fallback: nothing meaningful matched (e.g. only a TIME word signed
    # alone) — just join glosses raw.
    return " ".join(g.capitalize() for g in glosses) + "."


if __name__ == "__main__":
    # quick manual test
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY found - will try AI mode first.\n")
    else:
        print("No ANTHROPIC_API_KEY set - running in offline mode only.\n")

    all_words = ["I", "YOU", "WANT", "HAVE", "GO", "HELP", "WATER",
                 "COLLEGE", "CLASS", "TOMORROW", "TODAY", "HELLO",
                 "THANK_YOU", "YES", "NO"]

    print("--- Every word signed ALONE ---")
    for w in all_words:
        print([w], "->", glosses_to_sentence([w]))

    print("\n--- Common combinations ---")
    tests = [
        ["I", "WANT", "WATER"],
        ["YOU", "WANT", "WATER"],
        ["I", "HAVE", "WATER"],
        ["YOU", "HELP"],
        ["I", "HELP"],
        ["I", "GO"],
        ["YOU", "GO"],
        ["I", "GO", "COLLEGE"],
        ["I", "TOMORROW", "COLLEGE", "GO"],
        ["YOU", "TOMORROW", "COLLEGE", "GO"],
        ["I", "HAVE", "CLASS", "TODAY"],
        ["YOU", "HAVE", "CLASS", "TOMORROW"],
        ["WANT", "WATER"],
        ["HAVE", "CLASS"],
        ["WATER", "TODAY"],
        ["HELP", "WATER"],
        ["I", "HELP", "CLASS"],
        ["HELP", "COLLEGE"],
        ["HELP", "CLASS", "TOMORROW"],
    ]
    for t in tests:
        print(t, "->", glosses_to_sentence(t))
