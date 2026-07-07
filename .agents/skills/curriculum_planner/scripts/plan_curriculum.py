"""
Step 2 – Curriculum Planner
Reads all .md files from markdown_cache/, classifies subjects,
filters by age, and produces Weekly_Syllabus.md with 10 slots over 2 weeks:
  Week 1: 2x Math, 2x Show and Tell, 1x Happy Friday
  Week 2: 2x Math, 2x Show and Tell, 1x Happy Friday
"""

import sys, os, json, re
from pathlib import Path
from datetime import datetime

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
OUTPUT_FOLDER.mkdir(exist_ok=True)

# ---------- Subject Classifier rules ----------
MATH_KEYWORDS = [
    "count","number","shape","circle","square","triangle","rectangle",
    "plus","minus","equal","sort","pattern","big","small","more","less",
    "how many","addition","subtraction","math","maths","numeral","digit",
    "greater","fewer"
]
HAPPY_KEYWORDS = [
    "steam","experiment","science","float","sink","mix","pour","bubble",
    "magnet","colour mixing","color mixing","dissolve","react","hypothesis",
    "observe","prediction","result","material","liquid","solid"
]
SHOW_KEYWORDS = [
    "my family","my body","body parts","feelings","emotion","animal",
    "food","fruit","vegetable","colour","color","toy","school","weather",
    "season","transport","community","job","sport","clothing","bedroom",
    "monster","birthday","party","describe","talk about","show and tell",
    "sentence","what is","this is","i have","i like"
]

def contains_keyword(text: str, keyword: str) -> bool:
    pattern = r'\b' + re.escape(keyword) + r'\b'
    return bool(re.search(pattern, text))

def classify(md_text: str) -> str:
    low = md_text.lower()
    h_score   = sum(1 for k in HAPPY_KEYWORDS if contains_keyword(low, k))
    m_score   = sum(1 for k in MATH_KEYWORDS  if contains_keyword(low, k))
    st_score  = sum(1 for k in SHOW_KEYWORDS  if contains_keyword(low, k))
    if h_score > m_score and h_score > st_score:   return "Happy Friday"
    if m_score > st_score:                          return "Math"
    return "Show and Tell"

# ---------- Age-based difficulty filter ----------
# Returns True if the material is appropriate for the given age group
AGE_MAX_DIFFICULTY = {
    "2-3": 1, "3-4": 2, "4-5": 3, "5-6": 4
}
def difficulty_score(md_text: str) -> int:
    """Rough heuristic: 1=easy, 4=very hard"""
    low = md_text.lower()
    score = 1
    if any(contains_keyword(low, k) for k in ["write a sentence","paragraph","describe in detail","error correction"]): score = 4
    elif any(contains_keyword(low, k) for k in ["sentence","what are","plural","possessive"]): score = 3
    elif any(contains_keyword(low, k) for k in ["phrase","adjective","label","sort","categorize"]): score = 2
    return score

def is_appropriate(md_text: str, age: str) -> bool:
    max_d = AGE_MAX_DIFFICULTY.get(age, 3)
    return difficulty_score(md_text) <= max_d

# ---------- Topic Inference and Defaults ----------
DEFAULT_TOPICS = {
    "2-3": {
        "Math": "Numbers 1–3",
        "Show and Tell": "My Body",
        "Happy Friday": "Color Mixing"
    },
    "3-4": {
        "Math": "Number 1–5",
        "Show and Tell": "My Birthday Party",
        "Happy Friday": "Sink or Float"
    },
    "4-5": {
        "Math": "Number 6–10",
        "Show and Tell": "My School",
        "Happy Friday": "Magnets Investigation"
    },
    "5-6": {
        "Math": "Simple Addition & Subtraction",
        "Show and Tell": "Weather & Seasons",
        "Happy Friday": "Volcano Eruption"
    }
}

def infer_topic_for_subject(subject: str, sources: list[str], cache_folder: Path) -> str:
    combined_text = ""
    source_names_joined = " ".join(sources).lower()
    
    for src in sources:
        if src:
            md_file = cache_folder / f"{src}.md"
            if md_file.exists():
                combined_text += " " + md_file.read_text(encoding="utf-8").lower()
                
    combined_text = combined_text.lower() + " " + source_names_joined

    if subject == "Show and Tell":
        if any(contains_keyword(combined_text, w) for w in ["birthday", "candle", "cake", "age", "how old", "year old", "candles"]):
            return "My Birthday Party"
        if any(contains_keyword(combined_text, w) for w in ["family", "mother", "father", "parent", "brother", "sister", "grandma", "grandpa"]):
            return "My Family"
        if any(contains_keyword(combined_text, w) for w in ["body", "head", "shoulder", "knee", "toe", "eye", "ear", "mouth", "nose", "hand", "foot"]):
            return "My Body"
        if any(contains_keyword(combined_text, w) for w in ["feeling", "emotion", "happy", "sad", "angry", "scared", "excited", "tired"]):
            return "My Feelings"
        if any(contains_keyword(combined_text, w) for w in ["school", "classroom", "teacher", "pencil", "book", "bag", "ruler", "eraser"]):
            return "My School"
        if any(contains_keyword(combined_text, w) for w in ["toy", "doll", "ball", "car", "teddy", "robot", "blocks"]):
            return "My Toys"
        if any(contains_keyword(combined_text, w) for w in ["animal", "pet", "dog", "cat", "bird", "lion", "tiger", "bear", "elephant"]):
            return "Animals"
        if any(contains_keyword(combined_text, w) for w in ["food", "drink", "fruit", "vegetable", "apple", "banana", "bread", "milk", "juice"]):
            return "Food & Drinks"
        if any(contains_keyword(combined_text, w) for w in ["color", "colour", "red", "blue", "green", "yellow", "pink", "orange", "purple"]):
            return "Colors"
        if any(contains_keyword(combined_text, w) for w in ["transport", "car", "bus", "plane", "train", "boat", "vehicle"]):
            return "Transportation"
        if any(contains_keyword(combined_text, w) for w in ["weather", "sunny", "rainy", "windy", "cloudy", "snowy", "hot", "cold"]):
            return "Weather"
        if sources:
            return sources[0].replace("_", " ").replace("-", " ").title()
        return "Show and Tell Topic"

    elif subject == "Math":
        if any(contains_keyword(combined_text, w) for w in ["shape", "circle", "square", "triangle", "rectangle", "star", "oval", "heart"]):
            return "Shapes"
        if any(contains_keyword(combined_text, w) for w in ["plus", "minus", "add", "subtract", "addition", "subtraction", "sum", "equal"]):
            return "Simple Addition & Subtraction"
        if any(contains_keyword(combined_text, w) for w in ["pattern", "sequence", "repeat"]):
            return "Patterns"
        if any(contains_keyword(combined_text, w) for w in ["sort", "classify", "group", "category"]):
            return "Sorting & Classifying"
        if any(contains_keyword(combined_text, w) for w in ["big", "small", "tall", "short", "large", "compare", "greater", "less", "more", "fewer"]):
            return "Comparing Sizes & Quantities"
        if any(contains_keyword(combined_text, w) for w in ["number 1", "number 2", "number 3", "number 4", "number 5", "1-5", "1 to 5", "one", "two", "three", "four", "five"]):
            return "Number 1–5"
        if any(contains_keyword(combined_text, w) for w in ["number 6", "number 7", "number 8", "number 9", "number 10", "6-10", "6 to 10", "six", "seven", "eight", "nine", "ten"]):
            return "Number 6–10"
        if sources:
            return sources[0].replace("_", " ").replace("-", " ").title()
        return "Math Topic"

    elif subject == "Happy Friday":
        if any(contains_keyword(combined_text, w) for w in ["float", "sink", "water"]):
            return "Sink or Float"
        if any(contains_keyword(combined_text, w) for w in ["mix", "color mixing", "colour mixing", "paint", "secondary color"]):
            return "Color Mixing"
        if any(contains_keyword(combined_text, w) for w in ["magnet", "attract", "repel", "magnetic"]):
            return "Magnets Investigation"
        if any(contains_keyword(combined_text, w) for w in ["bubble", "soap", "blow"]):
            return "Bubble Fun"
        if any(contains_keyword(combined_text, w) for w in ["plant", "grow", "seed", "soil"]):
            return "How Plants Grow"
        if any(contains_keyword(combined_text, w) for w in ["volcano", "soda", "vinegar", "eruption"]):
            return "Volcano Eruption"
        if any(contains_keyword(combined_text, w) for w in ["dissolve", "sugar", "salt", "water"]):
            return "Dissolving Experiment"
        if sources:
            return sources[0].replace("_", " ").replace("-", " ").title()
        return "Happy Friday Science"

    return "General Topic"

# ---------- Main ----------
def main(age: str):
    md_files = sorted(CACHE_FOLDER.glob("*.md"))
    if not md_files:
        print("[Step 2] ERROR: No markdown files found in cache. Run Step 1 first.")
        return None

    buckets = {"Math": [], "Show and Tell": [], "Happy Friday": []}
    rejected = []

    for f in md_files:
        text    = f.read_text(encoding="utf-8")
        subject = classify(text)
        if not is_appropriate(text, age):
            rejected.append((f.stem, subject, "Too difficult for age " + age))
            continue
        buckets[subject].append(f.stem)

    # Determine topic for each subject based on actual files
    subject_topics = {}
    for subj in ["Math", "Show and Tell", "Happy Friday"]:
        sources = buckets[subj]
        if sources:
            topic = infer_topic_for_subject(subj, sources, CACHE_FOLDER)
        else:
            topic = DEFAULT_TOPICS.get(age, {}).get(subj, f"{subj} Topic")
        subject_topics[subj] = topic

    # Build 10-slot schedule: W1=(2M,2ST,1HF), W2=(2M,2ST,1HF)
    SLOTS = [
        ("Week 1","Math"),("Week 1","Math"),
        ("Week 1","Show and Tell"),("Week 1","Show and Tell"),
        ("Week 1","Happy Friday"),
        ("Week 2","Math"),("Week 2","Math"),
        ("Week 2","Show and Tell"),("Week 2","Show and Tell"),
        ("Week 2","Happy Friday"),
    ]

    schedule = []
    lesson_counters = {"Math": 0, "Show and Tell": 0, "Happy Friday": 0}
    missing = []

    for week, subj in SLOTS:
        pool  = buckets[subj]
        idx   = lesson_counters[subj]
        lesson_counters[subj] += 1
        topic = subject_topics[subj]
        if idx < len(pool):
            schedule.append({"week": week, "subject": subj, "source": pool[idx], "status": "OK", "topic": topic})
        else:
            schedule.append({"week": week, "subject": subj, "source": None, "status": "MISSING", "topic": topic})
            if subj not in missing: missing.append(subj)

    # Write Weekly_Syllabus.md
    ts      = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines   = [
        f"# Weekly Syllabus – Age {age}",
        f"_Generated: {ts}_\n",
        f"## Input summary",
        f"- Math materials found    : {len(buckets['Math'])}",
        f"- Show and Tell found     : {len(buckets['Show and Tell'])}",
        f"- Happy Friday found      : {len(buckets['Happy Friday'])}",
        f"- Rejected (age filter)  : {len(rejected)}\n",
        "## 10-Slot Schedule\n",
        "| # | Week | Subject | Topic | Source File | Status |",
        "|---|------|---------|-------|-------------|--------|",
    ]
    for i, slot in enumerate(schedule, 1):
        src = slot["source"] or "[MISSING – CẦN BỔ SUNG]"
        lines.append(f"| {i} | {slot['week']} | {slot['subject']} | {slot['topic']} | {src} | {slot['status']} |")

    if rejected:
        lines += ["\n## Rejected Materials (too difficult for age " + age + ")\n"]
        for name, subj, reason in rejected:
            lines.append(f"- **{name}** ({subj}): {reason}")

    if missing:
        lines += [
            "\n## ⚠️ Missing Materials\n",
            "The following subjects do not have enough source materials:\n",
        ]
        for s in missing:
            lines.append(f"- **{s}**: Please type `Tim hoc lieu + {age}` to find materials on Twinkl.")

    unused_paths = []
    for subj, pool in buckets.items():
        used = lesson_counters[subj]
        for f in pool[used:]:
            unused_paths.append((f, subj))
    if unused_paths:
        lines += ["\n## Unused Materials (can be archived)\n"]
        for name, subj in unused_paths:
            lines.append(f"- {name} ({subj})")

    out = OUTPUT_FOLDER / "Weekly_Syllabus.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Step 2] Syllabus written to {out}")

    # Save machine-readable schedule for Step 3
    sched_out = OUTPUT_FOLDER / "_schedule.json"
    sched_out.write_text(json.dumps({"age": age, "schedule": schedule}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Step 2] Schedule JSON saved to {sched_out}")
    return schedule

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plan_curriculum.py <age>  (e.g. 3-4)")
        sys.exit(1)
    result = main(sys.argv[1])
    sys.exit(0 if result is not None else 1)

