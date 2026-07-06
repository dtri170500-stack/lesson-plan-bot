import streamlit as st
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPORTING_DIR = WORKSPACE_ROOT / ".agents" / "reporting"
REPORT_PATH = REPORTING_DIR / "grading_report.json"

st.set_page_config(page_title="Academic Manager Dashboard", layout="wide")

def load_data():
    if not REPORT_PATH.exists():
        return None
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    st.title("🎓 Academic Manager: Lesson Plan Dashboard")
    st.markdown("Bảng tổng hợp điểm số và đánh giá tự động dựa trên tiêu chí học thuật.")
    
    data = load_data()
    
    if data is None:
        st.warning("Chưa có dữ liệu chấm điểm. Vui lòng chạy quy trình `weekly_routine.py` trước.")
        return
        
    # Thống kê tổng quan
    total = len(data)
    passed = sum(1 for d in data if d['status'] == 'PASS')
    failed = total - passed
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số Lesson Plans", total)
    col2.metric("Đạt chuẩn (≥ 50 đ)", passed)
    col3.metric("Không đạt chuẩn (< 50 đ)", failed, delta="-Cảnh báo" if failed > 0 else "")
    
    st.divider()
    
    # Hiển thị danh sách
    st.subheader("Danh sách Giáo án")
    
    for plan in data:
        status_color = "red" if plan['status'] == 'FAIL' else "green"
        status_icon = "🛑" if plan['status'] == 'FAIL' else "✅"
        
        with st.expander(f"{status_icon} {plan['filename']} - Điểm: {plan['total_score']}/100"):
            
            # Nếu thất bại, hiển thị báo động đỏ
            if plan['status'] == 'FAIL':
                st.error(f"**BÁO ĐỘNG THỊ GIÁC: GIÁO ÁN KHÔNG ĐẠT CHUẨN ({plan['total_score']} ĐIỂM)**")
                
                st.markdown("### ❌ CÁC MỤC BỊ CHẤM ĐIỂM KÉM")
                for item in plan['failed_items']:
                    st.markdown(f"- :red[{item}]")
                    
                st.markdown("### 💡 GỢI Ý SỬA LỖI CỤ THỂ")
                for sugg in plan['suggestions']:
                    st.markdown(f"- {sugg}")
            else:
                st.success(f"Giáo án đạt chuẩn ({plan['total_score']} điểm)")
            
            # Chi tiết điểm
            st.markdown("#### Chi tiết điểm số:")
            score_cols = st.columns(len(plan['scores']))
            for i, (crit, score) in enumerate(plan['scores'].items()):
                score_cols[i].metric(crit.split(' (')[0][:15] + "...", score)
                
            # Đọc nội dung file
            try:
                md_path = WORKSPACE_ROOT / "Output giáo án docs" / "markdown" / plan['filename']
                if md_path.exists():
                    st.download_button(
                        label="📄 Tải file Markdown",
                        data=md_path.read_text(encoding='utf-8'),
                        file_name=plan['filename'],
                        mime="text/markdown"
                    )
            except Exception as e:
                pass

if __name__ == "__main__":
    main()
