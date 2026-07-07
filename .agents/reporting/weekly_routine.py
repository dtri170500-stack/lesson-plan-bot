import sys
import os
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = WORKSPACE_ROOT / ".agents"
REPORTING_DIR = AGENTS_DIR / "reporting"

def run_pipeline_for_age(age: str, dry_run: bool = True):
    print(f"\n{'='*80}")
    print(f"🚀 STARTING PIPELINE FOR AGE GROUP: {age}")
    print(f"{'='*80}")
    
    script_path = AGENTS_DIR / "run_pipeline.py"
    cmd = [sys.executable, str(script_path), "--age", age]
    if dry_run:
        cmd.append("--dry-run")
        
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), env=env)
    if result.returncode != 0:
        print(f"\n❌ [ERROR] Pipeline failed for age {age}")
    else:
        print(f"\n✅ [SUCCESS] Pipeline completed for age {age}")

def run_grading():
    print(f"\n{'='*80}")
    print(f"📊 STARTING GRADING PROCESS")
    print(f"{'='*80}")
    
    script_path = REPORTING_DIR / "grade_lesson_plans.py"
    cmd = [sys.executable, str(script_path)]
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), env=env)
    if result.returncode != 0:
        print(f"\n❌ [ERROR] Grading failed")
    else:
        print(f"\n✅ [SUCCESS] Grading completed")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Weekly Lesson Plan Routine")
    parser.add_argument("--dry-run", action="store_true", help="Skip Google Drive upload")
    args = parser.parse_args()

    # 1. Generate lesson plans
    run_pipeline_for_age("3-4", dry_run=args.dry_run)
    run_pipeline_for_age("5-6", dry_run=args.dry_run)
    
    # 2. Grade them
    run_grading()
    
    print("\n🎉 Weekly routine complete. Run 'streamlit run .agents/reporting/streamlit_app.py' to view the dashboard.")

if __name__ == "__main__":
    main()
