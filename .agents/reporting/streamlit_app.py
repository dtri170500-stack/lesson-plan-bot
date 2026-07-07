import streamlit as st
import json
import re
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
REPORTING_DIR = WORKSPACE_ROOT / ".agents" / "reporting"
REPORT_PATH = REPORTING_DIR / "grading_report.json"

st.set_page_config(page_title="Academic Manager Dashboard", layout="wide")

# CSS for Glassmorphism design and bright sky blue background
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Apply background and font */
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 40%, #7dd3fc 100%) !important;
        background-attachment: fixed !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    
    /* Background glows */
    [data-testid="stAppViewContainer"]::before {
        content: "";
        position: fixed;
        top: 10%;
        left: 5%;
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, rgba(56, 189, 248, 0.45) 0%, rgba(56, 189, 248, 0) 70%);
        border-radius: 50%;
        z-index: -1;
        pointer-events: none;
    }
    [data-testid="stAppViewContainer"]::after {
        content: "";
        position: fixed;
        bottom: 10%;
        right: 5%;
        width: 450px;
        height: 450px;
        background: radial-gradient(circle, rgba(14, 165, 233, 0.35) 0%, rgba(14, 165, 233, 0) 70%);
        border-radius: 50%;
        z-index: -1;
        pointer-events: none;
    }

    /* Titles styling */
    h1, h2, h3, h4, h5, h6, p, span, div {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    .dashboard-title {
        color: #0c4a6e !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        margin-bottom: 5px !important;
        text-align: center;
    }
    
    .dashboard-subtitle {
        color: #0369a1 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        margin-bottom: 30px !important;
        text-align: center;
    }

    /* Glassmorphic Metrics Card */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin-bottom: 35px;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 20px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.06);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.45);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.1);
    }
    
    .metric-val {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
    }
    .val-total { color: #0f172a; }
    .val-passed { color: #047857; }
    .val-failed { color: #b91c1c; }
    
    .metric-lbl {
        font-size: 0.95rem;
        font-weight: 700;
        color: #334155;
        margin-top: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Glassmorphic Lesson Board */
    .glass-board {
        background: rgba(255, 255, 255, 0.35);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.45);
        border-radius: 24px;
        padding: 28px;
        margin-bottom: 30px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-board:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 45px 0 rgba(31, 38, 135, 0.12);
        background: rgba(255, 255, 255, 0.4);
    }
    
    /* Board Header */
    .board-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1.5px solid rgba(255, 255, 255, 0.3);
        padding-bottom: 16px;
        margin-bottom: 20px;
    }
    
    .board-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
    }
    
    /* Badges */
    .badge {
        padding: 6px 14px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-pass {
        background: rgba(16, 185, 129, 0.18);
        color: #065f46;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-fail {
        background: rgba(239, 68, 68, 0.18);
        color: #991b1b;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Two column grid inside board */
    .board-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 32px;
    }
    @media (max-width: 992px) {
        .board-grid {
            grid-template-columns: 1fr;
            gap: 20px;
        }
    }
    
    /* Progress items */
    .progress-item {
        margin-bottom: 16px;
    }
    
    .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }
    
    .progress-name {
        font-size: 0.9rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    .progress-percent {
        font-size: 0.9rem;
        font-weight: 800;
    }
    .percent-high { color: #047857; }
    .percent-medium { color: #b45309; }
    .percent-low { color: #b91c1c; }
    
    .progress-track {
        background: rgba(255, 255, 255, 0.35);
        border-radius: 10px;
        height: 10px;
        width: 100%;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 1s ease-in-out;
    }
    .fill-high {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
    }
    .fill-medium {
        background: linear-gradient(90deg, #fbbf24 0%, #d97706 100%);
    }
    .fill-low {
        background: linear-gradient(90deg, #f87171 0%, #dc2626 100%);
    }
    
    /* Recommendations & Alerts column */
    .status-panel {
        background: rgba(255, 255, 255, 0.25);
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.25);
        height: 100%;
        box-sizing: border-box;
    }
    
    .panel-title {
        font-size: 1rem;
        font-weight: 800;
        margin-top: 0;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .title-pass { color: #065f46; }
    .title-fail { color: #991b1b; }
    
    .fail-list, .suggestion-list {
        margin: 0;
        padding-left: 20px;
        font-size: 0.88rem;
        line-height: 1.5;
    }
    
    .fail-list li {
        color: #991b1b;
        font-weight: 600;
        margin-bottom: 6px;
    }
    
    .suggestion-list li {
        color: #334155;
        margin-bottom: 6px;
    }
    
    .success-msg {
        color: #047857;
        font-weight: 600;
        font-size: 0.92rem;
        line-height: 1.5;
        margin: 0;
    }
    
    /* Custom Streamlit Button integration */
    div.stButton {
        margin-top: 15px !important;
    }
    div.stButton > button {
        background: rgba(255, 255, 255, 0.5) !important;
        color: #0c4a6e !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border-radius: 12px !important;
        padding: 8px 20px !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
    }
    div.stButton > button:hover {
        background: #0284c7 !important;
        color: white !important;
        border-color: #0284c7 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(2, 132, 199, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    if not REPORT_PATH.exists():
        return None
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_percentage(crit_name, score):
    # Search for max score inside parentheses, e.g. "Data Extraction (15)" -> 15
    match = re.search(r'\((\d+)\)', crit_name)
    if match:
        max_score = int(match.group(1))
    else:
        max_score = 100
    
    clean_name = re.sub(r'\s*\(\d+\)', '', crit_name)
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    return clean_name, score, max_score, percentage

def main():
    st.markdown('<h1 class="dashboard-title">🎓 Academic Manager</h1>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Bảng tổng hợp điểm số và đánh giá tự động dựa trên tiêu chí học thuật.</div>', unsafe_allow_html=True)
    
    data = load_data()
    
    if data is None:
        st.warning("Chưa có dữ liệu chấm điểm. Vui lòng chạy quy trình `weekly_routine.py` trước.")
        return
        
    # Calculate overview stats
    total = len(data)
    passed = sum(1 for d in data if d['status'] == 'PASS')
    failed = total - passed
    
    # Render overview metric cards
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <p class="metric-val val-total">{total}</p>
            <p class="metric-lbl">Tổng số Lesson Plans</p>
        </div>
        <div class="metric-card">
            <p class="metric-val val-passed">{passed}</p>
            <p class="metric-lbl">Đạt chuẩn (≥ 50 đ)</p>
        </div>
        <div class="metric-card">
            <p class="metric-val val-failed">{failed}</p>
            <p class="metric-lbl">Không đạt chuẩn (< 50 đ)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render each lesson plan card
    for plan in data:
        status_text = "PASS" if plan['status'] == 'PASS' else "FAIL"
        status_class = "badge-pass" if plan['status'] == 'PASS' else "badge-fail"
        icon = "🟢" if plan['status'] == 'PASS' else "🔴"
        
        # Build progress bars
        progress_bars_html = ""
        for crit, score in plan['scores'].items():
            clean_name, val, max_val, pct = get_percentage(crit, score)
            
            # Determine color grade
            if pct >= 80:
                color_class = "fill-high"
                text_class = "percent-high"
            elif pct >= 50:
                color_class = "fill-medium"
                text_class = "percent-medium"
            else:
                color_class = "fill-low"
                text_class = "percent-low"
                
            progress_bars_html += f"""
            <div class="progress-item">
                <div class="progress-header">
                    <span class="progress-name">{clean_name}</span>
                    <span class="progress-percent {text_class}">{val}/{max_val} ({pct:.0f}%)</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill {color_class}" style="width: {pct}%;"></div>
                </div>
            </div>
            """
            
        # Build recommendations / details
        if plan['status'] == 'FAIL':
            failed_items_list = "".join(f"<li>{item}</li>" for item in plan['failed_items'])
            suggestions_list = "".join(f"<li>{sugg}</li>" for sugg in plan['suggestions'])
            
            details_html = f"""
            <div class="status-panel">
                <h4 class="panel-title title-fail">⚠️ LÝ DO KHÔNG ĐẠT</h4>
                <ul class="fail-list">
                    {failed_items_list}
                </ul>
                <h4 class="panel-title title-fail" style="margin-top: 18px;">💡 ĐỀ XUẤT HƯỚNG GIẢI QUYẾT</h4>
                <ul class="suggestion-list">
                    {suggestions_list}
                </ul>
            </div>
            """
        else:
            # Check if there are any specific lower grades despite passing overall
            low_grades_warnings = []
            for crit, score in plan['scores'].items():
                clean_name, val, max_val, pct = get_percentage(crit, score)
                if pct < 70:
                    low_grades_warnings.append(f"Tiêu chí <strong>{clean_name}</strong> đạt {pct:.0f}% ({val}/{max_val}).")
            
            if low_grades_warnings:
                warnings_list = "".join(f"<li>{warn}</li>" for warn in low_grades_warnings)
                details_html = f"""
                <div class="status-panel">
                    <h4 class="panel-title title-fail" style="color: #b45309;">⚠️ ĐIỂM THÀNH PHẦN THẤP</h4>
                    <ul class="suggestion-list" style="color: #b45309;">
                        {warnings_list}
                    </ul>
                    <p class="success-msg" style="color: #b45309; margin-top: 10px;">
                        💡 <em>Mặc dù giáo án đã đạt điểm đỗ tổng quát, bạn nên cải thiện các mục trên để chất lượng bài giảng tốt hơn.</em>
                    </p>
                </div>
                """
            else:
                details_html = f"""
                <div class="status-panel" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">🎉</div>
                    <h4 class="panel-title title-pass" style="margin-bottom: 6px;">ĐẠT TIÊU CHUẨN XUẤT SẮC</h4>
                    <p class="success-msg">Mọi tiêu chí giảng dạy và học liệu của giáo án này đều đáp ứng tốt các yêu cầu sư phạm!</p>
                </div>
                """

        board_html = f"""
        <div class="glass-board">
            <div class="board-header">
                <span class="board-title">{icon} {plan['filename']}</span>
                <span class="badge {status_class}">{status_text} • Điểm: {plan['total_score']}/100</span>
            </div>
            <div class="board-grid">
                <div>
                    {progress_bars_html}
                </div>
                <div>
                    {details_html}
                </div>
            </div>
        </div>
        """
        
        st.markdown(board_html, unsafe_allow_html=True)
        
        # Download button placed at the bottom of the card block
        try:
            md_path = WORKSPACE_ROOT / "Output giáo án docs" / "markdown" / plan['filename']
            if md_path.exists():
                st.download_button(
                    label=f"📄 Tải file Markdown ({plan['filename']})",
                    data=md_path.read_text(encoding='utf-8'),
                    file_name=plan['filename'],
                    mime="text/markdown",
                    key=f"dl_{plan['filename']}"
                )
        except Exception:
            pass

if __name__ == "__main__":
    main()

