import os
import json
import random
from pathlib import Path
import subprocess
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_FOLDER = WORKSPACE_ROOT / "Output giáo án docs"
REPORTING_DIR = WORKSPACE_ROOT / ".agents" / "reporting"
MD_FOLDER = OUTPUT_FOLDER / "markdown"
REPORT_PATH = REPORTING_DIR / "grading_report.json"

def evaluate_lesson_plan(md_content: str, filename: str) -> dict:
    """
    Evaluates a lesson plan against the rubric.
    In a real scenario, this would call an LLM (e.g. Gemini).
    Here we provide a robust mock evaluation with some random variation
    to demonstrate the alerting capabilities.
    """
    # Simple heuristic to determine "bad" lesson plans for testing
    # If filename has "Math", we'll sometimes make it fail.
    
    score_data = {
        "Data Extraction (15)": 15,
        "Montessori Standards (20)": 20,
        "Age Appropriateness (15)": 15,
        "Scaffolding (15)": 15,
        "Safety (10)": 10,
        "Engagement (15)": 15,
        "Formatting (10)": 10
    }
    
    failed_items = []
    suggestions = []
    
    # Let's mock a failure for demonstration if 'Math' or 'Lesson 2' is in the filename
    if "Math" in filename or random.random() < 0.3:
        score_data["Age Appropriateness (15)"] = 0
        score_data["Engagement (15)"] = 0
        score_data["Safety (10)"] = 0
        score_data["Scaffolding (15)"] = 0
        
        failed_items.append("Độ An Toàn Lớp Học (Cảnh báo đỏ)")
        failed_items.append("Chuẩn Phương Pháp Dạy Theo Độ Tuổi")
        failed_items.append("Tính Tò Mò, Hứng Thú")
        
        suggestions.append("Cảnh báo: Thiếu ghi chú an toàn (Safety Note) cho hoạt động sử dụng kéo hoặc vật nhỏ.")
        suggestions.append("Hoạt động quá tĩnh, cần bổ sung TPR (Total Physical Response) và các bài hát khởi động.")
        suggestions.append("Lesson plan thiếu Trò chơi/vận động/thiếu tính sáng tạo, học sinh phải ngồi ghế quá lâu.")
        
    elif "Show" in filename:
        # A mediocre one
        score_data["Montessori Standards (20)"] = 10
        score_data["Data Extraction (15)"] = 10
        failed_items.append("Tiêu chuẩn Montessori (Thiếu Control of Error)")
        suggestions.append("Chưa có cơ chế để học sinh tự kiểm tra lỗi (Self-correction). Cần bổ sung Word Mat úp sấp.")
    
    total_score = sum(score_data.values())
    
    return {
        "filename": filename,
        "total_score": total_score,
        "scores": score_data,
        "failed_items": failed_items,
        "suggestions": suggestions,
        "status": "PASS" if total_score >= 50 else "FAIL"
    }

def main():
    print(f"[GRADER] Looking for lesson plans in {MD_FOLDER}")
    
    if not MD_FOLDER.exists():
        print(f"[GRADER] Output directory not found. Please run the pipeline first.")
        return
        
    md_files = list(MD_FOLDER.glob("*.md"))
    if not md_files:
        print("[GRADER] No markdown files found to grade.")
        return
        
    print(f"[GRADER] Found {len(md_files)} lesson plans to grade.")
    
    report_data = []
    has_failures = False
    
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        result = evaluate_lesson_plan(content, md_file.name)
        report_data.append(result)
        
        if result["status"] == "FAIL":
            has_failures = True
            print(f"  ❌ FAIL: {md_file.name} (Score: {result['total_score']})")
        else:
            print(f"  ✅ PASS: {md_file.name} (Score: {result['total_score']})")
            
    # Save the report
    REPORTING_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
        
    print(f"\n[GRADER] Grading complete. Report saved to {REPORT_PATH.name}")
    
    # Trigger email alert if there are failures
    if has_failures:
        print("[GRADER] Failures detected. Triggering Email Alert System...")
        alert_script = REPORTING_DIR / "send_email_alert.py"
        subprocess.run([sys.executable, str(alert_script)])

if __name__ == "__main__":
    main()
