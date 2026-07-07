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
    "step5": AGENTS_DIR / "skills" / "lesson_plan_writer"  / "scripts" / "upload_gas.py",
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
            topic = stem
            
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
    parser.add_argument("--auto-approve", action="store_true", help="Bypass human checkpoint before upload")
    args = parser.parse_args()

    age          = args.age
    dry_run      = args.dry_run
    auto_approve = args.auto_approve

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

    # Step 4.5 - Grading lesson plans
    grade_script = AGENTS_DIR / "reporting" / "grade_lesson_plans.py"
    if not run_step("Step 4.5 – AI Grading & Assessment", grade_script, []):
        print("[PIPELINE] Warning: Grading failed.")

    # HUMAN CHECKPOINT
    if not dry_run:
        print(f"\n{'='*60}")
        print(f"  HUMAN CHECKPOINT (MANDATORY)")
        print(f"{'='*60}")
        print("[PIPELINE] Vui lòng kiểm tra các file chấm điểm trên Dashboard (http://localhost:9009) hoặc thư mục 'Output giao an docs'.")
        
        user_input = input("[PIPELINE] Nhập 'Duyệt.' để tiếp tục đồng bộ lên Drive/Sheet, hoặc nhấn Enter/gõ bất kỳ để báo chưa ổn: ")
        
        if user_input.strip() != 'Duyệt.':
            print("\n[PIPELINE] Phát hiện yêu cầu làm lại.")
            feedback = input("[PIPELINE] Vui lòng nhập đề xuất/góp ý để làm lại: ")
            
            # Save feedback
            feedback_path = WORKSPACE_ROOT / "Output giáo án docs" / "feedback.txt"
            try:
                with open(feedback_path, 'w', encoding='utf-8') as f:
                    f.write(feedback)
                print(f"[PIPELINE] Đã lưu ý kiến phản hồi tại: {feedback_path.name}")
            except Exception as e:
                print(f"[PIPELINE] Không thể lưu feedback: {e}")
                
            print("\n[PIPELINE] Dừng quy trình để sửa đổi theo ý kiến phản hồi.")
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
    
    # Auto-open the XLSX grading report
    xlsx_path = WORKSPACE_ROOT / "Output giáo án docs" / "grading_report.xlsx"
    if not xlsx_path.exists():
        xlsx_path = WORKSPACE_ROOT / "Output giao an docs" / "grading_report.xlsx"
        
    if xlsx_path.exists():
        try:
            print(f"[PIPELINE] Auto-opening grading report: {xlsx_path.name}")
            subprocess.run(["open", str(xlsx_path)])
        except Exception as e:
            print(f"[PIPELINE] Could not auto-open grading report: {e}")


if __name__ == "__main__":
    main()


