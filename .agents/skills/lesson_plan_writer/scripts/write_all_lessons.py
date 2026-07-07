"""
Step 3 – Lesson Plan Writer
Reads _schedule.json + source markdown files,
generates detailed lesson plan .md files (V3 format) for each slot.
"""
import sys, os, json, re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None

load_dotenv()

import unicodedata

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]

def find_normalized_dir(parent: Path, name: str) -> Path:
    target_nfc = unicodedata.normalize('NFC', name)
    target_nfd = unicodedata.normalize('NFD', name)
    p_nfc = parent / target_nfc
    if p_nfc.exists():
        return p_nfc
    p_nfd = parent / target_nfd
    if p_nfd.exists():
        return p_nfd
    if parent.exists():
        for child in parent.iterdir():
            if child.is_dir():
                child_norm = unicodedata.normalize('NFC', child.name)
                if child_norm == target_nfc:
                    return child
    return p_nfc

INPUT_FOLDER = find_normalized_dir(WORKSPACE_ROOT, "Nhập học liệu pdf và docs")
if not INPUT_FOLDER.exists():
    INPUT_FOLDER = WORKSPACE_ROOT / "Nhap hoc lieu pdf va docs"

CACHE_FOLDER  = INPUT_FOLDER / "markdown_cache"

OUTPUT_FOLDER = find_normalized_dir(WORKSPACE_ROOT, "Output giáo án docs")
if not OUTPUT_FOLDER.exists():
    OUTPUT_FOLDER = WORKSPACE_ROOT / "Output giao an docs"

MD_OUT_FOLDER = OUTPUT_FOLDER / "markdown"
MD_OUT_FOLDER.mkdir(parents=True, exist_ok=True)

SCHED_PATH = OUTPUT_FOLDER / "_schedule.json"


def extract_topic(md_text: str, source_name: str) -> str:
    """Infer lesson topic from first heading or filename."""
    for line in md_text.splitlines():
        line = line.strip()
        if line.startswith("# ") and len(line) > 2:
            return line[2:].strip()
    return source_name.replace("_", " ").replace("-", " ").title()


def extract_vocab(md_text: str, age: str) -> list:
    """Extract likely vocabulary words from markdown text."""
    words = re.findall(r'\b[A-Z][a-z]{2,12}\b', md_text)
    freq  = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    vocab = [w for w, c in sorted(freq.items(), key=lambda x: -x[1]) if c >= 2]
    return vocab[:8]


def call_llm_for_lesson(topic: str, lesson_n: int, age: str, md_text: str, subject: str, source: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here" or not genai:
        return None
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
You are an expert kindergarten teacher creating a lesson plan for {age} years old.
Subject: {subject}
Topic: {topic}
Worksheet: {source}
Lesson Number: {lesson_n} (Out of 4 in this unit)

Source Material Content:
{md_text}

PEDAGOGICAL RULES:
- Age 3-4: Very short attention span, TPR, high scaffolding. Max 15 min for worksheets.
- Age 5-6: Growing confidence, phonics, simple sentences.
- BLOOM'S TAXONOMY PROGRESSION:
    Lesson 1: Recognize basic vocabulary (matching, coloring). High scaffolding.
    Lesson 2: Spelling, word building, expanded context.
    Lesson 3: Sentence structure (syntax), grammar introduction.
    Lesson 4: Application and creative output (crafts, speaking).

Based on the Lesson Number ({lesson_n}) and the Taxonomy progression, generate ONLY the markdown content for:
#### Part 2: New Words & Concepts (12 min)
(Include Teacher/TA/Student actions and TPR instructions specific to this lesson)

#### Part 3: Guided Practice & Worksheet (15 min)
(Include Teacher/TA/Student actions. Reference the worksheet '{source}'. Include safety notes if crafts are involved.)

Write in English. Do not output any other parts of the lesson plan (No Warm-up, No Closing). Do not wrap in markdown code blocks.
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"  [WARN] LLM Call failed: {e}")
        return None


def generate_lesson_md(slot: dict, age: str, lesson_n: int) -> str:
    """Generate a full lesson plan markdown for one slot."""
    subject = slot["subject"]
    source  = slot.get("source")
    week    = slot["week"]

    if source:
        src_path = CACHE_FOLDER / f"{source}.md"
        md_text  = src_path.read_text(encoding="utf-8") if src_path.exists() else ""
    else:
        md_text = ""

    topic = slot.get("topic") or extract_topic(md_text, source or subject)
    vocab = extract_vocab(md_text, age)
    vocab_str = ", ".join(vocab) if vocab else "[Derive from worksheet content]"
    song  = SONG_SUGGESTIONS.get(subject, "A fun action song")

    if subject == "Happy Friday":
        p1, p2, p3, p4 = "10 min", "15 min", "20 min", "10 min"
    else:
        p1, p2, p3, p4 = "8 min", "12 min", "15 min", "10 min"

    age_note = AGE_NOTES.get(age, "")

    if age in ("2-3", "3-4"):
        tpr_note      = "Every new word must be introduced with a body action (TPR). Repeat each word 3 times with the action."
    else:
        tpr_note      = "Use TPR for new vocabulary, then encourage students to say the word + a short phrase independently."

    parts_2_3 = call_llm_for_lesson(topic, lesson_n, age, md_text, subject, source or "worksheet")
    
    if not parts_2_3:
        hf_section = ""
        if subject == "Happy Friday":
            hf_section = f"""
#### Part 3: STEAM Experiment & Guided Practice ({p3})
* **Teacher Action:** Demonstrate the experiment step by step. Name each material aloud. Clear workspace tables before starting.
* **TA Action:** Circulate and assist students who need 1-1 support. Monitor safety at all times.
* **Student Action:** Follow along with the experiment. Repeat key action words.
* **Language Target:** "It [floats / sinks / changes colour / bubbles]!"
* **Safety Note:** Ensure all materials are food-safe or non-toxic. Child-safe scissors only under close TA supervision. Clear floor space before any active transitions.
"""
        else:
            hf_section = f"""
#### Part 3: Guided Practice & Worksheet ({p3})
* **Teacher Action:** Distribute worksheet. Walk students through instructions using gesture.
* **TA Action:** Sit with any student needing support. Prompt with the Word Mat.
* **Student Action:** Complete the worksheet at their own pace.
* **Worksheet:** [Reference: {source or "worksheet from teacher materials"}]
* **Safety Note:** Child-safe scissors only, under close TA supervision if cutting activities are included.
"""
        parts_2_3 = f"""
#### Part 2: New Words & Concepts ({p2})
* **Teacher Action:** Hold up flashcard for each vocabulary word. {tpr_note}
* **TA Action:** Echo each word after the teacher. 
* **Student Action:** Repeat each word with the action.
* **Safety Note:** Ensure flashcards with small pictures are held high enough to prevent crowding.
{hf_section}
"""

    title = f"{topic} – {subject} Lesson {lesson_n}"

    md = f"""<h1 align="center">{title}</h1>
<p align="center"><strong>Target Group:</strong> Age {age} | <strong>Week:</strong> {week} | <strong>Subject:</strong> {subject}</p>

---

## LESSON {lesson_n}: {topic.upper()}

### 1. LESSON OVERVIEW
* **Objectives:** By the end of the lesson, students will be able to recognise and use key vocabulary related to "{topic}".
* **Vocabulary:** {vocab_str}
* **Materials:** Flashcards, Word Mat, coloured pencils, worksheet printouts, music speaker
* **Songs & Content:** {song}

> **Age note ({age}):** {age_note}

---

### 2. MONTESSORI & CLASSROOM MANAGEMENT NOTES
* **Montessori Principle:** Prepared environment – arrange flashcards and materials on trays at child height before students enter. Allow students to choose their work station.
* **Self-Correction (Control of Error):** Provide a Word Mat face-down beside each student. Students may flip it to self-check.
* **Positive Discipline:** Use stickers and high-fives as rewards. Attention grabber: clap a rhythm and students clap back.

---

### 3. STEP-BY-STEP PROCEDURE

#### Part 1: Warm-up & Song ({p1})
* **Teacher Action:** Greet students warmly at the door. Begin playing the warm-up song immediately. Demonstrate actions.
* **TA Action:** Help latecomers settle quickly. Sing and do actions alongside students to model.
* **Student Action:** Follow along with song actions. Repeat chorus phrases.
* **Safety Note:** Clear floor space before any movement activity. Push chairs under tables.

{parts_2_3}

#### Part 4: Review & Closing ({p4})
* **Teacher Action:** Lead a quick "Show Me" game – hold up a flashcard, students point to the corresponding item.
* **TA Action:** Begin tidying materials during the last 2 minutes. Lead a tidy-up song.
* **Student Action:** Help pack away worksheets and pencils. Line up for hand-washing.
* **Hygiene:** Students must wash hands after any lesson involving glue, paint, clay, or food materials.
* **Closing:** Teacher says goodbye in English. Students echo. End with a class cheer or high-five circle.

---
_Lesson plan generated by Agentic Workspace – {datetime.now().strftime("%Y-%m-%d")}_
"""
    return md


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


def main(age: str):
    if not SCHED_PATH.exists():
        print("[Step 3] ERROR: _schedule.json not found. Run Step 2 first.")
        return []

    data     = json.loads(SCHED_PATH.read_text(encoding="utf-8"))
    schedule = data["schedule"]

    lesson_counters = {}
    output_files    = []
    
    # Group slots by (subject, topic)
    topic_groups = {}
    for slot in schedule:
        if slot["status"] == "MISSING":
            print(f"  [SKIP] {slot['week']} – {slot['subject']}: no material.")
            continue

        subj = slot["subject"]
        source = slot["source"] or subj
        topic  = slot.get("topic") or extract_topic(
            (CACHE_FOLDER / f"{source}.md").read_text(encoding="utf-8") if (CACHE_FOLDER / f"{source}.md").exists() else "",
            source
        )
        
        key = (subj, topic)
        if key not in topic_groups:
            topic_groups[key] = []
        topic_groups[key].append(slot)

    # Generate one file per group
    for (subj, topic), slots in topic_groups.items():
        lesson_counters[subj] = lesson_counters.get(subj, 0)
        
        md_texts = []
        for slot in slots:
            lesson_counters[subj] += 1
            n = lesson_counters[subj]
            md_texts.append(generate_lesson_md(slot, age, n))
            
        safe_topic = re.sub(r'[\\/:*?"<>|]', '', topic)[:60].strip()
        file_name  = f"{safe_topic}.md"
        out_path   = MD_OUT_FOLDER / file_name
        
        # Combine all lessons for this topic into one document
        combined_md = "\n\n<br><br>\n\n".join(md_texts)
        out_path.write_text(combined_md, encoding="utf-8")
        print(f"  [OK]  Written: {file_name} (contains {len(slots)} lessons)")
        output_files.append(out_path)

    print(f"\n[Step 3] {len(output_files)} grouped lesson plan(s) written to {MD_OUT_FOLDER}")
    return output_files


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python write_all_lessons.py <age>")
        sys.exit(1)
    main(sys.argv[1])
    sys.exit(0)

