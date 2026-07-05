"""
run_pipeline.py – Master Pipeline Coordinator
Triggered by the command: Doc. <age>  (e.g. "Doc. 3-4")

Usage:
  python .agents/run_pipeline.py --age 3-4
  python .agents/run_pipeline.py --age 3-4 --dry-run   (skip GAS upload)
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]  # .agents/ -> workspace root
AGENTS_DIR     = Path(__file__).resolve().parent

SCRIPTS = {
    "step1": AGENTS_DIR / "skills" / "data_converter"     / "scripts" / "pdf_to_markdown.py",
    "step2": AGENTS_DIR / "skills" / "curriculum_planner" / "scripts" / "plan_curriculum.py",
    "step3": AGENTS_DIR / "skills" / "lesson_plan_writer"  / "scripts" / "write_all_lessons.py",
    "step4": AGENTS_DIR / "skills" / "lesson_plan_writer"  / "scripts" / "convert_to_docx.py",
    "step5": AGENTS_DIR / "skills" / "lesson_plan_writer"  / "scripts" / "upload_to_drive.py",
}


def run_step(label: str, script: Path, extra_args: list[str]) -> bool:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    cmd = [sys.executable, str(script)] + extra_args
    env = os.environ.copy(); env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), env=env)
    if result.returncode != 0:
        print(f"\n[PIPELINE] FAILED: {label} failed (exit {result.returncode}). Stopping.")
        return False
    print(f"[PIPELINE] OK: {label} complete.")
    return True


def batch_convert_docx(age: str) -> bool:
    """Step 4: convert all .md in markdown/ to .docx."""
    print(f"\n{'='*60}")
    print(f"  Step 4 – DOCX Renderer (batch)")
    print(f"{'='*60}")

    output_folder = WORKSPACE_ROOT / "Output giao an docs"
    if not output_folder.exists():
        output_folder = WORKSPACE_ROOT / "Output gi\u00e1o \u00e1n docs"

    md_folder   = output_folder / "markdown"
    md_files    = list(md_folder.glob("*.md")) if md_folder.exists() else []
    convert_script = SCRIPTS["step4"]
    converted   = 0
    errors      = 0

    for md_file in md_files:
        stem = md_file.stem
        if " - Lesson " in stem:
            topic = stem.split(" - Lesson ")[0].strip()
        else:
            topic = "General"
            
        topic_folder = output_folder / topic
        topic_folder.mkdir(parents=True, exist_ok=True)
        
        docx_name = stem + ".docx"
        docx_path = topic_folder / docx_name
        
        cmd = [sys.executable, str(convert_script), str(md_file), str(docx_path)]
        r   = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))
        if r.returncode == 0:
            print(f"  [OK]  {md_file.name} -> {topic}/{docx_name}")
            converted += 1
        else:
            print(f"  [ERR] {md_file.name}")
            errors += 1

    print(f"[Step 4] Converted {converted} file(s). Errors: {errors}.")
    return converted > 0


def main():
    parser = argparse.ArgumentParser(description="Lesson Plan Pipeline")
    parser.add_argument("--age",     required=True, help="Age group, e.g. 3-4")
    parser.add_argument("--dry-run", action="store_true", help="Skip Google Drive upload")
    args = parser.parse_args()

    age     = args.age
    dry_run = args.dry_run

    print(f"\n{'#'*60}")
    print(f"  LESSON PLAN PIPELINE  |  Age: {age}  |  Dry-run: {dry_run}")
    print(f"{'#'*60}")

    # Step 1 – PDF/DOCX → Markdown
    if not run_step("Step 1 – Data Converter", SCRIPTS["step1"], []):
        return

    # Step 2 – Classify + Schedule
    if not run_step("Step 2 – Curriculum Planner", SCRIPTS["step2"], [age]):
        return

    # Step 3 – Write lesson plans
    if not run_step("Step 3 – Lesson Plan Writer", SCRIPTS["step3"], [age]):
        return

    # Step 4 – Batch convert .md → .docx
    if not batch_convert_docx(age):
        print("[PIPELINE] Warning: no DOCX files produced. Skipping upload.")
        return

    # Step 5 – Upload to Google Drive + Sheet
    if dry_run:
        print("\n[PIPELINE] --dry-run flag set: skipping Google Drive upload.")
        print("[PIPELINE] DOCX files are ready in 'Output giao an docs/'.")
    else:
        if not run_step("Step 5 – Google Workspace Sync", SCRIPTS["step5"], [age]):
            print("[PIPELINE] Upload failed. DOCX files are still saved locally.")

    print(f"\n{'#'*60}")
    print(f"  PIPELINE COMPLETE  |  Age: {age}")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()


