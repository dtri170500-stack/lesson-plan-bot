"""
Step 3 – Lesson Plan Writer
Reads _schedule.json + source markdown files,
generates detailed lesson plan .md files (V3 format) for each slot.
"""

import sys, os, json, re
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
INPUT_FOLDER   = WORKSPACE_ROOT / "Nhap hoc lieu pdf va docs"
if not INPUT_FOLDER.exists():
    INPUT_FOLDER = WORKSPACE_ROOT / "Nh\u1eadp h\u1ecdc li\u1ec7u pdf v\u00e0 docs"
CACHE_FOLDER  = INPUT_FOLDER / "markdown_cache"
OUTPUT_FOLDER = WORKSPACE_ROOT / "Output giao an docs"
if not OUTPUT_FOLDER.exists():
    OUTPUT_FOLDER = WORKSPACE_ROOT / "Output gi\u00e1o \u00e1n docs"
MD_OUT_FOLDER = OUTPUT_FOLDER / "markdown"
MD_OUT_FOLDER.mkdir(parents=True, exist_ok=True)

SCHED_PATH = OUTPUT_FOLDER / "_schedule.json"


def extract_topic(md_text: str, source_name: str) -> str:
    """Infer lesson topic from first heading or filename."""
    for line in md_text.splitlines():
        line = line.strip()
        if line.startswith("# ") and len(line) > 2:
            return line[2:].strip()
    # Fallback: humanize filename
    return source_name.replace("_", " ").replace("-", " ").title()


def extract_vocab(md_text: str, age: str) -> list:
    """Extract likely vocabulary words from markdown text."""
    # Simple heuristic: find capitalised words that appear multiple times
    words = re.findall(r'\b[A-Z][a-z]{2,12}\b', md_text)
    freq  = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    vocab = [w for w, c in sorted(freq.items(), key=lambda x: -x[1]) if c >= 2]
    return vocab[:8]


SONG_SUGGESTIONS = {
    "Math"          : "\"Five Little Ducks\" or \"10 in the Bed\" (YouTube: Super Simple Songs)",
    "Show and Tell" : "\"Head, Shoulders, Knees & Toes\" or a topic-specific Hello Song",
    "Happy Friday"  : "\"What I Am\" by will.i.am or a simple action song to start the experiment",
}

AGE_NOTES = {
    "2-3": "Very short attention span (5-8 min). Use single words only, lots of TPR and repetition. No written output.",
    "3-4": "Emerging attention (8-12 min). Introduce simple phrases. High scaffolding required at all times.",
    "4-5": "Growing confidence. Short sentences (3-5 words). Can do guided writing with a word bank.",
    "5-6": "Near-school readiness. Simple sentences independently. Peer discussion encouraged.",
}


def generate_lesson_md(slot: dict, age: str, lesson_n: int) -> str:
    """Generate a full lesson plan markdown for one slot."""
    subject = slot["subject"]
    source  = slot.get("source")
    week    = slot["week"]

    # Read source material
    if source:
        src_path = CACHE_FOLDER / f"{source}.md"
        md_text  = src_path.read_text(encoding="utf-8") if src_path.exists() else ""
    else:
        md_text = ""

    topic = slot.get("topic") or extract_topic(md_text, source or subject)
    vocab = extract_vocab(md_text, age)
    vocab_str = ", ".join(vocab) if vocab else "[Derive from worksheet content]"
    song  = SONG_SUGGESTIONS.get(subject, "A fun action song")

    # Durations by subject
    if subject == "Happy Friday":
        p1, p2, p3, p4 = "10 min", "15 min", "20 min", "10 min"
    else:
        p1, p2, p3, p4 = "8 min", "12 min", "25 min", "10 min"

    age_note = AGE_NOTES.get(age, "")

    # Montessori / age-based activity notes
    if age in ("2-3", "3-4"):
        practice_note = "Use high-scaffolding activities: matching pictures to words, colouring, simple tracing. No open-ended writing."
        tpr_note      = "Every new word must be introduced with a body action (TPR). Repeat each word 3 times with the action."
    else:
        practice_note = "Introduce sentence frames. Allow students to fill in blanks from a visible word bank."
        tpr_note      = "Use TPR for new vocabulary, then encourage students to say the word + a short phrase independently."

    # Happy Friday experiment scaffold
    hf_section = ""
    if subject == "Happy Friday":
        hf_section = f"""
#### Part 3: STEAM Experiment & Guided Practice ({p3})
* **Teacher Action:** Demonstrate the experiment step by step. Name each material aloud ("This is a cup. Cup. Everyone say: cup.")
* **TA Action:** Circulate and assist students who need 1-1 support. Monitor safety at all times.
* **Student Action:** Follow along with the experiment. Repeat key action words (pour, mix, stir).
* **Language Target:** "It [floats / sinks / changes colour / bubbles]!" – Teacher models, students echo.
* **Safety Note:** Ensure all materials are food-safe or non-toxic. TA stands beside any student who may put materials in their mouth. No sharp tools. Use child-safe scissors only under close TA supervision.
"""
    else:
        hf_section = f"""
#### Part 3: Guided Practice & Worksheet ({p3})
* **Teacher Action:** Distribute worksheet. Walk students through instructions using gesture and demonstration, not verbal explanation alone.
* **TA Action:** Sit with any student needing support. Prompt with the Word Mat – do not give answers directly.
* **Student Action:** Complete the worksheet at their own pace. Students who finish early may colour or trace bonus words.
* **Worksheet:** [Reference: {source or "worksheet from teacher materials"}]
* **Answer Key (for Teachers):** [Derive correct answers from worksheet content and vocabulary list above. Mark answers on teacher copy before lesson.]
* **Safety Note:** Child-safe scissors only, under close TA supervision if cutting activities are included.
"""

    title = f"{topic} – {subject} Lesson {lesson_n}"

    md = f"""<h1 align="center">{title}</h1>
<p align="center"><strong>Target Group:</strong> Age {age} | <strong>Week:</strong> {week} | <strong>Subject:</strong> {subject}</p>

---

## LESSON {lesson_n}: {topic.upper()}

### 1. LESSON OVERVIEW
* **Objectives:** By the end of the lesson, students will be able to recognise and use key vocabulary related to "{topic}". Students will participate in at least one communicative activity using target language.
* **Vocabulary:** {vocab_str}
* **Structures:** "This is a ___.", "I see a ___.", "It is ___." (adapt to age {age})
* **Materials:** Flashcards, Word Mat, coloured pencils, worksheet printouts, music speaker
* **Worksheet:** {source or "[MISSING – teacher to source appropriate worksheet]"}
* **Songs & Content:** {song}

> **Age note ({age}):** {age_note}

---

### 2. MONTESSORI & CLASSROOM MANAGEMENT NOTES
* **Montessori Principle:** Prepared environment – arrange flashcards and materials on trays at child height before students enter. Allow students to choose their work station (colouring corner vs. puzzle corner) within the structured task.
* **Self-Correction (Control of Error):** Provide a Word Mat face-down beside each student. Students may flip it to self-check their spelling or matching – teacher does not correct aloud.
* **Positive Discipline:** Use stickers and high-fives as rewards. Attention grabber: clap a rhythm and students clap back before key instructions.

---

### 3. STEP-BY-STEP PROCEDURE

#### Part 1: Warm-up & Song ({p1})
* **Teacher Action:** Greet students warmly at the door. Begin playing the warm-up song immediately. Demonstrate actions.
* **TA Action:** Help latecomers settle quickly. Sing and do actions alongside students to model.
* **Student Action:** Follow along with song actions. Repeat chorus phrases.
* **Safety Note:** Clear floor space before any movement activity. Push chairs under tables.

#### Part 2: New Words & Concepts ({p2})
* **Teacher Action:** Hold up flashcard for each vocabulary word. Say the word clearly 3 times. Use a real object (realia) where possible. {tpr_note}
* **TA Action:** Echo each word after the teacher. Observe which students are hesitant and note for differentiated support.
* **Student Action:** Repeat each word with the action. Volunteer students may come up and touch/point to the correct flashcard.
* **Safety Note:** Ensure flashcards with small pictures are held high enough for all students to see – do not leave small cards where toddlers could put them in mouths.
{hf_section}
#### Part 4: Review & Closing ({p4})
* **Teacher Action:** Lead a quick "Show Me" game – hold up a flashcard, students point to the corresponding item or mime the word. Give 3-4 rounds.
* **TA Action:** Begin tidying materials during the last 2 minutes. Lead a tidy-up song.
* **Student Action:** Help pack away worksheets and pencils. Line up for hand-washing.
* **Hygiene:** Students must wash hands after any lesson involving glue, paint, clay, or food materials.
* **Closing:** Teacher says goodbye in English. Students echo. End with a class cheer or high-five circle.

---
_Lesson plan generated by Agentic Workspace – {datetime.now().strftime("%Y-%m-%d")}_
"""
    return md


def main(age: str):
    if not SCHED_PATH.exists():
        print("[Step 3] ERROR: _schedule.json not found. Run Step 2 first.")
        return []

    data     = json.loads(SCHED_PATH.read_text(encoding="utf-8"))
    schedule = data["schedule"]

    lesson_counters = {}
    output_files    = []

    for slot in schedule:
        if slot["status"] == "MISSING":
            print(f"  [SKIP] {slot['week']} – {slot['subject']}: no material.")
            continue

        subj = slot["subject"]
        lesson_counters[subj] = lesson_counters.get(subj, 0) + 1
        n    = lesson_counters[subj]

        source = slot["source"] or subj
        topic  = slot.get("topic") or extract_topic(
            (CACHE_FOLDER / f"{source}.md").read_text(encoding="utf-8") if (CACHE_FOLDER / f"{source}.md").exists() else "",
            source
        )

        md_text  = generate_lesson_md(slot, age, n)
        # File name rule: [TOPIC] - Lesson [N].md
        safe_topic = re.sub(r'[\\/:*?"<>|]', '', topic)[:60].strip()
        file_name  = f"{safe_topic} - Lesson {n}.md"
        out_path   = MD_OUT_FOLDER / file_name
        out_path.write_text(md_text, encoding="utf-8")
        print(f"  [OK]  Written: {file_name}")
        output_files.append(out_path)

    print(f"\n[Step 3] {len(output_files)} lesson plan(s) written to {MD_OUT_FOLDER}")
    return output_files


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python write_all_lessons.py <age>")
        sys.exit(1)
    result = main(sys.argv[1])
    sys.exit(0 if result else 1)

