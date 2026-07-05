"""
upload_gas.py – Upload DOCX files to Google Drive via GAS Web App
Naming convention: [MÔN HỌC] - [TÊN CHỦ ĐỀ] - Lesson [N]
Example: Show and Tell - Cake Cut-Out - Lesson 1

GAS expects GET request with ?payload=<JSON> where JSON has:
  { "files": [{ "fileName": ..., "base64": ..., "week": ..., "age": ..., "subject": ... }] }

Usage:
    python upload_gas.py <age>
    python upload_gas.py 3-4
"""

import sys, os, json, re, base64, urllib.parse
from pathlib import Path

# ── Auto-install requests if needed ──────────────────────────────────────────
try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

# ── Paths ─────────────────────────────────────────────────────────────────────
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH    = WORKSPACE_ROOT / ".agents" / "config.json"
OUTPUT_FOLDER  = WORKSPACE_ROOT / "Output giáo án docs"
if not OUTPUT_FOLDER.exists():
    OUTPUT_FOLDER = WORKSPACE_ROOT / "Output giao an docs"

with open(CONFIG_PATH, encoding="utf-8") as f:
    cfg = json.load(f)

GAS_URL = cfg.get("gas_web_app_url", "")


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_schedule() -> list:
    """Load _schedule.json from output folder."""
    sched_path = OUTPUT_FOLDER / "_schedule.json"
    if sched_path.exists():
        return json.loads(sched_path.read_text(encoding="utf-8")).get("schedule", [])
    return []


def build_rename_map(schedule: list) -> dict:
    """
    Build mapping: original_stem → (new_name, subject, lesson_num, week)

    Naming rule: [MÔN HỌC] - [TÊN CHỦ ĐỀ] - Lesson [N]
    Lesson number counts per-subject.
    Only slots with status == 'OK' are included.
    """
    rename_map = {}
    subject_counter: dict[str, int] = {}

    for slot in schedule:
        if slot.get("status") != "OK" or not slot.get("source"):
            continue

        source  = slot["source"]     # e.g. "Cake Cut-Out"
        subject = slot["subject"]    # e.g. "Show and Tell"
        week    = slot["week"]       # e.g. "Week 1"

        subject_counter[subject] = subject_counter.get(subject, 0) + 1
        lesson_num = subject_counter[subject]

        # Find matching DOCX file (match topic part of stem)
        matched_stem = None
        for docx in OUTPUT_FOLDER.glob("*.docx"):
            stem = docx.stem
            # Strip trailing " - Lesson N" to get topic
            topic_part = re.sub(r"\s*-\s*[Ll]esson\s*\d+$", "", stem).strip()
            if topic_part.lower() == source.lower():
                matched_stem = stem
                break

        if matched_stem is None:
            print(f"  [WARN] No DOCX matched for source: '{source}'")
            continue

        new_name = f"{subject} - {source} - Lesson {lesson_num}"
        rename_map[matched_stem] = {
            "new_name":   new_name,
            "subject":    subject,
            "lesson_num": lesson_num,
            "week":       week,
        }

    return rename_map


def call_gas(files_payload: list, age: str) -> dict:
    """
    Send files to GAS via GET request (recommended) or POST fallback.
    GAS format: { "files": [{ "fileName", "base64", "week", "age", "subject" }] }
    """
    if not GAS_URL:
        return {"status": "error", "message": "gas_web_app_url not set in config.json"}

    body = {"files": files_payload}
    encoded_payload = urllib.parse.quote(json.dumps(body, ensure_ascii=False))

    try:
        # Try GET first (as GAS doGet is the primary handler)
        url = f"{GAS_URL}?payload={encoded_payload}"
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [GET failed: {e}] – falling back to POST...")
        try:
            resp = requests.post(GAS_URL, json=body, timeout=120)
            resp.raise_for_status()
            return resp.json()
        except Exception as e2:
            return {"status": "error", "message": str(e2)}


def main(age: str):
    print(f"\n{'='*60}")
    print(f"  UPLOAD TO DRIVE  |  Age: {age}")
    print(f"{'='*60}\n")

    schedule   = load_schedule()
    rename_map = build_rename_map(schedule)

    docx_files = sorted(OUTPUT_FOLDER.glob("*.docx"))
    if not docx_files:
        print("[upload_gas] No DOCX files found in output folder.")
        return False

    print(f"Found {len(docx_files)} DOCX file(s):\n")
    for d in docx_files:
        new_info = rename_map.get(d.stem)
        new_name = new_info["new_name"] if new_info else d.stem
        print(f"  {d.name}  →  '{new_name}.docx'")

    print(f"\n{'─'*60}")
    print("Encoding and uploading...\n")

    # Build files payload
    files_payload = []
    for docx in docx_files:
        stem     = docx.stem
        info     = rename_map.get(stem)
        new_name = info["new_name"]   if info else stem
        subject  = info["subject"]    if info else "Show and Tell"
        week     = info["week"]       if info else "Week 1"

        print(f"  Encoding: {new_name}.docx ({len(docx.read_bytes())//1024} KB)...")
        encoded = base64.b64encode(docx.read_bytes()).decode("utf-8")

        files_payload.append({
            "fileName": new_name + ".docx",
            "base64":   encoded,
            "week":     week,
            "age":      age,
            "subject":  subject,
        })

    print(f"\n  Sending {len(files_payload)} file(s) to GAS Web App...")
    result = call_gas(files_payload, age)

    print(f"\n{'─'*60}")
    print(f"GAS Response:\n")

    total_ok = 0
    if result.get("status") == "ok":
        for r in result.get("results", []):
            if r.get("status") == "ok":
                print(f"  ✓ {r.get('fileName', '?')}")
                print(f"    Drive: {r.get('driveUrl', '(no url)')}")
                print(f"    Sheet: {r.get('sheetUpdate', '?')}")
                total_ok += 1
            else:
                print(f"  ✗ {r.get('fileName', '?')} – Error: {r.get('message', '?')}")
    else:
        print(f"  Error: {result.get('message', str(result))}")

    print(f"\n{'='*60}")
    print(f"  Done: {total_ok}/{len(files_payload)} uploaded successfully.")
    print(f"{'='*60}\n")
    return total_ok > 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python upload_gas.py <age>   (e.g. 3-4)")
        sys.exit(1)
    age_arg = sys.argv[1]
    sys.exit(0 if main(age_arg) else 1)
