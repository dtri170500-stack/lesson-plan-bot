import json
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPORTING_DIR = WORKSPACE_ROOT / ".agents" / "reporting"
REPORT_PATH = REPORTING_DIR / "grading_report.json"
OUTBOX_PATH = REPORTING_DIR / "email_outbox.txt"

def send_mock_email(failed_plans):
    print("\n" + "="*80)
    print("📧 MOCK EMAIL SYSTEM TRIGGERED")
    print("="*80)
    
    email_body = f"Kính gửi Quản lý Học thuật,\n\n"
    email_body += f"Hệ thống tự động phát hiện {len(failed_plans)} giáo án không đạt tiêu chuẩn (dưới 50 điểm) trong đợt tạo bài mới nhất ({datetime.now().strftime('%Y-%m-%d %H:%M')}).\n\n"
    email_body += "Vui lòng xem xét các chi tiết bên dưới và kiểm tra trên hệ thống Streamlit:\n\n"
    
    for plan in failed_plans:
        email_body += f"🛑 Tên File: {plan['filename']}\n"
        email_body += f"   - Điểm số: {plan['total_score']}/100\n"
        email_body += f"   - Các tiêu chí bị đánh giá kém:\n"
        for item in plan['failed_items']:
            email_body += f"     * {item}\n"
        email_body += f"   - Gợi ý sửa đổi:\n"
        for sugg in plan['suggestions']:
            email_body += f"     * {sugg}\n"
        email_body += "\n"
        
    email_body += "Trân trọng,\nAgentic Workspace Bot"
    
    # In ra terminal
    print(email_body)
    print("="*80)
    
    # Lưu vào file outbox để tiện xem lại
    with open(OUTBOX_PATH, 'w', encoding='utf-8') as f:
        f.write(email_body)
    
    print(f"[EMAIL] Thư cảnh báo đã được gửi (Mock) và lưu tại {OUTBOX_PATH.name}")

def main():
    if not REPORT_PATH.exists():
        print("[EMAIL] Không tìm thấy báo cáo chấm điểm.")
        return
        
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
        
    failed_plans = [plan for plan in report_data if plan['status'] == 'FAIL']
    
    if failed_plans:
        send_mock_email(failed_plans)
    else:
        print("[EMAIL] Tất cả giáo án đều đạt chuẩn. Không cần gửi cảnh báo.")

if __name__ == "__main__":
    main()
