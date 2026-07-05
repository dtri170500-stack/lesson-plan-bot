#!/usr/bin/env python3
"""
lesson_plan_mcp.py – MCP Server cho Lesson Plan Bot

Cung cấp các tools để Antigravity:
  1. run_pipeline        – Chạy toàn bộ pipeline (PDF→MD→Giáo án→DOCX)
  2. sync_to_google      – Upload DOCX lên Drive + ghi link vào Sheet
  3. list_output_files   – Liệt kê file DOCX đã tạo
  4. read_schedule       – Đọc lịch phân bổ (_schedule.json)
  5. read_weekly_syllabus– Đọc bảng tổng kết tuần
  6. list_input_files    – Liệt kê học liệu đầu vào
  7. get_project_status  – Báo cáo tổng trạng thái dự án

Chạy: python3 .agents/mcp_server/lesson_plan_mcp.py
"""

import json, subprocess, sys, os, pickle, re
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────────────
WORKSPACE = Path(__file__).resolve().parents[2]
AGENTS    = WORKSPACE / ".agents"
SCRIPTS   = AGENTS / "skills" / "lesson_plan_writer" / "scripts"

OUTPUT_FOLDER = WORKSPACE / "Output gi\u00e1o \u00e1n docs"
if not OUTPUT_FOLDER.exists():
    OUTPUT_FOLDER = WORKSPACE / "Output giao an docs"

INPUT_FOLDER  = WORKSPACE / "Nh\u1eadp h\u1ecdc li\u1ec7u pdf v\u00e0 docs"
if not INPUT_FOLDER.exists():
    INPUT_FOLDER = WORKSPACE / "Nhap hoc lieu pdf va docs"

PYTHON = sys.executable

# ── MCP Server ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "Lesson Plan Bot",
    instructions=(
        "MCP server cho hệ thống tự động sinh giáo án mầm non Việt Pháp. "
        "Dùng run_pipeline để chạy toàn bộ quy trình từ PDF sang DOCX, "
        "sync_to_google để đẩy lên Drive/Sheet, "
        "read_schedule để xem lịch phân bổ."
    )
)

# ─────────────────────────────────────────────────────────────────────────────
@mcp.tool()
def run_pipeline(age: str = "3-4", dry_run: bool = True) -> str:
    """
    Chạy toàn bộ pipeline: PDF → Markdown → Giáo án → DOCX.
    
    Args:
        age:     Độ tuổi học sinh, ví dụ '3-4', '4-5', '5-6'
        dry_run: True = chỉ tạo file local, không upload Drive
    
    Returns:
        Log đầu ra của pipeline.
    """
    script = AGENTS / "run_pipeline.py"
    cmd    = [PYTHON, str(script), "--age", age]
    if dry_run:
        cmd.append("--dry-run")
    
    result = subprocess.run(
        cmd, cwd=str(WORKSPACE),
        capture_output=True, text=True, timeout=300
    )
    output = (result.stdout + result.stderr).strip()
    status = "SUCCESS" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
    return f"[{status}]\n\n{output}"


@mcp.tool()
def sync_to_google(age: str = "3-4") -> str:
    """
    Upload các file DOCX giáo án lên Google Drive và ghi hyperlink
    vào đúng ô trong Google Sheet lịch chương trình.
    
    Yêu cầu: token OAuth đã được lưu (.agents/token.pickle).
    Nếu chưa có token, chạy lần đầu sẽ mở trình duyệt để đăng nhập.
    
    Args:
        age: Độ tuổi, ví dụ '3-4' hoặc '5-6'
    
    Returns:
        Kết quả upload và các link Drive được tạo.
    """
    script = SCRIPTS / "sync_to_google.py"
    result = subprocess.run(
        [PYTHON, str(script), "--age", age],
        cwd=str(WORKSPACE),
        capture_output=True, text=True, timeout=300
    )
    output = (result.stdout + result.stderr).strip()
    status = "SUCCESS" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
    return f"[{status}]\n\n{output}"


@mcp.tool()
def list_output_files(age: str = "") -> str:
    """
    Liệt kê tất cả file DOCX giáo án đã được tạo trong thư mục Output.
    
    Args:
        age: Lọc theo độ tuổi (tùy chọn). Để trống = liệt kê tất cả.
    
    Returns:
        Danh sách file DOCX theo từng chủ đề/topic.
    """
    if not OUTPUT_FOLDER.exists():
        return "Thư mục Output chưa tồn tại. Chạy run_pipeline trước."
    
    docx_files = sorted(OUTPUT_FOLDER.rglob("*.docx"))
    if not docx_files:
        return "Chưa có file DOCX nào. Chạy run_pipeline để tạo giáo án."
    
    lines = [f"Tìm thấy {len(docx_files)} file DOCX:\n"]
    current_folder = None
    for f in docx_files:
        folder = f.parent.name
        if folder != current_folder:
            lines.append(f"\n📁 {folder}/")
            current_folder = folder
        lines.append(f"   • {f.name}  ({f.stat().st_size // 1024} KB)")
    
    return "\n".join(lines)


@mcp.tool()
def read_schedule() -> str:
    """
    Đọc file _schedule.json – lịch phân bổ học liệu theo tuần và môn học.
    Cho biết slot nào đã có tài liệu (OK) và slot nào còn thiếu (MISSING).
    
    Returns:
        Bảng lịch phân bổ dạng text.
    """
    sched_path = OUTPUT_FOLDER / "_schedule.json"
    if not sched_path.exists():
        return "Chưa có _schedule.json. Chạy run_pipeline để tạo."
    
    data     = json.loads(sched_path.read_text(encoding="utf-8"))
    age      = data.get("age", "?")
    schedule = data.get("schedule", [])
    
    lines = [f"Lịch phân bổ – Độ tuổi {age}\n", "=" * 50]
    lesson_ctrs = {}
    for i, slot in enumerate(schedule, 1):
        subj   = slot["subject"]
        week   = slot["week"]
        topic  = slot.get("topic", "?")
        status = slot["status"]
        source = slot.get("source") or "—"
        emoji  = "✅" if status == "OK" else "❌"
        
        if status == "OK":
            lesson_ctrs[subj] = lesson_ctrs.get(subj, 0) + 1
            n = lesson_ctrs[subj]
            file_label = f"Lesson {n}"
        else:
            file_label = "MISSING"
        
        lines.append(
            f"{emoji} Slot {i:2d} | {week} | {subj:<20} | {topic:<25} | "
            f"{file_label:<10} | source: {source}"
        )
    
    # Summary
    ok_count  = sum(1 for s in schedule if s["status"] == "OK")
    mis_count = len(schedule) - ok_count
    lines += [
        "=" * 50,
        f"✅ OK: {ok_count} tiết   ❌ MISSING: {mis_count} tiết"
    ]
    return "\n".join(lines)


@mcp.tool()
def read_weekly_syllabus() -> str:
    """
    Đọc file Weekly_Syllabus.md – bảng tổng kết lịch tuần dạng Markdown.
    
    Returns:
        Nội dung Weekly_Syllabus.md.
    """
    syllabus = OUTPUT_FOLDER / "Weekly_Syllabus.md"
    if not syllabus.exists():
        return "Chưa có Weekly_Syllabus.md. Chạy run_pipeline để tạo."
    return syllabus.read_text(encoding="utf-8")


@mcp.tool()
def list_input_files() -> str:
    """
    Liệt kê tất cả file học liệu đầu vào trong thư mục 'Nhập học liệu pdf và docs'.
    
    Returns:
        Danh sách file PDF/DOCX đầu vào và trạng thái đã được chuyển đổi chưa.
    """
    if not INPUT_FOLDER.exists():
        return f"Thư mục đầu vào không tìm thấy: {INPUT_FOLDER}"
    
    cache   = INPUT_FOLDER / "markdown_cache"
    cached  = {f.stem for f in cache.glob("*.md")} if cache.exists() else set()
    
    files   = [f for f in INPUT_FOLDER.iterdir()
               if f.is_file() and f.suffix.lower() in (".pdf", ".docx", ".pptx")]
    
    if not files:
        return "Thư mục đầu vào trống. Hãy thêm file PDF/DOCX vào thư mục."
    
    lines = [f"Học liệu đầu vào ({len(files)} file):\n"]
    for f in sorted(files):
        converted = "✅ đã convert" if f.stem in cached else "⏳ chưa convert"
        lines.append(f"  • {f.name}  ({f.stat().st_size // 1024} KB)  [{converted}]")
    
    return "\n".join(lines)


@mcp.tool()
def get_project_status() -> str:
    """
    Báo cáo tổng trạng thái toàn bộ dự án Lesson Plan Bot:
    - Số file học liệu đầu vào
    - Trạng thái pipeline (schedule.json)
    - Số DOCX đã tạo
    - Trạng thái OAuth token
    - Các đường dẫn chính
    
    Returns:
        Báo cáo trạng thái tổng thể.
    """
    lines = ["=" * 55, "  LESSON PLAN BOT – PROJECT STATUS", "=" * 55, ""]
    
    # 1. Input
    input_files = list(INPUT_FOLDER.glob("*.pdf")) + list(INPUT_FOLDER.glob("*.docx")) \
                  if INPUT_FOLDER.exists() else []
    cache       = INPUT_FOLDER / "markdown_cache"
    cached      = list(cache.glob("*.md")) if cache.exists() else []
    lines += [
        "📥 ĐẦUVÀO",
        f"   Học liệu: {len(input_files)} file(s) trong '{INPUT_FOLDER.name}'",
        f"   Đã convert sang Markdown: {len(cached)} file(s)",
        "",
    ]
    
    # 2. Schedule
    sched_path = OUTPUT_FOLDER / "_schedule.json"
    if sched_path.exists():
        data     = json.loads(sched_path.read_text(encoding="utf-8"))
        schedule = data.get("schedule", [])
        age      = data.get("age", "?")
        ok_count = sum(1 for s in schedule if s["status"] == "OK")
        mis      = len(schedule) - ok_count
        topics   = list({s.get("topic", "") for s in schedule if s.get("topic")})
        lines += [
            "📋 LỊCH PHÂN BỔ",
            f"   Độ tuổi: {age}",
            f"   Tổng slot: {len(schedule)}  ✅ OK: {ok_count}  ❌ MISSING: {mis}",
            f"   Chủ đề: {', '.join(topics)}",
            "",
        ]
    else:
        lines += ["📋 LỊCH PHÂN BỔ: Chưa có (chưa chạy pipeline)", ""]
    
    # 3. Output DOCX
    docx_files = list(OUTPUT_FOLDER.rglob("*.docx")) if OUTPUT_FOLDER.exists() else []
    lines += [
        "📄 GIÁO ÁN ĐẦU RA",
        f"   DOCX đã tạo: {len(docx_files)} file(s)",
    ]
    for f in sorted(docx_files):
        lines.append(f"   • {f.parent.name}/{f.name}")
    lines.append("")
    
    # 4. Auth
    token_pickle = AGENTS / "token.pickle"
    token_json   = AGENTS / "token.json"
    if token_pickle.exists():
        token_status = "✅ token.pickle (OAuth hoàn tất)"
    elif token_json.exists():
        token_status = "✅ token.json (OAuth hoàn tất)"
    else:
        token_status = "⚠️  Chưa có token – lần đầu sync sẽ mở browser đăng nhập"
    lines += [
        "🔐 GOOGLE AUTH",
        f"   {token_status}",
        "",
    ]
    
    # 5. Paths
    lines += [
        "📁 ĐƯỜNG DẪN",
        f"   Workspace: {WORKSPACE}",
        f"   Input:     {INPUT_FOLDER}",
        f"   Output:    {OUTPUT_FOLDER}",
        f"   Config:    {AGENTS / 'config.json'}",
        "=" * 55,
    ]
    
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
